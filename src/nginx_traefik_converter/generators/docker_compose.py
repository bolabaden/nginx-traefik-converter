from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from nginx_traefik_converter.models.config import ProxyConfig

logger = logging.getLogger(__name__)


class DockerComposeGenerator:
    """Generator for Docker Compose with Traefik labels."""

    def generate(self, config: ProxyConfig) -> str:
        """Generate Docker Compose configuration with Traefik labels."""
        compose_config = {
            "version": "3.8",
            "services": {},
        }

        # Generate services from routes and services
        for route in config.routes:
            if route.service:
                service_name = route.service

                # Find corresponding service
                service = config.get_service_by_name(service_name)
                if service:
                    compose_config["services"][service_name] = (
                        self._generate_service_config(service, route)
                    )

        # Add services that don't have routes
        for service in config.services:
            if service.name not in compose_config["services"]:
                compose_config["services"][service.name] = (
                    self._generate_service_config(service, None)
                )

        return yaml.dump(compose_config, default_flow_style=False, sort_keys=False)

    def _generate_service_config(
        self,
        service: Any,
        route: Any | None,
    ) -> dict[str, Any]:
        """Generate service configuration for Docker Compose."""
        service_config = {
            "image": f"{service.name}:latest",  # Default image
            "labels": [],
        }

        # Add Traefik labels
        if route:
            # Enable Traefik
            service_config["labels"].append("traefik.enable=true")

            # Router labels
            router_name = route.name or f"{service.name}-router"
            service_config["labels"].append(
                f"traefik.http.routers.{router_name}.rule={route.to_traefik_rule()}",
            )

            # Service labels
            service_config["labels"].append(
                f"traefik.http.services.{service.name}.loadbalancer.server.port={service.port}",
            )

            # TLS labels
            if route.tls:
                service_config["labels"].append(
                    f"traefik.http.routers.{router_name}.tls=true",
                )
                if route.cert_resolver:
                    service_config["labels"].append(
                        f"traefik.http.routers.{router_name}.tls.certresolver={route.cert_resolver}",
                    )

            # Middleware labels
            if route.middlewares:
                service_config["labels"].append(
                    f"traefik.http.routers.{router_name}.middlewares={','.join(route.middlewares)}",
                )

            # Priority labels
            if route.priority > 0:
                service_config["labels"].append(
                    f"traefik.http.routers.{router_name}.priority={route.priority}",
                )

        # Add port mapping
        service_config["ports"] = [f"{service.port}:{service.port}"]

        return service_config
