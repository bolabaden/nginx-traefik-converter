from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

import yaml

from nginx_traefik_converter.generators.docker_compose import DockerComposeGenerator
from nginx_traefik_converter.generators.nginx_conf import NginxConfGenerator
from nginx_traefik_converter.generators.traefik_dynamic import TraefikDynamicGenerator
from nginx_traefik_converter.parsers.docker_compose import DockerComposeParser
from nginx_traefik_converter.parsers.nginx_conf import NginxConfParser
from nginx_traefik_converter.parsers.traefik_dynamic import TraefikDynamicParser

if TYPE_CHECKING:
    from pathlib import Path

    from nginx_traefik_converter.models.config import ProxyConfig

logger = logging.getLogger(__name__)


@dataclass
class ConversionResult:
    """Result of a configuration conversion."""

    config: ProxyConfig
    output_content: str
    format: str
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


class Parser(Protocol):
    """Parser protocol."""

    def parse(
        self,
        file_path: Path,
    ) -> ProxyConfig:
        """Parse configuration file."""
        ...


class ConfigGenerator(Protocol):
    """Config generator protocol."""

    def generate(self, config: ProxyConfig) -> str:
        """Generate configuration."""
        ...


class UniversalConverter:
    """Universal converter for nginx/Traefik configurations."""

    def __init__(self) -> None:
        self.parsers: dict[str, Parser] = {
            "docker-compose": DockerComposeParser(),
            "traefik-dynamic": TraefikDynamicParser(),
            "nginx-conf": NginxConfParser(),
        }

        self.generators: dict[str, ConfigGenerator] = {
            "traefik-dynamic": TraefikDynamicGenerator(),
            "nginx-conf": NginxConfGenerator(),
            "docker-compose": DockerComposeGenerator(),
        }

    def parse_config(
        self,
        input_file: Path,
        input_format: str | None = None,
    ) -> ProxyConfig:
        """Parse input configuration file."""
        if input_format is None:
            input_format = self._detect_format(input_file)

        if input_format not in self.parsers:
            msg = f"Unsupported input format: {input_format}"
            raise ValueError(msg)

        logger.info(f"Parsing {input_format} configuration from {input_file}")
        return self.parsers[input_format].parse(input_file)

    def generate_config(
        self,
        config: ProxyConfig,
        output_format: str,
    ) -> str:
        """Generate output configuration."""
        if output_format not in self.generators:
            msg = f"Unsupported output format: {output_format}"
            raise ValueError(msg)

        logger.info(f"Generating {output_format} configuration")
        return self.generators[output_format].generate(config)

    def validate_config(
        self,
        config_content: str,
        format: str,
    ) -> bool:
        """Validate generated configuration."""
        # Basic validation - in a real implementation, you'd want more sophisticated validation
        if format == "nginx-conf":
            return self._validate_nginx_config(config_content)
        if format == "traefik-dynamic":
            return self._validate_traefik_config(config_content)
        if format == "docker-compose":
            return self._validate_docker_compose_config(config_content)

        return True

    def convert(
        self,
        input_file: Path,
        output_format: str,
        input_format: str | None = None,
    ) -> ConversionResult:
        """Complete conversion process."""
        try:
            # Parse input
            config: ProxyConfig = self.parse_config(input_file, input_format)

            # Generate output
            output_content: str = self.generate_config(config, output_format)

            # Validate output
            is_valid: bool = self.validate_config(output_content, output_format)

            result: ConversionResult = ConversionResult(
                config=config,
                output_content=output_content,
                format=output_format,
            )

            if not is_valid:
                result.warnings.append("Generated configuration may have syntax errors")

            return result

        except Exception as e:
            logger.exception(f"Conversion failed: {e.__class__.__name__}: {e}")
            raise

    def _detect_format(self, file_path: Path) -> str:
        """Auto-detect configuration format based on file extension and content."""
        suffix: str = file_path.suffix.lower()

        if suffix in [".yml", ".yaml"]:
            # Try to read and detect based on content
            try:
                content: Any = yaml.safe_load(file_path.read_text(encoding="utf-8"))

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

    def _validate_nginx_config(
        self,
        config_content: str,
    ) -> bool:
        """Validate nginx configuration syntax."""
        try:
            # Basic nginx syntax validation
            # Check for common nginx directives
            required_patterns: list[str] = [
                r"server\s*\{",
                r"listen\s+\d+",
            ]

            for pattern in required_patterns:
                if not re.search(
                    pattern,
                    config_content,
                    re.IGNORECASE,
                ):
                    return False

            return True
        except Exception:
            return False

    def _validate_traefik_config(
        self,
        config_content: str,
    ) -> bool:
        """Validate Traefik configuration syntax."""
        try:
            # Try to parse as YAML/JSON
            yaml.safe_load(config_content)
            return True
        except Exception:
            return False

    def _validate_docker_compose_config(
        self,
        config_content: str,
    ) -> bool:
        """Validate Docker Compose configuration syntax."""
        try:
            # Try to parse as YAML
            yaml.safe_load(config_content)
            return True
        except Exception:
            return False
