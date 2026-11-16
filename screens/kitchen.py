
"""SLICE kitchen: prepare dough, tomato sauce, and cheese before using oven."""

import math
import random
import pygame

from screens.introduction import IntroScene
from settings import ASSETS_DIR, WIDTH, HEIGHT, ui

CREAM = (247, 233, 209)
PAPER = (255, 247, 232)
BROWN = (123, 86, 66)
YELLOW = (255, 215, 105)

HIT_ALPHA = 18

CHEF_SLIDE_DURATION = 0.65
CHEF_DIALOGUE_DELAY = 0.15
BUBBLE_POP_DURATION = 0.18
TYPE_SPEED = 45

CHEF_MAX_WIDTH = 440
CHEF_MAX_HEIGHT = 650
CHEF_CENTER_X = 240
CHEF_BOTTOM_OFFSET = 12

STEP_TEXT = {
    "dough": (
        "Step one, Chef! Click a dough ball to place it "
        "on the wooden board!"
    ),
    "tomato": (
        "Good! Now click the TOMATO SAUCE in the "
        "lower ingredient tray!"
    ),
    "cheese": (
        "Perfect! Click the CHEESE in the top tray "
        "to add the topping!"
    ),
    "ready": (
        "Well done, Chef! Our pizza is ready for the oven. "
        "Press A to go to the Oven!"
    ),
}


class KitchenScene:
    """Keep all ingredients clickable on their visible artwork."""

    _build_voice_sounds = IntroScene._build_voice_sounds
    _stop_narration = IntroScene._stop_narration
    _speak_new_letters = IntroScene._speak_new_letters

    def __init__(self, game):
        self.game = game

        # Fixed 1920x1080 artwork
        self.background = self._load_canvas("kitchen.png")
        self.ingredients_container = self._load_canvas(
            "ingredients_container.png"
        )
        self.wooden_board = self._load_canvas(
            "wooden_board.png"
        )
        self.dough_balls = self._load_canvas(
            "dough_balls.png"
        )

        # Hover images
        self.hover_images = {
            name: self._load_canvas(f"{filename}_hovered.png")
            for name, filename in (
                ("dough", "dough_balls"),
                ("tomato", "tomato"),
                ("cheese", "cheese"),
                ("ham", "ham"),
                ("pepperoni", "pepperoni"),
            )
        }

        # Use identical hit areas for hovering and clicking
        self.hit_masks = {}
        self.hit_bounds = {}

        for name, image in self.hover_images.items():
            mask, bounds = self._make_hit_mask(image)
            self.hit_masks[name] = mask
            self.hit_bounds[name] = bounds

        # Combine normal and hovered dough artwork
        original_dough_mask, original_dough_bounds = (
            self._make_hit_mask(self.dough_balls)
        )

        if original_dough_mask is not None:
            if self.hit_masks["dough"] is not None:
                original_dough_mask.draw(
                    self.hit_masks["dough"],
                    (0, 0)
                )

            self.hit_masks["dough"] = original_dough_mask
            self.hit_bounds["dough"] = original_dough_bounds

        # Support ingredient trays with outline-only sprites
        self.container_mask = (
            pygame.mask.from_surface(
                self.ingredients_container,
                HIT_ALPHA
            )
            if self.ingredients_container is not None
            else None
        )

        # Cache yellow outlines
        self.glows = {
            name: self._make_glow(
                self.dough_balls if name == "dough" else image
            )
            for name, image in self.hover_images.items()
        }

        # Wooden board location
        board = self._visible_bounds(self.wooden_board)

        self.board_center = (
            board.center
            if board
            else (
                round(WIDTH * 0.75),
                round(HEIGHT * 0.69)
            )
        )

        # Pizza artwork, in layer order
        self.placed_dough = self._make_pizza_image(
            "DOUGH.png", 0.80, 1.20
        )
        self.tomato_layer = self._make_pizza_image(
            "TOMATO CHEESE DOUGH.png", 0.80, 1.20
        )
        self.cheese_layer = self._make_pizza_image(
            "CHEESE TOPPING.png", 0.77, 1.16
        )

        self.pizza_images = (
            self.placed_dough,
            self.tomato_layer,
            self.cheese_layer,
        )

        self.pizza_rects = [
            image.get_rect(center=self.board_center)
            if image is not None
            else None
            for image in self.pizza_images
        ]

        # Pizza progress
        self.dough_placed = False
        self.tomato_placed = False
        self.cheese_placed = False

        # Once True, this order cannot return to the Kitchen
        self.pizza_sent_to_oven = False

        # States: dough -> tomato -> cheese -> ready -> exit -> finished
        self.tutorial_state = "dough"
        self.hovered_item = None

        # Chef
        self.chef = self._load_chef()

        self.guide_font = self._font(ui(16), "small")
        self.popup_font = self._font(ui(26), "dialogue")

        self.dialogue = STEP_TEXT["dough"]
        self.characters_shown = 0.0
        self.dialogue_started = False
        self.bubble_timer = 0.0

        self.chef_slide_time = 0.0
        self.chef_exit_time = 0.0

        # Narration
        self.voice_rng = random.Random()
        self.voice_sounds = {}
        self.voice_channel = None
        self.last_voice_time = -1000
        self.voice_delay = 65
        self.transitioning = False

        mixer_settings = pygame.mixer.get_init()

        if mixer_settings is not None:
            cached = getattr(
                IntroScene, "_voice_cache", None
            )

            if (
                getattr(
                    IntroScene,
                    "_voice_cache_settings",
                    None
                ) == mixer_settings
                and cached is not None
            ):
                self.voice_sounds = cached
            else:
                self._build_voice_sounds()
                IntroScene._voice_cache = self.voice_sounds
                IntroScene._voice_cache_settings = mixer_settings

    def _load_image(self, filename):
        """Load an asset from the Kitchen folder."""
        path = ASSETS_DIR / "KITCHEN" / filename

        try:
            return pygame.image.load(
                str(path)
            ).convert_alpha()

        except (OSError, pygame.error) as error:
            print(
                f"Kitchen image missing: {filename}: {error}"
            )
            return None

    def _load_canvas(self, filename):
        """Preserve fixed full-canvas positions."""
        image = self._load_image(filename)

        if (
            image is not None
            and image.get_size() != (WIDTH, HEIGHT)
        ):
            image = pygame.transform.smoothscale(
                image,
                (WIDTH, HEIGHT)
            )

        return image

    @staticmethod
    def _visible_bounds(image):
        """Return visible artwork bounds."""
        if image is None:
            return None

        rect = image.get_bounding_rect(
            min_alpha=HIT_ALPHA
        )

        return rect if rect.width and rect.height else None

    def _make_hit_mask(self, image):
        """Include filled sprites and enclosed outlines."""
        bounds = self._visible_bounds(image)

        if bounds is None:
            return None, None

        pixels = pygame.mask.from_surface(
            image.subsurface(bounds),
            HIT_ALPHA
        )

        padded = pygame.mask.Mask(
            (bounds.width + 4, bounds.height + 4)
        )

        padded.draw(pixels, (2, 2))

        # Find transparent space outside the ingredient
        outside = padded.copy()
        outside.invert()
        outside = outside.connected_component((0, 0))
        outside.invert()

        # Store in full-canvas coordinates
        full = pygame.mask.Mask((WIDTH, HEIGHT))

        full.draw(
            outside,
            (bounds.left - 2, bounds.top - 2)
        )

        return full, bounds

    @staticmethod
    def _contains(mask, pos):
        """Check a point against a hit mask."""
        if mask is None or pos is None:
            return False

        x, y = pos
        width, height = mask.get_size()

        return (
            0 <= x < width
            and 0 <= y < height
            and bool(mask.get_at((x, y)))
        )

    def _item_at(self, name, pos):
        """Detect an item whether hovered or not."""
        if self._contains(
            self.hit_masks.get(name),
            pos
        ):
            return True

        if name == "dough" or pos is None:
            return False

        bounds = self.hit_bounds.get(name)

        if bounds is None or not bounds.collidepoint(pos):
            return False

        # Fallback for incomplete hover outlines
        inset_x = max(
            1, round(bounds.width * 0.05)
        )
        inset_y = max(
            1, round(bounds.height * 0.05)
        )

        inner = bounds.inflate(
            -2 * inset_x,
            -2 * inset_y
        )

        return (
            inner.collidepoint(pos)
            and self._contains(self.container_mask, pos)
        )

    def _mouse_point(self, position=None):
        """Convert fullscreen mouse coordinates."""
        if position is None:
            position = pygame.mouse.get_pos()

        viewport = getattr(
            self.game, "_viewport", None
        )

        if (
            viewport is not None
            and viewport.width > 0
            and viewport.height > 0
        ):
            if viewport.collidepoint(position):
                return (
                    int(
                        (position[0] - viewport.x)
                        * WIDTH / viewport.width
                    ),
                    int(
                        (position[1] - viewport.y)
                        * HEIGHT / viewport.height
                    ),
                )

            if (
                0 <= position[0] < WIDTH
                and 0 <= position[1] < HEIGHT
            ):
                return (
                    int(position[0]),
                    int(position[1])
                )

            return None

        return (
            int(position[0]),
            int(position[1])
        )

    def _clicked_item(self, name, event_pos):
        """Use the same clickable area as hovering."""
        positions = (
            self._mouse_point(event_pos),
            self._mouse_point(pygame.mouse.get_pos()),
        )

        return any(
            self._item_at(name, position)
            for position in positions
        )

    def _update_hover(self):
        """Detect the hovered ingredient."""
        point = self._mouse_point()

        self.hovered_item = next(
            (
                name
                for name in (
                    "dough",
                    "cheese",
                    "ham",
                    "pepperoni",
                    "tomato",
                )
                if self._item_at(name, point)
            ),
            None,
        )

    def _font(self, size, fallback):
        """Load Fredoka font."""
        path = (
            ASSETS_DIR
            / "FONTS"
            / "Fredoka"
            / "static"
            / "Fredoka-SemiBold.ttf"
        )

        try:
            return pygame.font.Font(str(path), size)

        except (OSError, pygame.error):
            return (
                self.game.fonts.get(fallback)
                or pygame.font.Font(None, size)
            )

    def _load_chef(self):
        """Load the large tutorial chef."""
        path = (
            ASSETS_DIR
            / "WELCOME_TUT"
            / "tuts-chef.png"
        )

        try:
            image = pygame.image.load(
                str(path)
            ).convert_alpha()

            bounds = image.get_bounding_rect(
                min_alpha=10
            )

            if bounds.width and bounds.height:
                image = image.subsurface(bounds).copy()

            scale = min(
                ui(CHEF_MAX_WIDTH) / image.get_width(),
                ui(CHEF_MAX_HEIGHT) / image.get_height(),
            )

            return pygame.transform.smoothscale(
                image,
                (
                    max(
                        1,
                        round(image.get_width() * scale)
                    ),
                    max(
                        1,
                        round(image.get_height() * scale)
                    ),
                ),
            )

        except (OSError, pygame.error) as error:
            print(
                f"Kitchen chef unavailable: {error}"
            )
            return None

    def _make_pizza_image(
        self,
        filename,
        width_ratio,
        height_ratio,
    ):
        """Prepare an ingredient image for the board."""
        image = self._load_image(filename)
        bounds = self._visible_bounds(image)

        if bounds is None:
            # Visible fallback if an asset is missing
            image = pygame.Surface(
                (300, 220),
                pygame.SRCALPHA
            )

            if filename == "DOUGH.png":
                color = (248, 227, 176)
            elif filename.startswith("TOMATO"):
                color = (186, 72, 42)
            else:
                color = (247, 213, 108)

            pygame.draw.ellipse(
                image,
                color,
                image.get_rect()
            )

        else:
            image = image.subsurface(bounds).copy()

        board = self._visible_bounds(
            self.wooden_board
        )

        max_w = (
            board.width if board else ui(400)
        ) * width_ratio

        max_h = (
            board.height if board else ui(300)
        ) * height_ratio

        scale = min(
            max_w / image.get_width(),
            max_h / image.get_height()
        )

        return pygame.transform.smoothscale(
            image,
            (
                max(
                    1,
                    round(image.get_width() * scale)
                ),
                max(
                    1,
                    round(image.get_height() * scale)
                ),
            ),
        )

    def _make_glow(self, image):
        """Create a yellow outline around visible artwork."""
        bounds = self._visible_bounds(image)

        if bounds is None:
            return None, (0, 0)

        mask = pygame.mask.from_surface(
            image.subsurface(bounds),
            HIT_ALPHA
        )

        silhouette = mask.to_surface(
            setcolor=(*YELLOW, 255),
            unsetcolor=(0, 0, 0, 0),
        )

        thickness = max(3, ui(8))

        glow = pygame.Surface(
            (
                bounds.width + thickness * 2,
                bounds.height + thickness * 2,
            ),
            pygame.SRCALPHA,
        )

        for dx, dy in (
            (-thickness, 0),
            (thickness, 0),
            (0, -thickness),
            (0, thickness),
            (-thickness, -thickness),
            (-thickness, thickness),
            (thickness, -thickness),
            (thickness, thickness),
        ):
            glow.blit(
                silhouette,
                (
                    thickness + dx,
                    thickness + dy,
                ),
            )

        return glow, (
            bounds.x - thickness,
            bounds.y - thickness,
        )

    def _set_step(self, state):
        """Advance without sliding the chef out."""
        self._stop_narration()

        self.tutorial_state = state
        self.dialogue = STEP_TEXT[state]
        self.characters_shown = 0.0
        self.bubble_timer = 0.0
        self.dialogue_started = True

    def handle_event(self, event):
        """Handle ingredient clicks and kitchen navigation."""

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            state = self.tutorial_state

            if (
                state == "dough"
                and self._clicked_item("dough", event.pos)
            ):
                self.dough_placed = True
                self._set_step("tomato")

            elif (
                state == "tomato"
                and self._clicked_item("tomato", event.pos)
            ):
                self.tomato_placed = True
                self._set_step("cheese")

            elif (
                state == "cheese"
                and self._clicked_item("cheese", event.pos)
            ):
                self.cheese_placed = True
                self._set_step("ready")

            return

        if event.type != pygame.KEYDOWN:
            return

        # Once pizza is ready, ONLY A can advance.
        if self.tutorial_state == "ready":
            if event.key == pygame.K_a:
                self.pizza_sent_to_oven = True

                self._stop_narration()
                self.chef_exit_time = 0.0
                self.tutorial_state = "exit"

            elif event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self.characters_shown = float(
                    len(self.dialogue)
                )
                self._stop_narration()

            # D is deliberately disabled here.
            return

        if self.tutorial_state in (
            "dough",
            "tomato",
            "cheese",
        ):
            if event.key in (
                pygame.K_SPACE,
                pygame.K_RETURN,
                pygame.K_KP_ENTER,
            ):
                self.characters_shown = float(
                    len(self.dialogue)
                )
                self._stop_narration()

            return

        # Do not allow the player to restart this completed order.
        if self.tutorial_state == "finished":
            return

    def update(self, delta_time):
        """Animate the tutorial and handle the Kitchen lock."""

        if self.tutorial_state == "finished":
            # Prevent entering the completed kitchen again,
            # even if another scene tries to navigate here.
            manager = getattr(
                self.game, "scene_manager", None
            )

            if (
                self.pizza_sent_to_oven
                and manager is not None
                and manager.current_name == "kitchen"
            ):
                oven = manager.scenes.get("oven")

                destination = (
                    "welcome"
                    if getattr(oven, "oven_state", None) == "cooked"
                    else "oven"
                )

                manager.go_to(destination)

            return

        if self.tutorial_state == "exit":
            self.chef_exit_time += delta_time

            if self.chef_exit_time >= CHEF_SLIDE_DURATION:
                self.tutorial_state = "finished"
                self.game.scene_manager.go_to("oven")

            return

        self.chef_slide_time = min(
            CHEF_SLIDE_DURATION + CHEF_DIALOGUE_DELAY,
            self.chef_slide_time + delta_time,
        )

        if not self.dialogue_started:
            if self.chef_slide_time < (
                CHEF_SLIDE_DURATION + CHEF_DIALOGUE_DELAY
            ):
                return

            self.dialogue_started = True

        self.bubble_timer = min(
            BUBBLE_POP_DURATION,
            self.bubble_timer + delta_time,
        )

        old_count = int(self.characters_shown)

        self.characters_shown = min(
            float(len(self.dialogue)),
            self.characters_shown + TYPE_SPEED * delta_time,
        )

        self._speak_new_letters(
            self.dialogue,
            old_count,
            int(self.characters_shown),
        )

    @staticmethod
    def _draw_asset(target, image):
        """Draw full-canvas artwork."""
        if image is not None:
            target.blit(image, (0, 0))

    def _draw_chef(self, target):
        """Slide chef in and out from bottom-left."""
        if self.chef is None:
            return

        if self.tutorial_state == "exit":
            progress = max(
                0.0,
                1 - self.chef_exit_time / CHEF_SLIDE_DURATION
            )
        else:
            progress = min(
                1.0,
                self.chef_slide_time / CHEF_SLIDE_DURATION
            )

        progress = 1 - (1 - progress) ** 3

        x = round(
            -self.chef.get_width()
            + (
                ui(CHEF_CENTER_X)
                + self.chef.get_width()
            ) * progress
        )

        target.blit(
            self.chef,
            self.chef.get_rect(
                midbottom=(
                    x,
                    HEIGHT + ui(CHEF_BOTTOM_OFFSET),
                )
            ),
        )

    def _draw_glow(self, target, name):
        """Draw highlight behind chef, stronger on hover."""
        glow, pos = self.glows.get(
            name,
            (None, (0, 0))
        )

        if glow is not None:
            hovered = self.hovered_item == name

            pulse = (
                math.sin(
                    pygame.time.get_ticks() * 0.005
                ) + 1
            ) / 2

            alpha = (
                245 if hovered
                else round(165 + 40 * pulse)
            )

            glow.set_alpha(alpha)
            target.blit(glow, pos)

        if (
            self.hovered_item == name
            and self.hover_images.get(name) is not None
        ):
            image = self.hover_images[name].copy()
            image.set_alpha(180)

            target.blit(image, (0, 0))

    @staticmethod
    def _wrap(text, font, width):
        """Wrap dialogue into lines."""
        lines = []
        line = ""

        for word in text.split():
            trial = f"{line} {word}".strip()

            if font.size(trial)[0] <= width:
                line = trial
            else:
                if line:
                    lines.append(line)
                line = word

        if line:
            lines.append(line)

        return lines or [""]

    def _draw_dialogue(self, target):
        """Draw chef dialogue above highlights."""
        if (
            not self.dialogue_started
            or self.tutorial_state == "exit"
        ):
            return

        max_width = max(
            ui(250),
            WIDTH - ui(460)
        )

        lines = self._wrap(
            self.dialogue,
            self.popup_font,
            max_width - ui(42),
        )

        line_height = (
            self.popup_font.get_linesize()
            + ui(3)
        )

        width = max(
            ui(230),
            min(
                max_width,
                max(
                    self.popup_font.size(line)[0]
                    for line in lines
                ) + ui(42),
            ),
        )

        height = (
            len(lines) * line_height
            + ui(42)
        )

        bubble = pygame.Surface(
            (width, height),
            pygame.SRCALPHA,
        )

        pygame.draw.rect(
            bubble,
            CREAM,
            bubble.get_rect(),
            border_radius=ui(16),
        )

        pygame.draw.rect(
            bubble,
            BROWN,
            bubble.get_rect(),
            ui(3),
            border_radius=ui(16),
        )

        visible = self.dialogue[
            :int(self.characters_shown)
        ]

        visible_lines = self._wrap(
            visible,
            self.popup_font,
            max_width - ui(42),
        )

        for index, line in enumerate(visible_lines):
            bubble.blit(
                self.popup_font.render(
                    line,
                    True,
                    BROWN,
                ),
                (
                    ui(21),
                    ui(20) + index * line_height,
                ),
            )

        progress = (
            self.bubble_timer / BUBBLE_POP_DURATION
        )

        scale = (
            0.75
            + 0.25 * (1 - (1 - progress) ** 3)
        )

        small = pygame.transform.smoothscale(
            bubble,
            (
                max(1, round(width * scale)),
                max(1, round(height * scale)),
            ),
        )

        x = min(
            ui(380),
            max(
                ui(16),
                WIDTH - width - ui(20),
            ),
        )

        rect = small.get_rect(
            center=(
                x + width // 2,
                ui(120) + height // 2,
            )
        )

        target.blit(small, rect)

        if self.characters_shown >= len(self.dialogue):
            prompts = {
                "dough": "CLICK THE DOUGH",
                "tomato": "CLICK TOMATO SAUCE",
                "cheese": "CLICK CHEESE",
                "ready": "PRESS A TO GO TO OVEN",
            }

            text = self.guide_font.render(
                prompts.get(self.tutorial_state, ""),
                True,
                PAPER,
            )

            target.blit(
                text,
                (
                    rect.x + ui(8),
                    rect.bottom + ui(12),
                ),
            )

    def _draw_controls(self, target, highlight=False):
        """Highlight A. Hide D when the pizza is ready."""
        x = WIDTH - ui(270)
        y = HEIGHT - ui(47)

        items = (
            (("A", "Oven"),)
            if highlight
            else (
                ("A", "Oven"),
                ("D", "Cashier"),
            )
        )

        for key, label in items:
            active = highlight and key == "A"

            rect = pygame.Rect(
                x,
                y,
                ui(34),
                ui(28),
            )

            label_image = self.guide_font.render(
                label,
                True,
                PAPER,
            )

            if active:
                outline = pygame.Rect(
                    x - ui(8),
                    y - ui(7),
                    rect.width
                    + label_image.get_width()
                    + ui(32),
                    rect.height + ui(14),
                )

                pygame.draw.rect(
                    target,
                    (95, 62, 45),
                    outline,
                    border_radius=ui(11),
                )

                pygame.draw.rect(
                    target,
                    YELLOW,
                    outline,
                    ui(4),
                    border_radius=ui(11),
                )

            pygame.draw.rect(
                target,
                PAPER,
                rect,
                border_radius=ui(6),
            )

            pygame.draw.rect(
                target,
                YELLOW if active else BROWN,
                rect,
                ui(2),
                border_radius=ui(6),
            )

            letter = self.guide_font.render(
                key,
                True,
                BROWN,
            )

            target.blit(
                letter,
                letter.get_rect(center=rect.center),
            )

            target.blit(
                label_image,
                label_image.get_rect(
                    midleft=(
                        rect.right + ui(8),
                        rect.centery,
                    )
                ),
            )

            x += ui(130)

    def draw(self, target, mouse_pos):
        """Draw ingredients, pizza layers and tutorial."""
        self._update_hover()
        target.fill(CREAM)

        self._draw_asset(target, self.background)
        self._draw_asset(
            target, self.ingredients_container
        )
        self._draw_asset(target, self.wooden_board)

        # Pizza layers
        progress = (
            self.dough_placed,
            self.tomato_placed,
            self.cheese_placed,
        )

        for placed, image, rect in zip(
            progress,
            self.pizza_images,
            self.pizza_rects,
        ):
            if placed and image is not None:
                target.blit(image, rect)

        self._draw_asset(target, self.dough_balls)

        if self.tutorial_state != "finished":
            # Dim background
            overlay = pygame.Surface(
                (WIDTH, HEIGHT),
                pygame.SRCALPHA,
            )

            overlay.fill((35, 22, 16, 120))
            target.blit(overlay, (0, 0))

            # Highlight behind chef
            selected = (
                self.tutorial_state
                if self.tutorial_state in (
                    "dough",
                    "tomato",
                    "cheese",
                )
                else None
            )

            if selected:
                self._draw_glow(target, selected)

            # Chef above ingredient highlights
            self._draw_chef(target)

            # Dialogue above chef
            self._draw_dialogue(target)

            # Only A is displayed once ready
            if self.tutorial_state in ("ready", "exit"):
                self._draw_controls(
                    target,
                    highlight=True,
                )

        else:
            # Completed Kitchen stays locked for this order.
            pass
