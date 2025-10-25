import sys
import os
from core.kernel import Kernel

def check_venv():
    """Check if the application is running in a virtual environment."""
    if sys.prefix == sys.base_prefix:
        print("---")
        print("ERROR: It looks like you are not running this application in a virtual environment.")
        print("Please activate the virtual environment first.")
        print("Example: source .venv/bin/activate")
        print("---")
        sys.exit(1)

def main():
    """The main entry point of the application."""
    check_venv()
    print("Starting Sophia's kernel...")
    kernel = Kernel()
    kernel.start()
    print("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    main()
