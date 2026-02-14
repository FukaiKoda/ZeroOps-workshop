#!/usr/bin/env python3
import typer
import subprocess
import os
import sys
import shutil
from pathlib import Path
from rich.console import Console

app = typer.Typer()
console = Console()

SERVICE_NAME = "zeroops.service"

def _run_systemctl(command: str):
    """Run systemctl command for user service."""
    try:
        subprocess.run(
            ["systemctl", "--user", command, SERVICE_NAME],
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        return False

@app.command()
def start():
    """Start the ZeroOps background service."""
    console.print(f"[bold green]Starting {SERVICE_NAME}...[/bold green]")
    if _run_systemctl("start"):
        console.print("[green]Service started successfully.[/green]")
    else:
        console.print("[red]Failed to start service. Check logs for details.[/red]")

@app.command()
def stop():
    """Stop the ZeroOps background service."""
    if _run_systemctl("stop"):
        console.print("[yellow]Service stopped.[/yellow]")
    else:
        console.print("[red]Failed to stop service.[/red]")

@app.command()
def restart():
    """Restart the ZeroOps background service."""
    if _run_systemctl("restart"):
        console.print("[green]Service restarted.[/green]")
    else:
        console.print("[red]Failed to restart service.[/red]")

@app.command()
def status():
    """Check the status of the service."""
    # We want to show the output of status directly
    subprocess.run(["systemctl", "--user", "status", SERVICE_NAME])

@app.command()
def logs(follow: bool = False):
    """View service logs."""
    cmd = ["journalctl", "--user", "-u", SERVICE_NAME]
    if follow:
        cmd.append("-f")
    subprocess.run(cmd)

@app.command()
def ui():
    """Launch the TUI Client."""
    # Launch client using its own poetry environment
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    client_dir = base_dir / "client"
    
    if client_dir.exists():
        console.print("[bold cyan]Launching TUI...[/bold cyan]")
        try:
            # Check if poetry is available
            if shutil.which("poetry"):
                 subprocess.run(["poetry", "run", "python", "src/main.py", "tui"], cwd=str(client_dir))
            else:
                 console.print("[red]Poetry not found. Cannot launch client.[/red]")
        except Exception as e:
             console.print(f"[red]Error launching client: {e}[/red]")
    else:
        console.print("[red]Could not locate client directory.[/red]")

if __name__ == "__main__":
    app()
