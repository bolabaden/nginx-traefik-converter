from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import yaml

from nginx_traefik_converter.models.config import (
    Middleware,
    Protocol,
    ProxyConfig,
    Route,
    Service,
)
from nginx_traefik_converter.parsers.traefik_rule_parser import TraefikRuleParser

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class DockerComposeParser:
    """Parser for Docker Compose files with Traefik labels."""

    def parse(
        self,
        file_path: Path,
    ) -> ProxyConfig:
        """Parse docker-compose file with Traefik labels."""
        config = ProxyConfig()

        try:
            compose_data: dict[str, Any] = yaml.safe_load(
                file_path.read_text(
                    encoding="utf-8",
                    errors="strict",
                ),
            )

            services: dict[str, Any] = compose_data.get("services", {})

            for service_name, service_config in services.items():
                self._process_service(
                    config,
                    service_name,
                    service_config,
                )

        except Exception as e:
            logger.exception(f"Error parsing docker-compose file: {e.__class__.__name__}: {e}")
            raise

        return config

    def _process_service(
        self,
        config: ProxyConfig,
        service_name: str,
        service_config: dict[str, Any],
    ) -> None:
        """Process a single service from docker-compose."""
        labels: dict[str, str] = service_config.get("labels", {})

        # Convert labels list to dict if needed
        if isinstance(labels, list):
            # Convert list to dict
            label_dict: dict[str, str] = {}
            for label in labels:
                if "=" in label:
                    key, value = label.split("=", 1)
                    # Only casefold the key, preserve value case
                    label_dict[key.casefold()] = value
            labels = label_dict

        # Extract Traefik configuration
        traefik_labels: dict[str, str] = {
            k: v
            for k, v in labels.items()
            if k.casefold().startswith("traefik.")
        }

        if traefik_labels:
            self._process_traefik_labels(
                config,
                service_name,
                traefik_labels,
                service_config,
            )

    def _process_traefik_labels(
        self,
        config: ProxyConfig,
        service_name: str,
        labels: dict[str, str],
        service_config: dict[str, Any],
    ) -> None:
        """Process Traefik labels for a service."""
        # Extract routers - casefold keys, preserve values
        router_labels: dict[str, str] = {
            k.casefold(): v
            for k, v in labels.items()
            if k.casefold().startswith("traefik.routers.")
        }
        service_labels: dict[str, str] = {
            k.casefold(): v
            for k, v in labels.items()
            if k.casefold().startswith("traefik.services.")
        }
        middleware_labels: dict[str, str] = {
            k.casefold(): v
            for k, v in labels.items()
            if k.casefold().startswith("traefik.middlewares.")
        }

        # Group by router name
        routers: dict[str, dict[str, str]] = {}
        for label, value in router_labels.items():
            parts: list[str] = label.strip().split(".")
            if len(parts) >= 4:
                router_name: str = parts[3]
                property_name: str = ".".join(parts[4:])

                if router_name not in routers:
                    routers[router_name] = {}
                routers[router_name][property_name] = value.strip()

        # Create routes from routers
        for router_name, router_config in routers.items():
            route = Route(name=router_name)

            # Parse rule
            if "rule" in router_config:
                parsed_route: Route = TraefikRuleParser.parse_rule(router_config["rule"])
                route.host = parsed_route.host
                route.path = parsed_route.path
                route.path_prefix = parsed_route.path_prefix
                route.method = parsed_route.method
                route.headers = parsed_route.headers
                route.query_params = parsed_route.query_params
                route.client_ip = parsed_route.client_ip

            # Set priority
            if "priority" in router_config:
                route.priority = int(router_config["priority"])

            # Set TLS
            if (
                "tls" in router_config
                or "tls.certresolver" in router_config
            ):
                route.tls = True
                if "tls.certresolver" in router_config:
                    route.cert_resolver = router_config["tls.certresolver"]

            # Set middlewares
            if "middlewares" in router_config:
                route.middlewares = router_config["middlewares"].split(",")

            # Set service
            route.service = service_name

            config.add_route(route)

        # Create service
        service = Service(name=service_name)

        # Extract service configuration
        self._extract_service_config(
            service,
            service_labels,
            service_config,
        )

        config.add_service(service)

        # Process middlewares
        self._process_middlewares(
            config,
            middleware_labels,
        )

    def _extract_service_config(
        self,
        service: Service,
        service_labels: dict[str, str],
        service_config: dict[str, Any],
    ) -> None:
        """Extract service configuration from labels and service config."""
        # Extract service port
        for label, value in service_labels.items():
            if label.strip().endswith("loadbalancer.server.port"):
                service.port = int(value.strip())
            elif label.strip().endswith("loadbalancer.server.scheme"):
                if value.strip().casefold() == "https":
                    service.protocol = Protocol.HTTPS
                    service.tls = True

        # Extract from service config
        ports: list[Any] = service_config.get("ports", [])
        if ports:
            # Use first port mapping
            port_mapping: Any = ports[0]
            if isinstance(port_mapping, dict):
                service.port = int(port_mapping.get("target", 80))
            else:
                # Format: "8080:80" or "8080"
                port_mapping_str: str = str(port_mapping)
                if ":" in port_mapping_str:
                    _, container_port = port_mapping_str.strip().split(":", 1)
                    service.port = int(container_port)
                else:
                    service.port = int(port_mapping_str)

        # Add service IP (would need to be determined from container network)
        service.servers = [f"{service.name}"]  # Use service name as placeholder

    def _process_middlewares(
        self,
        config: ProxyConfig,
        middleware_labels: dict[str, str],
    ) -> None:
        """Process middleware configurations."""
        # Group by middleware name
        middlewares: dict[str, dict[str, str]] = {}
        for label, value in middleware_labels.items():
            parts: list[str] = label.strip().split(".")
            if len(parts) >= 4:
                middleware_name: str = parts[3]
                property_name: str = ".".join(parts[4:])

                if middleware_name not in middlewares:
                    middlewares[middleware_name] = {}
                middlewares[middleware_name][property_name] = value.strip()

        # Create middleware objects
        for middleware_name, middleware_config in middlewares.items():
            middleware = Middleware(name=middleware_name)

            # Determine middleware type and extract config
            if "headers.customrequestheaders" in middleware_config:
                middleware.type = "headers"
                middleware.config["customrequestheaders"] = self._parse_headers(middleware_config["headers.customrequestheaders"])
            elif "headers.customresponseheaders" in middleware_config:
                middleware.type = "headers"
                middleware.config["customresponseheaders"] = self._parse_headers(middleware_config["headers.customresponseheaders"])
            elif "redirectregex.regex" in middleware_config:
                middleware.type = "redirectregex"
                middleware.config["regex"] = middleware_config["redirectregex.regex"]
                if "redirectregex.replacement" in middleware_config:
                    middleware.config["replacement"] = middleware_config["redirectregex.replacement"]
            elif "stripprefix.prefixes" in middleware_config:
                middleware.type = "stripprefix"
                middleware.config["prefixes"] = middleware_config["stripprefix.prefixes"].split(",")  # type: ignore

            config.add_middleware(middleware)

    def _parse_headers(
        self,
        headers_str: str,
    ) -> dict[str, str]:
        """Parse headers string into dictionary."""
        headers: dict[str, str] = {}
        if not headers_str or not headers_str.strip():
            return {}
        for header in headers_str.strip().split(","):
            if "=" in header:
                key, value = header.strip().split("=", 1)
                headers[key.strip()] = value.strip()
        return headers
