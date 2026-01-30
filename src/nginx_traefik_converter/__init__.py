"""Universal nginx/Traefik configuration converter.

A comprehensive tool for converting between nginx and Traefik configurations,
supporting multiple input/output formats and bidirectional conversion.
"""

__version__ = "1.0.0"
__author__ = "Your Name"
__description__ = "Universal nginx/Traefik configuration converter"

from .split_docker_compose_yaml import (
    ConfigFormat,
    ConfigGenerator,
    ConfigParser,
    ConfigValidator,
    ProxyConfig,
    ProxyType,
    Route,
    Service,
    TraefikRuleParser,
)

__all__ = [
    "ConfigFormat",
    "ConfigGenerator",
    "ConfigParser",
    "ConfigValidator",
    "ProxyConfig",
    "ProxyType",
    "Route",
    "Service",
    "TraefikRuleParser",
]
