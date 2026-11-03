"""Start the SLICE game."""

from core.game import Game


def main():
    """Create the game and run it until the player exits."""
    Game().run()


if __name__ == "__main__":
    main()