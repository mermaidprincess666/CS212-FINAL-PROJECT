
"""The main character talks to herself after graduation."""

import pygame

from screens.common import draw_text_center
from settings import WIDTH, HEIGHT, CREAM, TITLE_COLOR


DARK_BROWN = (63, 43, 35)
PANEL_CREAM = (252, 243, 225, 238)
TERRACOTTA = (157, 83, 61)

TYPE_SPEED = 45

THOUGHT_DIALOGUE = [
    "Well... I finally did it. I graduated!",
    "All those years of studying, and now I'm finally here.",
    "So... what's next for me?",
    "I've always dreamed of having my own pizza restaurant.",
    "It sounds scary, starting something all by myself...",
    "But if I never try, how will I know?",
    "Okay! It's time to turn that little dream into something real!",
    "First things first... I need to choose who I want to be on this journey!"
]


class ThoughtsScene:

    def __init__(self, game):
        self.game = game

        self.name_font = game.fonts["button"]
        self.dialogue_font = game.fonts["dialogue"]
        self.label_font = game.fonts["small"]

        self.current_index = 0
        self.visible_characters = 0
        self.elapsed = 0.0
        self.finished_typing = False

        self.next_button = pygame.Rect(
            WIDTH - 190,
            HEIGHT - 82,
            145,
            43,
        )

        self.dialogue_box = pygame.Rect(
            55,
            HEIGHT - 185,
            WIDTH - 110,
            150,
        )

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.advance_dialogue()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.next_button.collidepoint(event.pos):
                self.advance_dialogue()

    def advance_dialogue(self):
        if not self.finished_typing:
            self.visible_characters = len(
                THOUGHT_DIALOGUE[self.current_index]
            )
            self.finished_typing = True
            return

        if self.current_index < len(THOUGHT_DIALOGUE) - 1:
            self.current_index += 1
            self.visible_characters = 0
            self.elapsed = 0.0
            self.finished_typing = False
        else:
            self.game.scene_manager.go_to("character")

    def update(self, delta_time):
        if not self.finished_typing:
            self.elapsed += delta_time

            self.visible_characters = min(
                len(THOUGHT_DIALOGUE[self.current_index]),
                int(self.elapsed * TYPE_SPEED),
            )

            if self.visible_characters >= len(
                THOUGHT_DIALOGUE[self.current_index]
            ):
                self.finished_typing = True

    def draw(self, target, mouse_pos):
        target.fill((219, 183, 153))

        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((63, 43, 35, 35))
        target.blit(overlay, (0, 0))

        draw_text_center(
            target,
            "A NEW BEGINNING",
            self.game.fonts["title"],
            TITLE_COLOR,
            (WIDTH // 2, 65),
        )

        pygame.draw.rect(
            target,
            PANEL_CREAM,
            self.dialogue_box,
            border_radius=16,
        )

        pygame.draw.rect(
            target,
            DARK_BROWN,
            self.dialogue_box,
            3,
            border_radius=16,
        )

        name_box = pygame.Rect(
            85,
            HEIGHT - 207,
            145,
            38,
        )

        pygame.draw.rect(
            target,
            TERRACOTTA,
            name_box,
            border_radius=9,
        )

        draw_text_center(
            target,
            "YOU",
            self.name_font,
            CREAM,
            name_box.center,
        )

        message = THOUGHT_DIALOGUE[self.current_index]
        displayed_text = message[:self.visible_characters]

        self.draw_wrapped_text(
            target,
            displayed_text,
            self.dialogue_font,
            DARK_BROWN,
            95,
            HEIGHT - 155,
            WIDTH - 190,
        )

        hovered = self.next_button.collidepoint(mouse_pos)

        button_color = (
            (177, 97, 72)
            if hovered
            else TERRACOTTA
        )

        pygame.draw.rect(
            target,
            button_color,
            self.next_button,
            border_radius=9,
        )

        button_label = (
            "FINISH"
            if self.current_index == len(THOUGHT_DIALOGUE) - 1
            else "NEXT"
        )

        draw_text_center(
            target,
            button_label,
            self.label_font,
            CREAM,
            self.next_button.center,
        )

    def draw_wrapped_text(
        self,
        target,
        text,
        font,
        color,
        x,
        y,
        max_width,
    ):
        words = text.split()
        lines = []
        line = ""

        for word in words:
            candidate = f"{line} {word}".strip()

            if font.size(candidate)[0] > max_width and line:
                lines.append(line)
                line = word
            else:
                line = candidate

        if line:
            lines.append(line)

        for index, line in enumerate(lines):
            rendered = font.render(line, True, color)
            target.blit(rendered, (x, y + index * 30))
