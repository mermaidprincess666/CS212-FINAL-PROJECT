import math
import pygame

from settings import WIDTH, HEIGHT, ASSETS_DIR


BLACK = (0, 0, 0)
DARK = (75, 39, 35)
TERRA = (177, 83, 62)
WHITE = (255, 252, 244)

INTRO_DIR = ASSETS_DIR / "INTRO"

HALF = WIDTH // 2
SLIDE_DURATION = 0.85
TYPE_SPEED = 45

PANEL_BORDER_COLOR = (91, 28, 27)
PANEL_BORDER_WIDTH = 20             # diagonal edges
PANEL_STRAIGHT_BORDER_WIDTH = 12    # straight (vertical) edges

# Black gap between different pairs (P2|P3 and P4|P5).
# Part of the layout, so pairs never need to be painted over.
PAIR_GAP = 20

# Black line inside a pair (P1|P2, P3|P4, P5|P6). 0 = fully merged.
MERGE_GAP = 8


STORY = [
    (1, "NARRATOR", "Somewhere in a little town, life moved at its own familiar pace."),
    (1, "NARRATOR", "Every day brought something ordinary. Another morning, another routine, another familiar face."),
    (1, "NARRATOR", "And somewhere among them was someone with a dream of their own."),

    (2, "NARRATOR", "Some dreams begin long before we even realize it."),
    (2, "NARRATOR", "For as long as they could remember, the kitchen had always felt like a second home."),
    (2, "NARRATOR", "To them, cooking was more than simply preparing food."),
    (2, "NARRATOR", "It was creativity. Passion. And the joy of sharing something made with care."),

    (3, "NARRATOR", "Years of studying, experimenting, and countless hours spent in the kitchen..."),
    (3, "NARRATOR", "Not to mention a few unfortunate cooking disasters."),
    (3, "NARRATOR", "And finally, the day had come."),
    (3, "PROTAGONIST (THOUGHTS)", "So... that's it, huh?"),
    (3, "PROTAGONIST (THOUGHTS)", "All those years of studying, and now I'm officially a culinary arts graduate."),
    (3, "PROTAGONIST (THOUGHTS)", "..."),
    (3, "PROTAGONIST (THOUGHTS)", "Guess I should start looking for a job."),

    (4, "PROTAGONIST (THOUGHTS)", "...Or."),
    (4, "PROTAGONIST (THOUGHTS)", "What if I didn't?"),
    (4, "PROTAGONIST (THOUGHTS)", "What if I made something of my own?"),
    (4, "PROTAGONIST (THOUGHTS)", "A place where I could serve my own recipes, experiment with new ideas, and do things my way."),
    (4, "PROTAGONIST (THOUGHTS)", "Heh."),
    (4, "PROTAGONIST (THOUGHTS)", "Now THAT sounds like a plan."),

    (5, "NARRATOR", "Of course, every dream needs somewhere to begin."),
    (5, "NARRATOR", "And sometimes, the perfect opportunity is hiding in plain sight."),

    (6, "NARRATOR", "An empty stall."),
    (6, "NARRATOR", "A fresh opportunity."),
    (6, "NARRATOR", "And a whole lot of possibilities."),
    (6, "NARRATOR", "And so, with a dream in mind and a recipe book in hand..."),
    (6, "NARRATOR", "A new adventure was about to begin."),
]


class IntroScene:
    def __init__(self, game):
        self.game = game

        self.dialogue_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            28,
            game.fonts.get("dialogue")
        )

        self.label_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            20,
            game.fonts.get("label")
        )

        self.button_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            21,
            game.fonts.get("small")
        )

        # Preload all six panels. Borders are computed once here and
        # cached in self.borders, then baked into the cached panel surface.
        self.panels = {}
        self.borders = {}

        for number in range(1, 7):
            path = INTRO_DIR / f"p{number}.png"

            try:
                image = pygame.image.load(
                    str(path)
                ).convert_alpha()

                image = pygame.transform.smoothscale(
                    image,
                    (WIDTH, HEIGHT)
                )

                # Odd panels: left border. Even panels: right border.
                side = "left" if number % 2 == 1 else "right"

                border = self._build_border(image, side)
                self.borders[number] = border

                image = image.copy()
                image.blit(border, (0, 0))

                self.panels[number] = image

            except (OSError, pygame.error):
                print(f"Missing panel: {path}")

                self.panels[number] = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )
                self.borders[number] = pygame.Surface(
                    (WIDTH, HEIGHT),
                    pygame.SRCALPHA
                )

        # Pair 0 = P1 + P2
        # Pair 1 = P3 + P4
        # Pair 2 = P5 + P6
        self.pair_x = {
            0: float(WIDTH),
            1: float(WIDTH),
            2: float(WIDTH),
        }

        self.pair_start = dict(self.pair_x)
        self.pair_target = dict(self.pair_x)

        self.transition_time = 0.0
        self.transitioning = False

        self.index = 0
        self.current_panel = 1

        self.characters_shown = 0.0
        self.advance_requested = False

        self.bubble_scale = 0.75
        self.bubble_timer = 0.0
        self.bubble_duration = 0.18

        self.bubble_positions = [
            (0.06, 0.13),
            (0.10, 0.55),
        ]

        self.back_button = pygame.Rect(
            35,
            HEIGHT - 60,
            130,
            42
        )

        self.skip_button = pygame.Rect(
            WIDTH - 325,
            HEIGHT - 60,
            130,
            42
        )

        self.next_button = pygame.Rect(
            WIDTH - 180,
            HEIGHT - 60,
            145,
            42
        )

        self.pending_index = 0

        self.reset()

    def _load_font(self, relative_path, size, fallback):
        path = ASSETS_DIR / "FONTS" / relative_path

        try:
            return pygame.font.Font(
                str(path),
                size
            )

        except (OSError, pygame.error):
            return fallback or pygame.font.Font(
                None,
                size
            )

    def _build_border(self, image, side):
        """
        Border follows the visible edge of the artwork.
        Rows whose edge sits on the image boundary (straight edge) use
        PANEL_STRAIGHT_BORDER_WIDTH; diagonal rows use PANEL_BORDER_WIDTH.
        """
        width, height = image.get_size()
        mask = pygame.mask.from_surface(image, 20)

        border = pygame.Surface((width, height), pygame.SRCALPHA)

        for y in range(height):
            if side == "left":
                xs = range(width)
            else:
                xs = range(width - 1, -1, -1)

            edge_x = None
            for x in xs:
                if mask.get_at((x, y)):
                    edge_x = x
                    break

            if edge_x is None:
                continue

            straight = edge_x <= 0 if side == "left" else edge_x >= width - 1
            w = (
                PANEL_STRAIGHT_BORDER_WIDTH
                if straight
                else PANEL_BORDER_WIDTH
            )

            if side == "left":
                rect = (edge_x, y, w, 1)
            else:
                rect = (edge_x - w + 1, y, w, 1)

            border.fill(PANEL_BORDER_COLOR, rect)

        # Keep the border strictly inside the opaque artwork.
        result = pygame.Surface((width, height), pygame.SRCALPHA)
        mask.to_surface(result, setsurface=border, unsetcolor=(0, 0, 0, 0))

        return result

    def _targets_for(self, current):
        """
        Screen x of each pair for the given current panel.

        Pairs sit on one strip with PAIR_GAP between them, so the gap is
        part of the layout and stays constant while sliding.
        Odd current panel  -> that pair's odd panel on the right half.
        Even current panel -> that pair fills the screen (shifted left by
        MERGE_GAP so the even panel's right edge is not clipped).
        """
        current_pair = (current - 1) // 2
        stride = WIDTH + PAIR_GAP

        if current % 2 == 1:
            camera = current_pair * stride - HALF
        else:
            camera = current_pair * stride + MERGE_GAP

        return {
            pair: float(pair * stride - camera)
            for pair in range(3)
        }

    def reset(self):
        self.reset_for_transition(
            reset_story=True
        )

    def reset_for_transition(self, reset_story=False):
        if reset_story:
            self.index = 0
            self.current_panel = 1

            self.pair_x = {
                0: float(WIDTH),
                1: float(WIDTH),
                2: float(WIDTH),
            }

            self.pair_start = dict(
                self.pair_x
            )

            self.pair_target = self._targets_for(1)

            self.transitioning = True

        else:
            self.pair_x = self._targets_for(
                self.current_panel
            )

            self.pair_start = dict(
                self.pair_x
            )

            self.pair_target = dict(
                self.pair_x
            )

            self.transitioning = False

        self.transition_time = 0.0

        self.characters_shown = 0.0
        self.advance_requested = False

        self.bubble_timer = 0.0
        self.bubble_scale = 0.75

        self.pending_index = self.index

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_RIGHT
            ):
                self.advance_requested = True

            elif event.key == pygame.K_LEFT:
                self._previous()

            elif event.key == pygame.K_ESCAPE:
                self.game.scene_manager.go_to(
                    "menu"
                )

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button != 1:
                return

            pos = event.pos

            if self.back_button.collidepoint(pos):
                self._previous()

            elif self.skip_button.collidepoint(pos):
                self.game.scene_manager.go_to(
                    "thoughts"
                )

            else:
                self.advance_requested = True

    def _previous(self):
        if self.transitioning:
            return

        if self.index == 0:
            self.game.scene_manager.go_to(
                "menu"
            )
            return

        self._change_story(
            self.index - 1
        )

    def _change_story(self, new_index):
        old_panel = self.current_panel

        self.index = new_index
        self.pending_index = new_index

        self.characters_shown = 0.0

        self.bubble_timer = 0.0
        self.bubble_scale = 0.75

        new_panel = STORY[self.index][0]

        self.current_panel = new_panel

        if new_panel != old_panel:
            self.pair_start = dict(
                self.pair_x
            )

            self.pair_target = self._targets_for(
                new_panel
            )

            self.transition_time = 0.0
            self.transitioning = True

    def update(self, delta_time):
        manager = self.game.scene_manager

        if getattr(
            manager,
            "screen_fade_state",
            "none"
        ) != "none":
            return

        if self.transitioning:
            self.transition_time += delta_time

            t = min(
                1.0,
                self.transition_time / SLIDE_DURATION
            )

            eased = t * t * (3 - 2 * t)

            for pair in self.pair_x:
                start = self.pair_start[pair]
                destination = self.pair_target[pair]

                self.pair_x[pair] = (
                    start
                    + (destination - start) * eased
                )

            if t >= 1.0:
                self.pair_x = dict(
                    self.pair_target
                )

                self.transitioning = False

        _, _, text = STORY[self.index]

        if self.advance_requested:
            self.advance_requested = False

            if not self.transitioning:
                if self.characters_shown < len(text):
                    self.characters_shown = float(
                        len(text)
                    )

                elif self.index + 1 < len(STORY):
                    self._change_story(
                        self.index + 1
                    )

                else:
                    manager.go_to(
                        "thoughts"
                    )
                    return

        if not self.transitioning:
            current_text = STORY[self.index][2]

            self.characters_shown = min(
                float(len(current_text)),
                self.characters_shown
                + TYPE_SPEED * delta_time
            )

            self.bubble_timer = min(
                self.bubble_duration,
                self.bubble_timer + delta_time
            )

            t = (
                self.bubble_timer
                / self.bubble_duration
            )

            self.bubble_scale = (
                0.75
                + 0.25 * (1 - (1 - t) ** 3)
            )

    def _draw_panels(self, target):
        # The black background is the gap. Nothing is painted over the
        # artwork or borders; gaps come from positions alone.
        target.fill(BLACK)

        for pair in range(3):
            pair_x = round(self.pair_x[pair])

            # Skip pairs that are completely offscreen.
            if pair_x >= WIDTH or pair_x + WIDTH + MERGE_GAP <= 0:
                continue

            odd_number = pair * 2 + 1
            even_number = odd_number + 1

            # Borders are already baked into these cached surfaces.
            target.blit(
                self.panels[odd_number],
                (pair_x, 0)
            )

            # Even panel is offset to open the black line inside the pair.
            target.blit(
                self.panels[even_number],
                (pair_x + MERGE_GAP, 0)
            )

    def _wrap_text(self, text, font, max_width):
        lines = []
        current = ""

        for word in text.split():
            test = f"{current} {word}".strip()

            if font.size(test)[0] <= max_width:
                current = test

            else:
                if current:
                    lines.append(current)

                current = word

        if current:
            lines.append(current)

        return lines or [""]

    def _draw_dialogue(self, target):
        if self.transitioning:
            return

        _, _, text = STORY[self.index]

        font = self.dialogue_font
        max_width = HALF - 40

        full_lines = self._wrap_text(
            text,
            font,
            max_width - 48
        )

        line_height = (
            font.get_linesize() + 5
        )

        bubble_width = max(
            220,
            min(
                max_width,
                max(
                    font.size(line)[0]
                    for line in full_lines
                ) + 48
            )
        )

        bubble_height = (
            len(full_lines) * line_height
            + 44
        )

        rx, ry = self.bubble_positions[
            self.index % len(
                self.bubble_positions
            )
        ]

        x = HALF + int(HALF * rx)
        y = int(HEIGHT * ry)

        x = max(
            HALF + 10,
            min(
                x,
                WIDTH - bubble_width - 20
            )
        )

        y = max(
            45,
            min(
                y,
                HEIGHT - bubble_height - 75
            )
        )

        bubble_surface = pygame.Surface(
            (bubble_width, bubble_height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            bubble_surface,
            (12, 12, 14, 245),
            bubble_surface.get_rect(),
            border_radius=17
        )

        visible_text = text[
            :int(self.characters_shown)
        ]

        visible_lines = self._wrap_text(
            visible_text,
            font,
            max_width - 48
        )

        text_y = 20

        for line in visible_lines:
            rendered = font.render(
                line,
                True,
                WHITE
            )

            bubble_surface.blit(
                rendered,
                (24, text_y)
            )

            text_y += line_height

        scale = self.bubble_scale

        scaled_width = max(
            1,
            int(bubble_width * scale)
        )

        scaled_height = max(
            1,
            int(bubble_height * scale)
        )

        scaled_bubble = pygame.transform.smoothscale(
            bubble_surface,
            (
                scaled_width,
                scaled_height
            )
        )

        center_x = (
            x + bubble_width // 2
        )

        center_y = (
            y + bubble_height // 2
        )

        bubble_rect = scaled_bubble.get_rect(
            center=(
                center_x,
                center_y
            )
        )

        target.blit(
            scaled_bubble,
            bubble_rect
        )

        if self.characters_shown >= len(text):
            bounce = int(
                3 * math.sin(
                    pygame.time.get_ticks()
                    * 0.008
                )
            )

            indicator = self.label_font.render(
                "▼",
                True,
                WHITE
            )

            target.blit(
                indicator,
                (
                    bubble_rect.right - 30,
                    bubble_rect.bottom - 27 + bounce
                )
            )

    def _draw_button(
        self,
        target,
        rect,
        label,
        mouse_pos
    ):
        hovered = rect.collidepoint(
            mouse_pos
        )

        color = (
            (202, 105, 76)
            if hovered
            else TERRA
        )

        pygame.draw.rect(
            target,
            DARK,
            rect.move(3, 4),
            border_radius=9
        )

        pygame.draw.rect(
            target,
            color,
            rect,
            border_radius=9
        )

        pygame.draw.rect(
            target,
            DARK,
            rect,
            2,
            border_radius=9
        )

        image = self.button_font.render(
            label,
            True,
            WHITE
        )

        target.blit(
            image,
            image.get_rect(
                center=rect.center
            )
        )

    def draw(self, target, mouse_pos):
        self._draw_panels(target)
        self._draw_dialogue(target)

        self._draw_button(
            target,
            self.back_button,
            "BACK",
            mouse_pos
        )

        self._draw_button(
            target,
            self.skip_button,
            "SKIP",
            mouse_pos
        )

        self._draw_button(
            target,
            self.next_button,
            "NEXT",
            mouse_pos
        )