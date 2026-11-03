"""Behavior checks for the menu, gate, and story screens."""

import math
import os
import unittest

# SDL dummy drivers, so the suite runs headless on a machine with no display.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from core.game import Game
from screens import gate_light
from screens.introduction import INTRO_DIALOGUE
from settings import (
    GATE_ANIMATION_TIME,
    GATE_FADE_START,
    GATE_LIGHT_APPEAR_TIME,
    GATE_LIGHT_DART_TIME,
    GATE_LIGHT_FLOAT_TIME,
    GATE_LIGHT_PRELUDE_TIME,
    GATE_LIGHT_START_RADIUS,
    GATE_TOTAL_TIME,
    HEIGHT,
    POP_LENGTH,
    WIDTH,
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

    def test_gate_light_wanders_then_dives_into_the_arch(self):
        menu = self.game.scene_manager.scenes["menu"]
        gate = self.game.scene_manager.scenes["gate"]
        light = menu.gate_light
        arch = menu.draw_camera(self.game.screen, 0.0)

        gate.restart()

        def step_to(seconds):
            """Run the cutscene at 60 fps until the clock reaches ``seconds``."""
            while gate.elapsed < seconds:
                gate.update(1 / 60)
                menu.draw_gate(self.game.screen, gate.elapsed, 1 / 60)

        # Sample in the middle of the float window, never on a phase boundary.
        step_to(GATE_LIGHT_APPEAR_TIME + GATE_LIGHT_FLOAT_TIME * 0.5)

        # Mid-wander the light is alive, inside the frame, and away from the gate.
        self.assertEqual(light.phase, gate_light.PHASE_FLOAT)
        self.assertFalse(light.particles)
        x, y = light.pos
        self.assertTrue(0 < x < WIDTH and 0 < y < HEIGHT)
        self.assertGreater(math.dist(light.pos, arch), 40)

        # Ninety percent along the dive, still before the prelude hands over.
        step_to(GATE_LIGHT_PRELUDE_TIME - GATE_LIGHT_DART_TIME * 0.1)

        # At the end of the dive it has reached the camera's gate position.
        self.assertEqual(light.phase, gate_light.PHASE_DART)
        self.assertLess(math.dist(light.pos, arch), 25.0)
        self.assertTrue(light.trail)

    def test_particles_are_held_until_the_final_cover(self):
        menu = self.game.scene_manager.scenes["menu"]
        gate = self.game.scene_manager.scenes["gate"]
        light = menu.gate_light

        gate.restart()

        def step_to(seconds):
            """Run the cutscene at 60 fps until the clock reaches ``seconds``."""
            while gate.elapsed < seconds:
                gate.update(1 / 60)
                menu.draw_gate(self.game.screen, gate.elapsed, 1 / 60)

        # Menu fade-out, the dive, and the ignition half of the door swing.
        step_to(GATE_LIGHT_PRELUDE_TIME + GATE_FADE_START * 0.5)
        self.assertEqual(light.phase, gate_light.PHASE_SPENT)
        self.assertFalse(light.particles)

        # Halfway through the cover the motes are alive and fanning outward.
        cover = GATE_LIGHT_PRELUDE_TIME + GATE_FADE_START
        cover += (GATE_TOTAL_TIME - GATE_FADE_START) * 0.5
        step_to(cover)

        self.assertTrue(light.particles)
        arch = light.pos
        reach = max(
            math.dist((particle["x"], particle["y"]), arch)
            for particle in light.particles
        )
        self.assertGreater(reach, GATE_LIGHT_START_RADIUS)

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