#!/usr/bin/env python
"""
Setup script for Gym Optimizer project.
This script will:
1. Create a virtual environment
2. Install dependencies
3. Create a .env file
4. Run migrations
5. Create a superuser
6. Initialize sample data
"""
import os
import sys
import subprocess
import platform
import random
import string
import shutil
from pathlib import Path


def is_venv():
    """Check if running in a virtual environment"""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)


def create_venv():
    """Create a virtual environment"""
    if is_venv():
        print("Already running in a virtual environment.")
        return True

    print("Creating a virtual environment...")
    try:
        subprocess.run([sys.executable, "-m", "venv", "venv"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error creating virtual environment: {e}")
        return False


def activate_venv():
    """Activate the virtual environment"""
    if is_venv():
        return

    if platform.system() == "Windows":
        activate_script = "venv\\Scripts\\activate.bat"
    else:
        activate_script = "venv/bin/activate"

    if os.path.exists(activate_script):
        print(f"Virtual environment created. Please activate it manually with:\n\t{activate_script}")
        print("Then run this script again.")
        sys.exit(0)
    else:
        print("Virtual environment activation script not found.")
        sys.exit(1)


def install_dependencies():
    """Install dependencies from requirements.txt"""
    if not is_venv():
        print("Not running in a virtual environment. Please activate it first.")
        return False

    print("Installing dependencies...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing dependencies: {e}")
        return False


def create_env_file():
    """Create .env file if it doesn't exist"""
    env_file = Path(".env")
    env_sample = Path(".env.sample")

    if env_file.exists():
        print(".env file already exists.")
        return

    if not env_sample.exists():
        print(".env.sample file not found.")
        return

    # Generate a random secret key
    secret_key = ''.join(random.choice(string.ascii_letters + string.digits + string.punctuation) for _ in range(50))

    # Read .env.sample and replace placeholders
    with open(env_sample, 'r') as f:
        env_content = f.read()

    env_content = env_content.replace('django-insecure-change-this-in-production', secret_key)

    # Write to .env
    with open(env_file, 'w') as f:
        f.write(env_content)

    print(".env file created.")


def run_migrations():
    """Run Django migrations"""
    print("Running migrations...")
    try:
        subprocess.run([sys.executable, "manage.py", "migrate"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running migrations: {e}")
        return False


def initialize_data():
    """Initialize sample data"""
    print("Initializing sample data...")
    try:
        subprocess.run([sys.executable, "initialize_data.py"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error initializing data: {e}")
        return False


def collect_static():
    """Collect static files"""
    print("Collecting static files...")
    try:
        subprocess.run([sys.executable, "manage.py", "collectstatic", "--noinput"], check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error collecting static files: {e}")
        return False


def main():
    """Main function to run setup steps"""
    print("Setting up Gym Optimizer project...\n")

    # Check if we're in the right directory
    if not os.path.exists("manage.py"):
        print("Error: manage.py not found. Please run this script from the project root directory.")
        sys.exit(1)

    # Create and activate virtual environment if needed
    if not is_venv():
        if create_venv():
            activate_venv()
        else:
            sys.exit(1)

    # Install dependencies
    if not install_dependencies():
        sys.exit(1)

    # Create .env file
    create_env_file()

    # Run migrations
    if not run_migrations():
        sys.exit(1)

    # Initialize sample data
    if not initialize_data():
        sys.exit(1)

    # Collect static files
    if not collect_static():
        sys.exit(1)

    print("\nSetup completed successfully!")
    print("\nYou can now start the development server with:")
    print("\tpython manage.py runserver")
    print("\nAccess the application at http://127.0.0.1:8000/")
    print("\nAdmin credentials:")
    print("\tUsername: admin")
    print("\tPassword: adminpassword")


if __name__ == "__main__":
    main()