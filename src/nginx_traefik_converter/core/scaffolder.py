from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from jinja2 import Template

from nginx_traefik_converter.parsers.docker_compose import DockerComposeParser
from nginx_traefik_converter.parsers.nginx_conf import NginxConfParser
from nginx_traefik_converter.parsers.traefik_dynamic import TraefikDynamicParser

if TYPE_CHECKING:
    from pathlib import Path

    from nginx_traefik_converter.models.config import ProxyConfig

logger = logging.getLogger(__name__)


class ConfigScaffolder:
    """Scaffolder for generating complete proxy setups."""

    def __init__(self) -> None:
        self.parsers: dict[str, Any] = {
            "docker-compose": DockerComposeParser(),
            "traefik-dynamic": TraefikDynamicParser(),
            "nginx-conf": NginxConfParser(),
        }

    def scaffold_project(
        self,
        input_file: Path,
        output_dir: Path,
        proxy_type: str,
        include_compose: bool = False,
        include_config: bool = False,
        include_docs: bool = False,
    ) -> dict[str, Any]:
        """Generate a complete proxy setup."""
        result: dict[str, Any] = {
            "success": True,
            "files": {},
            "errors": [],
            "warnings": [],
        }

        try:
            # Create output directory
            output_dir.mkdir(parents=True, exist_ok=True)

            # Parse input configuration
            config = self._parse_input_config(input_file)

            # Generate components based on flags
            if include_compose:
                self._generate_docker_compose(result, output_dir, config, proxy_type)

            if include_config:
                self._generate_proxy_config(result, output_dir, config, proxy_type)

            if include_docs:
                self._generate_documentation(result, output_dir, config, proxy_type)

            # Generate README
            self._generate_readme(result, output_dir, config, proxy_type)

        except Exception as e:
            logger.exception(f"Scaffolding failed: {e.__class__.__name__}: {e}")
            result["success"] = False
            result["errors"].append(str(e))

        return result

    def _parse_input_config(self, input_file: Path) -> ProxyConfig:
        """Parse input configuration file."""
        # Auto-detect format
        format = self._detect_format(input_file)

        if format not in self.parsers:
            msg = f"Unsupported input format: {format}"
            raise ValueError(msg)

        return self.parsers[format].parse(input_file)

    def _generate_docker_compose(
        self,
        result: dict[str, Any],
        output_dir: Path,
        config: ProxyConfig,
        proxy_type: str,
    ) -> None:
        """Generate docker-compose.yml."""
        try:
            if proxy_type == "traefik":
                compose_content = self._generate_traefik_compose(config)
            else:
                compose_content = self._generate_nginx_compose(config)

            compose_file = output_dir / "docker-compose.yml"
            compose_file.write_text(compose_content)
            result["files"][str(compose_file)] = True

        except Exception as e:
            result["files"][str(output_dir / "docker-compose.yml")] = False
            result["errors"].append(f"Failed to generate docker-compose.yml: {e}")

    def _generate_proxy_config(
        self,
        result: dict[str, Any],
        output_dir: Path,
        config: ProxyConfig,
        proxy_type: str,
    ) -> None:
        """Generate proxy configuration files."""
        try:
            if proxy_type == "traefik":
                config_content = self._generate_traefik_config(config)
                config_file = output_dir / "traefik-dynamic.yml"
            else:
                config_content = self._generate_nginx_config(config)
                config_file = output_dir / "nginx.conf"

            config_file.write_text(config_content)
            result["files"][str(config_file)] = True

        except Exception as e:
            config_file = output_dir / f"{proxy_type}-config"
            result["files"][str(config_file)] = False
            result["errors"].append(f"Failed to generate {proxy_type} config: {e}")

    def _generate_documentation(
        self,
        result: dict[str, Any],
        output_dir: Path,
        config: ProxyConfig,
        proxy_type: str,
    ) -> None:
        """Generate documentation."""
        try:
            docs_dir = output_dir / "docs"
            docs_dir.mkdir(exist_ok=True)

            # Generate setup guide
            setup_guide = self._generate_setup_guide(config, proxy_type)
            setup_file = docs_dir / "setup.md"
            setup_file.write_text(setup_guide)
            result["files"][str(setup_file)] = True

            # Generate configuration reference
            config_ref = self._generate_config_reference(config, proxy_type)
            ref_file = docs_dir / "configuration.md"
            ref_file.write_text(config_ref)
            result["files"][str(ref_file)] = True

        except Exception as e:
            result["errors"].append(f"Failed to generate documentation: {e}")

    def _generate_readme(
        self,
        result: dict[str, Any],
        output_dir: Path,
        config: ProxyConfig,
        proxy_type: str,
    ) -> None:
        """Generate README.md."""
        try:
            readme_content = self._generate_readme_content(config, proxy_type)
            readme_file = output_dir / "README.md"
            readme_file.write_text(readme_content)
            result["files"][str(readme_file)] = True

        except Exception as e:
            result["files"][str(output_dir / "README.md")] = False
            result["errors"].append(f"Failed to generate README.md: {e}")

    def _generate_traefik_compose(self, config: ProxyConfig) -> str:
        """Generate Traefik docker-compose.yml."""
        compose_template = """
version: '3.8'

services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.email=your-email@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
    ports:
      - "80:80"
      - "443:443"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./letsencrypt:/letsencrypt
    networks:
      - traefik

{% for service in services %}
  {{ service.name }}:
    image: {{ service.name }}:latest
    container_name: {{ service.name }}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.{{ service.name }}.rule=Host(`{{ service.name }}.localhost`)"
      - "traefik.http.services.{{ service.name }}.loadbalancer.server.port={{ service.port }}"
    networks:
      - traefik
{% endfor %}

networks:
  traefik:
    external: true
"""

        template = Template(compose_template)
        return template.render(services=config.services)

    def _generate_nginx_compose(self, config: ProxyConfig) -> str:
        """Generate nginx docker-compose.yml."""
        compose_template = """
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    container_name: nginx
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    networks:
      - nginx

{% for service in services %}
  {{ service.name }}:
    image: {{ service.name }}:latest
    container_name: {{ service.name }}
    networks:
      - nginx
{% endfor %}

networks:
  nginx:
    external: true
"""

        template = Template(compose_template)
        return template.render(services=config.services)

    def _generate_traefik_config(self, config: ProxyConfig) -> str:
        """Generate Traefik dynamic configuration."""
        from nginx_traefik_converter.generators.traefik_dynamic import (
            TraefikDynamicGenerator,
        )

        generator = TraefikDynamicGenerator()
        return generator.generate(config)

    def _generate_nginx_config(self, config: ProxyConfig) -> str:
        """Generate nginx configuration."""
        from nginx_traefik_converter.generators.nginx_conf import NginxConfGenerator

        generator = NginxConfGenerator()
        return generator.generate(config)

    def _generate_setup_guide(
        self,
        config: ProxyConfig,
        proxy_type: str,
    ) -> str:
        """Generate setup guide."""
        if proxy_type == "traefik":
            return self._generate_traefik_setup_guide(config)
        return self._generate_nginx_setup_guide(config)

    def _generate_traefik_setup_guide(
        self,
        config: ProxyConfig,
    ) -> str:
        """Generate Traefik setup guide."""
        return f"""# Traefik Setup Guide

## Prerequisites
- Docker and Docker Compose installed
- Domain name pointing to your server (for SSL certificates)

## Quick Start

1. **Update configuration**:
   - Edit `docker-compose.yml` and update the email address in the Traefik service
   - Update service hostnames in the labels

2. **Create external network**:
   ```bash
   docker network create traefik
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Access Traefik dashboard**:
   - Open http://localhost:8080 in your browser

## Configuration Details

- **Total Routes**: {len(config.routes)}
- **Total Services**: {len(config.services)}
- **Total Middlewares**: {len(config.middlewares)}

## SSL Certificates

Traefik will automatically obtain SSL certificates from Let's Encrypt for your domains.
Certificates are stored in the `./letsencrypt` directory.

## Troubleshooting

- Check logs: `docker-compose logs traefik`
- Verify network: `docker network ls`
- Check certificate status in Traefik dashboard
"""

    def _generate_nginx_setup_guide(self, config: ProxyConfig) -> str:
        """Generate nginx setup guide."""
        return f"""# Nginx Setup Guide

## Prerequisites
- Docker and Docker Compose installed
- SSL certificates (if using HTTPS)

## Quick Start

1. **Update configuration**:
   - Edit `nginx.conf` to match your requirements
   - Place SSL certificates in `./certs` directory

2. **Create external network**:
   ```bash
   docker network create nginx
   ```

3. **Start services**:
   ```bash
   docker-compose up -d
   ```

4. **Test configuration**:
   ```bash
   docker-compose exec nginx nginx -t
   ```

## Configuration Details

- **Total Routes**: {len(config.routes)}
- **Total Services**: {len(config.services)}
- **Total Middlewares**: {len(config.middlewares)}

## SSL Certificates

Place your SSL certificates in the `./certs` directory:
- Certificate: `./certs/yourdomain.crt`
- Private key: `./certs/yourdomain.key`

## Troubleshooting

- Check logs: `docker-compose logs nginx`
- Verify configuration: `docker-compose exec nginx nginx -t`
- Reload configuration: `docker-compose exec nginx nginx -s reload`
"""

    def _generate_config_reference(self, config: ProxyConfig, proxy_type: str) -> str:
        """Generate configuration reference."""
        return f"""# Configuration Reference

## Overview

This {proxy_type} configuration was generated from the input configuration.

## Routes

{{% for route in config.routes %}}
### Route: {{ route.name or loop.index }}
- **Host**: {{ route.host or 'default' }}
- **Path**: {{ route.path_prefix or route.path or '/' }}
- **Service**: {{ route.service or 'none' }}
- **TLS**: {{ 'Yes' if route.tls else 'No' }}
- **Middlewares**: {{ route.middlewares|join(', ') if route.middlewares else 'None' }}

{{% endfor %}}

## Services

{{% for service in config.services %}}
### Service: {{ service.name }}
- **Protocol**: {{ service.protocol.value }}
- **Port**: {{ service.port }}
- **Servers**: {{ service.servers|join(', ') }}
- **Load Balancer**: {{ service.load_balancer.value }}

{{% endfor %}}

## Middlewares

{{% for middleware in config.middlewares.values() %}}
### Middleware: {{ middleware.name }}
- **Type**: {{ middleware.type }}
- **Configuration**: {{ middleware.config }}

{{% endfor %}}
"""

    def _generate_readme_content(
        self,
        config: ProxyConfig,
        proxy_type: str,
    ) -> str:
        """Generate README content."""
        return f"""# {proxy_type.title()} Proxy Setup

This directory contains a complete {proxy_type} proxy setup generated from your configuration.

## Quick Start

1. **Review the configuration**:
   - `docker-compose.yml` - Container orchestration
   - `{"traefik-dynamic.yml" if proxy_type == "traefik" else "nginx.conf"}` - Proxy configuration
   - `docs/` - Documentation and setup guides

2. **Follow the setup guide**:
   - See `docs/setup.md` for detailed instructions

3. **Start the services**:
   ```bash
   docker-compose up -d
   ```

## Configuration Summary

- **Total Routes**: {len(config.routes)}
- **Total Services**: {len(config.services)}
- **Total Middlewares**: {len(config.middlewares)}

## Files

- `docker-compose.yml` - Docker Compose configuration
- `{"traefik-dynamic.yml" if proxy_type == "traefik" else "nginx.conf"}` - Proxy configuration
- `docs/setup.md` - Setup instructions
- `docs/configuration.md` - Configuration reference
- `README.md` - This file

## Support

For issues and questions, refer to the documentation in the `docs/` directory.
"""

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
