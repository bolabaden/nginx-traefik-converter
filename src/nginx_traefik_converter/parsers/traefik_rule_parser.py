from __future__ import annotations

import logging
import re

from nginx_traefik_converter.models.config import Route

logger = logging.getLogger(__name__)


class TraefikRuleParser:
    """Parser for Traefik routing rules with full syntax support."""

    # Comprehensive Traefik rule patterns
    RULE_PATTERNS: dict[str, re.Pattern[str]] = {
        "host": re.compile(r"Host\(`([^`]+)`\)", re.IGNORECASE),
        "host_regexp": re.compile(r"HostRegexp\(`([^`]+)`\)", re.IGNORECASE),
        "path": re.compile(r"Path\(`([^`]+)`\)", re.IGNORECASE),
        "path_prefix": re.compile(r"PathPrefix\(`([^`]+)`\)", re.IGNORECASE),
        "path_regexp": re.compile(r"PathRegexp\(`([^`]+)`\)", re.IGNORECASE),
        "method": re.compile(r"Method\(`([^`]+)`\)", re.IGNORECASE),
        "header": re.compile(r"Header\(`([^`]+)`,\s*`([^`]+)`\)", re.IGNORECASE),
        "header_regexp": re.compile(r"HeaderRegexp\(`([^`]+)`,\s*`([^`]+)`\)", re.IGNORECASE),
        "query": re.compile(r"Query\(`([^`]+)`,\s*`([^`]+)`\)", re.IGNORECASE),
        "query_regexp": re.compile(r"QueryRegexp\(`([^`]+)`,\s*`([^`]+)`\)", re.IGNORECASE),
        "client_ip": re.compile(r"ClientIP\(`([^`]+)`\)", re.IGNORECASE),
        "host_sni": re.compile(r"HostSNI\(`([^`]+)`\)", re.IGNORECASE),
        "host_sni_regexp": re.compile(r"HostSNIRegexp\(`([^`]+)`\)", re.IGNORECASE),
        "alpn": re.compile(r"ALPN\(`([^`]+)`\)", re.IGNORECASE),
    }

    @classmethod
    def parse_rule(
        cls,
        rule_string: str,
    ) -> Route:
        """Parse a Traefik rule string into a Route object."""
        route = Route()

        # Handle logical operators by splitting on && and ||
        # For now, we'll take the first host and path we find
        # In a production system, you'd want more sophisticated parsing

        # Extract host
        host_match: re.Match[str] | None = cls.RULE_PATTERNS["host"].search(rule_string)
        if host_match:
            route.host = host_match.group(1)
        else:
            host_regexp_match: re.Match[str] | None = cls.RULE_PATTERNS["host_regexp"].search(rule_string)
            if host_regexp_match:
                route.host = host_regexp_match.group(1)

        # Extract path
        path_match: re.Match[str] | None = cls.RULE_PATTERNS["path"].search(rule_string)
        if path_match:
            route.path = path_match.group(1)
        else:
            path_prefix_match = cls.RULE_PATTERNS["path_prefix"].search(rule_string)
            if path_prefix_match:
                route.path_prefix = path_prefix_match.group(1)
            else:
                path_regexp_match = cls.RULE_PATTERNS["path_regexp"].search(rule_string)
                if path_regexp_match:
                    route.path = f"~ {path_regexp_match.group(1)}"

        # Extract method
        method_match: re.Match[str] | None = cls.RULE_PATTERNS["method"].search(rule_string)
        if method_match:
            route.method = method_match.group(1)

        # Extract headers
        for header_match in cls.RULE_PATTERNS["header"].finditer(rule_string):
            route.headers[header_match.group(1)] = header_match.group(2)

        # Extract query parameters
        for query_match in cls.RULE_PATTERNS["query"].finditer(rule_string):
            route.query_params[query_match.group(1)] = query_match.group(2)

        # Extract client IP
        client_ip_match = cls.RULE_PATTERNS["client_ip"].search(rule_string)
        if client_ip_match:
            route.client_ip = client_ip_match.group(1)

        return route

    @classmethod
    def parse_complex_rule(cls, rule_string: str) -> list[Route]:
        """Parse complex rules with logical operators into multiple routes."""
        routes: list[Route] = []

        # Split on logical OR (||)
        or_parts: list[str] = rule_string.split("||")

        for or_part in or_parts:
            # Split on logical AND (&&)
            and_parts: list[str] = or_part.split("&&")

            route = Route()

            for and_part in and_parts:
                and_part: str = and_part.strip()

                # Apply each pattern to this part
                cls._apply_patterns_to_route(route, and_part)

            if route.host or route.path or route.path_prefix:
                routes.append(route)

        return routes

    @classmethod
    def _apply_patterns_to_route(
        cls,
        route: Route,
        rule_part: str,
    ) -> None:
        """Apply all patterns to a route from a rule part."""
        # Extract host
        host_match: re.Match[str] | None = cls.RULE_PATTERNS["host"].search(rule_part)
        if host_match is not None:
            route.host = host_match.group(1)
        else:
            host_regexp_match: re.Match[str] | None = cls.RULE_PATTERNS["host_regexp"].search(rule_part)
            if host_regexp_match is not None:
                route.host = host_regexp_match.group(1)

        # Extract path
        path_match: re.Match[str] | None = cls.RULE_PATTERNS["path"].search(rule_part)
        if path_match is not None:
            route.path = path_match.group(1)
        else:
            path_prefix_match: re.Match[str] | None = cls.RULE_PATTERNS["path_prefix"].search(rule_part)
            if path_prefix_match is not None:
                route.path_prefix = path_prefix_match.group(1)
            else:
                path_regexp_match: re.Match[str] | None = cls.RULE_PATTERNS["path_regexp"].search(rule_part)
                if path_regexp_match is not None:
                    route.path = f"~ {path_regexp_match.group(1)}"

        # Extract method
        method_match: re.Match[str] | None = cls.RULE_PATTERNS["method"].search(rule_part)
        if method_match is not None:
            route.method = method_match.group(1)

        # Extract headers
        for header_match in cls.RULE_PATTERNS["header"].finditer(rule_part):
            route.headers[header_match.group(1)] = header_match.group(2)

        # Extract query parameters
        for query_match in cls.RULE_PATTERNS["query"].finditer(rule_part):
            route.query_params[query_match.group(1)] = query_match.group(2)

        # Extract client IP
        client_ip_match: re.Match[str] | None = cls.RULE_PATTERNS["client_ip"].search(rule_part)
        if client_ip_match is not None:
            route.client_ip = client_ip_match.group(1)
