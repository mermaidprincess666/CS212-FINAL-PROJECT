
"""Choose which screen is active and handle fades between screens."""

import pygame

from core.shop_clock import ShopClock

from screens.character import CharacterScene
from screens.info import InfoScene
from screens.introduction import IntroScene
from screens.menu import GateScene, MenuScene
from screens.settings import SettingsScreen
from screens.credits import CreditsScreen
from screens.welcome import WelcomeScene
from screens.kitchen import KitchenScene
from screens.oven import OvenScene

from settings import (
    HEIGHT,
    SCREEN_FADE_COLOR,
    SCREEN_FADE_SPEED,
    WHITE_IN_TIME,
    WIDTH,
)


MENU_MUSIC_SCENES = {
    "menu",
    "continue",
    "settings",
    "about",
    "credits",
}


class SceneManager:
    """Route input and transitions between screens."""

    def __init__(self, game):
        self.game = game

        # One shared clock for all gameplay screens
        self.shop_clock = ShopClock(game)

        menu_scene = MenuScene(game)

        self.scenes = {
            "menu": menu_scene,
            "gate": GateScene(game, menu_scene),
            "intro": IntroScene(game),
            "character": CharacterScene(game),
            "welcome": WelcomeScene(game),
            "kitchen": KitchenScene(game),
            "oven": OvenScene(game),
            "continue": InfoScene(
                game,
                "Continue",
                [
                    "No saved game yet.",
                    "(Saving comes in a later stage.)",
                ],
            ),
            "settings": SettingsScreen(game),
            "credits": CreditsScreen(game),
        }

        self.current_name = "menu"
        self.next_name = "menu"

        self.screen_fade_state = "none"
        self.screen_fade_alpha = 0

        self.white_in_alpha = 0.0

        self.black_surface = pygame.Surface(
            (WIDTH, HEIGHT)
        )
        self.black_surface.fill(SCREEN_FADE_COLOR)

        self._sync_menu_music()

    @property
    def current_scene(self):
        """Return the current scene."""
        return self.scenes[self.current_name]

    def handle_event(self, event):
        """Handle global controls and scene input."""

        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_F11
        ):
            self.game.toggle_fullscreen()
            return

        if self.screen_fade_state != "none":
            return

        if (
            event.type == pygame.KEYDOWN
            and event.key == pygame.K_ESCAPE
            and self.current_name not in (
                "character",
                "welcome",
            )
        ):
            if self.current_name == "menu":
                self.game.running = False
            else:
                self.go_to("menu")
            return

        self.current_scene.handle_event(event)

    def go_to(self, name):
        """Fade out, switch scene, then fade in."""
        self._check_scene_name(name)

        if self.screen_fade_state == "none":
            self.next_name = name
            self.screen_fade_state = "out"

    def set_scene(self, name):
        """Switch immediately for gate animations."""
        self._check_scene_name(name)

        self.current_name = name
        self._sync_menu_music()

        if name == "gate":
            self.scenes["gate"].restart()

    def show_scene(self, name, white_fade=False):
        """Switch without a normal fade."""
        self._check_scene_name(name)

        reset_story = (
            name == "intro"
            and self.current_name in ("menu", "gate")
        )

        self._enter_scene(
            name,
            reset_story=reset_story,
        )

        if white_fade:
            self.white_in_alpha = 1.0

    def _enter_scene(self, name, reset_story):
        """Switch and clear previous dialogue state."""
        self.current_name = name
        self._sync_menu_music()

        if name == "gate":
            self.scenes["gate"].restart()

        self.scenes["intro"].reset_for_transition(
            reset_story
        )

    def _sync_menu_music(self):
        self.game.menu_music.set_active(
            self.current_name in MENU_MUSIC_SCENES
        )

    def _check_scene_name(self, name):
        if name not in self.scenes:
            available_screens = ", ".join(self.scenes)

            raise ValueError(
                f"Unknown screen '{name}'. "
                f"Available screens: {available_screens}"
            )

    def update(self, delta_time):
        """Update shop time, oven, scene, and fades."""

        # Shared clock runs while playing in any gameplay area
        if self.current_name in (
            "welcome",
            "kitchen",
            "oven",
        ):
            self.shop_clock.update(delta_time)

        # Oven continues cooking even in another scene
        self.scenes["oven"].update(delta_time)

        # Update active scene without updating oven twice
        if (
            self.screen_fade_state == "none"
            and self.current_name != "oven"
        ):
            self.current_scene.update(delta_time)

        # Fade out
        if self.screen_fade_state == "out":
            self.screen_fade_alpha += SCREEN_FADE_SPEED

            if self.screen_fade_alpha >= 255:
                self.screen_fade_alpha = 255
                origin = self.current_name

                self._enter_scene(
                    self.next_name,
                    reset_story=(
                        self.next_name == "intro"
                        and origin in ("menu", "gate")
                    ),
                )

                self.screen_fade_state = "in"

        # Fade in
        elif self.screen_fade_state == "in":
            self.screen_fade_alpha -= SCREEN_FADE_SPEED

            if self.screen_fade_alpha <= 0:
                self.screen_fade_alpha = 0
                self.screen_fade_state = "none"

        if self.white_in_alpha > 0:
            self.white_in_alpha = max(
                0.0,
                self.white_in_alpha
                - delta_time / WHITE_IN_TIME,
            )

    def draw(self, target, mouse_pos):
        """Draw scene, shared clock, and fades."""
        self.current_scene.draw(target, mouse_pos)

        # Welcome draws its own clock for tutorial highlights.
        # Kitchen and Oven share this same clock.
        if self.current_name in ("kitchen", "oven"):
            self.shop_clock.draw(target)

        if self.screen_fade_alpha > 0:
            self.black_surface.set_alpha(
                self.screen_fade_alpha
            )
            target.blit(
                self.black_surface,
                (0, 0),
            )

        if self.white_in_alpha > 0:
            self.game.warm_surface.set_alpha(
                int(255 * self._ease(self.white_in_alpha))
            )
            target.blit(
                self.game.warm_surface,
                (0, 0),
            )

    @staticmethod
    def _ease(progress):
        """Smooth transition easing."""
        progress = max(0.0, min(1.0, progress))

        return progress**3 * (
            progress * (progress * 6 - 15) + 10
        )
