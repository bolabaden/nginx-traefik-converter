from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import click
from pline import Pline
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core.converter import UniversalConverter
from .utils.logging import setup_logging

# Set up rich console and logging
console = Console()
setup_logging(console)
logger = logging.getLogger(__name__)


class NginxTraefikConverterGUI:
    """GUI application for nginx/Traefik converter using Pline."""

    def __init__(self) -> None:
        self.converter = UniversalConverter()
        self.console = console

    def run(self) -> None:
        """Run the GUI application."""
        try:
            # Create Pline application
            app = Pline(
                title="Universal nginx/Traefik Converter",
                description="Convert between nginx and Traefik configurations with support for Docker Compose, static files, and more.",
                width=800,
                height=600,
            )

            # Add input file selection
            input_file = app.file_input(
                label="Input Configuration File",
                help_text="Select the source configuration file to convert",
                file_types=[
                    ("All files", "*.*"),
                    ("YAML files", "*.yml;*.yaml"),
                    ("TOML files", "*.toml"),
                    ("Docker Compose", "docker-compose*.yml"),
                    ("Nginx config", "*.conf"),
                    ("JSON files", "*.json"),
                ],
            )

            # Add input format selection
            input_format = app.select(
                label="Input Format",
                help_text="Format of the input configuration (auto-detected if not specified)",
                options=[
                    ("Auto-detect", ""),
                    ("Docker Compose", "docker-compose"),
                    ("Traefik Dynamic", "traefik-dynamic"),
                    ("Nginx Config", "nginx-conf"),
                    ("YAML", "yaml"),
                    ("JSON", "json"),
                ],
                default="",
            )

            # Add output file selection
            output_file = app.file_save(
                label="Output Configuration File",
                help_text="Select where to save the converted configuration",
                file_types=[
                    ("Nginx config", "*.conf"),
                    ("YAML files", "*.yml"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*"),
                ],
            )

            # Add output format selection
            output_format = app.select(
                label="Output Format",
                help_text="Format for the output configuration",
                options=[
                    ("Nginx Config", "nginx-conf"),
                    ("Traefik Dynamic", "traefik-dynamic"),
                    ("Docker Compose", "docker-compose"),
                    ("YAML", "yaml"),
                    ("JSON", "json"),
                ],
                default="nginx-conf",
            )

            # Add conversion options
            include_ssl = app.checkbox(
                label="Include SSL Configuration",
                help_text="Include SSL/TLS configuration in output",
                default=True,
            )

            include_middlewares = app.checkbox(
                label="Include Middlewares",
                help_text="Convert and include middleware configuration",
                default=True,
            )

            validate_output = app.checkbox(
                label="Validate Output",
                help_text="Validate the generated configuration (requires nginx/traefik installed)",
                default=False,
            )

            verbose = app.checkbox(
                label="Verbose Output",
                help_text="Enable detailed logging output",
                default=False,
            )

            # Add advanced options
            custom_template = app.file_input(
                label="Custom Template (Optional)",
                help_text="Path to custom Jinja2 template for output generation",
                file_types=[
                    ("Template files", "*.j2;*.jinja"),
                    ("All files", "*.*"),
                ],
                required=False,
            )

            backup_original = app.checkbox(
                label="Backup Original",
                help_text="Create backup of original configuration file",
                default=True,
            )

            # Add convert button
            convert_button = app.button(
                label="Convert Configuration",
                style="primary",
            )

            # Handle conversion
            if convert_button:
                self._handle_conversion(
                    input_file=input_file,
                    input_format=input_format,
                    output_file=output_file,
                    output_format=output_format,
                    include_ssl=include_ssl,
                    include_middlewares=include_middlewares,
                    validate_output=validate_output,
                    verbose=verbose,
                    custom_template=custom_template,
                    backup_original=backup_original,
                )

            # Run the application
            app.run()

        except Exception as e:
            logger.exception(f"GUI application failed: {e}")
            console.print(f"[bold red]Error:[/bold red] {e}")
            sys.exit(1)

    def _handle_conversion(
        self,
        input_file: str,
        input_format: str,
        output_file: str,
        output_format: str,
        include_ssl: bool,
        include_middlewares: bool,
        validate_output: bool,
        verbose: bool,
        custom_template: str | None,
        backup_original: bool,
    ) -> None:
        """Handle the conversion process."""
        try:
            # Set up logging level
            if verbose:
                logging.getLogger().setLevel(logging.DEBUG)
                logger.debug("Verbose logging enabled")

            # Validate input file
            if not input_file:
                msg = "Input file is required"
                raise ValueError(msg)

            input_path = Path(input_file)
            if not input_path.exists():
                msg = f"Input file does not exist: {input_file}"
                raise ValueError(msg)

            # Create backup if requested
            if backup_original:
                backup_path = f"{input_file}.backup"
                try:
                    import shutil

                    shutil.copy2(input_file, backup_path)
                    logger.info(f"Created backup: {backup_path}")
                except Exception as e:
                    logger.warning(f"Could not create backup: {e}")

            # Perform conversion
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console,
            ) as progress:
                # Parse input configuration
                task1 = progress.add_task("Parsing input configuration...", total=None)

                if input_format == "docker-compose":
                    config = self.converter.parse_config(input_path, "docker-compose")
                elif input_format == "traefik-dynamic":
                    config = self.converter.parse_config(input_path, "traefik-dynamic")
                elif input_format == "nginx-conf":
                    config = self.converter.parse_config(input_path, "nginx-conf")
                else:
                    config = self.converter.parse_config(input_path)

                progress.update(task1, description="✓ Input parsed successfully")

                # Generate output
                task2 = progress.add_task(
                    "Generating output configuration...",
                    total=None,
                )

                if output_format == "nginx-conf":
                    output_content = self.converter.generate_config(
                        config,
                        "nginx-conf",
                    )
                elif output_format == "traefik-dynamic":
                    output_content = self.converter.generate_config(
                        config,
                        "traefik-dynamic",
                    )
                elif output_format == "docker-compose":
                    output_content = self.converter.generate_config(
                        config,
                        "docker-compose",
                    )
                else:
                    output_content = self.converter.generate_config(
                        config,
                        output_format,
                    )

                progress.update(task2, description="✓ Output generated successfully")

                # Validate if requested
                if validate_output and output_file:
                    task3 = progress.add_task(
                        "Validating output configuration...",
                        total=None,
                    )

                    if output_format == "nginx-conf":
                        is_valid = self.converter.validate_config(
                            output_content,
                            "nginx-conf",
                        )
                        if is_valid:
                            progress.update(
                                task3,
                                description="✓ Output validation passed",
                            )
                        else:
                            progress.update(
                                task3,
                                description="⚠ Output validation failed",
                            )
                            logger.warning(
                                "Generated configuration may have syntax errors",
                            )

            # Write output file
            if output_file:
                output_path = Path(output_file)
                output_path.write_text(output_content)
                self.console.print(
                    "\n[bold green]✓ Conversion completed successfully![/bold green]",
                )
                self.console.print(f"[blue]Output written to:[/blue] {output_file}")
            else:
                self.console.print(
                    "\n[bold yellow]Generated Configuration Preview:[/bold yellow]",
                )
                self.console.print(
                    output_content[:2000] + "..."
                    if len(output_content) > 2000
                    else output_content,
                )

            # Display summary
            self._display_conversion_summary(config)

        except Exception as e:
            logger.exception(f"Conversion failed: {e}")
            self.console.print(f"[bold red]Conversion failed:[/bold red] {e}")
            if verbose:
                import traceback

                logger.exception(traceback.format_exc())

    def _display_conversion_summary(self, config: Any) -> None:
        """Display a summary of the conversion results."""
        table = Table(title="Conversion Summary")
        table.add_column("Item", style="cyan")
        table.add_column("Count", style="magenta")

        table.add_row("Routes", str(len(config.routes)))
        table.add_row("Services", str(len(config.services)))
        table.add_row("Middlewares", str(len(config.middlewares)))

        self.console.print(table)


@click.command()
@click.option("--gui", is_flag=True, help="Launch GUI application")
def main(gui: bool) -> None:
    """Universal nginx/Traefik Configuration Converter."""
    if gui:
        app = NginxTraefikConverterGUI()
        app.run()
    else:
        # Fall back to CLI
        from .main import cli

        cli()


if __name__ == "__main__":
    main()
