"""Counter scene and interactive welcome tutorial for SLICE."""

import math
import random

import pygame

from screens.introduction import IntroScene
from settings import ASSETS_DIR, HEIGHT, WIDTH, ui


CREAM = (247, 233, 209)
PAPER = (255, 247, 232)
BROWN = (123, 86, 66)
YELLOW = (255, 215, 105)

TYPE_SPEED = 45

# Cash register size and position
REGISTER_WIDTH = 350
REGISTER_RIGHT_MARGIN = 55
REGISTER_BOTTOM_MARGIN = 20

# Cash register highlight
REGISTER_HIGHLIGHT_THICKNESS = 6
REGISTER_HIGHLIGHT_PADDING = 12
REGISTER_HIGHLIGHT_SPEED = 0.004

# Tutorial animation
CHEF_SLIDE_DURATION = 0.65
CHEF_DIALOGUE_DELAY = 0.15
BUBBLE_POP_DURATION = 0.18

# First customer: enters from the left and stops behind the counter
CAT_PATH = ASSETS_DIR / "MAIN" / "ANIMAL" / "cat.png"
CAT_MAX_WIDTH = 220
CAT_MAX_HEIGHT = 300
CAT_TARGET_CENTER_X = 0.54
CAT_BOTTOM_MARGIN = 165
CAT_WALK_DURATION = 1.8
CAT_ORDER_TEXT = "Meow! One Hawaiian pizza, please!"

TUTORIAL_LINES = [
    (
        "Welcome, {name}! We're understaffed, "
        "underpaid, and undercooked. Let's get cooking!"
    ),
    (
        "See that cash register over there? "
        "That's where all your hard-earned pizza money goes!"
    ),
    (
        "Every completed order earns you money. "
        "But make a mistake, and you might lose some!"
    ),
    (
        "See the clock in the top-left corner? "
        "That's your shop time! It's Day 1. "
        "We open at 10 AM and close at 8 PM. "
        "Every 30 seconds is one in-game hour!"
    ),
    (
        "Alright, enough talking! We've got pizzas "
        "to make and bills to pay. Ready, Chef?"
    ),
]


class WelcomeScene:
    """Display the counter and interactive welcome tutorial."""

    # Use the same synthesized voices as the introduction.
    _build_voice_sounds = IntroScene._build_voice_sounds
    _stop_narration = IntroScene._stop_narration
    _speak_new_letters = IntroScene._speak_new_letters

    def __init__(self, game):
        self.game = game

        self.background = self._load_image(
            ASSETS_DIR / "MAIN" / "game bg.png"
        )
        self.counter = self._load_image(
            ASSETS_DIR / "MAIN" / "counter.png"
        )
        self.register = self._load_register()
        self.tutorial_chef = self._load_tutorial_chef()
        self.cat = self._load_cat()

        # Flow: chef tutorial -> cat walks in -> cat orders -> gameplay
        self.phase = "chef"
        self.cat_walk_elapsed = 0.0
        self.cat_start_x = -self.cat.get_width() if self.cat else -ui(220)
        self.cat_target_x = round(WIDTH * CAT_TARGET_CENTER_X)
        self.cat_center_x = float(self.cat_start_x)
        self.current_order = None

        if self.background is not None:
            self.background = pygame.transform.smoothscale(
                self.background, (WIDTH, HEIGHT)
            )

        if self.counter is not None:
            self.counter = self._resize_width(self.counter, WIDTH)

        # Keep a dark copy of the foreground counter so the chef can stand
        # behind it without the counter suddenly turning bright.
        self.dimmed_counter = self._make_dimmed_counter()

        # Cache the dimmed HUD so it can be drawn in front of the counter.
        self.dimmed_clock = None
        self.dimmed_clock_text = None

        if self.register is not None:
            self.register = self._resize_width(
                self._crop(self.register), ui(REGISTER_WIDTH)
            )

        # The register always sits above the counter, even when dimmed.
        self.dimmed_register = None
        self.register_highlight = None
        if self.register is not None:
            self.dimmed_register = self.register.copy()
            self.dimmed_register.fill(
                (90, 90, 90), special_flags=pygame.BLEND_RGB_MULT
            )
            self.dimmed_register.fill(
                (23, 14, 10), special_flags=pygame.BLEND_RGB_ADD
            )
            self.register_highlight = self._create_register_highlight()

        self.popup_font = self._font(ui(28), "dialogue")
        self.label_font = self._font(ui(20), "label")
        self.guide_font = self._font(ui(16), "small")

        self.popup_x = ui(440)
        self.popup_y = ui(175)
        self.popup_max_width = WIDTH - ui(490)

        self.show_tutorial_popup = True
        self.tutorial_index = 0
        self.characters_shown = 0.0

        self.chef_slide_timer = 0.0
        self.dialogue_started = False

        self.bubble_timer = 0.0
        self.bubble_scale = 0.75

        # Initialize these before calling _refresh_dialogue().
        self.voice_rng = random.Random()
        self.voice_sounds = {}
        self.voice_channel = None
        self.last_voice_time = -1000
        self.voice_delay = 65
        self.transitioning = False

        mixer_settings = pygame.mixer.get_init()
        if mixer_settings is not None:
            cached = getattr(IntroScene, "_voice_cache", None)
            if (
                getattr(IntroScene, "_voice_cache_settings", None)
                == mixer_settings
                and cached is not None
            ):
                self.voice_sounds = cached
            else:
                self._build_voice_sounds()
                IntroScene._voice_cache = self.voice_sounds
                IntroScene._voice_cache_settings = mixer_settings

        self.dialogue = ""
        self._refresh_dialogue()

    def _load_image(self, path):
        """Load an image with transparency."""
        try:
            return pygame.image.load(str(path)).convert_alpha()
        except (OSError, pygame.error) as error:
            print(f"Could not load {path}: {error}")
            return None

    def _load_register(self):
        """Load cash register from either existing asset location."""
        paths = [
            ASSETS_DIR / "cregister_close.png",
            ASSETS_DIR / "MAIN" / "cregister_close.png",
        ]
        for path in paths:
            if path.is_file():
                image = self._load_image(path)
                if image is not None:
                    return image
        print("Cash register image not found.")
        return None

    def _crop(self, image):
        """Remove transparent margins without stretching the artwork."""
        bounds = image.get_bounding_rect(min_alpha=10)
        if bounds.width > 0 and bounds.height > 0:
            return image.subsurface(bounds).copy()
        return image

    def _resize_width(self, image, width):
        """Resize while preserving the original aspect ratio."""
        height = max(
            1, round(image.get_height() * width / image.get_width())
        )
        return pygame.transform.smoothscale(image, (width, height))

    def _make_dimmed_counter(self):
        """Create the counter as it looks under the dark tutorial overlay.

        The RGB operations preserve the PNG's transparent pixels, so the
        counter can cover the chef without drawing a dark rectangle.
        """
        if self.counter is None:
            return None

        image = self.counter.copy()
        # Same approximate result as the overlay (35, 22, 16, 165).
        image.fill((90, 90, 90), special_flags=pygame.BLEND_RGB_MULT)
        image.fill((23, 14, 10), special_flags=pygame.BLEND_RGB_ADD)
        return image

    def _draw_dimmed_clock(self, target):
        """Keep the darkened Day/time HUD above the foreground counter."""
        clock = self.game.scene_manager.shop_clock
        clock_text = (clock.day, clock.time_text())

        # Re-render only when the displayed day or time changes.
        if self.dimmed_clock_text != clock_text:
            # The clock draws itself at (ui(24), ui(24)), so this small
            # transparent surface includes its entire top-left panel.
            layer = pygame.Surface(
                (ui(230), ui(125)), pygame.SRCALPHA
            )
            clock.draw(layer)

            # Match the same dimness used for the foreground counter.
            # These operations preserve transparency around the HUD.
            layer.fill(
                (90, 90, 90), special_flags=pygame.BLEND_RGB_MULT
            )
            layer.fill(
                (23, 14, 10), special_flags=pygame.BLEND_RGB_ADD
            )

            self.dimmed_clock = layer
            self.dimmed_clock_text = clock_text

        if self.dimmed_clock is not None:
            target.blit(self.dimmed_clock, (0, 0))

    def _load_tutorial_chef(self):
        """Load and resize the tutorial chef."""
        image = self._load_image(
            ASSETS_DIR / "WELCOME_TUT" / "tuts-chef.png"
        )
        if image is None:
            return None

        image = self._crop(image)
        scale = min(
            ui(300) / image.get_width(),
            ui(425) / image.get_height(),
        )
        return pygame.transform.smoothscale(
            image,
            (
                max(1, round(image.get_width() * scale)),
                max(1, round(image.get_height() * scale)),
            ),
        )

    def _load_cat(self):
        """Load the first customer without distorting the PNG."""
        image = self._load_image(CAT_PATH)
        if image is None:
            return None

        image = self._crop(image)
        scale = min(
            ui(CAT_MAX_WIDTH) / image.get_width(),
            ui(CAT_MAX_HEIGHT) / image.get_height(),
        )
        return pygame.transform.smoothscale(
            image,
            (
                max(1, round(image.get_width() * scale)),
                max(1, round(image.get_height() * scale)),
            ),
        )

    def _font(self, size, fallback_name):
        path = (
            ASSETS_DIR
            / "FONTS"
            / "Fredoka/static/Fredoka-SemiBold.ttf"
        )
        try:
            return pygame.font.Font(str(path), size)
        except (OSError, pygame.error):
            return (
                self.game.fonts.get(fallback_name)
                or pygame.font.Font(None, size)
            )

    def _create_register_highlight(self):
        """Build a shape-following yellow outline for the register."""
        image = self.register
        if image is None:
            return None

        padding = max(10, ui(REGISTER_HIGHLIGHT_PADDING))
        thickness = max(3, ui(REGISTER_HIGHLIGHT_THICKNESS))

        mask = pygame.mask.from_surface(image, 10)
        silhouette = mask.to_surface(
            setcolor=(*YELLOW, 255),
            unsetcolor=(0, 0, 0, 0),
        )

        highlight = pygame.Surface(
            (
                image.get_width() + padding * 2,
                image.get_height() + padding * 2,
            ),
            pygame.SRCALPHA,
        )

        for dx in range(-thickness, thickness + 1):
            for dy in range(-thickness, thickness + 1):
                if dx * dx + dy * dy <= thickness * thickness:
                    highlight.blit(
                        silhouette, (padding + dx, padding + dy)
                    )
        return highlight

    def _register_rect(self):
        if self.register is None:
            return None
        return self.register.get_rect(
            bottomright=(
                WIDTH - ui(REGISTER_RIGHT_MARGIN),
                HEIGHT - ui(REGISTER_BOTTOM_MARGIN),
            )
        )

    def _counter_rect(self):
        if self.counter is None:
            return None
        return self.counter.get_rect(midbottom=(WIDTH // 2, HEIGHT))

    def _draw_register(self, target):
        if self.register is not None:
            target.blit(self.register, self._register_rect())

    def _draw_register_highlight(self, target):
        if self.register is None:
            return

        rect = self._register_rect()
        if self.register_highlight is not None:
            padding = max(10, ui(REGISTER_HIGHLIGHT_PADDING))
            pulse = math.sin(
                pygame.time.get_ticks() * REGISTER_HIGHLIGHT_SPEED
            )
            self.register_highlight.set_alpha(int(220 + 35 * pulse))
            target.blit(
                self.register_highlight,
                (rect.x - padding, rect.y - padding),
            )
        target.blit(self.register, rect)

    def _refresh_dialogue(self):
        selected = getattr(self.game, "selected_character", None) or {}
        name = str(selected.get("name", "CHEF")).title()
        new_text = TUTORIAL_LINES[self.tutorial_index].format(name=name)

        if self.dialogue != new_text:
            self._stop_narration()
            self.dialogue = new_text
            self.characters_shown = 0.0
            self.bubble_timer = 0.0
            self.bubble_scale = 0.75

    def _advance_tutorial(self):
        """Use SPACE for chef dialogue, then show the Okay button."""
        if not self.dialogue_started or self.phase != "chef":
            return

        if self.characters_shown < len(self.dialogue):
            self.characters_shown = float(len(self.dialogue))
            self._stop_narration()
        elif self.tutorial_index < len(TUTORIAL_LINES) - 1:
            self.tutorial_index += 1
            self._refresh_dialogue()
        # The final chef line requires the on-screen Okay button.

    def _acknowledge_chef(self):
        """Close the tutorial and let the cat walk into the shop."""
        if self.phase != "chef" or self.characters_shown < len(self.dialogue):
            return
        if self.tutorial_index != len(TUTORIAL_LINES) - 1:
            return

        self._stop_narration()
        self.show_tutorial_popup = False
        self.phase = "cat_enter"
        self.cat_walk_elapsed = 0.0
        self.cat_center_x = float(self.cat_start_x)

    def _accept_cat_order(self):
        """Accept the Hawaiian pizza order and enable normal navigation."""
        if self.phase != "cat_order":
            return

        self.current_order = "Hawaiian"
        self.phase = "playing"
        self.game.scene_manager.shop_clock.start()
        print("First customer order accepted: Hawaiian pizza")

    def _mouse_positions(self, position):
        """Support mouse clicks in both windowed and scaled fullscreen mode."""
        positions = [position]
        viewport = getattr(self.game, "_viewport", None)
        if viewport is not None and viewport.width > 0 and viewport.height > 0:
            positions.append((
                round((position[0] - viewport.x) * WIDTH / viewport.width),
                round((position[1] - viewport.y) * HEIGHT / viewport.height),
            ))
        return positions

    def _clicked(self, event_pos, rectangle):
        return any(rectangle.collidepoint(p) for p in self._mouse_positions(event_pos))

    def _okay_rect(self, bubble):
        """Place the response directly underneath the speaker's bubble."""
        return pygame.Rect(
            bubble.centerx - ui(67),
            bubble.bottom + ui(11),
            ui(134),
            ui(42),
        )

    def _go_to(self, name):
        if name in self.game.scene_manager.scenes:
            self._stop_narration()
            self.game.scene_manager.go_to(name)

    def handle_event(self, event):
        """Handle chef dialogue, clickable responses, and navigation."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == "chef":
                if (
                    self.tutorial_index == len(TUTORIAL_LINES) - 1
                    and self.dialogue_started
                    and self.characters_shown >= len(self.dialogue)
                    and self._clicked(
                        event.pos, self._okay_rect(self._chef_bubble_rect())
                    )
                ):
                    self._acknowledge_chef()
                return

            if self.phase == "cat_order":
                if self._clicked(event.pos, self._okay_rect(self._cat_bubble_rect())):
                    self._accept_cat_order()
                return

        if event.type != pygame.KEYDOWN:
            return

        if self.phase == "chef":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._advance_tutorial()
            return

        # Don't allow movement while the customer is walking or ordering.
        if self.phase != "playing":
            return

        if event.key == pygame.K_a:
            self._go_to("oven")
        elif event.key == pygame.K_d:
            self._go_to("kitchen")
        elif event.key == pygame.K_ESCAPE:
            self._go_to("character")

    def update(self, delta_time):
        """Animate chef dialogue or let the customer walk into position."""
        if self.phase == "cat_enter":
            self.cat_walk_elapsed = min(
                CAT_WALK_DURATION, self.cat_walk_elapsed + delta_time
            )
            progress = self.cat_walk_elapsed / CAT_WALK_DURATION
            eased = 1 - (1 - progress) ** 3
            self.cat_center_x = (
                self.cat_start_x
                + (self.cat_target_x - self.cat_start_x) * eased
            )
            if progress >= 1:
                self.cat_center_x = float(self.cat_target_x)
                self.phase = "cat_order"
            return

        if self.phase != "chef":
            return

        self._refresh_dialogue()
        self.chef_slide_timer += delta_time
        if not self.dialogue_started:
            if self.chef_slide_timer < (
                CHEF_SLIDE_DURATION + CHEF_DIALOGUE_DELAY
            ):
                return
            self.dialogue_started = True

        self.bubble_timer = min(
            BUBBLE_POP_DURATION, self.bubble_timer + delta_time
        )
        progress = self.bubble_timer / BUBBLE_POP_DURATION
        self.bubble_scale = 0.75 + 0.25 * (1 - (1 - progress) ** 3)

        old_count = int(self.characters_shown)
        self.characters_shown = min(
            float(len(self.dialogue)),
            self.characters_shown + TYPE_SPEED * delta_time,
        )
        self._speak_new_letters(
            self.dialogue, old_count, int(self.characters_shown)
        )

    def draw(self, target, mouse_pos):
        """Draw the scene with customers behind the foreground counter."""
        target.fill(CREAM)
        if self.background is not None:
            target.blit(self.background, (0, 0))

        # The cat is in the room, so it must appear BEFORE the counter.
        if self.phase in ("cat_enter", "cat_order", "playing"):
            self._draw_cat(target)

        if self.counter is not None:
            target.blit(self.counter, self._counter_rect())

        # Cash register and clock are always ABOVE the counter.
        self._draw_register(target)
        self.game.scene_manager.shop_clock.draw(target)

        if self.phase == "chef":
            self._draw_tutorial(target)
        elif self.phase == "cat_order":
            bubble = self._cat_bubble_rect()
            self._draw_cat_order(target, bubble)
            self._draw_okay_button(target, self._okay_rect(bubble))
        elif self.phase == "playing":
            self._draw_controls(target)

    def _draw_cat(self, target):
        """Draw a walking cat behind the foreground counter."""
        if self.cat is None:
            return

        bob = 0
        if self.phase == "cat_enter":
            bob = round(
                ui(3) * abs(math.sin(self.cat_walk_elapsed * 15))
            )

        rect = self.cat.get_rect(
            midbottom=(
                round(self.cat_center_x),
                HEIGHT - ui(CAT_BOTTOM_MARGIN) - bob,
            )
        )
        target.blit(self.cat, rect)

    def _draw_tutorial(self, target):
        """Dim the scene and place the chef BEHIND the foreground counter."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 22, 16, 165))
        target.blit(overlay, (0, 0))

        # First: chef appears bright, sliding in from the left.
        if self.tutorial_chef is not None:
            progress = min(
                1.0, self.chef_slide_timer / CHEF_SLIDE_DURATION
            )
            eased = 1 - (1 - progress) ** 3
            start_x = -self.tutorial_chef.get_width()
            end_x = ui(255)
            current_x = round(start_x + (end_x - start_x) * eased)

            chef_rect = self.tutorial_chef.get_rect(
                midbottom=(current_x, HEIGHT - ui(185))
            )
            target.blit(self.tutorial_chef, chef_rect)

        # Second: cover the chef's lower part with the darkened counter.
        # This preserves the foreground depth without a bright counter stripe.
        if self.dimmed_counter is not None:
            target.blit(self.dimmed_counter, self._counter_rect())

        # Always draw the cash register ABOVE the foreground counter.
        # Keep it dark until the chef explains it in dialogues 2 and 3.
        if self.tutorial_index in (1, 2):
            self._draw_register_highlight(target)
        elif self.dimmed_register is not None:
            target.blit(self.dimmed_register, self._register_rect())

        # Day/time is also always above the counter, but starts dimmed.
        self._draw_dimmed_clock(target)
        if self.tutorial_index == 3:
            self.game.scene_manager.shop_clock.draw(
                target, highlighted=True
            )

        if self.dialogue_started:
            bubble = self._draw_dialogue(target)
            is_final = self.tutorial_index == len(TUTORIAL_LINES) - 1
            if is_final:
                if self.characters_shown >= len(self.dialogue):
                    self._draw_okay_button(target, self._okay_rect(bubble))
            else:
                self._draw_space_guide(target)

    def _wrap_text(self, text, font, width):
        lines = []
        current = ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            if font.size(trial)[0] <= width:
                current = trial
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def _chef_bubble_rect(self):
        """Return the displayed chef bubble's rectangle, including pop scale."""
        font = self.popup_font
        text_width = self.popup_max_width - ui(48)
        lines = self._wrap_text(self.dialogue, font, text_width)
        line_height = font.get_linesize() + 5
        bubble_width = max(
            ui(220),
            min(
                self.popup_max_width,
                max(font.size(line)[0] for line in lines) + ui(48),
            ),
        )
        bubble_height = len(lines) * line_height + ui(44)
        x = max(ui(20), min(self.popup_x, WIDTH - bubble_width - ui(20)))
        y = max(ui(30), min(self.popup_y, HEIGHT - bubble_height - ui(75)))
        return pygame.Rect(
            x + bubble_width // 2 - round(bubble_width * self.bubble_scale) // 2,
            y + bubble_height // 2 - round(bubble_height * self.bubble_scale) // 2,
            max(1, round(bubble_width * self.bubble_scale)),
            max(1, round(bubble_height * self.bubble_scale)),
        )

    def _draw_dialogue(self, target):
        """Draw animated chef dialogue and return its on-screen rectangle."""
        font = self.popup_font
        text_width = self.popup_max_width - ui(48)
        full_lines = self._wrap_text(self.dialogue, font, text_width)
        line_height = font.get_linesize() + 5
        bubble_width = max(
            ui(220),
            min(
                self.popup_max_width,
                max(font.size(line)[0] for line in full_lines) + ui(48),
            ),
        )
        bubble_height = len(full_lines) * line_height + ui(44)

        bubble = pygame.Surface(
            (bubble_width, bubble_height), pygame.SRCALPHA
        )
        pygame.draw.rect(
            bubble, CREAM, bubble.get_rect(), border_radius=ui(17)
        )
        pygame.draw.rect(
            bubble, BROWN, bubble.get_rect(), ui(3), border_radius=ui(17)
        )

        visible = self.dialogue[:int(self.characters_shown)]
        for index, line in enumerate(self._wrap_text(visible, font, text_width)):
            rendered = font.render(line, True, BROWN)
            bubble.blit(rendered, (ui(24), ui(20) + index * line_height))

        rect = self._chef_bubble_rect()
        scaled = pygame.transform.smoothscale(bubble, rect.size)
        target.blit(scaled, rect)

        if (
            self.tutorial_index != len(TUTORIAL_LINES) - 1
            and self.characters_shown >= len(self.dialogue)
        ):
            bounce = round(
                ui(3) * math.sin(pygame.time.get_ticks() * 0.008)
            )
            arrow = self.label_font.render("▼", True, BROWN)
            target.blit(
                arrow,
                (rect.right - ui(30), rect.bottom - ui(27) + bounce),
            )
        return rect

    def _cat_bubble_rect(self):
        """Bubble above the counter when the cat reaches the center."""
        width = min(ui(465), WIDTH - ui(80))
        lines = self._wrap_text(CAT_ORDER_TEXT, self.label_font, width - ui(36))
        height = ui(82) + len(lines) * (self.label_font.get_linesize() + ui(4))
        return pygame.Rect(
            round(WIDTH * CAT_TARGET_CENTER_X) - width // 2,
            ui(88),
            width,
            height,
        )

    def _draw_cat_order(self, target, bubble):
        """Display the first customer's Hawaiian pizza request."""
        pygame.draw.rect(
            target, (91, 58, 44), bubble.move(0, ui(3)),
            border_radius=ui(15),
        )
        pygame.draw.rect(
            target, CREAM, bubble, border_radius=ui(15)
        )
        pygame.draw.rect(
            target, BROWN, bubble, ui(3), border_radius=ui(15)
        )

        title = self.guide_font.render("CUSTOMER ORDER", True, BROWN)
        target.blit(title, (bubble.x + ui(18), bubble.y + ui(12)))
        pizza = self.popup_font.render("HAWAIIAN PIZZA", True, BROWN)
        target.blit(pizza, (bubble.x + ui(18), bubble.y + ui(33)))

        line_y = bubble.y + ui(72)
        for line in self._wrap_text(
            CAT_ORDER_TEXT, self.label_font, bubble.width - ui(36)
        ):
            text = self.label_font.render(line, True, BROWN)
            target.blit(text, (bubble.x + ui(18), line_y))
            line_y += self.label_font.get_linesize() + ui(4)

    def _draw_okay_button(self, target, rect):
        """Interactive Okay. button beneath the speaker's dialogue."""
        mouse = pygame.mouse.get_pos()
        hovered = self._clicked(mouse, rect)
        color = (255, 226, 157) if hovered else PAPER

        pygame.draw.rect(
            target, (91, 58, 44), rect.move(0, ui(3)),
            border_radius=ui(11),
        )
        pygame.draw.rect(
            target, color, rect, border_radius=ui(11),
        )
        pygame.draw.rect(
            target, YELLOW if hovered else BROWN, rect, ui(3),
            border_radius=ui(11),
        )
        label = self.label_font.render("Okay.", True, BROWN)
        target.blit(label, label.get_rect(center=rect.center))

    def _draw_space_guide(self, target):
        """Draw SPACE to continue in the bottom-right."""
        y = HEIGHT - ui(24)
        label = self.guide_font.render("Next", True, (255, 238, 208))
        key_width = ui(66)
        key_height = ui(27)
        x = WIDTH - key_width - label.get_width() - ui(34)

        key_rect = pygame.Rect(
            x, y - key_height // 2, key_width, key_height
        )
        pygame.draw.rect(
            target,
            (103, 73, 60),
            key_rect.move(0, ui(2)),
            border_radius=ui(6),
        )
        pygame.draw.rect(
            target, (249, 235, 211), key_rect, border_radius=ui(6)
        )
        pygame.draw.rect(
            target, (125, 88, 69), key_rect, ui(2), border_radius=ui(6)
        )

        key = self.guide_font.render("SPACE", True, BROWN)
        target.blit(key, key.get_rect(center=key_rect.center))
        target.blit(
            label,
            label.get_rect(midleft=(key_rect.right + ui(9), y)),
        )

    def _draw_controls(self, target):
        """Bottom-right A/D navigation after the tutorial."""
        y = HEIGHT - ui(47)
        x = WIDTH - ui(300)
        items = [("A", "Oven"), ("D", "Kitchen")]

        for index, (letter, label) in enumerate(items):
            rect = pygame.Rect(x, y, ui(34), ui(28))
            pygame.draw.rect(
                target, PAPER, rect, border_radius=ui(6)
            )
            pygame.draw.rect(
                target, BROWN, rect, ui(2), border_radius=ui(6)
            )

            key_image = self.guide_font.render(letter, True, BROWN)
            target.blit(key_image, key_image.get_rect(center=rect.center))

            description = self.guide_font.render(label, True, PAPER)
            target.blit(
                description,
                description.get_rect(midleft=(rect.right + ui(8), rect.centery)),
            )

            x += ui(130)
            if index == 0:
                pygame.draw.line(
                    target,
                    BROWN,
                    (x - ui(12), y),
                    (x - ui(12), y + ui(28)),
                    ui(2),
                )
