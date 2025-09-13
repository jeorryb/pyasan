"""Command-line interface for PyASAN."""

import sys
from datetime import date, datetime
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .apod import APODClient
from .exceptions import PyASANError, ValidationError, APIError, AuthenticationError
from .models import APODResponse, APODBatch

console = Console()


def print_apod(apod: APODResponse, show_explanation: bool = True) -> None:
    """Print APOD information in a formatted way."""
    # Create title panel
    title_text = Text(apod.title, style="bold blue")
    title_panel = Panel(title_text, title=f"APOD - {apod.date}", border_style="blue")
    console.print(title_panel)
    
    # Create info table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")
    
    table.add_row("Date", str(apod.date))
    table.add_row("Media Type", apod.media_type.title())
    table.add_row("URL", apod.url)
    
    if apod.hdurl:
        table.add_row("HD URL", apod.hdurl)
    
    if apod.thumbnail_url:
        table.add_row("Thumbnail", apod.thumbnail_url)
    
    if apod.copyright:
        table.add_row("Copyright", apod.copyright)
    
    console.print(table)
    
    if show_explanation:
        console.print()
        explanation_panel = Panel(
            apod.explanation, 
            title="Explanation", 
            border_style="green",
            padding=(1, 2)
        )
        console.print(explanation_panel)


def print_apod_batch(batch: APODBatch, show_explanation: bool = True) -> None:
    """Print multiple APOD entries."""
    console.print(f"\n[bold cyan]Found {len(batch)} APOD entries[/bold cyan]\n")
    
    for i, apod in enumerate(batch):
        if i > 0:
            console.print("\n" + "─" * 80 + "\n")
        print_apod(apod, show_explanation)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show version information")
@click.pass_context
def main(ctx: click.Context, version: bool) -> None:
    """PyASAN - A Python wrapper and CLI for NASA's REST APIs."""
    if version:
        console.print(f"PyASAN version {__version__}")
        return
    
    if ctx.invoked_subcommand is None:
        console.print(ctx.get_help())


@main.group()
def apod() -> None:
    """Astronomy Picture of the Day commands."""
    pass


@apod.command("get")
@click.option(
    "--date", "-d",
    help="Date in YYYY-MM-DD format (default: today)"
)
@click.option(
    "--hd", is_flag=True,
    help="Get HD image URL if available"
)
@click.option(
    "--thumbs", is_flag=True,
    help="Get thumbnail URL for videos"
)
@click.option(
    "--no-explanation", is_flag=True,
    help="Don't show the explanation text"
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)"
)
def apod_get(
    date: Optional[str],
    hd: bool,
    thumbs: bool,
    no_explanation: bool,
    api_key: Optional[str]
) -> None:
    """Get Astronomy Picture of the Day for a specific date."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task("Fetching APOD...", total=None)
            
            client = APODClient(api_key=api_key)
            apod = client.get_apod(date=date, hd=hd, thumbs=thumbs)
            
        print_apod(apod, show_explanation=not no_explanation)
        
    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}", file=sys.stderr)
        console.print("[yellow]Get your free API key at https://api.nasa.gov/[/yellow]")
        sys.exit(1)
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except PyASANError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@apod.command("random")
@click.option(
    "--count", "-c", default=1, type=click.IntRange(1, 100),
    help="Number of random APODs to fetch (1-100)"
)
@click.option(
    "--hd", is_flag=True,
    help="Get HD image URLs if available"
)
@click.option(
    "--thumbs", is_flag=True,
    help="Get thumbnail URLs for videos"
)
@click.option(
    "--no-explanation", is_flag=True,
    help="Don't show the explanation text"
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)"
)
def apod_random(
    count: int,
    hd: bool,
    thumbs: bool,
    no_explanation: bool,
    api_key: Optional[str]
) -> None:
    """Get random Astronomy Picture(s) of the Day."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(f"Fetching {count} random APOD(s)...", total=None)
            
            client = APODClient(api_key=api_key)
            result = client.get_random_apod(count=count, hd=hd, thumbs=thumbs)
            
        if isinstance(result, APODResponse):
            print_apod(result, show_explanation=not no_explanation)
        else:
            print_apod_batch(result, show_explanation=not no_explanation)
            
    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}", file=sys.stderr)
        console.print("[yellow]Get your free API key at https://api.nasa.gov/[/yellow]")
        sys.exit(1)
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except PyASANError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@apod.command("range")
@click.option(
    "--start-date", "-s", required=True,
    help="Start date in YYYY-MM-DD format"
)
@click.option(
    "--end-date", "-e", required=True,
    help="End date in YYYY-MM-DD format"
)
@click.option(
    "--hd", is_flag=True,
    help="Get HD image URLs if available"
)
@click.option(
    "--thumbs", is_flag=True,
    help="Get thumbnail URLs for videos"
)
@click.option(
    "--no-explanation", is_flag=True,
    help="Don't show the explanation text"
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)"
)
def apod_range(
    start_date: str,
    end_date: str,
    hd: bool,
    thumbs: bool,
    no_explanation: bool,
    api_key: Optional[str]
) -> None:
    """Get Astronomy Pictures of the Day for a date range."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(f"Fetching APODs from {start_date} to {end_date}...", total=None)
            
            client = APODClient(api_key=api_key)
            batch = client.get_apod_range(
                start_date=start_date,
                end_date=end_date,
                hd=hd,
                thumbs=thumbs
            )
            
        print_apod_batch(batch, show_explanation=not no_explanation)
        
    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}", file=sys.stderr)
        console.print("[yellow]Get your free API key at https://api.nasa.gov/[/yellow]")
        sys.exit(1)
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except PyASANError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


@apod.command("recent")
@click.option(
    "--days", "-d", default=7, type=click.IntRange(1, 100),
    help="Number of recent days to fetch (1-100)"
)
@click.option(
    "--hd", is_flag=True,
    help="Get HD image URLs if available"
)
@click.option(
    "--thumbs", is_flag=True,
    help="Get thumbnail URLs for videos"
)
@click.option(
    "--no-explanation", is_flag=True,
    help="Don't show the explanation text"
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)"
)
def apod_recent(
    days: int,
    hd: bool,
    thumbs: bool,
    no_explanation: bool,
    api_key: Optional[str]
) -> None:
    """Get recent Astronomy Pictures of the Day."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True
        ) as progress:
            progress.add_task(f"Fetching {days} recent APODs...", total=None)
            
            client = APODClient(api_key=api_key)
            batch = client.get_recent_apods(days=days, hd=hd, thumbs=thumbs)
            
        print_apod_batch(batch, show_explanation=not no_explanation)
        
    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except AuthenticationError as e:
        console.print(f"[red]Authentication Error:[/red] {e}", file=sys.stderr)
        console.print("[yellow]Get your free API key at https://api.nasa.gov/[/yellow]")
        sys.exit(1)
    except APIError as e:
        console.print(f"[red]API Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except PyASANError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
