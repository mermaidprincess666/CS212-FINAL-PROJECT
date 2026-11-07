"""Main menu and the gate-opening transition animation."""

import math

import pygame

from screens.common import draw_button, draw_text_center, ease
from settings import (
    BUTTON_GAP,
    BUTTON_HEIGHT,
    BUTTON_START_Y,
    BUTTON_WIDTH,
    BUTTON_X,
    CREAM,
    GATE_ANIMATION_TIME,
    GATE_FADE_START,
    GATE_FOCUS,
    GATE_OPEN_AMOUNT,
    GATE_OPEN_DELAY,
    GATE_OPEN_TIME,
    GATE_TOTAL_TIME,
    GATE_ZOOM_END,
    GATE_ZOOM_TIME,
    HEIGHT,
    MENU_UI_FADE,
    MENU_UI_SLIDE,
    SRC_H,
    SRC_W,
    TITLE_COLOR,
    TITLE_HEIGHT,
    TITLE_WIDTH,
    TITLE_X,
    TITLE_Y,
    WHITE,
    WIDTH,
)


MENU_BUTTON_NAMES = ("START GAME", "CONTINUE", "SETTINGS", "ABOUT US", "EXIT")

class MenuScene:
    """Draw and handle the main menu and its gate artwork."""

    def __init__(self, game):
        self.game = game
        self.title_font = game.fonts["title"]
        self.button_font = game.fonts["button"]
        self.label_font = game.fonts["label"]

        self.title_area = pygame.Rect(TITLE_X, TITLE_Y, TITLE_WIDTH, TITLE_HEIGHT)
        self.buttons = []
        for index, name in enumerate(MENU_BUTTON_NAMES):
            button_y = BUTTON_START_Y + index * (BUTTON_HEIGHT + BUTTON_GAP)
            self.buttons.append(
                (name, pygame.Rect(BUTTON_X, button_y, BUTTON_WIDTH, BUTTON_HEIGHT))
            )

        panel_height = (
            len(self.buttons) * (BUTTON_HEIGHT + BUTTON_GAP) - BUTTON_GAP + 44
        )
        self.button_panel = pygame.Rect(
            BUTTON_X - 28, BUTTON_START_Y - 22, BUTTON_WIDTH + 56, panel_height
        )
        self.ui_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._compose_key = None
        self._camera_key = None
        self._camera_frame = None
        self._load_gate_artwork()

    def _load_gate_artwork(self):
        """Load the four gate images and prepare the still menu background."""
        self.gate_bg = self.game.assets.load_image("BG.png", (SRC_W, SRC_H))
        self.gate_frame = self.game.assets.load_image("gate fence.png", (SRC_W, SRC_H))
        left_full = self.game.assets.load_image("left gate.png", (SRC_W, SRC_H))
        right_full = self.game.assets.load_image("right gate.png", (SRC_W, SRC_H))

        self.left_rect = left_full.get_bounding_rect()
        self.right_rect = right_full.get_bounding_rect()
        # Trim each door to its opaque pixels, so swinging it open squashes the
        # door itself and not the transparent padding around it.
        self.left_gate = left_full.subsurface(self.left_rect).copy()
        self.right_gate = right_full.subsurface(self.right_rect).copy()
        self.gate_canvas = pygame.Surface((SRC_W, SRC_H)).convert()
        self.compose_scene(0)
        self.menu_background = pygame.transform.smoothscale(
            self.gate_canvas, (WIDTH, HEIGHT)
        )

    def handle_event(self, event):
        """Handle clicks on the main menu."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        for name, rect in self.buttons:
            if not rect.collidepoint(event.pos):
                continue

            if name == "START GAME":
                self.game.scene_manager.set_scene("gate")
            elif name == "EXIT":
                self.game.running = False
            else:
                destinations = {
                    "CONTINUE": "continue",
                    "SETTINGS": "settings",
                    "ABOUT US": "about",
                }
                self.game.scene_manager.go_to(destinations[name])
            return

    def update(self, delta_time):
        """The menu background is still, so it has no per-frame updates."""

    def draw(self, target, mouse_pos):
        """Draw the still gate background and menu controls."""
        target.blit(self.menu_background, (0, 0))
        self.draw_menu_ui(target, mouse_pos)

    def draw_menu_ui(self, target, mouse_pos, alpha=1.0, x_offset=0):
        """Draw the title and buttons on a transparent layer.

        They are composed on one scratch surface so the fade and the slide
        apply to the whole menu as a unit during the gate animation.
        """
        if alpha <= 0:
            return

        self.ui_layer.fill((0, 0, 0, 0))
        # CREAM at 170 alpha, so the gate art still reads through the panel.
        pygame.draw.rect(
            self.ui_layer, (252, 243, 225, 170), self.button_panel, border_radius=22
        )
        pygame.draw.rect(self.ui_layer, CREAM, self.title_area, border_radius=20)
        pygame.draw.rect(
            self.ui_layer, TITLE_COLOR, self.title_area, 4, border_radius=20
        )
        draw_text_center(
            self.ui_layer,
            "SLICE",
            self.title_font,
            TITLE_COLOR,
            (self.title_area.centerx, self.title_area.centery - 15),
        )
        draw_text_center(
            self.ui_layer,
            "by PyAgustinos",
            self.label_font,
            TITLE_COLOR,
            (self.title_area.centerx, self.title_area.centery + 30),
        )

        for name, rect in self.buttons:
            draw_button(self.ui_layer, rect, name, mouse_pos, self.button_font)

        self.ui_layer.set_alpha(int(255 * alpha))
        target.blit(self.ui_layer, (round(x_offset), 0))

    def compose_scene(self, open_amount):
        """Build the gate artwork, with the doors swung open by ``open_amount``.

        The result is cached, so the doors are only rescaled on the frames
        where their swing actually changes. Compositing invalidates the camera
        cache too, since the surface it crops from has just changed.
        """
        key = round(open_amount, 3)
        if key == self._compose_key:
            return
        self._compose_key = key

        swing = ease(open_amount)
        self.gate_canvas.blit(self.gate_bg, (0, 0))

        squash = 1 - swing * GATE_OPEN_AMOUNT
        left_width = max(1, round(self.left_rect.width * squash))
        right_width = max(1, round(self.right_rect.width * squash))
        if left_width == self.left_rect.width:
            left_image = self.left_gate
            right_image = self.right_gate
        else:
            left_image = pygame.transform.smoothscale(
                self.left_gate, (left_width, self.left_rect.height)
            )
            right_image = pygame.transform.smoothscale(
                self.right_gate, (right_width, self.right_rect.height)
            )

        self.gate_canvas.blit(left_image, (self.left_rect.x, self.left_rect.y))
        self.gate_canvas.blit(
            right_image, (self.right_rect.right - right_width, self.right_rect.y)
        )
        self.gate_canvas.blit(self.gate_frame, (0, 0))
        self._camera_key = None

    def draw_camera(self, target, zoom_progress):
        """Render the gate canvas through the same smooth zooming camera.

        Returns where the arch (``GATE_FOCUS``) lands on the screen, so the
        glow can sit on the gate while the camera drifts toward the center.
        """
        zoom = GATE_ZOOM_END**zoom_progress
        view_width = SRC_W / zoom
        view_height = SRC_H / zoom

        focus_x = GATE_FOCUS[0] / SRC_W
        focus_y = GATE_FOCUS[1] / SRC_H
        screen_focus_x = focus_x + (0.5 - focus_x) * zoom_progress
        screen_focus_y = focus_y + (0.5 - focus_y) * zoom_progress
        view_x = GATE_FOCUS[0] - screen_focus_x * view_width
        view_y = GATE_FOCUS[1] - screen_focus_y * view_height
        view_x = max(0.0, min(SRC_W - view_width, view_x))
        view_y = max(0.0, min(SRC_H - view_height, view_y))

        crop_x = int(math.floor(view_x))
        crop_y = int(math.floor(view_y))
        crop_width = min(SRC_W - crop_x, int(math.ceil(view_x + view_width)) - crop_x)
        crop_height = min(SRC_H - crop_y, int(math.ceil(view_y + view_height)) - crop_y)
        scale = WIDTH / view_width
        crop_width_px = max(1, round(crop_width * scale))
        crop_height_px = max(1, round(crop_height * scale))
        key = (crop_x, crop_y, crop_width, crop_height, crop_width_px, crop_height_px)
        if key != self._camera_key:
            # The camera only resamples when its crop or size changes, which
            # keeps the long still prelude as cheap as a single blit.
            self._camera_key = key
            crop = self.gate_canvas.subsurface(
                pygame.Rect(crop_x, crop_y, crop_width, crop_height)
            )
            self._camera_frame = pygame.transform.smoothscale(
                crop, (crop_width_px, crop_height_px)
            )
        target.blit(
            self._camera_frame,
            (round((crop_x - view_x) * scale), round((crop_y - view_y) * scale)),
        )
        return ((GATE_FOCUS[0] - view_x) * scale, (GATE_FOCUS[1] - view_y) * scale)

    def draw_gate(self, target, elapsed):
        """Draw the doors opening, then fade to the story scene."""
        gate_elapsed = elapsed

        open_amount = (gate_elapsed - GATE_OPEN_DELAY) / GATE_OPEN_TIME
        self.compose_scene(open_amount)
        self.draw_camera(target, ease(gate_elapsed / GATE_ZOOM_TIME))

        ui_progress = ease(elapsed / MENU_UI_FADE)
        self.draw_menu_ui(
            target,
            (-1, -1),
            (1 - ui_progress) ** 1.5,
            MENU_UI_SLIDE * ui_progress,
        )

        fade_progress = ease((gate_elapsed - GATE_FADE_START) / (GATE_TOTAL_TIME - GATE_FADE_START))
        if fade_progress > 0:
            self.game.warm_surface.set_alpha(round(255 * fade_progress**2))
            target.blit(self.game.warm_surface, (0, 0))


class GateScene:
    """Advance and draw the short animation between menu and story."""

    def __init__(self, game, menu_scene):
        self.game = game
        self.menu_scene = menu_scene
        self.covered = False
        self.restart()

    def restart(self):
        """Play the animation from the start, armed to hand over once."""
        self.elapsed = 0.0
        self.covered = False

    def handle_event(self, event):
        """A click or Enter/Space skips ahead, fading over to the story."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.game.scene_manager.go_to("intro")
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.game.scene_manager.go_to("intro")

    def update(self, delta_time):
        """Advance the cutscene clock, so its timing holds at any frame rate."""
        if self.game.scene_manager.screen_fade_state != "none" or self.covered:
            return

        self.elapsed += delta_time
        if self.elapsed >= GATE_ANIMATION_TIME:
            # The screen is fully covered at this instant; hand over exactly
            # once and let the overlay fade out over the story.
            self.covered = True
            self.game.scene_manager.show_scene("intro", white_fade=True)

    def draw(self, target, mouse_pos):
        """Draw the current frame of the gate animation."""
        self.menu_scene.draw_gate(target, self.elapsed)