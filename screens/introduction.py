
"""The opening story scene and its messaging-style dialogue."""

import math

import pygame

from screens.common import draw_button, draw_text_center
from settings import (
    BUTTON_BORDER,
    CREAM,
    FADE_SPEED,
    HEIGHT,
    LINE_HEIGHT,
    POP_FADE,
    POP_LENGTH,
    SCENE_COUNTER,
    SCENE_FLOOR,
    SCENE_LAMP,
    SCENE_WALL,
    TITLE_COLOR,
    TYPE_SPEED,
    WIDTH,
)


INTRO_DIALOGUE = [
    (
        "Mom",
        "Good morning, sweetheart! Today is your graduation, right?",
    ),
    (
        "You",
        "MOM!! IT'S MY GRADUATION! I can't believe I finally made it!!",
    ),
    (
        "Mom",
        "I'm so proud of you! This is only the beginning of something wonderful.",
    ),
    (
        "You",
        "I know! A fresh start, a new dream... and maybe my very own pizza restaurant?",
    ),
    (
        "Mom",
        "A pizza restaurant?! You really are serious about this, aren't you?",
    ),
    (
        "You",
        "Of course! I'm going to make it happen. Wish me luck, Mom!",
    ),
    (
        "Mom",
        "I believe in you, sweetheart. Just remember to enjoy the journey!",
    ),
    (
        "You",
        "I will, Mom! Love you! <3",
    ),
]


class IntroScene:
    """Handle the messaging conversation and story transitions."""

    def __init__(self, game):
        self.game = game

        self.dialogue_font = game.fonts["dialogue"]
        self.label_font = game.fonts["label"]
        self.name_font = game.fonts["name"]

        self.back_button = pygame.Rect(40, HEIGHT - 60, 140, 40)
        self.next_button = pygame.Rect(WIDTH - 180, HEIGHT - 60, 140, 40)
        self.skip_button = pygame.Rect(WIDTH - 340, HEIGHT - 60, 140, 40)

        self.chat_window = pygame.Rect(110, 75, WIDTH - 220, 510)

        self.index = 0
        self.text_alpha = 255
        self.fade_state = "none"
        self.pending_index = 0
        self.characters_shown = 0.0
        self.advance_requested = False

    def reset(self):
        """Start the story from its first message."""
        self.reset_for_transition(reset_story=True)

    def reset_for_transition(self, reset_story=False):
        """Clear typing and fade states."""
        if reset_story:
            self.index = 0

        self.text_alpha = 255
        self.fade_state = "none"
        self.pending_index = self.index
        self.characters_shown = 0.0
        self.advance_requested = False

    def handle_event(self, event):
        """Handle keyboard and mouse input."""

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self.advance_requested = True
                return

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        if self.back_button.collidepoint(event.pos):
            if self.index > 0:
                if self.fade_state == "none":
                    self.pending_index = self.index - 1
                    self.fade_state = "out"
            else:
                self.game.scene_manager.go_to("menu")

        elif self.skip_button.collidepoint(event.pos):
            self.game.scene_manager.go_to("thoughts")

        elif (
            self.next_button.collidepoint(event.pos)
            or self.chat_window.collidepoint(event.pos)
        ):
            self.advance_requested = True

    def update(self, delta_time):
        """Advance typing and fade between messages."""

        advance_requested = self.advance_requested
        self.advance_requested = False

        manager = self.game.scene_manager

        if manager.screen_fade_state != "none":
            return

        if advance_requested and self.fade_state == "none":
            typing_end = len(INTRO_DIALOGUE[self.index][1]) + POP_LENGTH

            if self.characters_shown < typing_end:
                self.characters_shown = typing_end

            elif self.index + 1 >= len(INTRO_DIALOGUE):
                manager.go_to("thoughts")

            else:
                self.pending_index = self.index + 1
                self.fade_state = "out"

        if self.fade_state == "out":
            self.text_alpha -= FADE_SPEED

            if self.text_alpha <= 0:
                self.text_alpha = 0
                self.index = self.pending_index
                self.characters_shown = 0.0
                self.fade_state = "in"

        elif self.fade_state == "in":
            self.text_alpha += FADE_SPEED

            if self.text_alpha >= 255:
                self.text_alpha = 255
                self.fade_state = "none"

        # Continue the typewriter animation.
        if (
            self.fade_state != "out"
            and manager.white_in_alpha < 0.4
            and self.characters_shown
            < len(INTRO_DIALOGUE[self.index][1]) + POP_LENGTH
        ):
            self.characters_shown = min(
                self.characters_shown + TYPE_SPEED,
                len(INTRO_DIALOGUE[self.index][1]) + POP_LENGTH,
            )

    def draw(self, target, mouse_pos):
        """Draw the messaging conversation with Mom."""

        speaker, text = INTRO_DIALOGUE[self.index]

        # Background
        target.fill(SCENE_WALL)

        pygame.draw.rect(
            target,
            SCENE_COUNTER,
            (0, 300, WIDTH, 90),
        )

        pygame.draw.rect(
            target,
            SCENE_FLOOR,
            (0, 390, WIDTH, HEIGHT - 390),
        )

        # Bakery decorations
        for lamp_x in (200, 1000):
            pygame.draw.line(
                target,
                TITLE_COLOR,
                (lamp_x, 0),
                (lamp_x, 55),
                3,
            )

            pygame.draw.circle(
                target,
                SCENE_LAMP,
                (lamp_x, 75),
                28,
            )

        # Main chat window
        pygame.draw.rect(
            target,
            (83, 53, 43),
            self.chat_window,
            border_radius=22,
        )

        inner_window = self.chat_window.inflate(-8, -8)

        pygame.draw.rect(
            target,
            CREAM,
            inner_window,
            border_radius=18,
        )

        # Chat header
        header = pygame.Rect(
            self.chat_window.x + 5,
            self.chat_window.y + 5,
            self.chat_window.width - 10,
            75,
        )

        pygame.draw.rect(
            target,
            (153, 165, 137),
            header,
            border_radius=16,
        )

        draw_text_center(
            target,
            "MESSAGES",
            self.name_font,
            (255, 250, 240),
            (header.centerx, header.y + 25),
        )

        draw_text_center(
            target,
            "My Mommy ^^",
            self.label_font,
            (255, 250, 240),
            (header.centerx, header.y + 53),
        )

        # Message bubble
        bubble_width = 780
        text_padding = 28
        max_text_width = bubble_width - (text_padding * 2)

        wrapped_lines = self._wrap_text(text, max_text_width)

        bubble_height = len(wrapped_lines) * LINE_HEIGHT + 75
        bubble_y = header.bottom + 65

        if speaker == "Mom":
            bubble_x = self.chat_window.x + 35
            bubble_color = (255, 250, 240)
            name_color = (153, 165, 137)
        else:
            bubble_x = self.chat_window.right - bubble_width - 35
            bubble_color = (190, 220, 190)
            name_color = (105, 135, 105)

        bubble = pygame.Rect(
            bubble_x,
            bubble_y,
            bubble_width,
            bubble_height,
        )

        pygame.draw.rect(
            target,
            bubble_color,
            bubble,
            border_radius=22,
        )

        pygame.draw.rect(
            target,
            (105, 65, 51),
            bubble,
            2,
            border_radius=22,
        )

        # Speaker name
        name_image = self.label_font.render(
            speaker,
            True,
            name_color,
        )

        name_image.set_alpha(self.text_alpha)

        target.blit(
            name_image,
            (bubble.x + text_padding, bubble.y + 15),
        )

        # Typed message
        self._draw_typed_text(
            target,
            text,
            bubble.x + text_padding,
            bubble.y + 45,
            max_text_width,
        )

        # Advance indicator
        typing_finished = len(text) + POP_LENGTH

        if (
            self.text_alpha == 255
            and self.characters_shown >= typing_finished
        ):
            bounce = int(
                4 * math.sin(pygame.time.get_ticks() * 0.008)
            )

            draw_text_center(
                target,
                "...",
                self.label_font,
                TITLE_COLOR,
                (
                    self.chat_window.centerx,
                    self.chat_window.bottom - 25 + bounce,
                ),
            )

        # Navigation buttons
        button_font = self.game.fonts["small"]

        draw_button(
            target,
            self.back_button,
            "BACK",
            mouse_pos,
            button_font,
        )

        draw_button(
            target,
            self.skip_button,
            "SKIP",
            mouse_pos,
            button_font,
        )

        draw_button(
            target,
            self.next_button,
            "NEXT",
            mouse_pos,
            button_font,
        )

    def _draw_typed_text(self, target, text, x, y, max_width):
        """Reveal the message one letter at a time."""

        lines = self._wrap_text(text, max_width)
        character_index = 0

        for line in lines:
            for letter_index, letter in enumerate(line):
                if character_index >= self.characters_shown:
                    return

                if letter != " ":
                    age = self.characters_shown - character_index
                    progress = min(1.0, age / POP_LENGTH)

                    alpha = int(
                        self.text_alpha
                        * (1 - (1 - progress) * POP_FADE)
                    )

                    image = self.dialogue_font.render(
                        letter,
                        True,
                        TITLE_COLOR,
                    )

                    image.set_alpha(alpha)

                    letter_x = (
                        x + self.dialogue_font.size(
                            line[:letter_index]
                        )[0]
                    )

                    target.blit(
                        image,
                        (int(letter_x), int(y)),
                    )

                character_index += 1

            y += LINE_HEIGHT

    def _wrap_text(self, text, max_width):
        """Wrap dialogue on word boundaries."""

        lines = []
        current_line = ""

        for word in text.split():
            candidate = (
                current_line + word + " "
                if current_line
                else word + " "
            )

            if self.dialogue_font.size(candidate)[0] <= max_width:
                current_line = candidate
            else:
                if current_line:
                    lines.append(current_line)

                current_line = word + " "

        if current_line:
            lines.append(current_line)

        return lines
