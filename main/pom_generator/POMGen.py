import PyInstaller.__main__
import sys
import os
import shutil
from playwright.sync_api import sync_playwright
import subprocess


def get_playwright_resources():
    """Get Playwright browser and driver paths"""
    try:
        # Install playwright browsers if not already installed
        subprocess.run(['playwright', 'install', 'chromium'], check=True)

        # Get the Playwright cache directory
        with sync_playwright() as p:
            browser_path = p.chromium.executable_path
            browser_dir = os.path.dirname(os.path.dirname(browser_path))
            return browser_dir
    except Exception as e:
        print(f"Error setting up Playwright: {e}")
        sys.exit(1)


def create_executable():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Get Playwright resources
    playwright_dir = get_playwright_resources()

    # Create a temporary directory to store Playwright files
    temp_dir = os.path.join(current_dir, 'temp_playwright')
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Copy Playwright files to temporary directory
        shutil.copytree(playwright_dir, os.path.join(temp_dir, 'playwright'), dirs_exist_ok=True)

        # Define the path to the main script
        main_script = os.path.join(current_dir, 'pom_generator.py')

        # Define PyInstaller arguments
        args = [
            main_script,  # Your main script
            '--name=POMGenerator',  # Name of the executable
            '--onefile',  # Create a single executable file
            '--windowed',  # Don't show console window on Windows
            '--icon=app_icon.ico',  # No icon (you can specify path to .ico file if you have one)
            f'--add-data={os.path.join(temp_dir, "playwright")};playwright',  # Include Playwright files
            # Add required packages
            '--hidden-import=playwright',
            '--hidden-import=playwright.sync_api',
            '--hidden-import=PyQt5',
            '--hidden-import=PyQt5.QtWidgets',
            '--hidden-import=PyQt5.QtGui',
            '--hidden-import=PyQt5.QtCore',
            # Clean build
            '--clean',
            # High compression
            '--noupx',
        ]

        if os.name == 'posix':  # For Linux/Mac
            args[5] = f'--add-data={os.path.join(temp_dir, "playwright")}:playwright'

        # Run PyInstaller
        PyInstaller.__main__.run(args)

    except Exception as e:
        print(f"Error during build process: {e}")
        sys.exit(1)

    finally:
        # Clean up temporary directory
        try:
            shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temporary directory: {e}")


if __name__ == '__main__':
    create_executable()