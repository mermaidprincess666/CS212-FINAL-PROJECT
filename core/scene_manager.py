"""Choose which screen is active and handle fades between screens."""

import pygame

from screens.characters import CharacterScene
from screens.info import InfoScene
from screens.introduction import IntroScene
from screens.menu import GateScene, MenuScene
from settings import HEIGHT, SCREEN_FADE_COLOR, SCREEN_FADE_SPEED, WHITE_IN_TIME, WIDTH


class SceneManager:
    """Route input and transitions between the game's screen objects."""

    def __init__(self, game):
        self.game = game
        menu_scene = MenuScene(game)
        self.scenes = {
            "menu": menu_scene,
            # The gate animates the menu's own artwork and camera, so it draws
            # through the same instance instead of loading the art twice.
            "gate": GateScene(game, menu_scene),
            "intro": IntroScene(game),
            "character": CharacterScene(game),
            "continue": InfoScene(game, "Continue", ["No saved game yet.", "(Saving comes in a later stage.)"]),
            "settings": InfoScene(game, "Settings", ["Settings will be added later."]),
            "about": InfoScene(game, "About Us", ["SLICE by PyAgustinos", "A cozy pizza restaurant game."]),
        }
        self.current_name = "menu"
        self.next_name = "menu"
        self.screen_fade_state = "none"
        self.screen_fade_alpha = 0
        # Strength of the story reveal: 1.0 straight after the gate covers the
        # screen, eased back to 0 as the story shows through the haze.
        self.white_in_alpha = 0.0
        # The shared fade overlay. The name is a leftover from the old single
        # file, which filled this with black; it now carries the ivory tint.
        self.black_surface = pygame.Surface((WIDTH, HEIGHT))
        self.black_surface.fill(SCREEN_FADE_COLOR)

    @property
    def current_scene(self):
        """The screen currently receiving input and drawing."""
        return self.scenes[self.current_name]

    def handle_event(self, event):
        """Handle global Escape behavior, then pass input to the active screen."""
        # Screens get no input while a fade is running, so a click cannot
        # land halfway across two scenes.
        if self.screen_fade_state != "none":
            return

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if self.current_name == "menu":
                self.game.running = False
            else:
                self.go_to("menu")
            return

        self.current_scene.handle_event(event)

    def go_to(self, name):
        """Fade out, switch to ``name``, then fade back in.

        Requests made during another fade are dropped rather than queued.
        """
        self._check_scene_name(name)
        if self.screen_fade_state == "none":
            self.next_name = name
            self.screen_fade_state = "out"

    def set_scene(self, name):
        """Switch immediately for the menu's gate-opening animation."""
        self._check_scene_name(name)
        self.current_name = name
        if name == "gate":
            self.scenes["gate"].restart()

    def show_scene(self, name, white_fade=False):
        """Switch without a fade, for when an animation already covers the view.

        The gate calls this the instant its light fills the screen.
        ``white_fade=True`` fades that overlay off over the new scene.
        """
        self._check_scene_name(name)
        # Restart the story only when it is entered fresh from the menu;
        # arriving from character selection keeps the player where they were.
        reset_story = name == "intro" and self.current_name in ("menu", "gate")
        self._enter_scene(name, reset_story=reset_story)
        if white_fade:
            self.white_in_alpha = 1.0

    def _enter_scene(self, name, reset_story):
        """Point at ``name`` and clear any dialogue presentation left behind."""
        self.current_name = name
        if name == "gate":
            self.scenes["gate"].restart()
        self.scenes["intro"].reset_for_transition(reset_story)

    def _check_scene_name(self, name):
        if name not in self.scenes:
            available_screens = ", ".join(self.scenes)
            raise ValueError(
                f"Unknown screen '{name}'. Available screens: {available_screens}"
            )

    def update(self, delta_time):
        """Update the active screen, the scene fade, and the story reveal."""
        if self.screen_fade_state == "none":
            self.current_scene.update(delta_time)

        # "out" covers the old scene, "in" clears off the new one. The active
        # screen only swaps in the gap between them, while the overlay is full.
        if self.screen_fade_state == "out":
            self.screen_fade_alpha += SCREEN_FADE_SPEED
            if self.screen_fade_alpha >= 255:
                self.screen_fade_alpha = 255
                origin = self.current_name
                self._enter_scene(
                    self.next_name,
                    reset_story=self.next_name == "intro" and origin in ("menu", "gate"),
                )
                self.screen_fade_state = "in"
        elif self.screen_fade_state == "in":
            self.screen_fade_alpha -= SCREEN_FADE_SPEED
            if self.screen_fade_alpha <= 0:
                self.screen_fade_alpha = 0
                self.screen_fade_state = "none"

        if self.white_in_alpha > 0:
            self.white_in_alpha = max(
                0.0, self.white_in_alpha - delta_time / WHITE_IN_TIME
            )

    def draw(self, target, mouse_pos):
        """Draw the active screen, then the shared fade layers."""
        self.current_scene.draw(target, mouse_pos)

        if self.screen_fade_alpha > 0:
            self.black_surface.set_alpha(self.screen_fade_alpha)
            target.blit(self.black_surface, (0, 0))

        if self.white_in_alpha > 0:
            self.game.warm_surface.set_alpha(int(255 * self._ease(self.white_in_alpha)))
            target.blit(self.game.warm_surface, (0, 0))

    @staticmethod
    def _ease(progress):
        """Use the gate's smooth easing curve for the white transition."""
        progress = max(0.0, min(1.0, progress))
        return progress**3 * (progress * (progress * 6 - 15) + 10)