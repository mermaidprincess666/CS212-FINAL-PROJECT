
"""Character selection screen and its portrait interactions."""

import math

import pygame

from screens.character_data import CHARACTERS
from screens.common import draw_text_center
from settings import ASSETS_DIR, CREAM, HEIGHT, WIDTH


TAN = (194, 151, 116)
TERRACOTTA = (157, 83, 61)
DARK_BROWN = (63, 43, 35)
PANEL_CREAM = (252, 243, 225, 228)
PORTRAIT_SIZE = (82, 58)

CHARACTER_OFFSET = (25, 30)
CHARACTER_CANVAS_SIZE = (round(WIDTH * 0.8), round(HEIGHT * 0.8))

FONT_DIR = ASSETS_DIR / "FONTS"

FONT_FILES = {
    "title": [
        FONT_DIR / "Lilita_One" / "LilitaOne-Regular.ttf",
        FONT_DIR / "LilitaOne-Regular.ttf",
    ],
    "name": [
        FONT_DIR / "Fredoka" / "static" / "Fredoka-SemiBold.ttf",
        FONT_DIR / "Fredoka" / "Fredoka-SemiBold.ttf",
        FONT_DIR / "Fredoka" / "Fredoka-VariableFont_wdth,wght.ttf",
        FONT_DIR / "Fredoka-SemiBold.ttf",
    ],
    "body": [
        FONT_DIR / "Nunito" / "static" / "Nunito-Regular.ttf",
        FONT_DIR / "Nunito" / "Nunito-Regular.ttf",
        FONT_DIR / "Nunito" / "Nunito-VariableFont_wght.ttf",
        FONT_DIR / "Nunito-Regular.ttf",
    ],
    "button": [
        FONT_DIR / "Fredoka" / "static" / "Fredoka-SemiBold.ttf",
        FONT_DIR / "Fredoka" / "Fredoka-SemiBold.ttf",
        FONT_DIR / "Fredoka" / "Fredoka-VariableFont_wdth,wght.ttf",
        FONT_DIR / "Fredoka-SemiBold.ttf",
    ],
    "small": [
        FONT_DIR / "Nunito" / "static" / "Nunito-SemiBold.ttf",
        FONT_DIR / "Nunito" / "Nunito-SemiBold.ttf",
        FONT_DIR / "Nunito" / "Nunito-VariableFont_wght.ttf",
        FONT_DIR / "Nunito-SemiBold.ttf",
    ],
    "arrow": [
        FONT_DIR / "Cabin_Sketch" / "CabinSketch-Bold.ttf",
    ],
}

TITLE_TEXT_COLOR = (166, 82, 60)
NAME_TEXT_COLOR = (103, 60, 43)
BODY_TEXT_COLOR = (73, 56, 46)


class CharacterScene:
    """Let players preview, select, and confirm characters."""

    def __init__(self, game):
        self.game = game

        self.title_font = self._load_font(
            "title", 90, game.fonts["title"]
        )
        self.heading_font = self.title_font

        self.name_font = self._load_font(
            "name", 36, game.fonts["title"]
        )
        self.body_font = self._load_font(
            "body", 22, game.fonts["button"]
        )
        self.button_font = self._load_font(
            "button", 21, game.fonts["button"]
        )
        self.label_font = self._load_font(
            "small", 19, game.fonts["small"]
        )
        self.arrow_font = self._load_font(
            "arrow", 80, game.fonts["title"]
        )

        self.selected_index = 0
        self.elapsed = 0.0
        self.transition_time = 0.0
        self.transition_from = None
        self.confirmed = False

        self.background = self._load_background()

        self.artwork = [
            self._load_character_art(character)
            for character in CHARACTERS
        ]

        self.left_arrow_btn = pygame.Rect(
            WIDTH // 2 - 210, 290, 64, 64
        )
        self.right_arrow_btn = pygame.Rect(
            WIDTH // 2 + 146, 290, 64, 64
        )

        self.back_button = pygame.Rect(
            38, HEIGHT - 62, 150, 44
        )
        self.confirm_button = pygame.Rect(
            WIDTH - 208, HEIGHT - 62, 170, 44
        )

        self._large_surfaces = [
            (
                self._scale_canvas(base),
                self._scale_canvas(talking),
                self._scale_canvas(hands),
            )
            for base, talking, hands in self.artwork
        ]

    def _load_font(self, font_type, size, fallback):
        for path in FONT_FILES[font_type]:
            try:
                return pygame.font.Font(str(path), size)
            except (FileNotFoundError, OSError, pygame.error):
                continue

        return fallback

    def _load_background(self):
        try:
            return self.game.assets.load_image(
                "choose_bg.png",
                (WIDTH, HEIGHT),
                subdirectory="CHOOSE",
            )
        except (FileNotFoundError, pygame.error):
            return None

    def _load_character_art(self, character):
        folder = f"MAIN/ANIMAL/{character['folder']}"

        base = self._load_full_sprite(
            character["portrait"], folder
        )
        talking = (
            self._load_full_sprite(
                character["talking"], folder
            )
            or base
        )
        hands = self._load_full_sprite(
            character["hands"], folder
        )

        if base is None:
            return None, None, None

        return base, talking, hands

    def _load_full_sprite(self, filename, folder):
        try:
            return self.game.assets.load_image(
                filename, subdirectory=folder
            )
        except (FileNotFoundError, pygame.error):
            return None

    @staticmethod
    def _scale_canvas(image):
        if image is None:
            return None

        return pygame.transform.smoothscale(
            image, CHARACTER_CANVAS_SIZE
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self._select(self.selected_index - 1)

            elif event.key == pygame.K_RIGHT:
                self._select(self.selected_index + 1)

            elif event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self._confirm()

            elif event.key == pygame.K_ESCAPE:
                self._back()

            return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if self.left_arrow_btn.collidepoint(event.pos):
                self._select(self.selected_index - 1)

            elif self.right_arrow_btn.collidepoint(event.pos):
                self._select(self.selected_index + 1)

            elif self.confirm_button.collidepoint(event.pos):
                self._confirm()

            elif self.back_button.collidepoint(event.pos):
                self._back()

    def _select(self, index):
        index %= len(CHARACTERS)

        if index == self.selected_index:
            return

        self.transition_from = (
            self._current_character_surface()
        )
        self.transition_time = 0.22
        self.selected_index = index
        self.confirmed = False

    def _confirm(self):
        self.game.selected_character = dict(
            CHARACTERS[self.selected_index]
        )
        self.confirmed = True

    def _back(self):
        self.game.scene_manager.go_to("intro")

    def _current_character_surface(self):
        base, _, _ = self._large_surfaces[
            self.selected_index
        ]
        return base

    def update(self, delta_time):
        self.elapsed += delta_time

        self.transition_time = max(
            0.0,
            self.transition_time - delta_time,
        )

        if self.transition_time == 0:
            self.transition_from = None

    def draw(self, target, mouse_pos):
        if self.background is not None:
            target.blit(self.background, (0, 0))
        else:
            target.fill((219, 183, 153))

        self._draw_heading(target)
        self._draw_selected_character(target)

        # Card stays behind the character's paws.
        self._draw_character_copy(target, mouse_pos)
        self._draw_selected_hands(target)

        self._draw_arrow_button(
            target,
            self.left_arrow_btn,
            "<",
            mouse_pos,
        )
        self._draw_arrow_button(
            target,
            self.right_arrow_btn,
            ">",
            mouse_pos,
        )

        self._draw_button(
            target,
            self.back_button,
            "BACK",
            mouse_pos,
        )

        confirm_text = (
            "CONFIRMED" if self.confirmed else "CONFIRM"
        )

        self._draw_button(
            target,
            self.confirm_button,
            confirm_text,
            mouse_pos,
            primary=True,
        )

        if self.confirmed:
            name = CHARACTERS[
                self.selected_index
            ]["name"]

            draw_text_center(
                target,
                f"{name} is ready for service!",
                self.label_font,
                BODY_TEXT_COLOR,
                (WIDTH // 2, HEIGHT - 110),
            )

    def _draw_heading(self, target):
        draw_text_center(
            target,
            "SELECT CHARACTER",
            self.heading_font,
            TITLE_TEXT_COLOR,
            (WIDTH // 2, 105),
        )

    def _draw_arrow_button(
        self, target, rect, symbol, mouse_pos
    ):
        hovered = rect.collidepoint(mouse_pos)

        color = (
            (190, 95, 70)
            if hovered
            else TERRACOTTA
        )

        draw_text_center(
            target,
            symbol,
            self.arrow_font,
            color,
            rect.center,
        )

    def _draw_selected_character(self, target):
        base, talking, _ = self._large_surfaces[
            self.selected_index
        ]

        bob = round(
            math.sin(self.elapsed * 2.2) * 2
        )

        canvas_width = CHARACTER_CANVAS_SIZE[0]

        center_x = (
            (WIDTH - canvas_width) // 2
            + CHARACTER_OFFSET[0]
        )

        base_y = (
            -30
            + CHARACTER_OFFSET[1]
            + bob
        )

        if self.transition_from is not None:
            progress = (
                1 - self.transition_time / 0.22
            )

            old = self.transition_from.copy()

            old.set_alpha(
                round(255 * (1 - progress))
            )

            target.blit(
                old, (center_x, base_y)
            )

        if base is None:
            return

        active = self.elapsed % 4.2
        mouth_alpha = 0

        if 3.15 <= active < 3.75:
            mouth_alpha = round(
                170
                * min(
                    (active - 3.15) / 0.18,
                    (3.75 - active) / 0.18,
                    1,
                )
            )

        image = base.copy()

        if (
            mouth_alpha > 0
            and talking is not None
        ):
            talking_image = talking.copy()
            talking_image.set_alpha(mouth_alpha)

            image.blit(
                talking_image, (0, 0)
            )

        image.set_alpha(
            round(
                255
                * min(
                    1.0,
                    (
                        0.22
                        - self.transition_time
                    )
                    / 0.22,
                )
            )
        )

        target.blit(
            image, (center_x, base_y)
        )

    def _draw_selected_hands(self, target):
        _, _, hands = self._large_surfaces[
            self.selected_index
        ]

        if hands is not None:
            hands.set_alpha(
                round(
                    255
                    * min(
                        1.0,
                        (
                            0.22
                            - self.transition_time
                        )
                        / 0.22,
                    )
                )
            )

            canvas_width = (
                CHARACTER_CANVAS_SIZE[0]
            )

            center_x = (
                (WIDTH - canvas_width) // 2
                + CHARACTER_OFFSET[0]
            )

            base_y = (
                10
                + CHARACTER_OFFSET[1]
                + round(
                    math.sin(
                        self.elapsed * 2.2
                    ) * 2
                )
            )

            target.blit(
                hands, (center_x, base_y)
            )

    def _draw_character_copy(
        self, target, mouse_pos=None
    ):
        character = CHARACTERS[
            self.selected_index
        ]

        panel = pygame.Rect(
            (WIDTH - 600) // 2,
            430,
            600,
            140,
        )

        parchment_color = (
            248, 241, 227
        )
        border_color = (
            139, 69, 19
        )
        shadow_color = (
            40, 25, 18, 70
        )

        # Card shadow.
        shadow_surf = pygame.Surface(
            (
                panel.width + 6,
                panel.height + 6,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            shadow_surf,
            shadow_color,
            (
                6,
                6,
                panel.width,
                panel.height,
            ),
            border_radius=16,
        )

        target.blit(
            shadow_surf,
            panel.topleft,
        )

        # Main description card.
        card_surface = pygame.Surface(
            (
                panel.width,
                panel.height,
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            card_surface,
            parchment_color,
            (
                0,
                0,
                panel.width,
                panel.height,
            ),
            border_radius=16,
        )

        pygame.draw.rect(
            card_surface,
            border_color,
            (
                0,
                0,
                panel.width,
                panel.height,
            ),
            width=3,
            border_radius=16,
        )

        inner_margin = 6

        pygame.draw.rect(
            card_surface,
            border_color,
            (
                inner_margin,
                inner_margin,
                panel.width - inner_margin * 2,
                panel.height - inner_margin * 2,
            ),
            width=1,
            border_radius=12,
        )

        target.blit(
            card_surface,
            panel.topleft,
        )

        # Character name.
        name_surf = self.name_font.render(
            character["name"].upper(),
            True,
            NAME_TEXT_COLOR,
        )

        target.blit(
            name_surf,
            (
                panel.x + 28,
                panel.y + 14,
            ),
        )

        # Dashed divider.
        line_y = panel.y + 64
        dash_width = 8
        dash_gap = 5
        current_x = panel.x + 30

        while current_x < panel.right - 30:
            pygame.draw.line(
                target,
                border_color,
                (current_x, line_y),
                (
                    min(
                        current_x + dash_width,
                        panel.right - 30,
                    ),
                    line_y,
                ),
                2,
            )

            current_x += (
                dash_width + dash_gap
            )

        self._draw_wrapped_description(
            target,
            character["description"],
            panel,
        )

    def _draw_wrapped_description(
        self, target, text, panel
    ):
        words = text.split()
        lines = []
        line = ""

        for word in words:
            candidate = (
                f"{line} {word}".strip()
            )

            if (
                self.body_font.size(
                    candidate
                )[0] > panel.width - 56
                and line
            ):
                lines.append(line)
                line = word
            else:
                line = candidate

        if line:
            lines.append(line)

        start_y = panel.y + 78
        line_spacing = 26

        for index, line in enumerate(lines):
            line_surf = self.body_font.render(
                line,
                True,
                BODY_TEXT_COLOR,
            )

            target.blit(
                line_surf,
                (
                    panel.x + 28,
                    start_y
                    + index * line_spacing,
                ),
            )

    def _draw_button(
        self,
        target,
        rect,
        label,
        mouse_pos,
        primary=False,
    ):
        hovered = rect.collidepoint(
            mouse_pos
        )

        fill = (
            TERRACOTTA
            if primary
            else CREAM
        )

        if hovered:
            fill = (
                (177, 97, 72)
                if primary
                else (255, 249, 239)
            )

        pygame.draw.rect(
            target,
            fill,
            rect,
            border_radius=10,
        )

        pygame.draw.rect(
            target,
            DARK_BROWN,
            rect,
            2,
            border_radius=10,
        )

        color = (
            CREAM
            if primary
            else DARK_BROWN
        )

        draw_text_center(
            target,
            label,
            self.button_font,
            color,
            rect.center,
        )
