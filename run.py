from core.kernel import Kernel


def main():
    """The main entry point of the application."""
    print("Starting Sophia's kernel...")
    kernel = Kernel()
    kernel.start()
    print("Sophia's kernel has been terminated.")


if __name__ == "__main__":
    main()
