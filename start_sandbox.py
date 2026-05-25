#!/usr/bin/env python3
import os
import sys
import subprocess
import venv
from pathlib import Path

VENV_DIR = Path(__file__).parent / ".venv_sandbox"
PROJECT_DIR = Path(__file__).parent
REQUIREMENTS_FILE = PROJECT_DIR / "requirements.txt"
PYPROJECT_FILE = PROJECT_DIR / "pyproject.toml"

def run_command(cmd, cwd=None, env=None, check=True):
    """Run a command and return the result."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=check
    )
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    return result

def create_virtual_environment():
    """Create a Python virtual environment."""
    print(f"Creating virtual environment at {VENV_DIR}")
    venv.create(VENV_DIR, with_pip=True)

def get_venv_python():
    """Get the path to the virtual environment's Python interpreter."""
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "python.exe")
    else:
        return str(VENV_DIR / "bin" / "python")

def get_venv_pip():
    """Get the path to the virtual environment's pip."""
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "pip.exe")
    else:
        return str(VENV_DIR / "bin" / "pip")

def get_venv_activate():
    """Get the path to the virtual environment's activate script."""
    if sys.platform == "win32":
        return str(VENV_DIR / "Scripts" / "activate.bat")
    else:
        return str(VENV_DIR / "bin" / "activate")

def install_dependencies():
    """Install project dependencies in the virtual environment."""
    print("Installing dependencies...")
    
    pip_path = get_venv_pip()
    
    print("Upgrading pip...")
    run_command([pip_path, "install", "--upgrade", "pip"])
    
    print("Installing setuptools...")
    run_command([pip_path, "install", "setuptools>=80.9.0"])
    
    print("Installing project in editable mode...")
    run_command([pip_path, "install", "-e", str(PROJECT_DIR)])
    
    print("Dependencies installed successfully!")

def setup_environment():
    """Setup the sandbox environment."""
    print("=" * 60)
    print("Setting up TradingAgents Sandbox Environment")
    print("=" * 60)
    
    if not VENV_DIR.exists():
        create_virtual_environment()
    else:
        print(f"Virtual environment already exists at {VENV_DIR}")
    
    install_dependencies()
    
    print("=" * 60)
    print("Environment setup complete!")
    print("=" * 60)

def run_application(mode="cli", ticker=None, date=None):
    """Run the TradingAgents application in the sandbox."""
    print(f"\nStarting TradingAgents in {mode} mode...")
    
    python_path = get_venv_python()
    
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_DIR)
    
    if mode == "cli":
        cmd = [python_path, "-m", "cli.main"]
        if ticker:
            cmd.extend(["--ticker", ticker])
        if date:
            cmd.extend(["--date", date])
    elif mode == "web":
        cmd = [python_path, "-m", "web.launch"]
    elif mode == "main":
        cmd = [python_path, str(PROJECT_DIR / "main.py")]
    else:
        print(f"Unknown mode: {mode}")
        return False
    
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_DIR,
            env=env,
            check=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Application failed with error: {e}", file=sys.stderr)
        return False

def show_help():
    """Show help information."""
    help_text = """
TradingAgents Sandbox Launcher

Usage:
    python start_sandbox.py [OPTIONS]

Options:
    --setup             Setup the virtual environment and install dependencies
    --cli               Run the CLI interface
    --web               Run the web interface
    --main              Run the main.py script
    --ticker TICKER     Specify a ticker symbol (for CLI mode)
    --date DATE         Specify a date (for CLI mode, format: YYYY-MM-DD)
    --help              Show this help message

Examples:
    python start_sandbox.py --setup              # Setup environment
    python start_sandbox.py --cli                # Run CLI
    python start_sandbox.py --cli --ticker 600519 --date 2024-05-10
    python start_sandbox.py --web                # Run web UI
    python start_sandbox.py --main               # Run main.py

If no mode is specified, the script will setup and run CLI by default.
"""
    print(help_text)

def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="TradingAgents Sandbox Launcher",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False
    )
    parser.add_argument("--setup", action="store_true", help="Setup environment")
    parser.add_argument("--cli", action="store_true", help="Run CLI mode")
    parser.add_argument("--web", action="store_true", help="Run web mode")
    parser.add_argument("--main", action="store_true", help="Run main.py")
    parser.add_argument("--ticker", type=str, help="Ticker symbol")
    parser.add_argument("--date", type=str, help="Date (YYYY-MM-DD)")
    parser.add_argument("--help", action="store_true", help="Show help")
    
    args = parser.parse_args()
    
    if args.help:
        show_help()
        return
    
    needs_setup = args.setup or not VENV_DIR.exists()
    
    if needs_setup:
        setup_environment()
    
    mode = "cli"
    if args.web:
        mode = "web"
    elif args.main:
        mode = "main"
    
    success = run_application(mode, args.ticker, args.date)
    
    if success:
        print("\nApplication exited successfully.")
    else:
        print("\nApplication exited with errors.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
