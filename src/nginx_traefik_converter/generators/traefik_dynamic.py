from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from nginx_traefik_converter.models.config import ProxyConfig

logger = logging.getLogger(__name__)


class TraefikDynamicGenerator:
    """Generator for Traefik dynamic configuration."""

    def generate(self, config: ProxyConfig) -> str:
        """Generate Traefik dynamic configuration."""
        traefik_config = {
            "http": {
                "routers": {},
                "services": {},
                "middlewares": {},
            },
        }

        # Generate routers
        for route in config.routes:
            router_config = {}

            # Add rule
            if route.host or route.path or route.path_prefix:
                router_config["rule"] = route.to_traefik_rule()

            # Add service
            if route.service:
                router_config["service"] = route.service

            # Add middlewares
            if route.middlewares:
                router_config["middlewares"] = route.middlewares

            # Add TLS
            if route.tls:
                router_config["tls"] = {}
                if route.cert_resolver:
                    router_config["tls"]["certResolver"] = route.cert_resolver

            # Add priority
            if route.priority > 0:
                router_config["priority"] = route.priority

            # Add entry points
            if route.entry_points:
                router_config["entryPoints"] = route.entry_points

            traefik_config["http"]["routers"][
                route.name or f"router-{len(traefik_config['http']['routers'])}"
            ] = router_config

        # Generate services
        for service in config.services:
            service_config = {
                "loadBalancer": {
                    "servers": [],
                },
            }

            # Add servers
            for server in service.servers:
                if service.protocol.value == "https":
                    server_url = f"https://{server}"
                else:
                    server_url = f"http://{server}"

                if ":" not in server:
                    server_url += f":{service.port}"

                service_config["loadBalancer"]["servers"].append(
                    {
                        "url": server_url,
                    },
                )

            # Add passHostHeader if needed
            service_config["loadBalancer"]["passHostHeader"] = True

            traefik_config["http"]["services"][service.name] = service_config

        # Generate middlewares
        for middleware in config.middlewares.values():
            middleware_config = {}

            if middleware.type == "headers":
                middleware_config["headers"] = middleware.config
            elif middleware.type == "redirectRegex":
                middleware_config["redirectRegex"] = middleware.config
            elif middleware.type == "stripPrefix":
                middleware_config["stripPrefix"] = middleware.config
            else:
                middleware_config[middleware.type] = middleware.config

            traefik_config["http"]["middlewares"][middleware.name] = middleware_config

        # Add TLS configuration if present
        if config.tls_config:
            traefik_config["tls"] = config.tls_config

        return yaml.dump(traefik_config, default_flow_style=False, sort_keys=False)
