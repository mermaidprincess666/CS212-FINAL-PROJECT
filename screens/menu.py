"""Main menu and the gate-opening transition animation."""

import math
from pathlib import Path

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

PIZZA_SCALE = 0.8
PIZZA_MARGIN = 20
LOGO_WIDTH_FACTOR = 2.4
LOGO_OVERLAP = 80
LOGO_TOP_MARGIN = 10
LOGO_SIDE_MARGIN = 10
CENTER_BIAS = 0.35


class MenuScene:
    """Draw and handle the main menu and its gate artwork."""

    def __init__(self, game):
        self.game = game
        self.title_font = game.fonts["title"]
        self.label_font = game.fonts["label"]

        self.title_area = pygame.Rect(
            TITLE_X, TITLE_Y, TITLE_WIDTH, TITLE_HEIGHT
        )

        # Sound button
        self.music_button_rect = pygame.Rect(24, 24, 67, 67)

        self.sound_on_image = self._load_sound_button("sound.png")
        self.sound_off_image = self._load_sound_button("sound_m.png")

        self.logo_image = None
        self.logo_rect = pygame.Rect(0, 0, 0, 0)

        self._music_pressed_until = 0
        self.buttons = []

        self.ui_layer = pygame.Surface(
            (WIDTH, HEIGHT), pygame.SRCALPHA
        )

        self._pressed_button = None
        self._pressed_until = 0

        self._compose_key = None
        self._camera_key = None
        self._camera_frame = None

        self._load_menu_artwork()
        self._load_gate_artwork()

    def _load_sound_button(self, filename):
        image = self.game.assets.load_image(
            filename,
            subdirectory="MENU/SOUND"
        ).convert_alpha()

        # Remove transparent padding around the artwork.
        bounds = image.get_bounding_rect(min_alpha=10)

        if bounds.width > 0 and bounds.height > 0:
            image = image.subsurface(bounds).copy()

        # Preserve the PNG's original aspect ratio.
        image_width, image_height = image.get_size()

        scale = min(
            self.music_button_rect.width / image_width,
            self.music_button_rect.height / image_height
        )

        new_size = (
            max(1, round(image_width * scale)),
            max(1, round(image_height * scale))
        )

        return pygame.transform.smoothscale(
            image,
            new_size
        )

    def _load_menu_artwork(self):
        source = self.game.assets.load_image(
            "pizza_menu.png",
            subdirectory="MENU/BUTTONS"
        )

        logo_source = self.game.assets.load_image(
            "title.png",
            subdirectory="MENU"
        )

        source_width, source_height = source.get_size()

        available_size = HEIGHT - TITLE_Y - TITLE_HEIGHT

        scale = (
            min(WIDTH, available_size)
            / max(source_width, source_height)
        ) * PIZZA_SCALE

        art_size = (
            round(source_width * scale),
            round(source_height * scale)
        )

        self.menu_art = pygame.transform.smoothscale(
            source, art_size
        )

        self.menu_art_rect = pygame.Rect(
            0, 0, *art_size
        )

        self.menu_art_rect.bottom = HEIGHT - PIZZA_MARGIN

        self.button_art = {}

        logo_width = round(
            art_size[0] * LOGO_WIDTH_FACTOR
        )

        logo_width = min(
            logo_width,
            WIDTH - 2 * LOGO_SIDE_MARGIN
        )

        logo_height = round(
            logo_source.get_height()
            * logo_width
            / logo_source.get_width()
        )

        max_height = (
            self.menu_art_rect.top
            + LOGO_OVERLAP
            - LOGO_TOP_MARGIN
        )

        if logo_height > max_height > 0:
            shrink = max_height / logo_height

            logo_width = max(
                1, round(logo_width * shrink)
            )

            logo_height = max(
                1, round(logo_height * shrink)
            )

        self.logo_image = pygame.transform.smoothscale(
            logo_source,
            (logo_width, logo_height)
        )

        right_x = (
            WIDTH
            - PIZZA_MARGIN
            - art_size[0] // 2
        )

        center_x = round(
            right_x
            + (WIDTH / 2 - right_x) * CENTER_BIAS
        )

        half_logo = (
            logo_width // 2
            + LOGO_SIDE_MARGIN
        )

        center_x = max(
            half_logo,
            min(center_x, WIDTH - half_logo)
        )

        self.menu_art_rect.centerx = center_x

        self.logo_rect = self.logo_image.get_rect(
            midbottom=(
                center_x,
                self.menu_art_rect.top + LOGO_OVERLAP
            )
        )

        scale_x = art_size[0] / source_width
        scale_y = art_size[1] / source_height

        for name, filename in MENU_BUTTONS:
            normal = self.game.assets.load_image(
                f"{filename}.png",
                subdirectory="MENU/BUTTONS"
            )

            hover = self.game.assets.load_image(
                f"{filename}_h.png",
                subdirectory="MENU/BUTTONS"
            )

            source_bounds = normal.get_bounding_rect(
                min_alpha=16
            )

            left = round(
                self.menu_art_rect.x
                + source_bounds.left * scale_x
            )

            top = round(
                self.menu_art_rect.y
                + source_bounds.top * scale_y
            )

            right = round(
                self.menu_art_rect.x
                + source_bounds.right * scale_x
            )

            bottom = round(
                self.menu_art_rect.y
                + source_bounds.bottom * scale_y
            )

            self.buttons.append(
                (
                    name,
                    pygame.Rect(
                        left,
                        top,
                        right - left,
                        bottom - top
                    )
                )
            )

            self.button_art[name] = (
                pygame.transform.smoothscale(
                    normal, art_size
                ),
                pygame.transform.smoothscale(
                    hover, art_size
                )
            )

    def _load_gate_artwork(self):
        self.gate_bg = self.game.assets.load_image(
            "BG.png", (SRC_W, SRC_H)
        )

        self.gate_frame = self.game.assets.load_image(
            "gate fence.png", (SRC_W, SRC_H)
        )

        left_full = self.game.assets.load_image(
            "left gate.png", (SRC_W, SRC_H)
        )

        right_full = self.game.assets.load_image(
            "right gate.png", (SRC_W, SRC_H)
        )

        self.left_rect = left_full.get_bounding_rect()
        self.right_rect = right_full.get_bounding_rect()

        self.left_gate = left_full.subsurface(
            self.left_rect
        ).copy()

        self.right_gate = right_full.subsurface(
            self.right_rect
        ).copy()

        self.gate_canvas = pygame.Surface(
            (SRC_W, SRC_H)
        ).convert()

        self.compose_scene(0)

        self.menu_background = pygame.transform.smoothscale(
            self.gate_canvas,
            (WIDTH, HEIGHT)
        )

    def handle_event(self, event):
        if (
            event.type != pygame.MOUSEBUTTONDOWN
            or event.button != 1
        ):
            return

        if self.music_button_rect.collidepoint(event.pos):
            self.game.menu_music.toggle()

            self._music_pressed_until = (
                pygame.time.get_ticks() + 110
            )
            return

        for name, rect in self.buttons:
            if not rect.collidepoint(event.pos):
                continue

            self._pressed_button = name
            self._pressed_until = (
                pygame.time.get_ticks() + 100
            )

            if name == "START GAME":
                self.game.scene_manager.set_scene("gate")

            elif name == "SETTINGS":
                settings_scene = (
                    self.game.scene_manager.scenes["settings"]
                )

                settings_scene.start_popup()

                # Immediate scene switch, no screen fade.
                self.game.scene_manager.set_scene("settings")

            elif name == "CREDIT":
                credits_scene = self.game.scene_manager.scenes["credits"]
                credits_scene.start_popup()
                self.game.scene_manager.set_scene("credits")

            elif name == "EXIT":
                self.game.running = False

            return

    def update(self, delta_time):
        pass

    def draw(self, target, mouse_pos):
        target.blit(
            self.menu_background,
            (0, 0)
        )

        self.draw_menu_ui(
            target, mouse_pos
        )

    def draw_menu_ui(
        self,
        target,
        mouse_pos,
        alpha=1.0,
        x_offset=0
    ):
        if alpha <= 0:
            return

        self.ui_layer.fill((0, 0, 0, 0))

        self.ui_layer.blit(
            self.menu_art,
            self.menu_art_rect
        )

        if self.logo_image is not None:
            self.ui_layer.blit(
                self.logo_image,
                self.logo_rect
            )

        self._draw_music_button(mouse_pos)

        for name, rect in self.buttons:
            hovered = rect.collidepoint(mouse_pos)

            normal, hover = self.button_art[name]
            image = hover if hovered else normal

            if (
                name == self._pressed_button
                and pygame.time.get_ticks()
                < self._pressed_until
            ):
                image_rect = rect.move(
                    -self.menu_art_rect.x,
                    -self.menu_art_rect.y
                )

                button_image = image.subsurface(
                    image_rect
                ).copy()

                pressed_size = (
                    max(1, round(rect.width * 0.97)),
                    max(1, round(rect.height * 0.97))
                )

                button_image = pygame.transform.smoothscale(
                    button_image,
                    pressed_size
                )

                self.ui_layer.blit(
                    button_image,
                    button_image.get_rect(
                        center=rect.center
                    )
                )

            else:
                self.ui_layer.blit(
                    image,
                    self.menu_art_rect
                )

        self.ui_layer.set_alpha(
            round(255 * alpha)
        )

        target.blit(
            self.ui_layer,
            (round(x_offset), 0)
        )

    def _draw_music_button(self, mouse_pos):
        rect = self.music_button_rect

        image = (
            self.sound_off_image
            if self.game.menu_music.muted
            else self.sound_on_image
        )

        hovered = rect.collidepoint(mouse_pos)

        pressed = (
            pygame.time.get_ticks()
            < self._music_pressed_until
        )

        # Keep the button's proportions during hover and click.
        scale = 0.94 if pressed else 1.06 if hovered else 1.0

        if scale != 1.0:
            image = pygame.transform.smoothscale(
                image,
                (
                    max(1, round(image.get_width() * scale)),
                    max(1, round(image.get_height() * scale))
                )
            )

        image_rect = image.get_rect(
            center=rect.center
        )

        self.ui_layer.blit(
            image,
            image_rect
        )

    def compose_scene(self, open_amount):
        key = round(open_amount, 3)

        if key == self._compose_key:
            return

        self._compose_key = key

        swing = ease(open_amount)

        self.gate_canvas.blit(
            self.gate_bg,
            (0, 0)
        )

        squash = 1 - swing * GATE_OPEN_AMOUNT

        left_width = max(
            1,
            round(self.left_rect.width * squash)
        )

        right_width = max(
            1,
            round(self.right_rect.width * squash)
        )

        if left_width == self.left_rect.width:
            left_image = self.left_gate
            right_image = self.right_gate

        else:
            left_image = pygame.transform.smoothscale(
                self.left_gate,
                (left_width, self.left_rect.height)
            )

            right_image = pygame.transform.smoothscale(
                self.right_gate,
                (right_width, self.right_rect.height)
            )

        self.gate_canvas.blit(
            left_image,
            (self.left_rect.x, self.left_rect.y)
        )

        self.gate_canvas.blit(
            right_image,
            (
                self.right_rect.right - right_width,
                self.right_rect.y
            )
        )

        self.gate_canvas.blit(
            self.gate_frame,
            (0, 0)
        )

        self._camera_key = None

    def draw_camera(self, target, zoom_progress):
        zoom = GATE_ZOOM_END ** zoom_progress

        view_width = SRC_W / zoom
        view_height = SRC_H / zoom

        focus_x = GATE_FOCUS[0] / SRC_W
        focus_y = GATE_FOCUS[1] / SRC_H

        screen_focus_x = (
            focus_x
            + (0.5 - focus_x) * zoom_progress
        )

        screen_focus_y = (
            focus_y
            + (0.5 - focus_y) * zoom_progress
        )

        view_x = (
            GATE_FOCUS[0]
            - screen_focus_x * view_width
        )

        view_y = (
            GATE_FOCUS[1]
            - screen_focus_y * view_height
        )

        view_x = max(
            0.0,
            min(SRC_W - view_width, view_x)
        )

        view_y = max(
            0.0,
            min(SRC_H - view_height, view_y)
        )

        crop_x = int(math.floor(view_x))
        crop_y = int(math.floor(view_y))

        crop_width = min(
            SRC_W - crop_x,
            int(math.ceil(view_x + view_width)) - crop_x
        )

        crop_height = min(
            SRC_H - crop_y,
            int(math.ceil(view_y + view_height)) - crop_y
        )

        scale = WIDTH / view_width

        crop_width_px = max(
            1,
            round(crop_width * scale)
        )

        crop_height_px = max(
            1,
            round(crop_height * scale)
        )

        key = (
            crop_x,
            crop_y,
            crop_width,
            crop_height,
            crop_width_px,
            crop_height_px
        )

        if key != self._camera_key:
            self._camera_key = key

            crop = self.gate_canvas.subsurface(
                pygame.Rect(
                    crop_x,
                    crop_y,
                    crop_width,
                    crop_height
                )
            )

            self._camera_frame = pygame.transform.smoothscale(
                crop,
                (crop_width_px, crop_height_px)
            )

        target.blit(
            self._camera_frame,
            (
                round((crop_x - view_x) * scale),
                round((crop_y - view_y) * scale)
            )
        )

        return (
            (GATE_FOCUS[0] - view_x) * scale,
            (GATE_FOCUS[1] - view_y) * scale
        )

    def draw_gate(self, target, elapsed):
        gate_elapsed = elapsed

        open_amount = (
            gate_elapsed - GATE_OPEN_DELAY
        ) / GATE_OPEN_TIME

        self.compose_scene(open_amount)

        self.draw_camera(
            target,
            ease(gate_elapsed / GATE_ZOOM_TIME)
        )

        ui_progress = ease(
            elapsed / MENU_UI_FADE
        )

        self.draw_menu_ui(
            target,
            (-1, -1),
            (1 - ui_progress) ** 1.5,
            MENU_UI_SLIDE * ui_progress
        )

        fade_progress = ease(
            (gate_elapsed - GATE_FADE_START)
            / (GATE_TOTAL_TIME - GATE_FADE_START)
        )

        if fade_progress > 0:
            self.game.warm_surface.set_alpha(
                round(255 * fade_progress ** 2)
            )

            target.blit(
                self.game.warm_surface,
                (0, 0)
            )


class GateScene:
    """Advance and draw the gate-opening animation."""

    def __init__(self, game, menu_scene):
        self.game = game
        self.menu_scene = menu_scene
        self.covered = False
        self.gate_open_sound = pygame.mixer.Sound(
            str(Path("ASSET") / "MUSIC" / "gateopen.mp3")
        )
        self.gate_sound_played = False
        self.restart()

    def restart(self):
        self.elapsed = 0.0
        self.covered = False
        self.gate_sound_played = False

    def handle_event(self, event):
        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            self.game.scene_manager.go_to("intro")

        elif (
            event.type == pygame.KEYDOWN
            and event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN
            )
        ):
            self.game.scene_manager.go_to("intro")

    def update(self, delta_time):
        if (
            self.game.scene_manager.screen_fade_state != "none"
            or self.covered
        ):
            return

        self.elapsed += delta_time

        if not self.gate_sound_played and self.elapsed >= GATE_OPEN_DELAY + 0.4:
            self.gate_sound_played = True
            if not self.game.menu_music.muted:
                self.gate_open_sound.play()

        if self.elapsed >= GATE_ANIMATION_TIME:
            self.covered = True

            self.game.scene_manager.show_scene(
                "intro",
                white_fade=True
            )

    def draw(self, target, mouse_pos):
        self.menu_scene.draw_gate(
            target,
            self.elapsed
        )