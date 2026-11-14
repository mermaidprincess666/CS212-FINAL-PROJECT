"""Main menu and the gate-opening transition animation."""

import math

import pygame

from screens.common import draw_text_center, ease
from settings import (
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
    WIDTH,
)


MENU_BUTTONS = (
    ("START GAME", "start"),
    ("SETTINGS", "setting"),
    ("CREDIT", "credit"),
    ("EXIT", "exit"),
)

# Layout tuning
PIZZA_SCALE = 0.8          # smaller = smaller pizza (gives the logo more room)
PIZZA_MARGIN = 20          # gap from the bottom/right screen edges
LOGO_WIDTH_FACTOR = 2.4    # logo width relative to the pizza width (bigger = bigger logo)
LOGO_OVERLAP = 80          # how far the logo dips onto the pizza (bigger = lower, allows a bigger logo)
LOGO_TOP_MARGIN = 10       # minimum gap from the top of the screen
LOGO_SIDE_MARGIN = 10      # minimum gap from the left/right of the screen
CENTER_BIAS = 0.35         # 0 = far right, 1 = exact screen center (title + pizza move together)


class MenuScene:
    """Draw and handle the main menu and its gate artwork."""

    def __init__(self, game):
        self.game = game
        self.title_font = game.fonts["title"]
        self.label_font = game.fonts["label"]

        self.title_area = pygame.Rect(TITLE_X, TITLE_Y, TITLE_WIDTH, TITLE_HEIGHT)
        self.music_button_rect = pygame.Rect(24, 24, 48, 48)
        self.logo_image = None
        self.logo_rect = pygame.Rect(0, 0, 0, 0)
        self._music_pressed_until = 0
        self.buttons = []
        self.ui_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._pressed_button = None
        self._pressed_until = 0
        self._compose_key = None
        self._camera_key = None
        self._camera_frame = None
        self._load_menu_artwork()
        self._load_gate_artwork()

    def _load_menu_artwork(self):
        """Load the pizza composition and logo, sharing one center line."""
        source = self.game.assets.load_image(
            "pizza_menu.png", subdirectory="MENU/BUTTONS"
        )
        logo_source = self.game.assets.load_image(
            "title.png", subdirectory="MENU"
        )

        source_width, source_height = source.get_size()
        available_size = HEIGHT - TITLE_Y - TITLE_HEIGHT
        scale = (
            min(WIDTH, available_size) / max(source_width, source_height)
        ) * PIZZA_SCALE
        art_size = (round(source_width * scale), round(source_height * scale))
        self.menu_art = pygame.transform.smoothscale(source, art_size)
        self.menu_art_rect = pygame.Rect(0, 0, *art_size)
        self.menu_art_rect.bottom = HEIGHT - PIZZA_MARGIN
        self.button_art = {}

        # Logo size: as big as requested, limited by screen width and the
        # space above the pizza.
        logo_width = round(art_size[0] * LOGO_WIDTH_FACTOR)
        logo_width = min(logo_width, WIDTH - 2 * LOGO_SIDE_MARGIN)
        logo_height = round(
            logo_source.get_height() * logo_width / logo_source.get_width()
        )
        max_height = self.menu_art_rect.top + LOGO_OVERLAP - LOGO_TOP_MARGIN
        if logo_height > max_height > 0:
            shrink = max_height / logo_height
            logo_width = max(1, round(logo_width * shrink))
            logo_height = max(1, round(logo_height * shrink))
        self.logo_image = pygame.transform.smoothscale(
            logo_source, (logo_width, logo_height)
        )

        # Shared center line: starts at the right edge position, then moves
        # part of the way toward the screen center, and stays on screen.
        right_x = WIDTH - PIZZA_MARGIN - art_size[0] // 2
        center_x = round(right_x + (WIDTH / 2 - right_x) * CENTER_BIAS)
        half_logo = logo_width // 2 + LOGO_SIDE_MARGIN
        center_x = max(half_logo, min(center_x, WIDTH - half_logo))

        self.menu_art_rect.centerx = center_x
        self.logo_rect = self.logo_image.get_rect(
            midbottom=(center_x, self.menu_art_rect.top + LOGO_OVERLAP)
        )

        scale_x = art_size[0] / source_width
        scale_y = art_size[1] / source_height
        for name, filename in MENU_BUTTONS:
            normal = self.game.assets.load_image(
                f"{filename}.png", subdirectory="MENU/BUTTONS"
            )
            hover = self.game.assets.load_image(
                f"{filename}_h.png", subdirectory="MENU/BUTTONS"
            )
            source_bounds = normal.get_bounding_rect(min_alpha=16)
            left = round(self.menu_art_rect.x + source_bounds.left * scale_x)
            top = round(self.menu_art_rect.y + source_bounds.top * scale_y)
            right = round(self.menu_art_rect.x + source_bounds.right * scale_x)
            bottom = round(self.menu_art_rect.y + source_bounds.bottom * scale_y)
            self.buttons.append(
                (name, pygame.Rect(left, top, right - left, bottom - top))
            )
            self.button_art[name] = (
                pygame.transform.smoothscale(normal, art_size),
                pygame.transform.smoothscale(hover, art_size),
            )

    def _load_gate_artwork(self):
        """Load the four gate images and prepare the still menu background."""
        self.gate_bg = self.game.assets.load_image("BG.png", (SRC_W, SRC_H))
        self.gate_frame = self.game.assets.load_image("gate fence.png", (SRC_W, SRC_H))
        left_full = self.game.assets.load_image("left gate.png", (SRC_W, SRC_H))
        right_full = self.game.assets.load_image("right gate.png", (SRC_W, SRC_H))

        self.left_rect = left_full.get_bounding_rect()
        self.right_rect = right_full.get_bounding_rect()
        # Trim transparent padding so the door itself is squashed.
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

        if self.music_button_rect.collidepoint(event.pos):
            self.game.menu_music.toggle()
            self._music_pressed_until = pygame.time.get_ticks() + 110
            return

        for name, rect in self.buttons:
            if not rect.collidepoint(event.pos):
                continue

            self._pressed_button = name
            self._pressed_until = pygame.time.get_ticks() + 100
            if name == "START GAME":
                self.game.scene_manager.set_scene("gate")
            elif name == "EXIT":
                self.game.running = False
            else:
                destinations = {
    "SETTINGS": "settings",
    "CREDIT": "credits",
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
        self.ui_layer.blit(self.menu_art, self.menu_art_rect)

        if self.logo_image is not None:
            self.ui_layer.blit(self.logo_image, self.logo_rect)

        self._draw_music_button(mouse_pos)

        for name, rect in self.buttons:
            hovered = rect.collidepoint(mouse_pos)
            normal, hover = self.button_art[name]
            image = hover if hovered else normal
            if name == self._pressed_button and pygame.time.get_ticks() < self._pressed_until:
                image_rect = rect.move(-self.menu_art_rect.x, -self.menu_art_rect.y)
                button_image = image.subsurface(image_rect).copy()
                pressed_size = (
                    max(1, round(rect.width * 0.97)),
                    max(1, round(rect.height * 0.97)),
                )
                button_image = pygame.transform.smoothscale(button_image, pressed_size)
                self.ui_layer.blit(button_image, button_image.get_rect(center=rect.center))
            else:
                self.ui_layer.blit(image, self.menu_art_rect)

        self.ui_layer.set_alpha(int(255 * alpha))
        target.blit(self.ui_layer, (round(x_offset), 0))

    def _draw_music_button(self, mouse_pos):
        """Draw a compact speaker toggle in the padded top-left corner."""
        rect = self.music_button_rect
        hovered = rect.collidepoint(mouse_pos)
        pressed = pygame.time.get_ticks() < self._music_pressed_until
        fill = (235, 220, 195) if hovered else CREAM
        pygame.draw.rect(self.ui_layer, fill, rect, border_radius=12)
        pygame.draw.rect(self.ui_layer, TITLE_COLOR, rect, 2, border_radius=12)

        center_x = rect.centerx
        center_y = rect.centery + int(pressed)
        speaker = [
            (center_x - 12, center_y - 5),
            (center_x - 6, center_y - 5),
            (center_x + 2, center_y - 11),
            (center_x + 2, center_y + 11),
            (center_x - 6, center_y + 5),
            (center_x - 12, center_y + 5),
        ]
        pygame.draw.polygon(self.ui_layer, TITLE_COLOR, speaker)

        if self.game.menu_music.muted:
            pygame.draw.line(
                self.ui_layer, TITLE_COLOR,
                (center_x + 7, center_y - 6), (center_x + 14, center_y + 6), 3,
            )
            pygame.draw.line(
                self.ui_layer, TITLE_COLOR,
                (center_x + 14, center_y - 6), (center_x + 7, center_y + 6), 3,
            )
        else:
            pygame.draw.arc(
                self.ui_layer, TITLE_COLOR,
                pygame.Rect(center_x - 5, center_y - 10, 17, 20),
                -math.pi / 3, math.pi / 3, 2,
            )
            pygame.draw.arc(
                self.ui_layer, TITLE_COLOR,
                pygame.Rect(center_x - 7, center_y - 14, 25, 28),
                -math.pi / 3, math.pi / 3, 2,
            )

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
            destinations = {
    "SETTINGS": "settings",
    "CREDIT": "credits",
}

       # Rebuild only when the crop or output size changes.
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
            # Hand off once the cover is fully opaque.
            self.covered = True
            self.game.scene_manager.show_scene("intro", white_fade=True)

    def draw(self, target, mouse_pos):
        """Draw the current frame of the gate animation."""
        self.menu_scene.draw_gate(target, self.elapsed)