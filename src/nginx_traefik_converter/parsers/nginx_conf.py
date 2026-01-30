from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import TYPE_CHECKING

from nginx_traefik_converter.models.config import (
    LoadBalancerType,
    ProxyConfig,
    Route,
    Service,
)

if TYPE_CHECKING:
    import os

logger = logging.getLogger(__name__)


class NginxConfParser:
    """Parser for nginx configuration files."""

    def parse(
        self,
        file_path: os.PathLike | str,
    ) -> ProxyConfig:
        """Parse nginx configuration file."""
        config = ProxyConfig()

        try:
            content: str = Path(file_path).read_text(encoding="utf-8")

            # Parse upstream blocks
            self._parse_upstreams(config, content)

            # Parse server blocks
            self._parse_server_blocks(config, content)

        except Exception as e:
            logger.exception(f"Error parsing nginx configuration: {e.__class__.__name__}: {e}")
            raise

        return config

    def _parse_upstreams(
        self,
        config: ProxyConfig,
        content: str,
    ) -> None:
        """Parse upstream blocks from nginx configuration."""
        upstream_pattern: str = r"upstream\s+(\w+)\s*\{([^}]+)\}"

        for match in re.finditer(
            upstream_pattern,
            content,
            re.MULTILINE | re.DOTALL,
        ):
            upstream_name: str = match.group(1)
            upstream_content: str = match.group(2)

            service = Service(name=upstream_name)

            # Parse server directives
            server_pattern: str = r"server\s+([^;]+);"
            for server_match in re.finditer(server_pattern, upstream_content):
                server_line: str = server_match.group(1).strip()

                # Extract server address and port
                if ":" in server_line:
                    server_parts: list[str] = server_line.split(":")
                    server: str = server_parts[0].strip()
                    port_part: str = server_parts[1].strip()

                    # Extract port number
                    port_match: re.Match[str] | None = re.search(r"(\d+)", port_part)
                    if port_match:
                        service.port = int(port_match.group(1))

                    service.servers.append(server)
                else:
                    service.servers.append(server_line)

            # Parse load balancing method
            if "least_conn" in upstream_content:
                service.load_balancer = LoadBalancerType.LEAST_CONN
            elif "ip_hash" in upstream_content:
                service.load_balancer = LoadBalancerType.IP_HASH

            config.add_service(service)

    def _parse_server_blocks(
        self,
        config: ProxyConfig,
        content: str,
    ) -> None:
        """Parse server blocks from nginx configuration."""
        server_pattern: str = r"server\s*\{([^}]+)\}"

        for match in re.finditer(server_pattern, content, re.MULTILINE | re.DOTALL):
            server_content: str = match.group(1)

            route = Route()

            # Parse server_name
            server_name_match: re.Match[str] | None = re.search(
                r"server_name\s+([^;]+);",
                server_content,
            )
            if server_name_match:
                server_names: list[str] = server_name_match.group(1).strip().split()
                if server_names:
                    route.host = server_names[0]  # Take the first server name

            # Parse listen directive
            listen_match: re.Match[str] | None = re.search(
                r"listen\s+([^;]+);",
                server_content,
            )
            if listen_match:
                listen_directive: str = listen_match.group(1).strip()
                if "ssl" in listen_directive:
                    route.tls = True

            # Parse location blocks
            self._parse_location_blocks(route, server_content)

            # Parse client IP restrictions
            allow_match: re.Match[str] | None = re.search(
                r"allow\s+([^;]+);",
                server_content,
            )
            if allow_match:
                route.client_ip = allow_match.group(1).strip()

            config.add_route(route)

    def _parse_location_blocks(
        self,
        route: Route,
        server_content: str,
    ) -> None:
        """Parse location blocks within a server block."""
        location_pattern: str = r"location\s+([^{]+)\s*\{([^}]+)\}"

        for match in re.finditer(
            location_pattern,
            server_content,
            re.MULTILINE | re.DOTALL,
        ):
            location_match: str = match.group(1).strip()
            location_content: str = match.group(2)

            # Parse location path
            if location_match.startswith("~"):
                # Regex location
                route.path = location_match
            elif location_match.startswith("="):
                # Exact location
                route.path = location_match[1:]
            else:
                # Prefix location
                route.path_prefix = location_match

            # Parse proxy_pass
            proxy_pass_match: re.Match[str] | None = re.search(
                r"proxy_pass\s+([^;]+);",
                location_content,
            )
            if proxy_pass_match:
                proxy_pass: str = proxy_pass_match.group(1).strip()

                # Extract service name from proxy_pass
                if proxy_pass.startswith("http://"):
                    service_name: str = proxy_pass[7:]  # Remove 'http://'
                    if ":" in service_name:
                        service_name: str = service_name.split(":")[0]
                    route.service = service_name
                elif proxy_pass.startswith("https://"):
                    service_name: str = proxy_pass[8:]  # Remove 'https://'
                    if ":" in service_name:
                        service_name: str = service_name.split(":")[0]
                    route.service = service_name
                    route.tls = True
                else:
                    route.service = proxy_pass

            # Parse method restrictions
            method_match: re.Match[str] | None = re.search(
                r"if\s*\(\s*\$request_method\s*!~\s*\^\(([^)]+)\)",
                location_content,
            )
            if method_match:
                route.method = method_match.group(1).replace("|", ",")

            # Parse header checks
            header_pattern: str = r'if\s*\(\s*\$http_([^)]+)\s*!=\s*"([^"]+)"'
            for header_match in re.finditer(header_pattern, location_content):
                header_name: str = header_match.group(1).replace("_", "-")
                header_value: str = header_match.group(2)
                route.headers[header_name] = header_value

            # Parse query parameter checks
            query_pattern: str = r'if\s*\(\s*\$arg_([^)]+)\s*!=\s*"([^"]+)"'
            for query_match in re.finditer(query_pattern, location_content):
                param_name: str = query_match.group(1)
                param_value: str = query_match.group(2)
                route.query_params[param_name] = param_value
