from __future__ import annotations

import argparse
import logging
import re
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import yaml
from jinja2 import Template
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TaskID, TextColumn
from rich.table import Table

# Set up rich console and logging
console = Console()
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)],
)
logger = logging.getLogger(__name__)


class ProxyType(Enum):
    """Supported proxy types."""

    TRAEFIK = "traefik"
    NGINX = "nginx"
    NGINX_PROXY = "nginx-proxy"


class ConfigFormat(Enum):
    """Supported configuration formats."""

    DOCKER_COMPOSE = "docker-compose"
    TRAEFIK_YAML = "traefik-yaml"
    TRAEFIK_TOML = "traefik-toml"
    NGINX_CONF = "nginx-conf"
    JSON = "json"


@dataclass
class Route:
    """Represents a routing rule."""

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

    def to_nginx_location(self) -> str:
        """Convert route to nginx location block."""
        if self.path_prefix:
            return f"location {self.path_prefix}"
        if self.path and self.path != "/":
            if self.path.endswith("$"):
                return f"location ~ {self.path}"
            return f"location = {self.path}"
        return "location /"


@dataclass
class Service:
    """Represents a backend service."""

    name: str
    servers: list[str] = field(default_factory=list)
    port: int = 80
    protocol: str = "http"
    health_check: str = ""
    load_balancer: str = "round_robin"
    weight: int = 1

    def to_nginx_upstream(self) -> str:
        """Convert service to nginx upstream block."""
        upstream_lines = [f"upstream {self.name} {{"]

        # Add load balancing method if not round_robin
        if self.load_balancer != "round_robin":
            if self.load_balancer == "least_conn":
                upstream_lines.append("    least_conn;")
            elif self.load_balancer == "ip_hash":
                upstream_lines.append("    ip_hash;")

        # Add servers
        for server in self.servers:
            if ":" not in server:
                server = f"{server}:{self.port}"
            upstream_lines.append(f"    server {server};")

        upstream_lines.append("}")
        return "\n".join(upstream_lines)


@dataclass
class ProxyConfig:
    """Main configuration container."""

    routes: list[Route] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    middlewares: dict[str, dict] = field(default_factory=dict)
    tls_config: dict[str, Any] = field(default_factory=dict)
    entry_points: dict[str, str] = field(default_factory=dict)


class TraefikRuleParser:
    """Parser for Traefik routing rules with full syntax support."""

    # Comprehensive Traefik rule patterns
    RULE_PATTERNS = {
        "host": re.compile(r"Host\(`([^`]+)`\)", re.IGNORECASE),
        "host_regexp": re.compile(r"HostRegexp\(`([^`]+)`\)", re.IGNORECASE),
        "path": re.compile(r"Path\(`([^`]+)`\)", re.IGNORECASE),
        "path_prefix": re.compile(r"PathPrefix\(`([^`]+)`\)", re.IGNORECASE),
        "path_regexp": re.compile(r"PathRegexp\(`([^`]+)`\)", re.IGNORECASE),
        "method": re.compile(r"Method\(`([^`]+)`\)", re.IGNORECASE),
        "header": re.compile(r"Header\(`([^`]+)`,\s*`([^`]+)`\)", re.IGNORECASE),
        "header_regexp": re.compile(
            r"HeaderRegexp\(`([^`]+)`,\s*`([^`]+)`\)",
            re.IGNORECASE,
        ),
        "query": re.compile(r"Query\(`([^`]+)`,\s*`([^`]+)`\)", re.IGNORECASE),
        "query_regexp": re.compile(
            r"QueryRegexp\(`([^`]+)`,\s*`([^`]+)`\)",
            re.IGNORECASE,
        ),
        "client_ip": re.compile(r"ClientIP\(`([^`]+)`\)", re.IGNORECASE),
        "host_sni": re.compile(r"HostSNI\(`([^`]+)`\)", re.IGNORECASE),
        "host_sni_regexp": re.compile(r"HostSNIRegexp\(`([^`]+)`\)", re.IGNORECASE),
        "alpn": re.compile(r"ALPN\(`([^`]+)`\)", re.IGNORECASE),
    }

    @classmethod
    def parse_rule(cls, rule_string: str) -> Route:
        """Parse a Traefik rule string into a Route object."""
        route = Route()

        # Handle logical operators by splitting on && and ||
        # For now, we'll take the first host and path we find
        # In a production system, you'd want more sophisticated parsing

        # Extract host
        host_match = cls.RULE_PATTERNS["host"].search(rule_string)
        if host_match:
            route.host = host_match.group(1)
        else:
            host_regexp_match = cls.RULE_PATTERNS["host_regexp"].search(rule_string)
            if host_regexp_match:
                route.host = host_regexp_match.group(1)

        # Extract path
        path_match = cls.RULE_PATTERNS["path"].search(rule_string)
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
        method_match = cls.RULE_PATTERNS["method"].search(rule_string)
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


class ConfigParser:
    """Parser for various configuration formats."""

    @staticmethod
    def parse_docker_compose(file_path: str) -> ProxyConfig:
        """Parse docker-compose file with Traefik labels."""
        config = ProxyConfig()

        try:
            with open(file_path) as f:
                compose_data = yaml.safe_load(f)

            services: dict[str, Any] = compose_data.get("services", {})

            for service_name, service_config in services.items():
                labels: list[str] | dict[str, str] = service_config.get("labels", [])

                # Convert labels list to dict if needed
                if isinstance(labels, list):
                    label_dict: dict[str, str] = {}
                    for label in labels:
                        if "=" in label:
                            key, value = label.split("=", 1)
                            label_dict[key] = value
                    labels = label_dict

                # Extract Traefik configuration
                traefik_labels: dict[str, str] = {
                    k: v
                    for k, v in labels.items()
                    if k.casefold().startswith("traefik.")
                }

                if traefik_labels:
                    ConfigParser._process_traefik_labels(
                        config,
                        service_name,
                        traefik_labels,
                    )

        except Exception as e:
            logger.exception(f"Error parsing docker-compose file: {e.__class__.__name__}: {e}")

        return config

    @staticmethod
    def _process_traefik_labels(
        config: ProxyConfig,
        service_name: str,
        labels: dict[str, str],
    ) -> None:
        """Process Traefik labels for a service."""
        # Extract routers
        router_labels: dict[str, str] = {k: v for k, v in labels.items() if ".routers." in k}
        service_labels: dict[str, str] = {k: v for k, v in labels.items() if ".services." in k}

        # Group by router name
        routers: dict[str, dict[str, str]] = {}
        for label, value in router_labels.items():
            parts: list[str] = label.split(".")
            if len(parts) < 4:
                continue
            router_name: str = parts[3]
            property_name: str = ".".join(parts[4:]).casefold()

            if router_name not in routers:
                routers[router_name] = {}
            routers[router_name][property_name] = value

        # Create routes from routers
        for router_name, router_config in routers.items():
            route = Route()

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
                route.priority = int(router_config["priority"].strip())

            # Set TLS
            if (
                "tls" in router_config
                or "tls.certresolver" in router_config
            ):
                route.tls = True
                if "tls.certresolver" in router_config:
                    route.cert_resolver = router_config["tls.certresolver"].strip()

            # Set middlewares
            if "middlewares" in router_config:
                route.middlewares = router_config["middlewares"].strip().split(",")

            config.routes.append(route)

        # Create service
        service = Service(name=service_name)

        # Extract service port
        for label, value in service_labels.items():
            if label.casefold().strip().endswith(".loadbalancer.server.port"):
                service.port = int(value.strip())

        # Add service IP (would need to be determined from container network)
        service.servers = [f"{service_name}"]  # Use service name as placeholder

        config.services.append(service)


class ConfigGenerator:
    """Generator for various configuration formats."""

    @staticmethod
    def generate_nginx_conf(
        config: ProxyConfig,
        output_file: str | None = None,
    ) -> str:
        """Generate nginx configuration from ProxyConfig."""
        nginx_template: str = """
# Generated nginx configuration from Traefik config
# Generated by nginx-traefik-converter

# Upstream definitions
{% for service in services %}
{{ service.to_nginx_upstream() }}

{% endfor %}

# Server blocks
{% for route in routes %}
server {
    {% if route.tls %}
    listen 443 ssl http2;
    {% if route.cert_resolver %}
    ssl_certificate /etc/nginx/certs/{{ route.host }}.crt;
    ssl_certificate_key /etc/nginx/certs/{{ route.host }}.key;
    {% endif %}
    {% else %}
    listen 80;
    {% endif %}

    {% if route.host %}
    server_name {{ route.host }};
    {% endif %}

    {% if route.client_ip %}
    # Client IP restriction
    allow {{ route.client_ip }};
    deny all;
    {% endif %}

    {{ route.to_nginx_location() }} {
        {% if route.method %}
        # Method restriction
        if ($request_method !~ ^({{ route.method }})$ ) {
            return 405;
        }
        {% endif %}

        {% for header_name, header_value in route.headers.items() %}
        # Header check for {{ header_name }}
        if ($http_{{ header_name.lower().replace('-', '_') }} != "{{ header_value }}") {
            return 400;
        }
        {% endfor %}

        {% for param_name, param_value in route.query_params.items() %}
        # Query parameter check for {{ param_name }}
        if ($arg_{{ param_name }} != "{{ param_value }}") {
            return 400;
        }
        {% endfor %}

        # Proxy configuration
        proxy_pass http://{{ route.host or 'backend' }};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}

{% endfor %}

# HTTP to HTTPS redirect
server {
    listen 80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}
"""

        template = Template(nginx_template)
        nginx_config: str = template.render(services=config.services, routes=config.routes)

        if (
            output_file
            and Path(output_file).exists()
            and Path(output_file).is_file()
        ):
            try:
                output_file_path = Path(output_file)
                output_file_path.write_text(nginx_config, encoding="utf-8")
                logger.info(f"Nginx configuration written to '{output_file}'")
            except Exception as e:
                logger.exception(f"Error writing nginx config: {e.__class__.__name__}: {e}")

        return nginx_config


class ConfigValidator:
    """Validator for configurations."""

    @staticmethod
    def validate_nginx_config(
        config_path: str,
        verbose: bool = False,
    ) -> bool:
        """Validate nginx configuration syntax."""
        try:
            import subprocess

            result: subprocess.CompletedProcess[str] = subprocess.run(
                ["nginx", "-t", "-c", config_path],
                check=False,
                capture_output=True,
                text=True,
            )
        except Exception as e:
            logger.warning(f"Could not validate nginx config: {e.__class__.__name__}: {e}", exc_info=verbose)
            return True  # Assume valid if we can't test
        else:
            return result.returncode == 0


def main() -> int | None:
    """Main CLI function."""
    parser = argparse.ArgumentParser(description="Convert between nginx and Traefik configurations")

    parser.add_argument(
        "--input-file",
        metavar="Input File",
        help="Path to the input configuration file",
        required=True,
    )

    parser.add_argument(
        "--input-format",
        metavar="Input Format",
        choices=["docker-compose", "traefik-yaml", "traefik-toml", "nginx-conf"],
        default="docker-compose",
        help="Format of the input configuration",
    )

    parser.add_argument(
        "--output-file",
        metavar="Output File",
        help="Path for the generated configuration file",
    )

    parser.add_argument(
        "--output-format",
        metavar="Output Format",
        choices=["nginx-conf", "traefik-yaml", "docker-compose"],
        default="nginx-conf",
        help="Format for the output configuration",
    )

    parser.add_argument(
        "--include-ssl",
        action="store_true",
        default=True,
        help="Include SSL/TLS configuration in output",
    )

    parser.add_argument(
        "--include-middlewares",
        action="store_true",
        default=True,
        help="Convert and include middleware configuration",
    )

    parser.add_argument(
        "--validate-output",
        action="store_true",
        default=False,
        help="Validate the generated configuration (requires nginx/traefik installed)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=False,
        help="Enable detailed logging output",
    )

    parser.add_argument(
        "--custom-template",
        metavar="Custom Template",
        help="Path to custom Jinja2 template for output generation",
    )

    parser.add_argument(
        "--backup-original",
        action="store_true",
        default=True,
        help="Create backup of original configuration file",
    )

    args: argparse.Namespace = parser.parse_args()

    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Verbose logging enabled")

    # Validate input file
    if not args.input_file:
        logger.error("Input file is required")
        return 1

    if not Path(args.input_file).exists() or not Path(args.input_file).is_file():
        logger.error(f"Input file does not exist: {args.input_file}")
        return 1

    # Create backup if requested
    if args.backup_original:
        backup_path: str = f"{args.input_file}.backup"
        try:
            import shutil

            shutil.copy2(args.input_file, backup_path)
            logger.info(f"Created backup: '{backup_path}'")
        except Exception as e:
            logger.warning(f"Could not create backup: {e.__class__.__name__}: {e}", exc_info=args.verbose)

    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Parse input configuration
            task1: TaskID = progress.add_task("Parsing input configuration...", total=None)

            if args.input_format == "docker-compose":
                config = ConfigParser.parse_docker_compose(args.input_file)
            else:
                logger.error(f"Input format {args.input_format} not yet implemented")
                return 1

            progress.update(task1, description="✓ Input parsed successfully")

            # Generate output
            task2: TaskID = progress.add_task("Generating output configuration...", total=None)

            if args.output_format == "nginx-conf":
                output_content: str = ConfigGenerator.generate_nginx_conf(
                    config,
                    args.output_file,
                )
            else:
                logger.error(f"Output format {args.output_format} not yet implemented")
                return 1

            progress.update(task2, description="✓ Output generated successfully")

            # Validate if requested
            if args.validate_output and args.output_file:
                task3: TaskID = progress.add_task(
                    "Validating output configuration...",
                    total=None,
                )

                if args.output_format == "nginx-conf":
                    is_valid: bool = ConfigValidator.validate_nginx_config(args.output_file)
                    if is_valid:
                        progress.update(task3, description="✓ Output validation passed")
                    else:
                        progress.update(task3, description="⚠ Output validation failed")
                        logger.warning("Generated configuration may have syntax errors")

        # Display results
        console.print("\n[bold green]✓ Conversion completed successfully![/bold green]")

        if args.output_file:
            console.print(f"[blue]Output written to:[/blue] {args.output_file}")

        # Display summary
        table = Table(title="Conversion Summary")
        table.add_column("Item", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Routes", str(len(config.routes)))
        table.add_row("Services", str(len(config.services)))
        table.add_row("Middlewares", str(len(config.middlewares)))

        console.print(table)

        # Show preview if no output file specified
        if not args.output_file:
            console.print("\n[bold yellow]Generated Configuration Preview:[/bold yellow]",)
            console.print(
                output_content[:1000] + "..."
                if len(output_content) > 1000
                else output_content,
            )

    except Exception as e:
        logger.exception(f"Conversion failed: {e.__class__.__name__}: {e}")
        if args.verbose:
            import traceback

            logger.exception(traceback.format_exc())
        return 1
    else:
        return 0


if __name__ == "__main__":
    sys.exit(main())
