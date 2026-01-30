from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .core.analyzer import ConfigAnalyzer
from .core.converter import UniversalConverter
from .core.scaffolder import ConfigScaffolder
from .core.validator import ConfigValidator
from .utils.logging import setup_logging

# Set up rich console and logging
console = Console()
setup_logging(console)

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version="1.0.0", prog_name="nginx-traefik-converter")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
@click.option("--quiet", "-q", is_flag=True, help="Suppress output except errors")
def cli(verbose: bool, quiet: bool) -> None:
    """Universal nginx/Traefik Configuration Converter.

    A comprehensive tool for converting between nginx and Traefik configurations,
    supporting multiple input/output formats and bidirectional conversion.
    """
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.argument("output_file", type=click.Path(path_type=Path))
@click.option(
    "--input-format",
    "-i",
    type=click.Choice(
        ["docker-compose", "traefik-dynamic", "nginx-conf", "json", "yaml"],
    ),
    help="Input format (auto-detected if not specified)",
)
@click.option(
    "--output-format",
    "-o",
    type=click.Choice(
        ["traefik-dynamic", "nginx-conf", "docker-compose", "json", "yaml"],
    ),
    help="Output format (auto-detected if not specified)",
)
@click.option("--validate/--no-validate", default=True, help="Validate configuration")
@click.option("--dry-run", is_flag=True, help="Preview output without writing files")
@click.option("--force", is_flag=True, help="Overwrite existing output file")
def convert(
    input_file: Path,
    output_file: Path,
    input_format: str | None,
    output_format: str | None,
    validate: bool,
    dry_run: bool,
    force: bool,
) -> None:
    """Convert between configuration formats.

    INPUT_FILE: Path to the input configuration file
    OUTPUT_FILE: Path for the output configuration file
    """
    try:
        converter = UniversalConverter()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Parse input configuration
            task1 = progress.add_task("Parsing input configuration...", total=None)

            config = converter.parse_config(input_file, input_format)

            progress.update(task1, description="✓ Input parsed successfully")

            # Generate output
            task2 = progress.add_task("Generating output configuration...", total=None)

            output_content = converter.generate_config(config, output_format)

            progress.update(task2, description="✓ Output generated successfully")

            # Validate if requested
            if validate and not dry_run:
                task3 = progress.add_task(
                    "Validating output configuration...",
                    total=None,
                )

                is_valid = converter.validate_config(output_content, output_format)
                if is_valid:
                    progress.update(task3, description="✓ Output validation passed")
                else:
                    progress.update(task3, description="⚠ Output validation failed")
                    logger.warning("Generated configuration may have syntax errors")

        # Write output file
        if not dry_run:
            if output_file.exists() and not force:
                msg = f"Output file {output_file} already exists. Use --force to overwrite."
                raise click.ClickException(
                    msg,
                )

            output_file.write_text(output_content)
            console.print(
                "\n[bold green]✓ Conversion completed successfully![/bold green]",
            )
            console.print(f"[blue]Output written to:[/blue] {output_file}")
        else:
            console.print(
                "\n[bold yellow]Dry run - Generated Configuration Preview:[/bold yellow]",
            )
            console.print(
                output_content[:2000] + "..."
                if len(output_content) > 2000
                else output_content,
            )

        # Display summary
        display_conversion_summary(config)

    except Exception as e:
        logger.exception(f"Conversion failed: {e}")
        if click.get_current_context().get_help_option():
            raise click.ClickException(str(e))
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(
        ["docker-compose", "traefik-dynamic", "nginx-conf", "json", "yaml"],
    ),
    help="Configuration format (auto-detected if not specified)",
)
@click.option("--detailed", "-d", is_flag=True, help="Show detailed analysis")
def analyze(config_file: Path, format: str | None, detailed: bool) -> None:
    """Analyze and display configuration details.

    CONFIG_FILE: Path to the configuration file to analyze
    """
    try:
        analyzer = ConfigAnalyzer()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Analyzing configuration...", total=None)

            analysis = analyzer.analyze_config(config_file, format, detailed)

            progress.update(task, description="✓ Analysis completed")

        # Display analysis results
        display_analysis_results(analysis, detailed)

    except Exception as e:
        logger.exception(f"Analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-dir",
    "-o",
    type=click.Path(path_type=Path),
    default=Path("./proxy-setup"),
    help="Output directory",
)
@click.option(
    "--proxy-type",
    "-p",
    type=click.Choice(["traefik", "nginx"]),
    default="traefik",
    help="Target proxy type",
)
@click.option("--include-compose", is_flag=True, help="Generate docker-compose.yml")
@click.option("--include-config", is_flag=True, help="Generate proxy configuration")
@click.option("--include-docs", is_flag=True, help="Generate documentation")
@click.option("--include-all", is_flag=True, help="Include all components")
def scaffold(
    input_file: Path,
    output_dir: Path,
    proxy_type: str,
    include_compose: bool,
    include_config: bool,
    include_docs: bool,
    include_all: bool,
) -> None:
    """Generate complete proxy setup with configs and documentation.

    INPUT_FILE: Path to the input configuration file
    """
    try:
        if include_all:
            include_compose = include_config = include_docs = True

        if not any([include_compose, include_config, include_docs]):
            msg = "Must specify at least one component to include"
            raise click.ClickException(msg)

        scaffolder = ConfigScaffolder()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Generating proxy setup...", total=None)

            result = scaffolder.scaffold_project(
                input_file=input_file,
                output_dir=output_dir,
                proxy_type=proxy_type,
                include_compose=include_compose,
                include_config=include_config,
                include_docs=include_docs,
            )

            progress.update(task, description="✓ Scaffolding completed")

        # Display results
        console.print("\n[bold green]✓ Project scaffolded successfully![/bold green]")
        console.print(f"[blue]Output directory:[/blue] {output_dir}")

        display_scaffold_results(result)

    except Exception as e:
        logger.exception(f"Scaffolding failed: {e}")
        sys.exit(1)


@cli.command()
@click.argument("config_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--format",
    "-f",
    type=click.Choice(
        ["docker-compose", "traefik-dynamic", "nginx-conf", "json", "yaml"],
    ),
    help="Configuration format (auto-detected if not specified)",
)
def validate(config_file: Path, format: str | None) -> None:
    """Validate configuration syntax and best practices.

    CONFIG_FILE: Path to the configuration file to validate
    """
    try:
        validator = ConfigValidator()

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Validating configuration...", total=None)

            result = validator.validate_file(config_file, format)

            progress.update(task, description="✓ Validation completed")

        # Display validation results
        display_validation_results(result)

    except Exception as e:
        logger.exception(f"Validation failed: {e}")
        sys.exit(1)


def display_conversion_summary(config: Any) -> None:
    """Display a summary of the conversion results."""
    table = Table(title="Conversion Summary")
    table.add_column("Item", style="cyan")
    table.add_column("Count", style="magenta")

    table.add_row("Routes", str(len(config.routes)))
    table.add_row("Services", str(len(config.services)))
    table.add_row("Middlewares", str(len(config.middlewares)))

    console.print(table)


def display_analysis_results(analysis: dict[str, Any], detailed: bool) -> None:
    """Display analysis results."""
    if detailed:
        # Detailed analysis with multiple tables
        for section, data in analysis.items():
            if isinstance(data, dict) and data:
                table = Table(title=f"{section.title()} Analysis")
                for key, value in data.items():
                    table.add_column(key, style="cyan")
                    table.add_row(str(value))
                console.print(table)
    else:
        # Summary analysis
        table = Table(title="Configuration Analysis")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")

        for key, value in analysis.items():
            if isinstance(value, (int, str)):
                table.add_row(key, str(value))

        console.print(table)


def display_scaffold_results(result: dict[str, Any]) -> None:
    """Display scaffolding results."""
    table = Table(title="Generated Files")
    table.add_column("File", style="cyan")
    table.add_column("Status", style="magenta")

    for file_path, status in result.get("files", {}).items():
        table.add_row(str(file_path), "✓ Generated" if status else "✗ Failed")

    console.print(table)


def display_validation_results(result: dict[str, Any]) -> None:
    """Display validation results."""
    if result.get("valid", False):
        console.print("[bold green]✓ Configuration is valid![/bold green]")
    else:
        console.print("[bold red]✗ Configuration has issues:[/bold red]")

        for error in result.get("errors", []):
            console.print(f"  • {error}")

        for warning in result.get("warnings", []):
            console.print(f"  ⚠ {warning}")


if __name__ == "__main__":
    cli()
