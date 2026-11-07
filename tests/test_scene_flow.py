"""Behavior checks for the menu, gate, and story screens."""

import os
import unittest

# SDL dummy drivers, so the suite runs headless on a machine with no display.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from core.game import Game
from screens.introduction import INTRO_DIALOGUE
from settings import (
    GATE_ANIMATION_TIME,
    GATE_FADE_START,
    GATE_TOTAL_TIME,
    POP_LENGTH,
)


class SceneFlowTests(unittest.TestCase):
    """Cover the menu buttons, the gate cutscene, and dialogue advancement."""

    def setUp(self):
        pygame.init()
        self.game = Game()

    def tearDown(self):
        pygame.quit()

    def test_menu_buttons_keep_their_destinations(self):
        menu = self.game.scene_manager.scenes["menu"]
        expected_destinations = {
            "CONTINUE": "continue",
            "SETTINGS": "settings",
            "ABOUT US": "about",
        }

        for label, destination in expected_destinations.items():
            with self.subTest(button=label):
                button = dict(menu.buttons)[label]
                event = pygame.event.Event(
                    pygame.MOUSEBUTTONDOWN, button=1, pos=button.center
                )
                menu.handle_event(event)
                self.assertEqual(self.game.scene_manager.next_name, destination)
                self.game.scene_manager.screen_fade_state = "none"

    def test_start_and_exit_buttons_keep_their_actions(self):
        manager = self.game.scene_manager
        menu = manager.scenes["menu"]
        buttons = dict(menu.buttons)

        manager.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=buttons["START GAME"].center
            )
        )
        self.assertEqual(manager.current_name, "gate")

        manager.set_scene("menu")
        self.game.running = True
        manager.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=buttons["EXIT"].center
            )
        )
        self.assertFalse(self.game.running)

    def test_every_registered_screen_can_draw(self):
        manager = self.game.scene_manager
        for name, scene in manager.scenes.items():
            with self.subTest(screen=name):
                scene.draw(self.game.screen, (0, 0))

    def test_gate_opens_into_the_intro(self):
        manager = self.game.scene_manager
        manager.set_scene("gate")

        frames = int(GATE_ANIMATION_TIME * 60) + 20
        for _ in range(frames):
            manager.update(1 / 60)

        self.assertEqual(manager.current_name, "intro")
        self.assertGreater(manager.white_in_alpha, 0)
        self.assertEqual(manager.scenes["intro"].index, 0)

    def test_gate_transition_uses_a_fade_without_particle_effects(self):
        menu = self.game.scene_manager.scenes["menu"]
        gate = self.game.scene_manager.scenes["gate"]
        gate.restart()
        midpoint = GATE_FADE_START + (GATE_TOTAL_TIME - GATE_FADE_START) * 0.5

        menu.draw_gate(self.game.screen, midpoint)

        self.assertFalse(hasattr(menu, "gate_light"))
        self.assertGreater(self.game.warm_surface.get_alpha(), 0)
        self.assertLess(self.game.warm_surface.get_alpha(), 255)

    def test_gate_keyboard_skip_uses_the_black_fade(self):
        manager = self.game.scene_manager
        manager.set_scene("gate")
        manager.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
        )

        for _ in range(52):
            manager.update(1 / 60)

        self.assertEqual(manager.current_name, "intro")
        self.assertEqual(manager.screen_fade_state, "none")
        self.assertEqual(manager.scenes["intro"].index, 0)

    def test_first_advance_finishes_typing_before_changing_line(self):
        manager = self.game.scene_manager
        manager.show_scene("intro")
        intro = manager.scenes["intro"]
        space = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)

        intro.handle_event(space)
        manager.update(1 / 60)
        expected_end = len(INTRO_DIALOGUE[0][1]) + POP_LENGTH
        self.assertEqual(intro.characters_shown, expected_end)
        self.assertEqual(intro.index, 0)

        intro.handle_event(space)
        manager.update(1 / 60)
        self.assertEqual(intro.fade_state, "out")
        self.assertEqual(intro.index, 0)


if __name__ == "__main__":
    unittest.main()