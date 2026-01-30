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

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


class TraefikDynamicParser:
    """Parser for Traefik dynamic configuration files."""

    def parse(self, file_path: Path) -> ProxyConfig:
        """Parse Traefik dynamic configuration file."""
        config = ProxyConfig()

        try:
            with open(file_path) as f:
                traefik_data = yaml.safe_load(f)

            # Parse HTTP configuration
            if "http" in traefik_data:
                self._parse_http_config(config, traefik_data["http"])

            # Parse TCP configuration
            if "tcp" in traefik_data:
                self._parse_tcp_config(config, traefik_data["tcp"])

            # Parse TLS configuration
            if "tls" in traefik_data:
                config.tls_config = traefik_data["tls"]

        except Exception as e:
            logger.exception(f"Error parsing Traefik dynamic configuration: {e}")
            raise

        return config

    def _parse_http_config(
        self,
        config: ProxyConfig,
        http_data: dict[str, Any],
    ) -> None:
        """Parse HTTP configuration section."""
        # Parse routers
        if "routers" in http_data:
            for router_name, router_config in http_data["routers"].items():
                route = self._parse_router(router_name, router_config)
                config.add_route(route)

        # Parse services
        if "services" in http_data:
            for service_name, service_config in http_data["services"].items():
                service = self._parse_service(service_name, service_config)
                config.add_service(service)

        # Parse middlewares
        if "middlewares" in http_data:
            for middleware_name, middleware_config in http_data["middlewares"].items():
                middleware = self._parse_middleware(middleware_name, middleware_config)
                config.add_middleware(middleware)

    def _parse_tcp_config(self, config: ProxyConfig, tcp_data: dict[str, Any]) -> None:
        """Parse TCP configuration section."""
        # Parse TCP routers
        if "routers" in tcp_data:
            for router_name, router_config in tcp_data["routers"].items():
                route = self._parse_tcp_router(router_name, router_config)
                config.add_route(route)

        # Parse TCP services
        if "services" in tcp_data:
            for service_name, service_config in tcp_data["services"].items():
                service = self._parse_tcp_service(service_name, service_config)
                config.add_service(service)

    def _parse_router(self, name: str, router_config: dict[str, Any]) -> Route:
        """Parse HTTP router configuration."""
        route = Route(name=name)

        # Parse rule
        if "rule" in router_config:
            from nginx_traefik_converter.parsers.traefik_rule_parser import (
                TraefikRuleParser,
            )

            parsed_route = TraefikRuleParser.parse_rule(router_config["rule"])
            route.host = parsed_route.host
            route.path = parsed_route.path
            route.path_prefix = parsed_route.path_prefix
            route.method = parsed_route.method
            route.headers = parsed_route.headers
            route.query_params = parsed_route.query_params
            route.client_ip = parsed_route.client_ip

        # Parse service
        if "service" in router_config:
            route.service = router_config["service"]

        # Parse middlewares
        if "middlewares" in router_config:
            middlewares = router_config["middlewares"]
            if isinstance(middlewares, list):
                route.middlewares = middlewares
            elif isinstance(middlewares, str):
                route.middlewares = [middlewares]

        # Parse TLS
        if "tls" in router_config:
            route.tls = True
            if (
                isinstance(router_config["tls"], dict)
                and "certResolver" in router_config["tls"]
            ):
                route.cert_resolver = router_config["tls"]["certResolver"]

        # Parse priority
        if "priority" in router_config:
            route.priority = int(router_config["priority"])

        # Parse entry points
        if "entryPoints" in router_config:
            entry_points = router_config["entryPoints"]
            if isinstance(entry_points, list):
                route.entry_points = entry_points
            elif isinstance(entry_points, str):
                route.entry_points = [entry_points]

        return route

    def _parse_tcp_router(self, name: str, router_config: dict[str, Any]) -> Route:
        """Parse TCP router configuration."""
        route = Route(name=name)

        # Parse rule
        if "rule" in router_config:
            from nginx_traefik_converter.parsers.traefik_rule_parser import (
                TraefikRuleParser,
            )

            parsed_route = TraefikRuleParser.parse_rule(router_config["rule"])
            route.host = parsed_route.host
            route.client_ip = parsed_route.client_ip

        # Parse service
        if "service" in router_config:
            route.service = router_config["service"]

        # Parse TLS
        if "tls" in router_config:
            route.tls = True

        return route

    def _parse_service(self, name: str, service_config: dict[str, Any]) -> Service:
        """Parse HTTP service configuration."""
        service = Service(name=name)

        if "loadBalancer" in service_config:
            lb_config = service_config["loadBalancer"]

            # Parse servers
            if "servers" in lb_config:
                servers = lb_config["servers"]
                if isinstance(servers, list):
                    for server in servers:
                        if isinstance(server, dict) and "url" in server:
                            service.servers.append(server["url"])
                        elif isinstance(server, str):
                            service.servers.append(server)

            # Parse passHostHeader
            if "passHostHeader" in lb_config:
                # This would be handled in middleware conversion
                pass

            # Parse responseForwarding
            if "responseForwarding" in lb_config:
                # This would be handled in middleware conversion
                pass

        return service

    def _parse_tcp_service(self, name: str, service_config: dict[str, Any]) -> Service:
        """Parse TCP service configuration."""
        service = Service(name=name, protocol=Protocol.TCP)

        if "loadBalancer" in service_config:
            lb_config = service_config["loadBalancer"]

            # Parse servers
            if "servers" in lb_config:
                servers = lb_config["servers"]
                if isinstance(servers, list):
                    for server in servers:
                        if isinstance(server, dict) and "address" in server:
                            service.servers.append(server["address"])
                        elif isinstance(server, str):
                            service.servers.append(server)

        return service

    def _parse_middleware(
        self,
        name: str,
        middleware_config: dict[str, Any],
    ) -> Middleware:
        """Parse middleware configuration."""
        middleware = Middleware(name=name)

        # Determine middleware type and extract config
        for middleware_type, config in middleware_config.items():
            middleware.type = middleware_type
            middleware.config = config
            break  # Take the first middleware type

        return middleware
