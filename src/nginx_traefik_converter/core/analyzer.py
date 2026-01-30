from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from nginx_traefik_converter.parsers.docker_compose import DockerComposeParser
from nginx_traefik_converter.parsers.nginx_conf import NginxConfParser
from nginx_traefik_converter.parsers.traefik_dynamic import TraefikDynamicParser

if TYPE_CHECKING:
    from pathlib import Path

    from nginx_traefik_converter.models.config import ProxyConfig

logger = logging.getLogger(__name__)


class ConfigAnalyzer:
    """Analyzer for configuration files."""

    def __init__(self) -> None:
        self.parsers: dict[str, Any] = {
            "docker-compose": DockerComposeParser(),
            "traefik-dynamic": TraefikDynamicParser(),
            "nginx-conf": NginxConfParser(),
        }

    def analyze_config(
        self,
        file_path: Path,
        format: str | None = None,
        detailed: bool = False,
    ) -> dict[str, Any]:
        """Analyze a configuration file and return detailed information."""
        analysis: dict[str, Any] = {}

        try:
            # Parse the configuration
            if format is None:
                format = self._detect_format(file_path)

            if format not in self.parsers:
                msg = f"Unsupported format: {format}"
                raise ValueError(msg)

            config = self.parsers[format].parse(file_path)

            # Basic analysis
            analysis["format"] = format
            analysis["file_path"] = str(file_path)
            analysis["total_routes"] = len(config.routes)
            analysis["total_services"] = len(config.services)
            analysis["total_middlewares"] = len(config.middlewares)

            if detailed:
                # Detailed analysis
                analysis["routes"] = self._analyze_routes(config.routes)
                analysis["services"] = self._analyze_services(config.services)
                analysis["middlewares"] = self._analyze_middlewares(config.middlewares)
                analysis["tls_config"] = self._analyze_tls_config(config.tls_config)
                analysis["entry_points"] = self._analyze_entry_points(
                    config.entry_points,
                )

            # Summary statistics
            analysis["summary"] = self._generate_summary(config)

        except Exception as e:
            logger.exception(f"Analysis failed: {e.__class__.__name__}: {e}")
            analysis["error"] = str(e)

        return analysis

    def _analyze_routes(
        self,
        routes: list[Any],
    ) -> dict[str, Any]:
        """Analyze routes in detail."""
        route_analysis: dict[str, Any] = {
            "by_host": {},
            "by_path": {},
            "with_tls": 0,
            "with_middlewares": 0,
            "by_priority": {},
        }

        for route in routes:
            # Count by host
            host = route.host or "default"
            route_analysis["by_host"][host] = route_analysis["by_host"].get(host, 0) + 1

            # Count by path
            path = route.path_prefix or route.path or "/"
            route_analysis["by_path"][path] = route_analysis["by_path"].get(path, 0) + 1

            # Count TLS routes
            if route.tls:
                route_analysis["with_tls"] += 1

            # Count routes with middlewares
            if route.middlewares:
                route_analysis["with_middlewares"] += 1

            # Count by priority
            priority = route.priority
            route_analysis["by_priority"][priority] = (
                route_analysis["by_priority"].get(priority, 0) + 1
            )

        return route_analysis

    def _analyze_services(
        self,
        services: list[Any],
    ) -> dict[str, Any]:
        """Analyze services in detail."""
        service_analysis: dict[str, Any] = {
            "by_protocol": {},
            "by_load_balancer": {},
            "total_servers": 0,
            "average_servers_per_service": 0,
        }

        total_servers = 0

        for service in services:
            # Count by protocol
            protocol = service.protocol.value
            service_analysis["by_protocol"][protocol] = (
                service_analysis["by_protocol"].get(protocol, 0) + 1
            )

            # Count by load balancer type
            lb_type = service.load_balancer.value
            service_analysis["by_load_balancer"][lb_type] = (
                service_analysis["by_load_balancer"].get(lb_type, 0) + 1
            )

            # Count total servers
            total_servers += len(service.servers)

        service_analysis["total_servers"] = total_servers
        if services:
            service_analysis["average_servers_per_service"] = total_servers / len(
                services,
            )

        return service_analysis

    def _analyze_middlewares(
        self,
        middlewares: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze middlewares in detail."""
        middleware_analysis: dict[str, Any] = {
            "by_type": {},
            "total_count": len(middlewares),
        }

        for middleware in middlewares.values():
            middleware_type = middleware.type
            middleware_analysis["by_type"][middleware_type] = (
                middleware_analysis["by_type"].get(middleware_type, 0) + 1
            )

        return middleware_analysis

    def _analyze_tls_config(
        self,
        tls_config: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyze TLS configuration."""
        return {
            "has_config": bool(tls_config),
            "config_keys": list(tls_config.keys()) if tls_config else [],
        }

    def _analyze_entry_points(
        self,
        entry_points: dict[str, str],
    ) -> dict[str, Any]:
        """Analyze entry points."""
        return {
            "count": len(entry_points),
            "names": list(entry_points.keys()),
            "addresses": list(entry_points.values()),
        }

    def _generate_summary(
        self,
        config: ProxyConfig,
    ) -> dict[str, Any]:
        """Generate a summary of the configuration."""
        summary: dict[str, Any] = {
            "complexity_score": self._calculate_complexity_score(config),
            "recommendations": self._generate_recommendations(config),
            "security_notes": self._generate_security_notes(config),
        }

        return summary

    def _calculate_complexity_score(
        self,
        config: ProxyConfig,
    ) -> int:
        """Calculate a complexity score from 1-10."""
        score = 1

        # Base score for having routes
        if config.routes:
            score += 2

        # Add points for number of routes
        if len(config.routes) > 5:
            score += 2
        elif len(config.routes) > 2:
            score += 1

        # Add points for number of services
        if len(config.services) > 3:
            score += 2
        elif len(config.services) > 1:
            score += 1

        # Add points for middlewares
        if config.middlewares:
            score += 1

        # Add points for TLS
        tls_routes = sum(1 for route in config.routes if route.tls)
        if tls_routes > 0:
            score += 1

        # Add points for complex routing rules
        complex_routes = sum(
            1
            for route in config.routes
            if route.headers or route.query_params or route.client_ip
        )
        if complex_routes > 0:
            score += 1

        return min(score, 10)

    def _generate_recommendations(
        self,
        config: ProxyConfig,
    ) -> list[str]:
        """Generate recommendations based on the configuration."""
        recommendations: list[str] = []

        # Check for missing TLS
        non_tls_routes = [
            route for route in config.routes if not route.tls and route.host
        ]
        if non_tls_routes:
            recommendations.append("Consider enabling TLS for production routes")

        # Check for missing middlewares
        routes_without_middlewares = [
            route for route in config.routes if not route.middlewares
        ]
        if routes_without_middlewares:
            recommendations.append(
                "Consider adding security middlewares (rate limiting, headers)",
            )

        # Check for load balancing
        single_server_services = [
            service for service in config.services if len(service.servers) == 1
        ]
        if single_server_services:
            recommendations.append(
                "Consider adding multiple servers for high availability",
            )

        return recommendations

    def _generate_security_notes(
        self,
        config: ProxyConfig,
    ) -> list[str]:
        """Generate security-related notes."""
        security_notes: list[str] = []

        # Check for client IP restrictions
        ip_restricted_routes = [route for route in config.routes if route.client_ip]
        if ip_restricted_routes:
            security_notes.append(
                f"{len(ip_restricted_routes)} routes have IP restrictions",
            )

        # Check for header-based security
        header_routes = [route for route in config.routes if route.headers]
        if header_routes:
            security_notes.append(
                f"{len(header_routes)} routes use header-based routing",
            )

        return security_notes

    def _detect_format(
        self,
        file_path: Path,
    ) -> str:
        """Auto-detect configuration format."""
        suffix = file_path.suffix.lower()

        if suffix in [".yml", ".yaml"]:
            # Try to read and detect based on content
            try:
                import yaml

                with open(file_path) as f:
                    content = yaml.safe_load(f)

                if isinstance(content, dict):
                    if "services" in content:
                        return "docker-compose"
                    if "http" in content or "tcp" in content:
                        return "traefik-dynamic"

                return "yaml"
            except Exception:
                return "yaml"

        elif suffix == ".conf":
            return "nginx-conf"
        elif suffix in {".json", ".toml"}:
            return "traefik-dynamic"

        return "docker-compose"
