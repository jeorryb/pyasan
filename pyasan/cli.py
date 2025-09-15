"""Command-line interface for PyASAN."""

import sys
from typing import Optional

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .apod import APODClient
from .mars import MarsRoverPhotosClient
from .exceptions import PyASANError, ValidationError, APIError, AuthenticationError
from .models import APODResponse, APODBatch
from .mars_models import MarsPhotosResponse, ManifestResponse

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
            apod.explanation, title="Explanation", border_style="green", padding=(1, 2)
        )
        console.print(explanation_panel)


def print_apod_batch(batch: APODBatch, show_explanation: bool = True) -> None:
    """Print multiple APOD entries."""
    console.print(f"\n[bold cyan]Found {len(batch)} APOD entries[/bold cyan]\n")

    for i, apod in enumerate(batch):
        if i > 0:
            console.print("\n" + "─" * 80 + "\n")
        print_apod(apod, show_explanation)


def print_mars_photo(photo, show_details: bool = True) -> None:
    """Print Mars rover photo information in a formatted way."""
    # Create title panel
    title_text = Text(f"Sol {photo.sol} - {photo.camera.full_name}", style="bold red")
    title_panel = Panel(
        title_text,
        title=f"{photo.rover.name.title()} Rover - {photo.earth_date}",
        border_style="red",
    )
    console.print(title_panel)

    if show_details:
        # Create info table
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("Field", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        table.add_row("Photo ID", str(photo.id))
        table.add_row("Sol", str(photo.sol))
        table.add_row("Earth Date", str(photo.earth_date))
        table.add_row("Camera", f"{photo.camera.name} ({photo.camera.full_name})")
        table.add_row("Rover", f"{photo.rover.name.title()} ({photo.rover.status})")
        table.add_row("Image URL", photo.img_src)

        console.print(table)


def print_mars_photos(photos: MarsPhotosResponse, show_details: bool = True) -> None:
    """Print multiple Mars rover photos."""
    if len(photos) == 0:
        console.print("[yellow]No photos found for the specified criteria.[/yellow]")
        return

    console.print(f"\n[bold cyan]Found {len(photos)} Mars rover photos[/bold cyan]\n")

    for i, photo in enumerate(photos):
        if i > 0:
            console.print("\n" + "─" * 80 + "\n")
        print_mars_photo(photo, show_details)


def print_manifest(manifest_response: ManifestResponse) -> None:
    """Print Mars rover mission manifest."""
    manifest = manifest_response.photo_manifest

    # Create title panel
    title_text = Text(f"{manifest.name.title()} Mission Manifest", style="bold red")
    title_panel = Panel(title_text, border_style="red")
    console.print(title_panel)

    # Create mission info table
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    table.add_row("Launch Date", str(manifest.launch_date))
    table.add_row("Landing Date", str(manifest.landing_date))
    table.add_row("Status", manifest.status.title())
    table.add_row("Max Sol", str(manifest.max_sol))
    table.add_row("Max Date", str(manifest.max_date))
    table.add_row("Total Photos", f"{manifest.total_photos:,}")

    console.print(table)

    # Show recent sols with photos
    console.print("\n[bold cyan]Recent Sols with Photos (last 10):[/bold cyan]")
    recent_photos = (
        manifest.photos[-10:] if len(manifest.photos) > 10 else manifest.photos
    )

    sols_table = Table()
    sols_table.add_column("Sol", style="cyan")
    sols_table.add_column("Earth Date", style="white")
    sols_table.add_column("Photos", style="green")
    sols_table.add_column("Cameras", style="yellow")

    for photo_info in recent_photos:
        cameras_str = ", ".join(photo_info.cameras[:3])  # Show first 3 cameras
        if len(photo_info.cameras) > 3:
            cameras_str += f" (+{len(photo_info.cameras) - 3} more)"

        sols_table.add_row(
            str(photo_info.sol),
            str(photo_info.earth_date),
            str(photo_info.total_photos),
            cameras_str,
        )

    console.print(sols_table)


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


@main.group()
def mars() -> None:
    """Mars Rover Photos commands."""
    pass


@apod.command("get")
@click.option("--date", "-d", help="Date in YYYY-MM-DD format (default: today)")
@click.option("--hd", is_flag=True, help="Get HD image URL if available")
@click.option("--thumbs", is_flag=True, help="Get thumbnail URL for videos")
@click.option("--no-explanation", is_flag=True, help="Don't show the explanation text")
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def apod_get(
    date: Optional[str],
    hd: bool,
    thumbs: bool,
    no_explanation: bool,
    api_key: Optional[str],
) -> None:
    """Get Astronomy Picture of the Day for a specific date."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
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
    "--count",
    "-c",
    default=1,
    type=click.IntRange(1, 100),
    help="Number of random APODs to fetch (1-100)",
)
@click.option("--hd", is_flag=True, help="Get HD image URLs if available")
@click.option("--thumbs", is_flag=True, help="Get thumbnail URLs for videos")
@click.option("--no-explanation", is_flag=True, help="Don't show the explanation text")
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def apod_random(
    count: int, hd: bool, thumbs: bool, no_explanation: bool, api_key: Optional[str]
) -> None:
    """Get random Astronomy Picture(s) of the Day."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
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
    "--start-date", "-s", required=True, help="Start date in YYYY-MM-DD format"
)
@click.option("--end-date", "-e", required=True, help="End date in YYYY-MM-DD format")
@click.option("--hd", is_flag=True, help="Get HD image URLs if available")
@click.option("--thumbs", is_flag=True, help="Get thumbnail URLs for videos")
@click.option("--no-explanation", is_flag=True, help="Don't show the explanation text")
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def apod_range(
    start_date: str,
    end_date: str,
    hd: bool,
    thumbs: bool,
    no_explanation: bool,
    api_key: Optional[str],
) -> None:
    """Get Astronomy Pictures of the Day for a date range."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(
                f"Fetching APODs from {start_date} to {end_date}...", total=None
            )

            client = APODClient(api_key=api_key)
            batch = client.get_apod_range(
                start_date=start_date, end_date=end_date, hd=hd, thumbs=thumbs
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
    "--days",
    "-d",
    default=7,
    type=click.IntRange(1, 100),
    help="Number of recent days to fetch (1-100)",
)
@click.option("--hd", is_flag=True, help="Get HD image URLs if available")
@click.option("--thumbs", is_flag=True, help="Get thumbnail URLs for videos")
@click.option("--no-explanation", is_flag=True, help="Don't show the explanation text")
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def apod_recent(
    days: int, hd: bool, thumbs: bool, no_explanation: bool, api_key: Optional[str]
) -> None:
    """Get recent Astronomy Pictures of the Day."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
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


@mars.command("photos")
@click.option(
    "--rover",
    "-r",
    required=True,
    type=click.Choice(
        ["perseverance", "curiosity", "opportunity", "spirit"], case_sensitive=False
    ),
    help="Mars rover name",
)
@click.option(
    "--sol", "-s", type=int, help="Martian sol (day) - cannot be used with --earth-date"
)
@click.option(
    "--earth-date",
    "-d",
    help="Earth date in YYYY-MM-DD format - cannot be used with --sol",
)
@click.option(
    "--camera", "-c", help="Camera abbreviation (e.g., FHAZ, RHAZ, MAST, NAVCAM)"
)
@click.option("--page", "-p", type=int, help="Page number for pagination")
@click.option(
    "--no-details", is_flag=True, help="Don't show detailed photo information"
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def mars_photos(
    rover: str,
    sol: Optional[int],
    earth_date: Optional[str],
    camera: Optional[str],
    page: Optional[int],
    no_details: bool,
    api_key: Optional[str],
) -> None:
    """Get Mars rover photos by sol or Earth date."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Fetching {rover.title()} rover photos...", total=None)

            client = MarsRoverPhotosClient(api_key=api_key)
            photos = client.get_photos(
                rover=rover, sol=sol, earth_date=earth_date, camera=camera, page=page
            )

        print_mars_photos(photos, show_details=not no_details)

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


@mars.command("latest")
@click.option(
    "--rover",
    "-r",
    required=True,
    type=click.Choice(
        ["perseverance", "curiosity", "opportunity", "spirit"], case_sensitive=False
    ),
    help="Mars rover name",
)
@click.option(
    "--no-details", is_flag=True, help="Don't show detailed photo information"
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def mars_latest(rover: str, no_details: bool, api_key: Optional[str]) -> None:
    """Get latest photos from a Mars rover."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(f"Fetching latest {rover.title()} photos...", total=None)

            client = MarsRoverPhotosClient(api_key=api_key)
            photos = client.get_latest_photos(rover=rover)

        print_mars_photos(photos, show_details=not no_details)

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


@mars.command("manifest")
@click.option(
    "--rover",
    "-r",
    required=True,
    type=click.Choice(
        ["perseverance", "curiosity", "opportunity", "spirit"], case_sensitive=False
    ),
    help="Mars rover name",
)
@click.option(
    "--api-key",
    envvar="NASA_API_KEY",
    help="NASA API key (can also be set via NASA_API_KEY env var)",
)
def mars_manifest(rover: str, api_key: Optional[str]) -> None:
    """Get mission manifest for a Mars rover."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task(
                f"Fetching {rover.title()} mission manifest...", total=None
            )

            client = MarsRoverPhotosClient(api_key=api_key)
            manifest = client.get_manifest(rover=rover)

        print_manifest(manifest)

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


@mars.command("cameras")
@click.option(
    "--rover",
    "-r",
    required=True,
    type=click.Choice(
        ["perseverance", "curiosity", "opportunity", "spirit"], case_sensitive=False
    ),
    help="Mars rover name",
)
def mars_cameras(rover: str) -> None:
    """List available cameras for a Mars rover."""
    try:
        client = MarsRoverPhotosClient()
        cameras = client.get_rover_cameras(rover=rover)

        console.print(f"\n[bold cyan]{rover.title()} Rover Cameras:[/bold cyan]\n")

        for camera in cameras:
            console.print(f"  • {camera}")

        console.print("\n[dim]Use these camera names with the 'photos' command.[/dim]")

    except ValidationError as e:
        console.print(f"[red]Validation Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)
    except PyASANError as e:
        console.print(f"[red]Error:[/red] {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
