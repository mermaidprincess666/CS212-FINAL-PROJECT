import math
import random
from array import array
import sys
import pygame

from settings import WIDTH, HEIGHT, ASSETS_DIR, ui


BLACK = (0, 0, 0)
DARK = (75, 39, 35)
TERRA = (177, 83, 62)
WHITE = (255, 252, 244)

INTRO_DIR = ASSETS_DIR / "INTRO"

HALF = WIDTH // 2
SLIDE_DURATION = 0.85
TYPE_SPEED = 45

PANEL_BORDER_COLOR = (91, 28, 27)
PANEL_BORDER_WIDTH = ui(20)
PANEL_STRAIGHT_BORDER_WIDTH = ui(12)
PAIR_GAP = ui(20)
MERGE_GAP = ui(8)


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
            ui(28),
            game.fonts.get("dialogue")
        )

        self.label_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(20),
            game.fonts.get("label")
        )

        self.button_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(21),
            game.fonts.get("small")
        )

        # Deep speech-like gibberish voice; no audio file required.
        self.voice_rng = random.Random()
        self.voice_sounds = {}
        self.voice_channel = None
        self.last_voice_time = -1000
        self.voice_delay = 65
        mixer_settings = pygame.mixer.get_init()
        if getattr(IntroScene, "_voice_cache_settings", None) != mixer_settings:
            self._build_voice_sounds()
            IntroScene._voice_cache = self.voice_sounds
            IntroScene._voice_cache_settings = mixer_settings
        else:
            self.voice_sounds = IntroScene._voice_cache

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

        self.pending_index = 0
        self.space_held_since = None
        self.space_skip_triggered = False
        self.hold_to_skip_ms = 1000
        self.guide_font = self._load_font(
            "Fredoka/static/Fredoka-SemiBold.ttf", ui(14), self.button_font
        )

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

    def _build_voice_sounds(self):
        """Generate a small set of deep gibberish sounds efficiently."""
        mixer = pygame.mixer.get_init()
        if mixer is None:
            return
        sample_rate, sample_format, channels = mixer
        if sample_format != -16:
            print("Gibberish voice requires a signed 16-bit audio mixer.")
            return

        # Reuse 15 short sounds rather than synthesizing 78 at startup.
        vowels = {
            "a": (730, 1150, 2450),
            "e": (480, 1750, 2500),
            "i": (330, 2150, 2900),
            "o": (520, 950, 2400),
            "u": (370, 850, 2200),
        }
        vowel_cycle = "aoeuiouaeoiaueo"
        syllables = {}
        for vowel, (f1, f2, f3) in vowels.items():
            syllables[vowel] = []
            for variant in range(3):
                pitch = 112 + ("aeiou".index(vowel) * 7 + variant * 13) % 45
                duration = 0.095 + variant * 0.012
                frame_count = int(sample_rate * duration)
                samples = array("h")
                phase = 0.0
                noise_state = 13579 + variant * 41
                # Calculate harmonic weights ONCE, not for every sample.
                weights = []
                for harmonic in range(1, 11):
                    frequency = harmonic * pitch
                    formant = (
                        1.15 * math.exp(-((frequency - f1) / 220) ** 2)
                        + 0.85 * math.exp(-((frequency - f2) / 310) ** 2)
                        + 0.35 * math.exp(-((frequency - f3) / 420) ** 2)
                    )
                    weights.append((0.10 + formant) / harmonic ** 0.7)
                weight_total = sum(weights)
                for frame in range(frame_count):
                    progress = frame / frame_count
                    attack = min(1.0, progress / 0.11)
                    release = min(1.0, (1.0 - progress) / 0.22)
                    envelope = max(0.0, min(attack, release))
                    bend = 1.0 + (variant - 1) * 0.13 * (progress - 0.5)
                    phase += 2 * math.pi * pitch * bend / sample_rate
                    voice = sum(
                        weight * math.sin(harmonic * phase)
                        for harmonic, weight in enumerate(weights, 1)
                    ) / weight_total
                    noise_state = (1103515245 * noise_state + 12345) & 0x7fffffff
                    noise = noise_state / 1073741824.0 - 1.0
                    breath = 0.10 * max(0.0, 1.0 - progress / 0.22)
                    value = max(-32768, min(32767, int(
                        22000 * envelope * (voice * (1 - breath) + noise * breath)
                    )))
                    samples.extend([value] * channels)
                if sys.byteorder != "little":
                    samples.byteswap()
                sound = pygame.mixer.Sound(buffer=samples.tobytes())
                sound.set_volume(1.0)
                syllables[vowel].append(sound)

        self.voice_sounds = {
            letter: syllables[
                letter if letter in vowels else vowel_cycle[index % len(vowel_cycle)]
            ]
            for index, letter in enumerate("abcdefghijklmnopqrstuvwxyz")
        }

    def _stop_narration(self):
        if self.voice_channel is not None:
            self.voice_channel.stop()
            self.voice_channel = None
        self.last_voice_time = -1000

    def _speak_new_letters(self, text, old_count, new_count):
        if self.transitioning or not self.voice_sounds:
            return

        if getattr(self.game.menu_music, "muted", False):
            self._stop_narration()
            return

        # Only make a sound when a new spoken character appears.
        new_characters = text[old_count:new_count]
        letters = [character.lower() for character in new_characters if character.isascii() and character.isalpha()]
        if not letters:
            return

        now = pygame.time.get_ticks()
        if now - self.last_voice_time < self.voice_delay:
            return

        letter = letters[-1]
        variants = self.voice_sounds.get(letter)
        if not variants:
            return

        sound = self.voice_rng.choice(variants)
        if self.voice_channel is not None:
            self.voice_channel.stop()

        self.voice_channel = sound.play()
        self.last_voice_time = now
        # Variable spacing makes the voice feel like babbling, not a metronome.
        self.voice_delay = self.voice_rng.randint(42, 78)

    def _build_border(self, image, side):
        """
        Border follows the visible edge of the artwork.
        """
        width, height = image.get_size()
        mask = pygame.mask.from_surface(image, 20)

        border = pygame.Surface(
            (width, height),
            pygame.SRCALPHA
        )

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

            straight = (
                edge_x <= 0
                if side == "left"
                else edge_x >= width - 1
            )

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

        result = pygame.Surface(
            (width, height),
            pygame.SRCALPHA
        )

        mask.to_surface(
            result,
            setsurface=border,
            unsetcolor=(0, 0, 0, 0)
        )

        return result

    def _targets_for(self, current):
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
        self._stop_narration()

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
        self.space_held_since = None
        self.space_skip_triggered = False

        self.bubble_timer = 0.0
        self.bubble_scale = 0.75

        self.pending_index = self.index

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.space_held_since is None:
                    self.space_held_since = pygame.time.get_ticks()
                    self.space_skip_triggered = False
            elif event.key in (pygame.K_RETURN, pygame.K_RIGHT):
                self.advance_requested = True
            elif event.key == pygame.K_LEFT:
                self._previous()
            elif event.key == pygame.K_ESCAPE:
                self._stop_narration()
                self.game.scene_manager.go_to("menu")

        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                if self.space_held_since is not None and not self.space_skip_triggered:
                    self.advance_requested = True
                self.space_held_since = None
                self.space_skip_triggered = False

    def _previous(self):
        if self.transitioning:
            return

        if self.index == 0:
            self._stop_narration()

            self.game.scene_manager.go_to(
                "menu"
            )
            return

        self._change_story(
            self.index - 1
        )

    def _change_story(self, new_index):
        self._stop_narration()

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
            self._stop_narration()
            return

        if self.space_held_since is not None and not self.space_skip_triggered:
            elapsed = pygame.time.get_ticks() - self.space_held_since
            if elapsed >= self.hold_to_skip_ms:
                self.space_skip_triggered = True
                self._stop_narration()
                manager.go_to("character")
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
                    self._stop_narration()

                elif self.index + 1 < len(STORY):
                    self._change_story(
                        self.index + 1
                    )

                else:
                    self._stop_narration()

                    manager.go_to("character")
                    return

        if not self.transitioning:
            current_text = STORY[self.index][2]

            old_count = int(self.characters_shown)
            self.characters_shown = min(
                float(len(current_text)),
                self.characters_shown + TYPE_SPEED * delta_time
            )
            new_count = int(self.characters_shown)
            self._speak_new_letters(current_text, old_count, new_count)

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
        target.fill(BLACK)

        for pair in range(3):
            pair_x = round(self.pair_x[pair])

            if pair_x >= WIDTH or pair_x + WIDTH + MERGE_GAP <= 0:
                continue

            odd_number = pair * 2 + 1
            even_number = odd_number + 1

            target.blit(
                self.panels[odd_number],
                (pair_x, 0)
            )

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
        max_width = HALF - ui(40)

        full_lines = self._wrap_text(
            text,
            font,
            max_width - ui(48)
        )

        line_height = (
            font.get_linesize() + 5
        )

        bubble_width = max(
            ui(220),
            min(
                max_width,
                max(
                    font.size(line)[0]
                    for line in full_lines
                ) + ui(48)
            )
        )

        bubble_height = (
            len(full_lines) * line_height
            + ui(44)
        )

        rx, ry = self.bubble_positions[
            self.index % len(
                self.bubble_positions
            )
        ]

        x = HALF + int(HALF * rx)
        y = int(HEIGHT * ry)

        x = max(
            HALF + ui(10),
            min(
                x,
                WIDTH - bubble_width - ui(20)
            )
        )

        y = max(
            ui(45),
            min(
                y,
                HEIGHT - bubble_height - ui(75)
            )
        )

        bubble_surface = pygame.Surface(
            (bubble_width, bubble_height),
            pygame.SRCALPHA
        )

        pygame.draw.rect(
            bubble_surface,
            (247, 233, 209),  # #F7E9D1 dialogue background
            bubble_surface.get_rect(),
            border_radius=ui(17)
        )
        pygame.draw.rect(
            bubble_surface,
            (123, 86, 66),  # #7B5642 dialogue border
            bubble_surface.get_rect(),
            width=ui(3),
            border_radius=ui(17)
        )

        visible_text = text[
            :int(self.characters_shown)
        ]

        visible_lines = self._wrap_text(
            visible_text,
            font,
            max_width - ui(48)
        )

        text_y = ui(20)

        for line in visible_lines:
            rendered = font.render(
                line,
                True,
                (123, 86, 66)
            )

            bubble_surface.blit(
                rendered,
                (ui(24), text_y)
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
            bounce = round(
                ui(3) * math.sin(
                    pygame.time.get_ticks()
                    * 0.008
                )
            )

            indicator = self.label_font.render(
                "▼",
                True,
                (123, 86, 66)
            )

            target.blit(
                indicator,
                (
                    bubble_rect.right - ui(30),
                    bubble_rect.bottom - ui(27) + bounce
                )
            )

    def _draw_navigation_guide(self, target):
        """Compact bottom-left SPACE controls with a hold progress ring."""
        cream = (255, 238, 208)
        dark_bg = (39, 25, 23)
        accent = (245, 173, 104)

        key_width, key_height = ui(66), ui(27)
        circle_size = ui(28)
        gap = ui(9)
        divider_gap = ui(15)
        x = ui(16)
        center_y = HEIGHT - ui(24)

        next_text = self.guide_font.render("Next", True, cream)
        hold_text = self.guide_font.render("Hold to skip", True, cream)

        key_rect = pygame.Rect(x, center_y - key_height // 2, key_width, key_height)
        pygame.draw.rect(
            target, (103, 73, 60), key_rect.move(0, ui(2)),
            border_radius=ui(6)
        )
        pygame.draw.rect(target, (249, 235, 211), key_rect, border_radius=ui(6))
        pygame.draw.rect(
            target, (125, 88, 69), key_rect, ui(2),
            border_radius=ui(6)
        )
        space_label = self.guide_font.render("SPACE", True, (123, 86, 66))
        target.blit(space_label, space_label.get_rect(center=key_rect.center))

        x = key_rect.right + gap
        target.blit(next_text, next_text.get_rect(midleft=(x, center_y)))

        x += next_text.get_width() + divider_gap
        pygame.draw.line(
            target, (124, 101, 88),
            (x, center_y - ui(11)), (x, center_y + ui(11)), ui(1)
        )
        x += divider_gap

        circle_rect = pygame.Rect(x, center_y - circle_size // 2, circle_size, circle_size)
        radius = ui(12)
        pygame.draw.circle(
            target, (105, 85, 75), circle_rect.center, radius, ui(3)
        )

        progress = 0.0
        if self.space_held_since is not None and not self.space_skip_triggered:
            elapsed = pygame.time.get_ticks() - self.space_held_since
            progress = min(1.0, max(0.0, elapsed / self.hold_to_skip_ms))

        if progress > 0:
            steps = max(2, int(64 * progress))
            points = []
            for i in range(steps + 1):
                angle = -math.pi / 2 + 2 * math.pi * progress * i / steps
                points.append((
                    round(circle_rect.centerx + radius * math.cos(angle)),
                    round(circle_rect.centery + radius * math.sin(angle)),
                ))
            pygame.draw.lines(target, accent, False, points, ui(3))

        symbol_font = self.guide_font
        symbol = symbol_font.render("S", True, accent if progress else cream)
        target.blit(symbol, symbol.get_rect(center=circle_rect.center))

        x = circle_rect.right + gap
        target.blit(hold_text, hold_text.get_rect(midleft=(x, center_y)))

    def draw(self, target, mouse_pos):
        self._draw_panels(target)
        self._draw_dialogue(target)
        self._draw_navigation_guide(target)
