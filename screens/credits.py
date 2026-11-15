
"""SLICE credits screen with automatic looping credits and smooth popup."""

import pygame

from settings import WIDTH, HEIGHT, ASSETS_DIR


# SLICE color palette
DARK_BROWN = (92, 49, 36)
TERRACOTTA = (177, 83, 62)
TERRACOTTA_HOVER = (198, 105, 79)
SOFT_CREAM = (255, 241, 215)
MUTED_BROWN = (139, 91, 70)


class CreditsScreen:
    """Credits modal with smooth popup and upward scrolling."""

    def __init__(self, game):
        self.game = game

        # Fonts
        self.title_font = self._load_font(
            "Lilita_One/LilitaOne-Regular.ttf",
            50,
            game.fonts["title"]
        )

        self.heading_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            29,
            game.fonts["label"]
        )

        self.name_font = self._load_font(
            "Nunito/static/Nunito-Regular.ttf",
            26,
            game.fonts["small"]
        )

        self.subtitle_font = self._load_font(
            "Nunito/static/Nunito-SemiBold.ttf",
            20,
            game.fonts["small"]
        )

        self.button_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            23,
            game.fonts["button"]
        )

        # Credits card
        self.modal = pygame.Rect(0, 0, 960, 540)
        self.modal.center = (WIDTH // 2, HEIGHT // 2)

        self.credits_bg = pygame.image.load(
            str(ASSETS_DIR / "CREDITS" / "credits_bg.png")
        ).convert_alpha()

        self.credits_bg = pygame.transform.smoothscale(
            self.credits_bg,
            self.modal.size
        )

        # Dark background overlay
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

        # Credits viewing area
        self.scroll_area = pygame.Rect(
            135, 190, 690, 245
        )

        # Automatic upward scrolling
        self.scroll_speed = 35.0
        self.scroll_position = 0.0
        self.content_height = 0

        # Back button
        self.back_button = pygame.Rect(
            380, 455, 200, 45
        )

        # Credits content
        self.credits = [
            (
                "GAME DEVELOPERS",
                [
                    "Adelantar, Chloe Kaye Isabelle",
                    "Cawaling, Divine Joy",
                    "Cortel, Roehla",
                    "Galve, Hanna Sophia",
                    "Solis, Charleigh Kim",
                ]
            ),
            (
                "LEAD DEVELOPERS",
                [
                    "Cortel, Roehla",
                    "Galve, Hanna Sophia",
                ]
            ),
            (
                "ARTISTS",
                [
                    "Cawaling, Divine Joy",
                    "Galve, Hanna Sophia",
                    "Solis, Charleigh Kim",

                ]
            ),
            (
                "AUDIO & SOUND",
                [
                    "Adelantar, Chloe Kaye Isabelle",
                    "Cortel, Roehla",
                    "Galve, Hanna Sophia",
                ]
            ),
            (
                "GAME FLOW",
                [
                    "Adelantar, Chloe Kaye Isabelle",
                    "Cortel, Roehla",
                    "Galve, Hanna Sophia",
                    "Solis, Charleigh Kim",
                ]
            ),
            (
                "SPECIAL THANKS",
                [
                    "Maem Trixie Anne Depra",
                ]
            ),
        ]

        # Cached surfaces
        self.background_snapshot = None

        self.modal_surface = pygame.Surface(
            self.modal.size,
            pygame.SRCALPHA
        )

        self._calculate_content_height()
        self._reset_scroll()

    def _load_font(self, relative_path, size, fallback):
        font_path = ASSETS_DIR / "FONTS" / relative_path

        try:
            return pygame.font.Font(
                str(font_path),
                size
            )
        except (FileNotFoundError, OSError, pygame.error):
            return fallback

    def _calculate_content_height(self):
        """Calculate total credits height."""

        total_height = 20

        for heading, names in self.credits:
            total_height += 55
            total_height += len(names) * 42
            total_height += 32

        self.content_height = total_height

    def _reset_scroll(self):
        """Start credits at their original position."""

        self.scroll_position = 0.0

    def start_popup(self):
        """Open credits without a screen fade."""

        self.popup_progress = 0.0
        self.popup_scale = 0.88
        self.popup_active = True

        self._reset_scroll()
        self.background_snapshot = None

    def update(self, delta_time):
        if not self.popup_active:
            return

        # Smooth popup animation
        if self.popup_progress < 1.0:
            self.popup_progress = min(
                1.0,
                self.popup_progress
                + delta_time / self.popup_duration
            )

        t = self.popup_progress
        eased = 1 - (1 - t) ** 3

        self.popup_scale = 0.88 + 0.12 * eased

        # Automatically move credits upward
        if self.popup_progress >= 1.0:
            self.scroll_position += (
                self.scroll_speed * delta_time
            )

            # Restart from original position
            if self.scroll_position >= self.content_height:
                self._reset_scroll()

    def _mouse_to_modal(self, mouse_pos):
        scale = max(self.popup_scale, 0.01)

        popup_width = self.modal.width * scale
        popup_height = self.modal.height * scale

        popup_x = (WIDTH - popup_width) / 2
        popup_y = (HEIGHT - popup_height) / 2

        return (
            (mouse_pos[0] - popup_x) / scale,
            (mouse_pos[1] - popup_y) / scale
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._close()
                return

        elif (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            mouse_pos = self._mouse_to_modal(event.pos)

            if self.back_button.collidepoint(mouse_pos):
                self._close()

    def _close(self):
        """Return to menu without a fade."""

        self.popup_active = False
        self.background_snapshot = None

        self.game.scene_manager.set_scene("menu")

    def draw_button(self, surface, rect, text, mouse_pos):
        hovered = rect.collidepoint(mouse_pos)

        color = (
            TERRACOTTA_HOVER
            if hovered
            else TERRACOTTA
        )

        # Button shadow
        pygame.draw.rect(
            surface,
            (196, 151, 119),
            rect.move(0, 3),
            border_radius=12
        )

        # Button background
        pygame.draw.rect(
            surface,
            color,
            rect,
            border_radius=12
        )

        # Button outline
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
            SOFT_CREAM
        )

        surface.blit(
            text_surface,
            text_surface.get_rect(center=rect.center)
        )

    def _draw_scroll_content(self, surface):
        """Draw automatically scrolling credits inside the card."""

        scroll_surface = pygame.Surface(
            self.scroll_area.size,
            pygame.SRCALPHA
        )

        center_x = self.scroll_area.width // 2

        # Start at original position and move upward
        y = 20 - self.scroll_position

        for heading, names in self.credits:
            # Section heading
            heading_surface = self.heading_font.render(
                heading,
                True,
                TERRACOTTA
            )

            heading_rect = heading_surface.get_rect(
                centerx=center_x,
                top=round(y)
            )

            scroll_surface.blit(
                heading_surface,
                heading_rect
            )

            y += 55

            # Names
            for name in names:
                name_surface = self.name_font.render(
                    name,
                    True,
                    DARK_BROWN
                )

                name_rect = name_surface.get_rect(
                    centerx=center_x,
                    top=round(y)
                )

                scroll_surface.blit(
                    name_surface,
                    name_rect
                )

                y += 42

            y += 32

        surface.blit(
            scroll_surface,
            self.scroll_area.topleft
        )

    def _draw_modal_content(self, surface, mouse_pos):
        # Credits card
        surface.blit(
            self.credits_bg,
            (0, 0)
        )

        # Main title - slightly higher
        title = self.title_font.render(
            "CREDITS",
            True,
            DARK_BROWN
        )

        surface.blit(
            title,
            title.get_rect(center=(480, 82))
        )

        # Subtitle
        subtitle = self.subtitle_font.render(
            "SLICE  •  BY PYAGUSTINOS",
            True,
            MUTED_BROWN
        )

        surface.blit(
            subtitle,
            subtitle.get_rect(center=(480, 155))
        )

        # Animated credits
        self._draw_scroll_content(surface)

        # Fixed Back button
        self.draw_button(
            surface,
            self.back_button,
            "BACK",
            mouse_pos
        )

    def _draw_background(self, screen):
        """Draw the menu background without flashing."""

        if self.background_snapshot is None:
            background = pygame.Surface(
                (WIDTH, HEIGHT)
            ).convert()

            menu_scene = self.game.scene_manager.scenes.get(
                "menu"
            )

            if menu_scene is not None:
                menu_scene.draw(
                    background,
                    (-1000, -1000)
                )
            else:
                background.fill((219, 183, 153))

            background.blit(
                self.overlay,
                (0, 0)
            )

            self.background_snapshot = background

        screen.blit(
            self.background_snapshot,
            (0, 0)
        )

    def draw(self, screen, mouse_pos):
        # Stable menu background
        self._draw_background(screen)

        # Clear modal surface
        self.modal_surface.fill(
            (0, 0, 0, 0)
        )

        local_mouse = self._mouse_to_modal(
            mouse_pos
        )

        # Draw credits
        self._draw_modal_content(
            self.modal_surface,
            local_mouse
        )

        # Smooth popup scaling
        scale = self.popup_scale

        scaled_size = (
            max(1, round(self.modal.width * scale)),
            max(1, round(self.modal.height * scale))
        )

        scaled_modal = pygame.transform.smoothscale(
            self.modal_surface,
            scaled_size
        )

        popup_rect = scaled_modal.get_rect(
            center=(WIDTH // 2, HEIGHT // 2)
        )

        screen.blit(
            scaled_modal,
            popup_rect
        )
