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
CHEF_EXIT_DURATION = 0.65
CHEF_DIALOGUE_DELAY = 0.15

# Match the larger bottom-left chef placement used in kitchen.py.
CHEF_MAX_WIDTH = 440
CHEF_MAX_HEIGHT = 650
CHEF_CENTER_X = 240
CHEF_BOTTOM_OFFSET = 12
BUBBLE_POP_DURATION = 0.18

# First customer: enters from the left and stops behind the counter
CAT_PATH = ASSETS_DIR / "MAIN" / "ANIMAL" / "CAT" / "cat.png"
CAT_MAX_WIDTH = 340
CAT_MAX_HEIGHT = 455
CAT_TARGET_CENTER_X = 0.54
CAT_BOTTOM_MARGIN = 165
CAT_WALK_DURATION = 3.6
CAT_REACTION_DURATION = 1.8
CAT_EXIT_DURATION = 3.0
CAT_ORDER_TEXT = "Meow! One cheese pizza, please!"
CAT_ORDER_CHEF_TEXT = (
    "Our first customer ordered a cheese pizza! "
    "That's tomato sauce and cheese on one delicious pizza. "
    "Press Okay to accept the order, Chef!"
)
ORDER_REWARD = 50
REGISTER_OPEN_DURATION = 1.8
ORDER_PIZZA_WIDTH = 130

# Customer patience: 60 real seconds = two in-game hours.
CUSTOMER_WAIT_SECONDS = 100.0
PATIENCE_BAR_WIDTH = 170
PATIENCE_BAR_HEIGHT = 20
PATIENCE_BAR_HEAD_GAP = 42
PATIENCE_TUTORIAL_TEXT = (
    "See that bar above our customer's head, Chef? "
    "That's their patience! It shrinks while they wait. "
    "If it runs out, they'll get angry. "
    "So don't keep them waiting too long!"
)
KITCHEN_NAV_TUTORIAL_TEXT = (
    "Time to make that cheese pizza! See the controls "
    "at the bottom-right? Press D to go to the Kitchen. "
    "Go ahead, Chef, give it a try!"
)

SERVE_TUTORIAL_TEXT = (
    "That pizza is cooked, Chef! Now click the highlighted customer "
    "to serve their cheese pizza. Hurry, they have been waiting!"
)
SERVE_FINISHED_TEXT = (
    "Now that is a happy customer! Great work, Chef! "
    "Our first cheese pizza has been served!"
)

CAT_SERVE_GLOW_THICKNESS = 8

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
        self.open_register = self._load_register("cregister_open.png")
        self.tutorial_chef = self._load_tutorial_chef()
        self.cat = self._load_cat()
        self.cheese_pizza = self._load_order_pizza()

        # Flow: welcome -> cat walks in alone -> chef explains the order
        # -> chef stays for patience and navigation lessons -> gameplay
        self.phase = "chef"
        self.cat_walk_elapsed = 0.0
        self.cat_start_x = -self.cat.get_width() if self.cat else -ui(220)
        self.cat_target_x = round(WIDTH * CAT_TARGET_CENTER_X)
        self.cat_center_x = float(self.cat_start_x)
        self.customer_reaction_elapsed = 0.0
        self.cat_exit_elapsed = 0.0
        self.cat_exit_start_x = float(self.cat_target_x)
        self.cat_exit_target_x = float(WIDTH + (self.cat.get_width() // 2 if self.cat else ui(200)) + ui(30))
        self.current_order = None
        self.customer_wait_started_at = None
        self.customer_wait_stopped_at = None
        self.customer_angry = False
        self.customer_served = False
        self.order_status = "waiting"
        self.register_open_timer = 0.0
        self.reward_display_timer = 0.0
        self.cat_angry = None
        if self.cat is not None:
            self.cat_angry = self.cat.copy()
            self.cat_angry.fill(
                (255, 160, 160), special_flags=pygame.BLEND_RGB_MULT
            )

        # Shape-following glow and click mask for the first customer.
        self.cat_mask = (
            pygame.mask.from_surface(self.cat, 20)
            if self.cat is not None else None
        )
        self.cat_glow = self._make_cat_glow()
        self.counter_mask = None  # Filled when the counter is scaled below.

        if self.background is not None:
            self.background = pygame.transform.smoothscale(
                self.background, (WIDTH, HEIGHT)
            )

        if self.counter is not None:
            self.counter = self._resize_width(self.counter, WIDTH)
            self.counter_mask = pygame.mask.from_surface(self.counter, 20)

        # Keep a dark copy of the counter for tutorial scenes.
        # The chef will be drawn in front of this layer.
        self.dimmed_counter = self._make_dimmed_counter()

        # Cache the dimmed HUD so it can be drawn in front of the counter.
        self.dimmed_clock = None
        self.dimmed_clock_text = None

        if self.register is not None:
            self.register = self._resize_width(
                self._crop(self.register), ui(REGISTER_WIDTH)
            )
        if self.open_register is not None:
            self.open_register = self._resize_width(
                self._crop(self.open_register), ui(REGISTER_WIDTH)
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
        self.patience_font = self._font(ui(15), "small")
        self.reward_font = self._font(ui(30), "label")

        self.popup_x = ui(440)
        self.popup_y = ui(175)
        self.popup_max_width = WIDTH - ui(490)

        self.show_tutorial_popup = True
        self.tutorial_index = 0
        self.characters_shown = 0.0

        self.chef_slide_timer = 0.0
        self.chef_exit_timer = 0.0
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

    def _load_register(self, filename="cregister_close.png"):
        """Load cash register artwork from either existing asset location."""
        paths = [
            ASSETS_DIR / filename,
            ASSETS_DIR / "MAIN" / filename,
        ]
        for path in paths:
            if path.is_file():
                image = self._load_image(path)
                if image is not None:
                    return image
        print("Cash register image not found.")
        return None

    def _load_order_pizza(self):
        """Load the cheese pizza shown with the customer's order."""
        image = self._load_image(
            ASSETS_DIR / "KITCHEN" / "COOKED CHEESE PIZZA FINAL.png"
        )
        if image is None:
            return None

        image = self._crop(image)
        scale = min(
            ui(ORDER_PIZZA_WIDTH) / image.get_width(),
            ui(ORDER_PIZZA_WIDTH) / image.get_height(),
        )
        return pygame.transform.smoothscale(
            image,
            (
                max(1, round(image.get_width() * scale)),
                max(1, round(image.get_height() * scale)),
            ),
        )

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
            ui(CHEF_MAX_WIDTH) / image.get_width(),
            ui(CHEF_MAX_HEIGHT) / image.get_height(),
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
        image = (
            self.open_register
            if self.register_open_timer > 0
            and self.open_register is not None
            else self.register
        )
        if image is not None:
            target.blit(
                image,
                image.get_rect(
                    bottomright=(
                        WIDTH - ui(REGISTER_RIGHT_MARGIN),
                        HEIGHT - ui(REGISTER_BOTTOM_MARGIN),
                    )
                ),
            )

    def _draw_reward(self, target):
        """Show the one-time order payment above the cash register."""
        if self.reward_display_timer <= 0:
            return

        register_rect = self._register_rect()
        if register_rect is None:
            return

        label = self.reward_font.render(f"+{ORDER_REWARD}", True, (74, 128, 72))
        panel = pygame.Rect(
            0, 0, label.get_width() + ui(24), label.get_height() + ui(12)
        )
        panel.midbottom = (
            register_rect.centerx,
            register_rect.top - ui(10),
        )
        pygame.draw.rect(target, CREAM, panel, border_radius=ui(10))
        pygame.draw.rect(
            target, (74, 128, 72), panel, ui(2), border_radius=ui(10)
        )
        target.blit(label, label.get_rect(center=panel.center))

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

    def _make_cat_glow(self):
        """Make a yellow outline matching the cat's visible shape."""
        if self.cat is None or self.cat_mask is None:
            return None

        thickness = max(3, ui(CAT_SERVE_GLOW_THICKNESS))
        silhouette = self.cat_mask.to_surface(
            setcolor=(*YELLOW, 255),
            unsetcolor=(0, 0, 0, 0),
        )
        glow = pygame.Surface(
            (self.cat.get_width() + 2 * thickness,
             self.cat.get_height() + 2 * thickness),
            pygame.SRCALPHA,
        )
        for dx, dy in (
            (-thickness, 0), (thickness, 0),
            (0, -thickness), (0, thickness),
            (-thickness, -thickness), (-thickness, thickness),
            (thickness, -thickness), (thickness, thickness),
        ):
            glow.blit(silhouette, (thickness + dx, thickness + dy))
        return glow

    def _cat_is_clicked(self, event_position):
        """Only accept clicks on visible cat pixels above the counter."""
        cat_rect = self._cat_rect()
        if self.cat_mask is None or cat_rect is None:
            return False

        counter_rect = self._counter_rect()
        for x, y in self._mouse_positions(event_position):
            if not cat_rect.collidepoint(x, y):
                continue
            local_x = x - cat_rect.x
            local_y = y - cat_rect.y
            if not self.cat_mask.get_at((local_x, local_y)):
                continue

            # The cat stands BEHIND the counter: its hidden feet
            # are not clickable through the countertop.
            if counter_rect is not None and self.counter_mask is not None:
                cx = x - counter_rect.x
                cy = y - counter_rect.y
                if (0 <= cx < self.counter_mask.get_size()[0]
                        and 0 <= cy < self.counter_mask.get_size()[1]
                        and self.counter_mask.get_at((cx, cy))):
                    continue
            return True
        return False

    def _start_serving_intro(self):
        """Return from Oven, slide chef in, and highlight the cat."""
        if self.phase != "playing" or self.order_status == "served":
            return
        self.phase = "serve_intro"
        self._set_chef_dialogue(SERVE_TUTORIAL_TEXT, slide_in=True)

    def _finish_serving(self):
        """Slide the chef away once the player acknowledges success."""
        if self.phase != "served" or self.characters_shown < len(self.dialogue):
            return
        self._stop_narration()
        self.phase = "serve_exit"
        self.chef_exit_timer = 0.0
        self.dialogue_started = False

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

        # Hide the bubble and send the chef back off the left edge
        # before allowing the first customer to enter.
        self._stop_narration()
        self.dialogue_started = False
        self.chef_exit_timer = 0.0
        self.phase = "chef_exit"

    def _set_chef_dialogue(self, text, slide_in=False):
        """Start the chef's next sentence, optionally entering from the left."""
        self._stop_narration()
        self.dialogue = text
        self.characters_shown = 0.0
        self.bubble_timer = 0.0
        self.bubble_scale = 0.75
        if slide_in:
            self.chef_slide_timer = 0.0
            self.chef_exit_timer = 0.0
            self.dialogue_started = False
        else:
            # A new sentence from a chef who is already on-screen.
            self.dialogue_started = True

    def _update_chef_dialogue(self, delta_time):
        """Run chef entrance, pop animation, typing, and voice."""
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

    def _accept_cat_order(self):
        """Accept the cheese pizza order and continue with the chef in place."""
        if self.phase != "cat_order":
            return

        self.current_order = "Cheese"
        self.order_status = "waiting"
        # Keep the chef standing here. Continue directly with the
        # patience lesson instead of sliding out and back in.
        self.phase = "patience_intro"
        self.show_tutorial_popup = True
        self._set_chef_dialogue(PATIENCE_TUTORIAL_TEXT, slide_in=False)
        print("First customer order accepted: Cheese pizza")

    def _finish_patience_intro(self):
        """Teach the D key after explaining customer patience."""
        if self.phase != "patience_intro":
            return
        if self.characters_shown < len(self.dialogue):
            return

        # Keep the chef in place for the next tutorial sentence.
        self._stop_narration()
        self.phase = "navigation_intro"
        self.dialogue = KITCHEN_NAV_TUTORIAL_TEXT
        self.characters_shown = 0.0
        self.bubble_timer = 0.0
        self.bubble_scale = 0.75
        self.dialogue_started = True

    def _begin_kitchen_navigation(self):
        """Hide the chef before taking the player to the Kitchen."""
        if self.phase != "navigation_intro":
            return
        if self.characters_shown < len(self.dialogue):
            self.characters_shown = float(len(self.dialogue))
            self._stop_narration()
            return

        self._stop_narration()
        self.dialogue_started = False
        self.chef_exit_timer = 0.0
        self.phase = "navigation_exit"

    def _patience_remaining(self):
        """Read the shared shop clock, so waiting continues in other scenes."""
        if self.customer_wait_started_at is None:
            return CUSTOMER_WAIT_SECONDS
        clock = self.game.scene_manager.shop_clock
        current_time = (
            self.customer_wait_stopped_at
            if self.customer_wait_stopped_at is not None
            else clock.elapsed_seconds
        )
        elapsed = current_time - self.customer_wait_started_at
        return max(0.0, CUSTOMER_WAIT_SECONDS - max(0.0, elapsed))

    def _sync_patience(self):
        """Notice timeouts, even if the player has been away."""
        if (
            self.phase == "playing"
            and self.current_order is not None
            and not self.customer_served
            and not self.customer_angry
            and self._patience_remaining() <= 0
        ):
            self.customer_angry = True
            self.order_status = "angry"
            print("Customer is angry: waiting time ran out!")

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

    def _order_ready(self):
        """Check the shared oven state before allowing the customer to be served."""
        manager = getattr(self.game, "scene_manager", None)
        oven = manager.scenes.get("oven") if manager is not None else None
        return (
            self.current_order == "Cheese"
            and getattr(oven, "oven_state", None) == "cooked"
        )

    def _serve_customer(self, event_pos):
        """Serve the ready order once when the highlighted customer is clicked."""
        if (
            self.phase != "serve_intro"
            or self.customer_served
            or not self._order_ready()
            or not self._cat_is_clicked(event_pos)
        ):
            return

        manager = self.game.scene_manager
        self.customer_wait_stopped_at = manager.shop_clock.elapsed_seconds
        self.customer_served = True
        self.customer_angry = False
        self.order_status = "served"
        self.register_open_timer = REGISTER_OPEN_DURATION
        self.reward_display_timer = REGISTER_OPEN_DURATION
        self._stop_narration()
        self.dialogue_started = False
        self.phase = "customer_reaction"
        self.customer_reaction_elapsed = 0.0
        self.chef_exit_timer = 0.0
        print(f"Cheese pizza served: +{ORDER_REWARD}")

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
        """Handle chef dialogue, customer serving, and navigation."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.phase == "serve_intro":
                self._serve_customer(event.pos)
                return

            if self.phase == "served":
                if (self.dialogue_started
                        and self.characters_shown >= len(self.dialogue)
                        and self._clicked(
                            event.pos, self._okay_rect(self._chef_bubble_rect())
                        )):
                    self._finish_serving()
                return
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
                if (
                    self.dialogue_started
                    and self.characters_shown >= len(self.dialogue)
                    and self._clicked(
                        event.pos, self._okay_rect(self._chef_bubble_rect())
                    )
                ):
                    self._accept_cat_order()
                return

            if self.phase == "patience_intro":
                if (
                    self.characters_shown >= len(self.dialogue)
                    and self._clicked(
                        event.pos, self._okay_rect(self._chef_bubble_rect())
                    )
                ):
                    self._finish_patience_intro()
                return

        if event.type != pygame.KEYDOWN:
            return

        if self.phase in ("serve_intro", "served"):
            if (event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER)
                    and self.characters_shown < len(self.dialogue)):
                self.characters_shown = float(len(self.dialogue))
                self._stop_narration()
            return

        if self.phase == "chef":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                self._advance_tutorial()
            return

        if self.phase == "patience_intro":
            if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.characters_shown < len(self.dialogue):
                    self.characters_shown = float(len(self.dialogue))
                    self._stop_narration()
                else:
                    self._finish_patience_intro()
            return

        if self.phase == "navigation_intro":
            # Only D moves the player forward in this guided step.
            if event.key == pygame.K_d:
                self._begin_kitchen_navigation()
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_KP_ENTER):
                if self.characters_shown < len(self.dialogue):
                    self.characters_shown = float(len(self.dialogue))
                    self._stop_narration()
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
        """Animate the arriving customer and the chef's guided lessons."""
        self.register_open_timer = max(
            0.0, self.register_open_timer - delta_time
        )
        self.reward_display_timer = max(
            0.0, self.reward_display_timer - delta_time
        )
        if self.phase in ("chef_exit", "navigation_exit", "serve_exit"):
            self.chef_exit_timer = min(
                CHEF_EXIT_DURATION,
                self.chef_exit_timer + delta_time,
            )

            if self.chef_exit_timer >= CHEF_EXIT_DURATION:
                if self.phase == "serve_exit":
                    self.phase = "done"
                elif self.phase == "chef_exit":
                    self.show_tutorial_popup = False
                    self.phase = "cat_enter"
                    self.cat_walk_elapsed = 0.0
                    self.cat_center_x = float(self.cat_start_x)
                    # The customer enters first with no chef on-screen.
                else:
                    # Start the day and patience timer once navigation training ends.
                    self.show_tutorial_popup = False
                    self.phase = "playing"
                    clock = self.game.scene_manager.shop_clock
                    clock.start()
                    self.customer_wait_started_at = clock.elapsed_seconds
                    self._go_to("kitchen")
            return

        if self.phase == "customer_reaction":
            # Keep the YA ME! TE! speech bubble on-screen while the
            # chef slides back to the left.
            self.customer_reaction_elapsed += delta_time
            self.chef_exit_timer = min(
                CHEF_EXIT_DURATION, self.chef_exit_timer + delta_time
            )
            if self.customer_reaction_elapsed >= CAT_REACTION_DURATION:
                self.phase = "customer_exit"
                self.cat_exit_elapsed = 0.0
                self.cat_exit_start_x = float(self.cat_center_x)
            return

        if self.phase == "customer_exit":
            # Customer walks out to the right behind the counter.
            self.cat_exit_elapsed = min(
                CAT_EXIT_DURATION, self.cat_exit_elapsed + delta_time
            )
            progress = self.cat_exit_elapsed / CAT_EXIT_DURATION
            eased = progress * progress * (3 - 2 * progress)
            self.cat_center_x = (
                self.cat_exit_start_x
                + (self.cat_exit_target_x - self.cat_exit_start_x) * eased
            )
            if progress >= 1.0:
                # Only NOW does the chef return with congratulations.
                self.phase = "served"
                self._set_chef_dialogue(SERVE_FINISHED_TEXT, slide_in=True)
            return

        if self.phase == "cat_enter":
            self.cat_walk_elapsed = min(
                CAT_WALK_DURATION, self.cat_walk_elapsed + delta_time
            )
            progress = self.cat_walk_elapsed / CAT_WALK_DURATION

            # Keep the customer moving steadily across the room.
            # A gentle ease-out makes their stop feel natural.
            eased = progress * progress * (3 - 2 * progress)
            self.cat_center_x = (
                self.cat_start_x
                + (self.cat_target_x - self.cat_start_x) * eased
            )
            if progress >= 1:
                self.cat_center_x = float(self.cat_target_x)
                self.phase = "cat_order"
                # Show the cat's order first. NOW the chef slides in
                # to explain it and offer the Okay response.
                self._set_chef_dialogue(CAT_ORDER_CHEF_TEXT, slide_in=True)
            return

        if self.phase == "playing":
            self._sync_patience()
            oven = self.game.scene_manager.scenes.get("oven")
            if (self.current_order is not None
                    and self.order_status != "served"
                    and oven is not None
                    and getattr(oven, "oven_state", None) == "cooked"):
                self._start_serving_intro()
            return

        if self.phase not in (
            "chef", "cat_order", "patience_intro", "navigation_intro",
            "serve_intro", "served"
        ):
            return

        if self.phase == "chef":
            self._refresh_dialogue()

        self._update_chef_dialogue(delta_time)

    def draw(self, target, mouse_pos):
        """Draw the scene with customers behind the foreground counter."""
        self._sync_patience()
        target.fill(CREAM)
        if self.background is not None:
            target.blit(self.background, (0, 0))

        # The cat is in the room, so it must appear BEFORE the counter.
        if self.phase in (
            "cat_enter", "cat_order", "patience_intro",
            "navigation_intro", "navigation_exit", "playing",
            "serve_intro", "customer_reaction", "customer_exit"
        ):
            self._draw_cat(target)

        if self.counter is not None:
            target.blit(self.counter, self._counter_rect())

        # Cash register and clock are always ABOVE the counter.
        self._draw_register(target)
        self.game.scene_manager.shop_clock.draw(target)
        self._draw_reward(target)

        if self.phase in ("chef", "chef_exit"):
            self._draw_tutorial(target)
        elif self.phase in ("cat_enter", "cat_order"):
            self._draw_customer_order_tutorial(target)
        elif self.phase in ("patience_intro", "navigation_intro", "navigation_exit"):
            self._draw_patience_tutorial(target)
        elif self.phase == "playing":
            if not self.customer_served:
                self._draw_cat_order(target, self._cat_bubble_rect())
                self._draw_patience_bar(target)
            if self.customer_angry:
                self._draw_angry_message(target)
            self._draw_controls(target)
        elif self.phase in (
            "serve_intro", "customer_reaction", "customer_exit",
            "served", "serve_exit"
        ):
            self._draw_serving_tutorial(target)
        elif self.phase == "done":
            # Empty counter, ready for the next customer's future order.
            pass

    def _draw_customer_order_tutorial(self, target):
        """Show the cat, chef commentary, and order in the correct depth."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 22, 16, 125))
        target.blit(overlay, (0, 0))

        # The customer stays behind the counter, while the chef stands
        # in front of it after the order pops up.
        self._draw_cat(target)
        if self.dimmed_counter is not None:
            target.blit(self.dimmed_counter, self._counter_rect())
        if self.phase == "cat_order":
            self._draw_chef(target)
        if self.dimmed_register is not None:
            target.blit(self.dimmed_register, self._register_rect())
        self._draw_dimmed_clock(target)

        # The order is displayed once the customer reaches the counter.
        if self.phase == "cat_order":
            self._draw_cat_order(target, self._cat_bubble_rect())

        if self.phase in ("cat_enter", "cat_order") and self.dialogue_started:
            bubble = self._draw_dialogue(target)
            if (
                self.phase == "cat_order"
                and self.characters_shown >= len(self.dialogue)
            ):
                self._draw_okay_button(target, self._okay_rect(bubble))

    def _draw_cat_highlight(self, target):
        """Keep a pulsing yellow cat outline visible before the player clicks."""
        rect = self._cat_rect()
        if rect is None or self.cat_glow is None:
            return
        thickness = max(3, ui(CAT_SERVE_GLOW_THICKNESS))
        pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) / 2
        self.cat_glow.set_alpha(round(190 + 55 * pulse))
        target.blit(
            self.cat_glow,
            (rect.x - thickness, rect.y - thickness),
        )

    def _draw_served_message(self, target):
        """Show the customer's response after receiving the pizza."""
        bubble = self._cat_bubble_rect()
        bubble.height = ui(105)
        pygame.draw.rect(
            target, (91, 58, 44), bubble.move(0, ui(3)),
            border_radius=ui(15),
        )
        pygame.draw.rect(target, CREAM, bubble, border_radius=ui(15))
        pygame.draw.rect(target, BROWN, bubble, ui(3), border_radius=ui(15))
        tag = self.guide_font.render("ORDER SERVED!", True, BROWN)
        label = self.popup_font.render("YA ME! TE!", True, BROWN)
        target.blit(tag, (bubble.x + ui(18), bubble.y + ui(13)))
        target.blit(label, (bubble.x + ui(18), bubble.y + ui(45)))

    def _draw_serving_tutorial(self, target):
        """Reaction first, customer exit second, chef celebration last."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 22, 16, 140))
        target.blit(overlay, (0, 0))

        # The cat is behind the counter while waiting and leaving.
        if self.phase in ("serve_intro", "customer_reaction", "customer_exit"):
            if self.phase == "serve_intro":
                self._draw_cat_highlight(target)
            self._draw_cat(target)

        if self.dimmed_counter is not None:
            target.blit(self.dimmed_counter, self._counter_rect())

        # Before serving, the chef gives the click instruction.
        # While the cat says YA ME! TE!, the chef exits to the left.
        # After the cat has left, the chef enters again.
        if self.phase in (
            "serve_intro", "customer_reaction", "served", "serve_exit"
        ):
            self._draw_chef(target)

        if self.dimmed_register is not None:
            target.blit(self.dimmed_register, self._register_rect())
        self._draw_dimmed_clock(target)
        if self.reward_display_timer > 0:
            self._draw_register(target)
            self._draw_reward(target)

        if self.phase == "serve_intro":
            self._draw_patience_bar(target)
            self._draw_cat_order(target, self._cat_bubble_rect())
        elif self.phase == "customer_reaction":
            self._draw_served_message(target)

        # Dialogue always stays above the chef and cash register.
        if self.phase in ("serve_intro", "served") and self.dialogue_started:
            bubble = self._draw_dialogue(target)
            if (
                self.phase == "served"
                and self.characters_shown >= len(self.dialogue)
            ):
                self._draw_okay_button(target, self._okay_rect(bubble))

    def _cat_rect(self, bob=0):
        """Keep the cat and patience bar anchored to the same character."""
        if self.cat is None:
            return None
        return self.cat.get_rect(
            midbottom=(
                round(self.cat_center_x),
                HEIGHT - ui(CAT_BOTTOM_MARGIN) - bob,
            )
        )

    def _draw_cat(self, target):
        """Draw a walking cat behind the foreground counter."""
        if self.cat is None:
            return

        bob = 0
        if self.phase == "cat_enter":
            bob = round(ui(3) * abs(math.sin(self.cat_walk_elapsed * 9)))
        elif self.phase == "customer_exit":
            bob = round(ui(3) * abs(math.sin(self.cat_exit_elapsed * 9)))

        image = self.cat_angry if self.customer_angry else self.cat
        target.blit(image, self._cat_rect(bob))

    def _draw_patience_bar(self, target, highlighted=False):
        """Shrink a green/yellow/red bar above the customer's head."""
        cat_rect = self._cat_rect()
        if cat_rect is None or self.current_order is None:
            return

        bar_width = ui(PATIENCE_BAR_WIDTH)
        bar_height = ui(PATIENCE_BAR_HEIGHT)
        bar = pygame.Rect(
            cat_rect.centerx - bar_width // 2,
            max(ui(48), cat_rect.top - ui(PATIENCE_BAR_HEAD_GAP)),
            bar_width,
            bar_height,
        )
        remaining = self._patience_remaining()
        fraction = max(0.0, min(1.0, remaining / CUSTOMER_WAIT_SECONDS))

        if highlighted:
            glow = bar.inflate(ui(12), ui(12))
            pygame.draw.rect(
                target, YELLOW, glow, ui(4), border_radius=ui(12)
            )

        pygame.draw.rect(
            target, (75, 52, 42), bar.move(0, ui(3)),
            border_radius=ui(8),
        )
        pygame.draw.rect(target, (63, 52, 47), bar, border_radius=ui(8))

        inner = bar.inflate(-ui(6), -ui(6))
        if fraction > 0.5:
            fill_color = (99, 197, 109)
        elif fraction > 0.25:
            fill_color = (245, 195, 78)
        else:
            fill_color = (222, 81, 67)

        filled_width = round(inner.width * fraction)
        if filled_width > 0:
            fill_rect = pygame.Rect(
                inner.left, inner.top, filled_width, inner.height
            )
            pygame.draw.rect(
                target, fill_color, fill_rect, border_radius=ui(5)
            )

        pygame.draw.rect(
            target, PAPER, bar, ui(2), border_radius=ui(8)
        )

        title = self.patience_font.render("PATIENCE", True, PAPER)
        seconds = math.ceil(remaining)
        time_text = f"{seconds // 60:02d}:{seconds % 60:02d}"
        timer = self.patience_font.render(time_text, True, PAPER)
        label_y = bar.top - title.get_height() - ui(5)

        # Small shadow makes the labels readable against the room.
        for text_image, x in (
            (title, bar.left),
            (timer, bar.right - timer.get_width()),
        ):
            shadow = text_image.copy()
            shadow.fill((65, 43, 34), special_flags=pygame.BLEND_RGB_MULT)
            target.blit(shadow, (x + ui(1), label_y + ui(2)))
            target.blit(text_image, (x, label_y))

    def _draw_patience_tutorial(self, target):
        """Teach customer patience while the full bar is highlighted."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 22, 16, 150))
        target.blit(overlay, (0, 0))

        # The customer remains behind the counter, but the chef is
        # drawn afterward so the chef stays in front of the counter.
        self._draw_cat(target)
        if self.dimmed_counter is not None:
            target.blit(self.dimmed_counter, self._counter_rect())
        self._draw_chef(target)
        if self.dimmed_register is not None:
            target.blit(self.dimmed_register, self._register_rect())
        self._draw_dimmed_clock(target)

        self._draw_patience_bar(
            target, highlighted=(self.phase == "patience_intro")
        )
        if self.phase in ("patience_intro", "navigation_intro") and self.dialogue_started:
            bubble = self._draw_dialogue(target)
            if (
                self.phase == "patience_intro"
                and self.characters_shown >= len(self.dialogue)
            ):
                self._draw_okay_button(target, self._okay_rect(bubble))

        # Show normal A/D positions, but spotlight D during the navigation step.
        if self.phase == "navigation_intro":
            self._draw_controls(target, highlight_key="D")

    def _draw_angry_message(self, target):
        """Show that the cat is upset once the patience bar runs out."""
        width = min(ui(455), WIDTH - ui(90))
        rect = pygame.Rect(
            round(self.cat_center_x) - width // 2,
            ui(74), width, ui(78)
        )
        pygame.draw.rect(
            target, (255, 225, 209), rect, border_radius=ui(14)
        )
        pygame.draw.rect(
            target, (193, 70, 57), rect, ui(3), border_radius=ui(14)
        )
        label = self.guide_font.render("ANGRY CUSTOMER!", True, (193, 70, 57))
        complaint = self.label_font.render(
            "MEOW! I've been waiting forever!", True, BROWN
        )
        target.blit(label, (rect.x + ui(15), rect.y + ui(10)))
        target.blit(complaint, (rect.x + ui(15), rect.y + ui(35)))

    def _draw_chef(self, target):
        """Slide the chef in from the left and back out when finished."""
        if self.tutorial_chef is None:
            return

        if self.phase in (
            "chef_exit", "navigation_exit", "serve_exit", "customer_reaction"
        ):
            # Reverse the entrance animation to return to the left edge.
            progress = max(
                0.0, 1.0 - self.chef_exit_timer / CHEF_EXIT_DURATION
            )
        else:
            progress = min(1.0, self.chef_slide_timer / CHEF_SLIDE_DURATION)

        eased = 1 - (1 - progress) ** 3
        start_x = -self.tutorial_chef.get_width()
        end_x = ui(CHEF_CENTER_X)
        x = round(start_x + (end_x - start_x) * eased)
        chef_rect = self.tutorial_chef.get_rect(
            midbottom=(x, HEIGHT + ui(CHEF_BOTTOM_OFFSET))
        )
        target.blit(self.tutorial_chef, chef_rect)

    def _draw_tutorial(self, target):
        """Dim the room and draw the large chef in front of the counter."""
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((35, 22, 16, 165))
        target.blit(overlay, (0, 0))

        # The counter stays dimmed, but does not cover the chef.
        if self.dimmed_counter is not None:
            target.blit(self.dimmed_counter, self._counter_rect())

        # Draw the chef AFTER the counter so the chef is in front.
        self._draw_chef(target)

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

        # Dialogue is drawn LAST, above the highlighted register,
        # bright clock, large chef, and counter.
        if self.phase == "chef" and self.dialogue_started:
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
        popup_y = (
            ui(305)
            if self.phase in (
                "cat_order",
                "patience_intro", "navigation_intro",
                "serve_intro", "served", "serve_exit"
            )
            else self.popup_y
        )
        y = max(ui(30), min(popup_y, HEIGHT - bubble_height - ui(75)))
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
            self.phase == "chef"
            and self.tutorial_index != len(TUTORIAL_LINES) - 1
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
        """Place the order, including its pizza, immediately above the cat."""
        width = min(ui(540), WIDTH - ui(80))
        height = ui(150)
        cat_rect = self._cat_rect()
        bubble_bottom = (
            cat_rect.top - ui(48)
            if cat_rect is not None
            else ui(385)
        )
        return pygame.Rect(
            round(self.cat_center_x) - width // 2,
            max(ui(24), bubble_bottom - height),
            width,
            height,
        )

    def _draw_cat_order(self, target, bubble):
        """Display the cheese pizza requested by the first customer."""
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
        pizza_name = self.popup_font.render("CHEESE PIZZA", True, BROWN)
        target.blit(pizza_name, (bubble.x + ui(18), bubble.y + ui(34)))

        pizza_rect = None
        if self.cheese_pizza is not None:
            pizza_rect = self.cheese_pizza.get_rect(
                midright=(bubble.right - ui(18), bubble.centery)
            )
            target.blit(self.cheese_pizza, pizza_rect)

        text_right = (
            pizza_rect.left - ui(14)
            if pizza_rect is not None
            else bubble.right - ui(18)
        )
        text_width = max(ui(160), text_right - bubble.x - ui(18))
        line_y = bubble.y + ui(77)
        for line in self._wrap_text(CAT_ORDER_TEXT, self.label_font, text_width):
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

    def _draw_controls(self, target, highlight_key=None):
        """Show A/D controls and highlight D when the chef asks for it."""
        y = HEIGHT - ui(47)
        x = WIDTH - ui(300)
        items = [("A", "Oven"), ("D", "Kitchen")]

        for index, (letter, label) in enumerate(items):
            rect = pygame.Rect(x, y, ui(34), ui(28))
            active = highlight_key == letter
            muted = highlight_key is not None and not active

            label_color = (170, 151, 131) if muted else PAPER
            description = self.guide_font.render(label, True, label_color)

            if active:
                # Yellow pulsing outline surrounds the entire "D Kitchen" guide.
                total_width = rect.width + ui(8) + description.get_width()
                guide_rect = pygame.Rect(
                    rect.x - ui(9),
                    rect.y - ui(8),
                    total_width + ui(18),
                    rect.height + ui(16),
                )
                pulse = math.sin(pygame.time.get_ticks() * 0.005)
                border_size = max(2, ui(3) + round((pulse + 1) * ui(1)))
                pygame.draw.rect(
                    target, (95, 62, 45), guide_rect, border_radius=ui(11)
                )
                pygame.draw.rect(
                    target, YELLOW, guide_rect, border_size,
                    border_radius=ui(11),
                )

            pygame.draw.rect(
                target,
                (157, 136, 115) if muted else (255, 237, 188) if active else PAPER,
                rect,
                border_radius=ui(6),
            )
            pygame.draw.rect(
                target, YELLOW if active else BROWN, rect, ui(2),
                border_radius=ui(6),
            )

            key_image = self.guide_font.render(
                letter, True, (90, 74, 62) if muted else BROWN
            )
            target.blit(key_image, key_image.get_rect(center=rect.center))
            target.blit(
                description,
                description.get_rect(midleft=(rect.right + ui(8), rect.centery)),
            )

            x += ui(130)
            if index == 0 and highlight_key is None:
                pygame.draw.line(
                    target,
                    BROWN,
                    (x - ui(12), y),
                    (x - ui(12), y + ui(28)),
                    ui(2),
                )
