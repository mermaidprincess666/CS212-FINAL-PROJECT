
"""Welcome screen shown after confirming a character in SLICE."""

import math

import pygame

from settings import ASSETS_DIR, HEIGHT, WIDTH, ui


CREAM = (247, 233, 209)
PAPER = (255, 247, 232)
BROWN = (123, 86, 66)
DARK = (63, 43, 35)
TERRACOTTA = (166, 82, 60)


class WelcomeScene:
    """Greet the selected chef before the first day begins."""

    def __init__(self, game):
        self.game = game
        self.elapsed = 0.0
        self.character_key = None
        self.character_image = None

        self.title_font = self._font(
            "Lilita_One/LilitaOne-Regular.ttf",
            ui(58),
            game.fonts["title"],
        )
        self.name_font = self._font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(31),
            game.fonts["button"],
        )
        self.body_font = self._font(
            "Nunito/static/Nunito-Regular.ttf",
            ui(22),
            game.fonts["button"],
        )
        self.button_font = self._font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(23),
            game.fonts["button"],
        )

        self.start_button = pygame.Rect(
            WIDTH // 2 - ui(125),
            HEIGHT - ui(106),
            ui(250),
            ui(56),
        )
        self.back_button = pygame.Rect(
            ui(34),
            HEIGHT - ui(70),
            ui(130),
            ui(43),
        )

    def _font(self, filename, size, fallback):
        try:
            return pygame.font.Font(
                str(ASSETS_DIR / "FONTS" / filename),
                size,
            )
        except (OSError, pygame.error):
            return fallback

    def _character(self):
        return getattr(
            self.game, "selected_character", None
        ) or {}

    def _refresh_character(self):
        character = self._character()
        key = (
            character.get("folder"),
            character.get("portrait"),
        )

        if key == self.character_key:
            return

        self.character_key = key
        self.character_image = None

        if not all(key):
            return

        try:
            image = self.game.assets.load_image(
                character["portrait"],
                subdirectory=(
                    f"MAIN/ANIMAL/{character['folder']}"
                ),
            ).convert_alpha()

            bounds = image.get_bounding_rect(min_alpha=12)

            if bounds.width and bounds.height:
                image = image.subsurface(bounds).copy()

            max_width = ui(270)
            max_height = ui(270)

            scale = min(
                max_width / image.get_width(),
                max_height / image.get_height(),
            )

            self.character_image = (
                pygame.transform.smoothscale(
                    image,
                    (
                        max(
                            1,
                            round(image.get_width() * scale),
                        ),
                        max(
                            1,
                            round(image.get_height() * scale),
                        ),
                    ),
                )
            )

        except (
            OSError,
            FileNotFoundError,
            pygame.error,
        ) as error:
            print(
                f"Welcome character artwork unavailable: {error}"
            )

    def _center_text(
        self, target, text, font, color, y
    ):
        image = font.render(text, True, color)
        target.blit(
            image,
            image.get_rect(center=(WIDTH // 2, y)),
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
                pygame.K_SPACE,
            ):
                self._begin_day()

            elif event.key == pygame.K_ESCAPE:
                self._back()

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if self.start_button.collidepoint(event.pos):
                self._begin_day()

            elif self.back_button.collidepoint(event.pos):
                self._back()

    def _back(self):
        self.game.scene_manager.go_to("character")

    def _begin_day(self):
        next_scene = "day_intro"

        if next_scene not in self.game.scene_manager.scenes:
            print(
                "Create and register 'day_intro' "
                "to enable BEGIN DAY 1."
            )
            return

        self.game.scene_manager.go_to(next_scene)

    def update(self, delta_time):
        self.elapsed += delta_time
        self._refresh_character()

    def draw(self, target, mouse_pos):
        target.fill(CREAM)

        outer = pygame.Rect(
            ui(16),
            ui(16),
            WIDTH - ui(32),
            HEIGHT - ui(32),
        )

        pygame.draw.rect(
            target,
            PAPER,
            outer,
            border_radius=ui(25),
        )
        pygame.draw.rect(
            target,
            TERRACOTTA,
            outer,
            ui(5),
            border_radius=ui(25),
        )

        inner = outer.inflate(-ui(24), -ui(24))
        pygame.draw.rect(
            target,
            BROWN,
            inner,
            ui(2),
            border_radius=ui(18),
        )

        tile = ui(17)

        for row in range(3):
            for col in range(5):
                if (row + col) % 2 == 0:
                    pygame.draw.rect(
                        target,
                        (220, 151, 117),
                        (
                            ui(44) + col * tile,
                            ui(44) + row * tile,
                            tile,
                            tile,
                        ),
                    )

        name = str(
            self._character().get("name", "CHEF")
        ).upper()

        self._center_text(
            target,
            f"WELCOME, {name}!",
            self.title_font,
            TERRACOTTA,
            ui(103),
        )

        self._center_text(
            target,
            "Your pizza adventure starts here!",
            self.body_font,
            DARK,
            ui(158),
        )

        if self.character_image is not None:
            bob = round(
                math.sin(self.elapsed * 2.4) * ui(3)
            )

            rect = self.character_image.get_rect(
                midbottom=(
                    WIDTH // 2,
                    ui(435) + bob,
                )
            )

            target.blit(self.character_image, rect)

        panel = pygame.Rect(
            WIDTH // 2 - ui(355),
            ui(438),
            ui(710),
            ui(112),
        )

        pygame.draw.rect(
            target,
            (211, 182, 157),
            panel.move(ui(5), ui(6)),
            border_radius=ui(14),
        )
        pygame.draw.rect(
            target,
            PAPER,
            panel,
            border_radius=ui(14),
        )
        pygame.draw.rect(
            target,
            BROWN,
            panel,
            ui(3),
            border_radius=ui(14),
        )

        self._center_text(
            target,
            "A fresh day and a new beginning!",
            self.name_font,
            BROWN,
            panel.y + ui(37),
        )

        self._center_text(
            target,
            "Get ready to take orders and bake your first pizza.",
            self.body_font,
            DARK,
            panel.y + ui(79),
        )

        self._button(
            target,
            self.start_button,
            "BEGIN DAY 1",
            mouse_pos,
            True,
        )

        self._button(
            target,
            self.back_button,
            "BACK",
            mouse_pos,
            False,
        )

    def _button(
        self,
        target,
        rect,
        text,
        mouse_pos,
        primary,
    ):
        hovered = rect.collidepoint(mouse_pos)

        if primary:
            color = (
                (183, 97, 72)
                if hovered
                else TERRACOTTA
            )
        else:
            color = (
                (255, 251, 243)
                if hovered
                else PAPER
            )

        pygame.draw.rect(
            target,
            color,
            rect,
            border_radius=ui(10),
        )

        pygame.draw.rect(
            target,
            DARK,
            rect,
            ui(2),
            border_radius=ui(10),
        )

        rendered = self.button_font.render(
            text,
            True,
            PAPER if primary else DARK,
        )

        target.blit(
            rendered,
            rendered.get_rect(center=rect.center),
        )
