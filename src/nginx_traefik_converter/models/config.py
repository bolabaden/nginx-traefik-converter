from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LoadBalancerType(Enum):
    """Load balancer types."""

    ROUND_ROBIN = "round_robin"
    LEAST_CONN = "least_conn"
    IP_HASH = "ip_hash"
    WEIGHTED = "weighted"


class Protocol(Enum):
    """Protocol types."""

    HTTP = "http"
    HTTPS = "https"
    TCP = "tcp"
    UDP = "udp"


@dataclass
class Route:
    """Represents a routing rule."""

    name: str = ""
    host: str = ""
    path: str = "/"
    path_prefix: str = ""
    method: str = ""
    headers: dict[str, str] = field(default_factory=dict)
    query_params: dict[str, str] = field(default_factory=dict)
    client_ip: str = ""
    priority: int = 0
    middlewares: list[str] = field(default_factory=list)
    tls: bool = False
    cert_resolver: str = ""
    service: str = ""
    entry_points: list[str] = field(default_factory=list)

    def to_nginx_location(self) -> str:
        """Convert route to nginx location block."""
        if self.path_prefix:
            return f"location {self.path_prefix}"
        if self.path and self.path != "/":
            if self.path.endswith("$"):
                return f"location ~ {self.path}"
            return f"location = {self.path}"
        return "location /"

    def to_traefik_rule(self) -> str:
        """Convert route to Traefik rule string."""
        conditions = []

        if self.host:
            conditions.append(f"Host(`{self.host}`)")

        if self.path_prefix:
            conditions.append(f"PathPrefix(`{self.path_prefix}`)")
        elif self.path and self.path != "/":
            conditions.append(f"Path(`{self.path}`)")

        if self.method:
            conditions.append(f"Method(`{self.method}`)")

        for header_name, header_value in self.headers.items():
            conditions.append(f"Header(`{header_name}`, `{header_value}`)")

        for param_name, param_value in self.query_params.items():
            conditions.append(f"Query(`{param_name}`, `{param_value}`)")

        if self.client_ip:
            conditions.append(f"ClientIP(`{self.client_ip}`)")

        return " && ".join(conditions) if conditions else "Host(`localhost`)"


@dataclass
class Service:
    """Represents a backend service."""

    name: str
    servers: list[str] = field(default_factory=list)
    port: int = 80
    protocol: Protocol = Protocol.HTTP
    health_check: str = ""
    load_balancer: LoadBalancerType = LoadBalancerType.ROUND_ROBIN
    weight: int = 1
    tls: bool = False
    tls_insecure: bool = False

    def to_nginx_upstream(self) -> str:
        """Convert service to nginx upstream block."""
        upstream_lines: list[str] = [f"upstream {self.name} {{"]

        # Add load balancing method if not round_robin
        if self.load_balancer == LoadBalancerType.LEAST_CONN:
            upstream_lines.append("    least_conn;")
        elif self.load_balancer == LoadBalancerType.IP_HASH:
            upstream_lines.append("    ip_hash;")

        # Add servers
        upstream_lines.extend(
            f"    server {server if ':' in server else f'{server}:{self.port}'};"
            for server in self.servers
        )

        upstream_lines.append("}")
        return "\n".join(upstream_lines)


@dataclass
class Middleware:
    """Represents a middleware configuration."""

    name: str
    type: str = ""
    config: dict[str, Any] = field(default_factory=dict)

    def to_traefik_config(self) -> dict[str, Any]:
        """Convert middleware to Traefik configuration."""
        return {self.name: {self.type: self.config}}


@dataclass
class ProxyConfig:
    """Main configuration container."""

    routes: list[Route] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    middlewares: dict[str, Middleware] = field(default_factory=dict)
    tls_config: dict[str, Any] = field(default_factory=dict)
    entry_points: dict[str, str] = field(default_factory=dict)
    version: str = "3.0"

    def add_route(self, route: Route) -> None:
        """Add a route to the configuration."""
        self.routes.append(route)

    def add_service(self, service: Service) -> None:
        """Add a service to the configuration."""
        self.services.append(service)

    def add_middleware(self, middleware: Middleware) -> None:
        """Add a middleware to the configuration."""
        self.middlewares[middleware.name] = middleware

    def get_service_by_name(self, name: str) -> Service | None:
        """Get a service by name."""
        for service in self.services:
            if service.name == name:
                return service
        return None

    def get_route_by_name(self, name: str) -> Route | None:
        """Get a route by name."""
        for route in self.routes:
            if route.name == name:
                return route
        return None
