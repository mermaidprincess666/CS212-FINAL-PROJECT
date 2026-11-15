
"""Settings screen with a compact layout and smooth popup animation."""

import pygame

from settings import WIDTH, HEIGHT, ASSETS_DIR


# SLICE color palette
DARK_BROWN = (92, 49, 36)
TERRACOTTA = (177, 83, 62)
TERRACOTTA_HOVER = (198, 105, 79)
SOFT_CREAM = (255, 241, 215)

# Sage-green sliders
SLIDER_TRACK = (218, 204, 178)
SLIDER_FILL = (116, 151, 115)
SLIDER_HOVER = (92, 132, 92)
SLIDER_KNOB = (255, 245, 225)


class SettingsScreen:
    """Animated settings modal for audio and display options."""

    def __init__(self, game):
        self.game = game

        self.music_volume = 100
        self.sound_volume = 100
        self.fullscreen = game.fullscreen

        # Fonts
        self.title_font = self._load_font(
            "Lilita_One/LilitaOne-Regular.ttf",
            40,
            game.fonts["title"]
        )

        self.label_font = self._load_font(
            "Nunito/static/Nunito-SemiBold.ttf",
            21,
            game.fonts["label"]
        )

        self.button_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            20,
            game.fonts["button"]
        )

        self.small_font = self._load_font(
            "Nunito/static/Nunito-Regular.ttf",
            18,
            game.fonts["small"]
        )

        # Narrower modal for the updated card
        self.modal = pygame.Rect(0, 0, 680, 580)
        self.modal.center = (WIDTH // 2, HEIGHT // 2)

        # Card image
        self.setting_bg = pygame.image.load(
            str(ASSETS_DIR / "SETTING" / "setting_bg.png")
        ).convert_alpha()

        self.setting_bg = pygame.transform.smoothscale(
            self.setting_bg,
            self.modal.size
        )

        # Static dark overlay
        self.overlay = pygame.Surface(
            (WIDTH, HEIGHT),
            pygame.SRCALPHA
        )
        self.overlay.fill((30, 19, 14, 115))

        # Popup animation
        self.popup_progress = 0.0
        self.popup_duration = 0.22
        self.popup_scale = 0.88
        self.popup_active = False

        # Layout relative to 680x580 modal
        self.content_left = 175
        self.content_right = 505
        self.content_center = 340

        self.music_label_y = 162
        self.sound_label_y = 259

        self.music_slider = pygame.Rect(
            175, 204, 330, 11
        )

        self.sound_slider = pygame.Rect(
            175, 301, 330, 11
        )

        self.fullscreen_button = pygame.Rect(
            175, 367, 330, 46
        )

        self.reset_button = pygame.Rect(
            175, 441, 155, 46
        )

        self.back_button = pygame.Rect(
            350, 441, 155, 46
        )

        self.dragging = None
        self.background_snapshot = None

        self.modal_surface = pygame.Surface(
            self.modal.size,
            pygame.SRCALPHA
        )

    def _load_font(self, relative_path, size, fallback):
        font_path = ASSETS_DIR / "FONTS" / relative_path

        try:
            return pygame.font.Font(str(font_path), size)
        except (FileNotFoundError, OSError, pygame.error):
            return fallback

    def start_popup(self):
        self.popup_progress = 0.0
        self.popup_scale = 0.88
        self.popup_active = True
        self.dragging = None
        self.background_snapshot = None

    def update(self, delta_time):
        if not self.popup_active:
            return

        if self.popup_progress < 1.0:
            self.popup_progress = min(
                1.0,
                self.popup_progress
                + delta_time / self.popup_duration
            )

        t = self.popup_progress
        eased = 1 - (1 - t) ** 3

        self.popup_scale = 0.88 + 0.12 * eased

    def _mouse_to_modal(self, mouse_pos):
        scale = max(self.popup_scale, 0.01)

        popup_width = self.modal.width * scale
        popup_height = self.modal.height * scale

        popup_x = (WIDTH - popup_width) / 2
        popup_y = (HEIGHT - popup_height) / 2

        local_x = (mouse_pos[0] - popup_x) / scale
        local_y = (mouse_pos[1] - popup_y) / scale

        return local_x, local_y

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close()
                return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            mouse_pos = self._mouse_to_modal(event.pos)

            if self.music_slider.inflate(
                20, 30
            ).collidepoint(mouse_pos):
                self.dragging = "music"
                self.change_slider(mouse_pos)

            elif self.sound_slider.inflate(
                20, 30
            ).collidepoint(mouse_pos):
                self.dragging = "sound"
                self.change_slider(mouse_pos)

            elif self.fullscreen_button.collidepoint(mouse_pos):
                self.game.toggle_fullscreen()
                self.fullscreen = self.game.fullscreen

            elif self.reset_button.collidepoint(mouse_pos):
                self._reset_settings()

            elif self.back_button.collidepoint(mouse_pos):
                self._close()

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                mouse_pos = self._mouse_to_modal(event.pos)
                self.change_slider(mouse_pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = None

    def _close(self):
        self.dragging = None
        self.popup_active = False
        self.background_snapshot = None
        self.game.scene_manager.set_scene("menu")

    def _reset_settings(self):
        self.music_volume = 70
        self.sound_volume = 85
        self.game.menu_music.set_volume(0.70)

        if self.game.fullscreen:
            self.game.toggle_fullscreen()

        self.fullscreen = False

    def change_slider(self, mouse_pos):
        if self.dragging == "music":
            slider = self.music_slider
            value = "music"

        elif self.dragging == "sound":
            slider = self.sound_slider
            value = "sound"

        else:
            return

        percentage = (mouse_pos[0] - slider.x) / slider.width
        percentage = max(0, min(1, percentage))

        volume = round(percentage * 100)

        if value == "music":
            self.music_volume = volume
            self.game.menu_music.set_volume(volume / 100)
        else:
            self.sound_volume = volume

    def draw_slider(self, surface, slider, volume, mouse_pos):
        hovered = slider.inflate(24, 30).collidepoint(mouse_pos)

        # Track
        pygame.draw.rect(
            surface,
            SLIDER_TRACK,
            slider,
            border_radius=8
        )

        # Green progress
        fill_width = round(slider.width * volume / 100)

        if fill_width > 0:
            fill_rect = pygame.Rect(
                slider.x,
                slider.y,
                fill_width,
                slider.height
            )

            pygame.draw.rect(
                surface,
                SLIDER_HOVER if hovered else SLIDER_FILL,
                fill_rect,
                border_radius=8
            )

        handle_x = slider.x + fill_width

        # Knob shadow
        pygame.draw.circle(
            surface,
            (184, 169, 142),
            (handle_x, slider.centery + 2),
            12
        )

        # Cream knob
        pygame.draw.circle(
            surface,
            SLIDER_KNOB,
            (handle_x, slider.centery),
            11
        )

        # Green outline
        pygame.draw.circle(
            surface,
            SLIDER_HOVER if hovered else SLIDER_FILL,
            (handle_x, slider.centery),
            11,
            2
        )

        pygame.draw.circle(
            surface,
            SLIDER_FILL,
            (handle_x, slider.centery),
            3
        )

    def draw_button(
        self,
        surface,
        rect,
        text,
        mouse_pos,
        secondary=False
    ):
        hovered = rect.collidepoint(mouse_pos)

        if secondary:
            fill = (
                (245, 221, 194)
                if hovered
                else (255, 238, 213)
            )
            text_color = DARK_BROWN
        else:
            fill = (
                TERRACOTTA_HOVER
                if hovered
                else TERRACOTTA
            )
            text_color = SOFT_CREAM

        # Shadow
        pygame.draw.rect(
            surface,
            (196, 151, 119),
            rect.move(0, 3),
            border_radius=12
        )

        # Button
        pygame.draw.rect(
            surface,
            fill,
            rect,
            border_radius=12
        )

        pygame.draw.rect(
            surface,
            DARK_BROWN,
            rect,
            2,
            border_radius=12
        )

        text_surface = self.button_font.render(
            text,
            True,
            text_color
        )

        text_rect = text_surface.get_rect(
            center=rect.center
        )

        surface.blit(text_surface, text_rect)

    def draw_setting_label(self, surface, text, value, y):
        label = self.label_font.render(
            text,
            True,
            DARK_BROWN
        )

        surface.blit(
            label,
            (self.content_left, y)
        )

        value_text = self.label_font.render(
            f"{value}%",
            True,
            DARK_BROWN
        )

        value_rect = value_text.get_rect(
            right=self.content_right,
            top=y
        )

        surface.blit(value_text, value_rect)

    def _draw_modal_content(self, surface, mouse_pos):
        # Card background
        surface.blit(self.setting_bg, (0, 0))

        # Title
        title = self.title_font.render(
            "SETTINGS",
            True,
            DARK_BROWN
        )

        title_rect = title.get_rect(
            center=(340, 90)
        )

        surface.blit(title, title_rect)

        # Music volume
        self.draw_setting_label(
            surface,
            "Music Volume",
            self.music_volume,
            self.music_label_y
        )

        self.draw_slider(
            surface,
            self.music_slider,
            self.music_volume,
            mouse_pos
        )

        # Sound effects
        self.draw_setting_label(
            surface,
            "Sound Effects",
            self.sound_volume,
            self.sound_label_y
        )

        self.draw_slider(
            surface,
            self.sound_slider,
            self.sound_volume,
            mouse_pos
        )

        # Fullscreen
        fullscreen_text = (
            "Fullscreen: ON"
            if self.game.fullscreen
            else "Fullscreen: OFF"
        )

        self.draw_button(
            surface,
            self.fullscreen_button,
            fullscreen_text,
            mouse_pos
        )

        # Reset
        self.draw_button(
            surface,
            self.reset_button,
            "RESET",
            mouse_pos,
            secondary=True
        )

        # Back
        self.draw_button(
            surface,
            self.back_button,
            "BACK",
            mouse_pos
        )

    def _draw_background(self, screen):
        if self.background_snapshot is None:
            background = pygame.Surface(
                (WIDTH, HEIGHT)
            ).convert()

            menu_scene = self.game.scene_manager.scenes.get("menu")

            if menu_scene is not None:
                menu_scene.draw(background, (-1000, -1000))
            else:
                background.fill((219, 183, 153))

            background.blit(self.overlay, (0, 0))
            self.background_snapshot = background

        screen.blit(self.background_snapshot, (0, 0))

    def draw(self, screen, mouse_pos):
        self._draw_background(screen)

        self.modal_surface.fill((0, 0, 0, 0))

        local_mouse = self._mouse_to_modal(mouse_pos)

        self._draw_modal_content(
            self.modal_surface,
            local_mouse
        )

        scale = self.popup_scale

        scaled_width = max(
            1, round(self.modal.width * scale)
        )

        scaled_height = max(
            1, round(self.modal.height * scale)
        )

        scaled_modal = pygame.transform.smoothscale(
            self.modal_surface,
            (scaled_width, scaled_height)
        )

        popup_rect = scaled_modal.get_rect(
            center=(WIDTH // 2, HEIGHT // 2)
        )

        screen.blit(scaled_modal, popup_rect)
