from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import yaml

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of configuration validation."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class ConfigValidator:
    """Validator for various configuration formats."""

    def validate_file(
        self,
        file_path: Path,
        format: str | None = None,
    ) -> ValidationResult:
        """Validate a configuration file."""
        result = ValidationResult(valid=True)

        try:
            if format == "nginx-conf":
                return self._validate_nginx_config(file_path)
            if format == "traefik-dynamic":
                return self._validate_traefik_config(file_path)
            if format == "docker-compose":
                return self._validate_docker_compose_config(file_path)
            # Auto-detect format
            format = self._detect_format(file_path)
            return self.validate_file(file_path, format)

        except Exception as e:
            result.valid = False
            result.errors.append(f"Validation failed: {e}")

        return result

    def _validate_nginx_config(self, file_path: Path) -> ValidationResult:
        """Validate nginx configuration syntax."""
        result = ValidationResult(valid=True)

        try:
            with open(file_path) as f:
                content = f.read()

            # Basic nginx syntax validation
            required_patterns = [
                r"server\s*\{",
                r"listen\s+\d+",
            ]

            for pattern in required_patterns:
                if not re.search(pattern, content, re.IGNORECASE):
                    result.warnings.append(
                        f"Missing required nginx directive: {pattern}",
                    )

            # Check for common nginx syntax errors
            if "server {" in content and "}" not in content:
                result.errors.append("Unclosed server block")

            if "location " in content and "proxy_pass" not in content:
                result.warnings.append("Location block without proxy_pass directive")

        except Exception as e:
            result.valid = False
            result.errors.append(f"Error reading nginx config: {e}")

        return result

    def _validate_traefik_config(self, file_path: Path) -> ValidationResult:
        """Validate Traefik configuration syntax."""
        result = ValidationResult(valid=True)

        try:
            with open(file_path) as f:
                content = yaml.safe_load(f)

            if not isinstance(content, dict):
                result.errors.append("Configuration must be a YAML object")
                result.valid = False
                return result

            # Validate HTTP section
            if "http" in content:
                http_config = content["http"]
                if not isinstance(http_config, dict):
                    result.errors.append("HTTP section must be an object")
                    result.valid = False
                else:
                    # Validate routers
                    if "routers" in http_config:
                        routers = http_config["routers"]
                        if not isinstance(routers, dict):
                            result.errors.append("Routers must be an object")
                            result.valid = False
                        else:
                            for router_name, router_config in routers.items():
                                if not isinstance(router_config, dict):
                                    result.errors.append(
                                        f"Router {router_name} must be an object",
                                    )
                                    result.valid = False
                                elif "rule" not in router_config:
                                    result.warnings.append(
                                        f"Router {router_name} missing rule",
                                    )

                    # Validate services
                    if "services" in http_config:
                        services = http_config["services"]
                        if not isinstance(services, dict):
                            result.errors.append("Services must be an object")
                            result.valid = False
                        else:
                            for service_name, service_config in services.items():
                                if not isinstance(service_config, dict):
                                    result.errors.append(
                                        f"Service {service_name} must be an object",
                                    )
                                    result.valid = False
                                elif "loadBalancer" not in service_config:
                                    result.warnings.append(
                                        f"Service {service_name} missing loadBalancer",
                                    )

            # Validate TLS section
            if "tls" in content:
                tls_config = content["tls"]
                if not isinstance(tls_config, dict):
                    result.errors.append("TLS section must be an object")
                    result.valid = False

        except yaml.YAMLError as e:
            result.valid = False
            result.errors.append(f"YAML syntax error: {e.__class__.__name__}: {e}")
        except Exception as e:
            result.valid = False
            result.errors.append(
                f"Error reading Traefik config: {e.__class__.__name__}: {e}",
            )

        return result

    def _validate_docker_compose_config(self, file_path: Path) -> ValidationResult:
        """Validate Docker Compose configuration syntax."""
        result = ValidationResult(valid=True)

        try:
            with open(file_path) as f:
                content = yaml.safe_load(f)

            if not isinstance(content, dict):
                result.errors.append("Configuration must be a YAML object")
                result.valid = False
                return result

            # Validate services section
            if "services" not in content:
                result.errors.append("Missing services section")
                result.valid = False
            else:
                services = content["services"]
                if not isinstance(services, dict):
                    result.errors.append("Services must be an object")
                    result.valid = False
                else:
                    for service_name, service_config in services.items():
                        if not isinstance(service_config, dict):
                            result.errors.append(
                                f"Service {service_name} must be an object",
                            )
                            result.valid = False
                        else:
                            # Validate Traefik labels
                            labels = service_config.get("labels", [])
                            if isinstance(labels, list):
                                for label in labels:
                                    if isinstance(label, str) and label.startswith(
                                        "traefik.",
                                    ):
                                        # Basic Traefik label validation
                                        if "=" not in label:
                                            result.warnings.append(
                                                f"Invalid Traefik label format: {label}",
                                            )

        except yaml.YAMLError as e:
            result.valid = False
            result.errors.append(f"YAML syntax error: {e.__class__.__name__}: {e}")
        except Exception as e:
            result.valid = False
            result.errors.append(
                f"Error reading Docker Compose config: {e.__class__.__name__}: {e}",
            )

        return result

    def _detect_format(self, file_path: Path) -> str:
        """Auto-detect configuration format based on file extension and content."""
        suffix = file_path.suffix.lower()

        if suffix in [".yml", ".yaml"]:
            # Try to read and detect based on content
            try:
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
        elif suffix == ".json":
            return "traefik-dynamic"  # Assume Traefik JSON format
        elif suffix == ".toml":
            return "traefik-dynamic"  # Assume Traefik TOML format

        # Default to docker-compose for unknown formats
        return "docker-compose"
