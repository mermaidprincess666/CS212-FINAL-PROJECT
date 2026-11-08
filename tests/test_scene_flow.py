"""Behavior checks for the menu, gate, and story screens."""

import os
import unittest
from unittest.mock import patch

# Use SDL's dummy drivers for headless tests.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from core.game import Game
from screens.characters import CharacterScene
from screens.character_data import CHARACTERS
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
            "SETTINGS": "settings",
            "CREDIT": "about",
        }
        self.assertEqual(
            {label for label, _ in menu.buttons},
            {"START GAME", "SETTINGS", "CREDIT", "EXIT"},
        )

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

    def test_menu_music_toggle_and_scene_group(self):
        manager = self.game.scene_manager
        music = self.game.menu_music
        menu = manager.scenes["menu"]

        self.assertEqual(menu.music_button_rect.topleft, (24, 24))
        self.assertFalse(music.muted)

        with patch.object(pygame.mixer.music, "play") as play, patch.object(
            pygame.mixer.music, "stop"
        ) as stop, patch.object(pygame.mixer.music, "set_volume") as set_volume:
            manager._enter_scene("settings", reset_story=False)
            manager._enter_scene("about", reset_story=False)
            play.assert_not_called()
            stop.assert_not_called()

            click = pygame.event.Event(
                pygame.MOUSEBUTTONDOWN,
                button=1,
                pos=menu.music_button_rect.center,
            )
            menu.handle_event(click)
            self.assertTrue(music.muted)
            set_volume.assert_called_once_with(0.0)

            menu.handle_event(click)
            self.assertFalse(music.muted)
            self.assertEqual(set_volume.call_count, 2)
            self.assertEqual(set_volume.call_args_list[-1].args, (1.0,))
            play.assert_not_called()

            manager._enter_scene("gate", reset_story=False)
            stop.assert_called_once_with()
            manager._enter_scene("menu", reset_story=False)
            play.assert_called_once_with(-1)

    def test_every_registered_screen_can_draw(self):
        manager = self.game.scene_manager
        for name, scene in manager.scenes.items():
            with self.subTest(screen=name):
                scene.draw(self.game.screen, (0, 0))

    def test_character_selection_supports_keyboard_and_mouse(self):
        manager = self.game.scene_manager
        manager.show_scene("character")
        scene = manager.scenes["character"]

        manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_LEFT))
        self.assertEqual(scene.selected_index, 4)
        manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RIGHT))
        self.assertEqual(scene.selected_index, 0)

        monkey_portrait = scene.portrait_rects[2]
        manager.handle_event(
            pygame.event.Event(
                pygame.MOUSEBUTTONDOWN, button=1, pos=monkey_portrait.center
            )
        )
        self.assertEqual(scene.selected_index, 2)

        manager.handle_event(
            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        )
        self.assertEqual(self.game.selected_character["id"], "monkey")
        self.assertEqual(self.game.selected_character["ability"], "standard")
        self.assertEqual({character["ability"] for character in CHARACTERS}, {"standard"})

    def test_character_selection_draws_when_art_is_missing(self):
        with patch.object(
            self.game.assets, "load_image", side_effect=FileNotFoundError
        ):
            scene = CharacterScene(self.game)

        self.assertIsNone(scene.background)
        self.assertTrue(all(base is None for base, _, _ in scene.artwork))
        scene.draw(self.game.screen, (0, 0))

    def test_character_art_layers_keep_the_full_canvas_ratio(self):
        scene = self.game.scene_manager.scenes["character"]

        for idle, talking, hands in scene._large_surfaces:
            self.assertEqual(idle.get_size(), (960, 540))
            self.assertEqual(talking.get_size(), idle.get_size())
            self.assertEqual(hands.get_size(), idle.get_size())

    def test_character_escape_returns_to_the_intro(self):
        manager = self.game.scene_manager
        manager.show_scene("character")

        manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))

        self.assertEqual(manager.next_name, "intro")
        self.assertEqual(manager.screen_fade_state, "out")

    def test_f11_toggles_scaled_fullscreen_mode(self):
        manager = self.game.scene_manager

        manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
        self.assertTrue(self.game.fullscreen)
        manager.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_F11))
        self.assertFalse(self.game.fullscreen)

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