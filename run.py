"""
Skill Assessment System - Universal Launcher

This file handles everything:
- Python environment setup
- Virtual environment creation
- Dependency installation
- Browser auto-launch
- FastAPI server startup
"""

import os
import sys
import subprocess
import time
import webbrowser
import platform
import warnings
from pathlib import Path

# Suppress non-critical warnings for cleaner console output
warnings.filterwarnings('ignore', category=UserWarning, module='pydantic')
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*ARC4.*')


class ServerLauncher:
    """Unified server launcher with environment setup"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / "venv"
        self.requirements_file = self.project_root / "requirements.txt"
        self.is_windows = platform.system() == "Windows"
        
    def check_python(self):
        """Check if Python is properly installed"""
        print("=" * 50)
        print("Checking Python Installation...")
        print("=" * 50)
        
        try:
            version = subprocess.check_output(
                [sys.executable, "--version"], 
                stderr=subprocess.STDOUT,
                text=True
            ).strip()
            print(f"✓ Python found: {version}")
            return True
        except Exception as e:
            print(f"✗ Error: Python is not properly installed")
            print(f"  Details: {e}")
            print("\n  Please install Python from https://python.org")
            return False
    
    def setup_virtual_environment(self):
        """Create virtual environment if it doesn't exist"""
        print("\n" + "=" * 50)
        print("Setting Up Virtual Environment...")
        print("=" * 50)
        
        if self.venv_path.exists():
            print(f"✓ Virtual environment already exists at: {self.venv_path}")
            return True
        
        try:
            print(f"Creating virtual environment...")
            subprocess.run(
                [sys.executable, "-m", "venv", str(self.venv_path)],
                check=True,
                capture_output=True
            )
            print(f"✓ Virtual environment created successfully")
            return True
        except Exception as e:
            print(f"✗ Failed to create virtual environment")
            print(f"  Error: {e}")
            return False
    
    def get_python_executable(self):
        """Get the path to Python executable in venv"""
        if self.is_windows:
            return self.venv_path / "Scripts" / "python.exe"
        else:
            return self.venv_path / "bin" / "python"
    
    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        print("\n" + "=" * 50)
        print("Upgrading pip...")
        print("=" * 50)
        
        python_exe = self.get_python_executable()
        
        try:
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "--upgrade", "pip"],
                check=True,
                capture_output=True
            )
            print("✓ pip upgraded successfully")
            return True
        except Exception as e:
            print(f"⚠ Warning: Could not upgrade pip (non-critical)")
            print(f"  Error: {e}")
            return False  # Non-critical, continue anyway
    
    def install_dependencies(self):
        """Install/update project dependencies"""
        print("\n" + "=" * 50)
        print("Installing Dependencies...")
        print("=" * 50)
        
        if not self.requirements_file.exists():
            print(f"✗ requirements.txt not found at: {self.requirements_file}")
            return False
        
        python_exe = self.get_python_executable()
        
        try:
            print(f"Installing packages from requirements.txt...")
            subprocess.run(
                [str(python_exe), "-m", "pip", "install", "-r", str(self.requirements_file)],
                check=True
            )
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to install dependencies")
            print(f"  Error: {e}")
            return False
        except Exception as e:
            print(f"✗ Unexpected error during dependency installation")
            print(f"  Error: {e}")
            return False
    
    def open_browser(self, port=19440, delay=4):
        """Open browser to API endpoint after delay"""
        def open_url():
            time.sleep(delay)
            url = f"http://localhost:{port}"
            print(f"\n📱 Opening browser at {url}...")
            try:
                webbrowser.open(url)
            except Exception as e:
                print(f"⚠ Could not open browser automatically: {e}")
                print(f"  Visit {url} manually in your browser")
        
        # Run in separate thread so it doesn't block server
        import threading
        thread = threading.Thread(target=open_url, daemon=True)
        thread.start()
    
    def start_server(self):
        """Start the FastAPI server"""
        print("\n" + "=" * 50)
        print("Starting FastAPI Server...")
        print("=" * 50)
        
        # Import here to ensure dependencies are installed
        try:
            import uvicorn
            from app.core import settings
        except ImportError as e:
            print(f"✗ Failed to import required modules")
            print(f"  Error: {e}")
            print(f"  Make sure dependencies are installed")
            return False
        
        print(f"Server will run at: http://{settings.API_HOST}:{settings.API_PORT}")
        print(f"API Docs: http://localhost:{settings.API_PORT}/docs")
        print(f"\nPress CTRL+C to stop the server\n")
        
        # Open browser in background
        self.open_browser(port=settings.API_PORT)
        
        try:
            # Start the server
            uvicorn.run(
                "app.main:app",
                host=settings.API_HOST,
                port=settings.API_PORT,
                reload=settings.API_RELOAD,
                log_level="info"
            )
            return True
        except KeyboardInterrupt:
            print("\n\n" + "=" * 50)
            print("Server stopped by user")
            print("=" * 50)
            return True
        except Exception as e:
            print(f"\n✗ Error starting server: {e}")
            return False
    
    def run(self):
        """Execute the full startup sequence"""
        print("\n")
        print("╔" + "=" * 48 + "╗")
        print("║" + " " * 48 + "║")
        print("║" + "  SKILL ASSESSMENT SYSTEM - LAUNCHER".center(48) + "║")
        print("║" + " " * 48 + "║")
        print("╚" + "=" * 48 + "╝")
        print()
        
        # Step 1: Check Python
        if not self.check_python():
            self.pause_and_exit(1)
            return False
        
        # Step 2: Setup virtual environment
        if not self.setup_virtual_environment():
            self.pause_and_exit(1)
            return False
        
        # Step 3: Upgrade pip
        self.upgrade_pip()
        
        # Step 4: Install dependencies
        if not self.install_dependencies():
            self.pause_and_exit(1)
            return False
        
        # Step 5: Start server
        if not self.start_server():
            self.pause_and_exit(1)
            return False
        
        return True
    
    def pause_and_exit(self, code=0):
        """Pause console (for Windows) and exit"""
        if self.is_windows:
            try:
                input("\nPress ENTER to exit...")
            except:
                pass
        sys.exit(code)


def main():
    """Main entry point"""
    launcher = ServerLauncher()
    success = launcher.run()
    
    if not success:
        launcher.pause_and_exit(1)
    
    launcher.pause_and_exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nExiting...")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        sys.exit(1)
