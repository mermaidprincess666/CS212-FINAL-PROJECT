
"""SLICE oven scene: click the switch, cook, then serve at the counter."""

import math
import random
import pygame

from screens.introduction import IntroScene
from settings import ASSETS_DIR, WIDTH, HEIGHT, ui


CREAM = (247, 233, 209)
PAPER = (255, 247, 232)
BROWN = (123, 86, 66)
YELLOW = (255, 215, 105)

# Oven layout
OVEN_WIDTH = 900
OVEN_CENTER_X = 0.50
OVEN_CENTER_Y = 0.52

DOOR_SIZE = 0.73
TIMER_SIZE = 0.15
SWITCH_SIZE = 0.095
INDICATOR_SIZE = 0.020

DOOR_POSITION = (0.405, 0.53)
TIMER_POSITION = (0.885, 0.34)
SWITCH_POSITION = (0.875, 0.53)
INDICATOR_POSITION = (0.815, 0.785)

# Oven behavior
COOK_TIME_SECONDS = 5
SWITCH_ROTATION = 32
SWITCH_ROTATION_DURATION = 0.40
INDICATOR_BLINK_INTERVAL = 0.35
SWITCH_CLICK_PADDING = 55

# Center the timer text
TIMER_TEXT_OFFSET_X = 0
TIMER_TEXT_OFFSET_Y = 0

# Chef
CHEF_MAX_WIDTH = 440
CHEF_MAX_HEIGHT = 650
CHEF_CENTER_X = 240
CHEF_BOTTOM_OFFSET = 12

CHEF_SLIDE_DURATION = 0.65
CHEF_DIALOGUE_DELAY = 0.15
BUBBLE_POP_DURATION = 0.18
TYPE_SPEED = 45

SWITCH_TEXT = (
    "Almost there, Chef! Click the highlighted rotary switch "
    "to turn the oven on and bake the pizza!"
)

READY_TEXT = (
    "It's cooked! Ready to serve! Press A to return to the "
    "Counter and serve our customer before their patience runs out!"
)


class OvenScene:
    """Run a cooking cycle and guide the player back to the Counter."""

    _build_voice_sounds = IntroScene._build_voice_sounds
    _stop_narration = IntroScene._stop_narration
    _speak_new_letters = IntroScene._speak_new_letters

    def __init__(self, game):
        self.game = game

        # Background
        self.background = self._load_image(
            "bg_oven_kitchen.png"
        )

        if self.background is not None:
            self.background = pygame.transform.smoothscale(
                self.background,
                (WIDTH, HEIGHT),
            )

        # Main oven
        self.oven = self._resize(
            self._load_image("oven.png", crop=True),
            ui(OVEN_WIDTH),
        )

        oven_width = (
            self.oven.get_width()
            if self.oven is not None
            else ui(OVEN_WIDTH)
        )

        # Original oven door
        self.oven_door = self._resize(
            self._load_image(
                "oven_door.png",
                crop=True,
            ),
            round(oven_width * DOOR_SIZE),
        )

        # Replacement door with pizza inside
        self.oven_with_pizza = self._resize(
            self._load_image(
                "ovenwithpiz.png",
                crop=True,
            ),
            round(oven_width * DOOR_SIZE),
        )

        # Timer display
        self.screen_timer = self._resize(
            self._load_image(
                "screen_timer.png",
                crop=True,
            ),
            round(oven_width * TIMER_SIZE),
        )

        # Rotary switch
        self.rotary_switch = self._resize(
            self._load_image(
                "rotary_switch.png",
                crop=True,
            ),
            round(oven_width * SWITCH_SIZE),
        )

        # Fixed pivot prevents wobbling
        self.switch_rotation_image = (
            self._make_switch_rotation_image()
        )

        # Indicator lights
        self.indicator = self._resize(
            self._load_image(
                "indicator.png",
                crop=True,
            ),
            round(oven_width * INDICATOR_SIZE),
        )

        self.indicator_blink = self._resize(
            self._load_image(
                "indicator_blink.png",
                crop=True,
            ),
            round(oven_width * INDICATOR_SIZE),
        )

        # Fonts
        self.guide_font = self._font(
            ui(16),
            "small",
        )

        self.timer_font = self._font(
            ui(24),
            "small",
        )

        self.status_font = self._font(
            ui(27),
            "dialogue",
        )

        self.popup_font = self._font(
            ui(26),
            "dialogue",
        )

        self.chef = self._load_chef()

        # Oven states: idle -> cooking -> cooked
        self.oven_state = "idle"
        self.time_remaining = 0.0

        self.switch_angle = 0.0
        self.switch_animation_time = 0.0
        self.blink_timer = 0.0
        self.switch_hovered = False

        # Chef animation states
        self.chef_mode = "enter"
        self.chef_exit_destination = None
        self.chef_animation_time = 0.0

        # Dialogue
        self.dialogue = SWITCH_TEXT
        self.characters_shown = 0.0
        self.bubble_timer = 0.0
        self.dialogue_started = False
        self.oven_visited = False

        # Narration system
        self.voice_rng = random.Random()
        self.voice_sounds = {}
        self.voice_channel = None
        self.last_voice_time = -1000
        self.voice_delay = 65
        self.transitioning = False

        mixer_settings = pygame.mixer.get_init()

        if mixer_settings is not None:
            cached = getattr(
                IntroScene,
                "_voice_cache",
                None,
            )

            if (
                getattr(
                    IntroScene,
                    "_voice_cache_settings",
                    None,
                ) == mixer_settings
                and cached is not None
            ):
                self.voice_sounds = cached
            else:
                self._build_voice_sounds()

                IntroScene._voice_cache = self.voice_sounds
                IntroScene._voice_cache_settings = mixer_settings

    def _load_image(self, filename, crop=False):
        """Load oven artwork from ASSETS/KITCHEN."""
        path = ASSETS_DIR / "KITCHEN" / filename

        try:
            image = pygame.image.load(
                str(path)
            ).convert_alpha()

            if crop:
                bounds = image.get_bounding_rect(
                    min_alpha=10
                )

                if bounds.width and bounds.height:
                    image = image.subsurface(
                        bounds
                    ).copy()

            return image

        except (OSError, pygame.error) as error:
            print(
                f"Could not load oven asset {filename}: {error}"
            )
            return None

    @staticmethod
    def _resize(image, width):
        """Scale without stretching the image."""
        if image is None:
            return None

        width = max(1, round(width))

        height = max(
            1,
            round(
                image.get_height()
                * width / image.get_width()
            ),
        )

        return pygame.transform.smoothscale(
            image,
            (width, height),
        )

    def _make_switch_rotation_image(self):
        """Keep the knob centered when rotating."""
        if self.rotary_switch is None:
            return None

        side = (
            max(self.rotary_switch.get_size())
            + ui(8)
        )

        canvas = pygame.Surface(
            (side, side),
            pygame.SRCALPHA,
        )

        canvas.blit(
            self.rotary_switch,
            self.rotary_switch.get_rect(
                center=(side // 2, side // 2)
            ),
        )

        return canvas

    def _font(self, size, fallback):
        """Load the Fredoka font."""
        path = (
            ASSETS_DIR
            / "FONTS"
            / "Fredoka"
            / "static"
            / "Fredoka-SemiBold.ttf"
        )

        try:
            return pygame.font.Font(
                str(path),
                size,
            )

        except (OSError, pygame.error):
            return (
                self.game.fonts.get(fallback)
                or pygame.font.Font(None, size)
            )

    def _load_chef(self):
        """Load the large bottom-left chef."""
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
                f"Oven chef unavailable: {error}"
            )
            return None

    def _oven_rect(self):
        """Return oven position."""
        if self.oven is None:
            return None

        return self.oven.get_rect(
            center=(
                round(WIDTH * OVEN_CENTER_X),
                round(HEIGHT * OVEN_CENTER_Y),
            )
        )

    @staticmethod
    def _component_center(oven_rect, ratio):
        """Calculate a component's position."""
        return (
            oven_rect.left
            + round(oven_rect.width * ratio[0]),

            oven_rect.top
            + round(oven_rect.height * ratio[1]),
        )

    def _component_rect(
        self,
        image,
        oven_rect,
        ratio,
    ):
        """Get component rectangle."""
        if image is None or oven_rect is None:
            return None

        return image.get_rect(
            center=self._component_center(
                oven_rect,
                ratio,
            )
        )

    def _switch_rect(self):
        """Get the rotary switch position."""
        return self._component_rect(
            self.rotary_switch,
            self._oven_rect(),
            SWITCH_POSITION,
        )

    def _switch_hitbox(self):
        """Make the rotary switch easier to click."""
        rect = self._switch_rect()

        if rect is None:
            return None

        return rect.inflate(
            ui(SWITCH_CLICK_PADDING),
            ui(SWITCH_CLICK_PADDING),
        )

    def _logical_positions(self, position):
        """Support fullscreen and windowed mouse coordinates."""
        positions = [position]

        viewport = getattr(
            self.game,
            "_viewport",
            None,
        )

        if (
            viewport is not None
            and viewport.width > 0
            and viewport.height > 0
        ):
            if viewport.collidepoint(position):
                positions.append(
                    (
                        round(
                            (position[0] - viewport.x)
                            * WIDTH / viewport.width
                        ),
                        round(
                            (position[1] - viewport.y)
                            * HEIGHT / viewport.height
                        ),
                    )
                )

        return positions

    def _on_switch(self, position):
        """Check whether mouse touches the switch."""
        rect = self._switch_hitbox()

        if rect is None:
            return False

        return any(
            rect.collidepoint(point)
            for point in self._logical_positions(position)
        )

    def _kitchen_locked(self):
        """Check whether the pizza has left the Kitchen."""
        manager = getattr(
            self.game,
            "scene_manager",
            None,
        )

        kitchen = (
            manager.scenes.get("kitchen")
            if manager is not None
            else None
        )

        return bool(
            getattr(
                kitchen,
                "pizza_sent_to_oven",
                False,
            )
        )

    def _active(self):
        """Only animate the chef while the oven scene is active."""
        manager = getattr(
            self.game,
            "scene_manager",
            None,
        )

        return bool(
            manager is not None
            and manager.current_name == "oven"
            and manager.screen_fade_state == "none"
        )

    def _set_dialogue(self, text):
        """Start a new chef dialogue with a slide-in animation."""
        self._stop_narration()

        self.dialogue = text
        self.characters_shown = 0.0
        self.bubble_timer = 0.0
        self.dialogue_started = False

        self.chef_mode = "enter"
        self.chef_animation_time = 0.0

    def _start_cooking(self):
        """Turn oven on and immediately replace the door image."""
        if self.oven_state != "idle":
            return

        if self.chef_mode not in ("enter", "in"):
            return

        self._stop_narration()

        self.oven_state = "cooking"
        self.time_remaining = float(COOK_TIME_SECONDS)

        # Rotate from original PNG orientation
        self.switch_angle = 0.0
        self.switch_animation_time = 0.0

        self.blink_timer = 0.0

        # Chef leaves while the oven is cooking
        self.chef_mode = "exit"
        self.chef_animation_time = 0.0
        self.chef_exit_destination = None

        print(
            "Oven ON: pizza cooking, ovenwithpiz.png displayed."
        )

    def _finish_cooking(self):
        """Complete baking and bring the chef back."""
        self.oven_state = "cooked"
        self.time_remaining = 0.0
        self.switch_angle = SWITCH_ROTATION

        # Chef slides back in for serving instructions
        self._set_dialogue(READY_TEXT)

        print("COOKED! READY TO SERVE!")

    def handle_event(self, event):
        """Handle switch interaction and guided navigation."""
        if event.type == pygame.MOUSEMOTION:
            self.switch_hovered = self._on_switch(
                event.pos
            )
            return

        if (
            event.type == pygame.MOUSEBUTTONDOWN
            and event.button == 1
        ):
            if (
                self.oven_state == "idle"
                and self._on_switch(event.pos)
            ):
                self._start_cooking()

            return

        if event.type != pygame.KEYDOWN:
            return

        # A -> Counter, only when cooked
        if event.key == pygame.K_a:
            if (
                self.oven_state == "cooked"
                and self.chef_exit_destination is None
            ):
                self._stop_narration()

                self.chef_mode = "exit"
                self.chef_animation_time = 0.0
                self.chef_exit_destination = "welcome"

        # D -> Kitchen is blocked after pizza is prepared
        elif event.key == pygame.K_d:
            if (
                not self._kitchen_locked()
                and self.oven_state == "idle"
            ):
                self.game.scene_manager.go_to(
                    "kitchen"
                )

        # Skip typewriter without skipping tutorial
        elif event.key in (
            pygame.K_SPACE,
            pygame.K_RETURN,
            pygame.K_KP_ENTER,
        ):
            if (
                self.chef_mode == "in"
                and self.characters_shown < len(self.dialogue)
            ):
                self.characters_shown = float(
                    len(self.dialogue)
                )

                self._stop_narration()

    def update(self, delta_time):
        """Update cooking even when player visits another scene."""

        # Cooking timer runs independently of the active scene
        if self.oven_state == "cooking":
            self.switch_animation_time = min(
                SWITCH_ROTATION_DURATION,
                self.switch_animation_time + delta_time,
            )

            progress = (
                self.switch_animation_time
                / SWITCH_ROTATION_DURATION
            )

            eased = (
                progress * progress * (3 - 2 * progress)
            )

            self.switch_angle = (
                SWITCH_ROTATION * eased
            )

            self.blink_timer += delta_time

            self.time_remaining = max(
                0.0,
                self.time_remaining - delta_time,
            )

            if self.time_remaining <= 0:
                self._finish_cooking()

        # SceneManager updates the Oven globally, so do not
        # animate the chef until player enters this scene.
        if not self._active():
            return

        self.oven_visited = True

        # Chef enters or leaves
        if self.chef_mode in ("enter", "exit"):
            self.chef_animation_time = min(
                CHEF_SLIDE_DURATION,
                self.chef_animation_time + delta_time,
            )

            if (
                self.chef_animation_time
                >= CHEF_SLIDE_DURATION
            ):
                if self.chef_mode == "exit":
                    self.chef_mode = "hidden"

                    if (
                        self.chef_exit_destination
                        == "welcome"
                    ):
                        self.chef_exit_destination = None

                        self.game.scene_manager.go_to(
                            "welcome"
                        )

                else:
                    self.chef_mode = "in"

            return

        if self.chef_mode != "in":
            return

        if not self.dialogue_started:
            self.dialogue_started = True

        # Dialogue pop animation
        self.bubble_timer = min(
            BUBBLE_POP_DURATION,
            self.bubble_timer + delta_time,
        )

        # Typewriter
        old_count = int(self.characters_shown)

        self.characters_shown = min(
            float(len(self.dialogue)),
            self.characters_shown + TYPE_SPEED * delta_time,
        )

        # Narration sound
        self._speak_new_letters(
            self.dialogue,
            old_count,
            int(self.characters_shown),
        )

    def _draw_component(
        self,
        target,
        image,
        oven_rect,
        ratio,
    ):
        """Draw a component in its fixed oven position."""
        rect = self._component_rect(
            image,
            oven_rect,
            ratio,
        )

        if rect is not None:
            target.blit(image, rect)

    def _draw_switch(self, target, oven_rect):
        """Highlight and rotate the rotary switch."""
        if self.rotary_switch is None:
            return

        center = self._component_center(
            oven_rect,
            SWITCH_POSITION,
        )

        # Highlight rotary switch before cooking starts
        is_step = self.oven_state == "idle"

        is_hovered = self._on_switch(
            pygame.mouse.get_pos()
        )

        if is_step:
            pulse = (
                math.sin(
                    pygame.time.get_ticks() * 0.005
                ) + 1
            ) / 2

            radius = (
                self.rotary_switch.get_width() // 2
                + ui(11)
            )

            # Dark outer outline
            pygame.draw.circle(
                target,
                (123, 78, 36),
                center,
                radius + ui(2),
                ui(5),
            )

            # Yellow highlighted ring
            pygame.draw.circle(
                target,
                YELLOW,
                center,
                radius,
                ui(7)
                if is_hovered
                else ui(4 + round(2 * pulse)),
            )

        # Original orientation before click
        if (
            abs(self.switch_angle) < 0.01
            or self.switch_rotation_image is None
        ):
            image = self.rotary_switch

        else:
            # Negative rotation is clockwise in Pygame
            image = pygame.transform.rotozoom(
                self.switch_rotation_image,
                -self.switch_angle,
                1.0,
            )

        target.blit(
            image,
            image.get_rect(center=center),
        )

    def _draw_indicator(self, target, oven_rect):
        """Blink green while cooking, stay green when cooked."""
        image = self.indicator

        if self.oven_state == "cooking":
            lit = (
                int(
                    self.blink_timer
                    / INDICATOR_BLINK_INTERVAL
                ) % 2 == 0
            )

            if lit and self.indicator_blink is not None:
                image = self.indicator_blink

        elif self.oven_state == "cooked":
            if self.indicator_blink is not None:
                image = self.indicator_blink

        self._draw_component(
            target,
            image,
            oven_rect,
            INDICATOR_POSITION,
        )

    def _draw_timer(self, target, oven_rect):
        """Center MM:SS inside screen_timer.png."""
        rect = self._component_rect(
            self.screen_timer,
            oven_rect,
            TIMER_POSITION,
        )

        if rect is None:
            return

        seconds = max(
            0,
            math.ceil(self.time_remaining),
        )

        timer_text = (
            f"{seconds // 60:02d}:{seconds % 60:02d}"
        )

        image = self.timer_font.render(
            timer_text,
            True,
            BROWN,
        )

        target.blit(
            image,
            image.get_rect(
                center=(
                    rect.centerx + ui(TIMER_TEXT_OFFSET_X),
                    rect.centery + ui(TIMER_TEXT_OFFSET_Y),
                )
            ),
        )

    def _draw_chef(self, target):
        """Slide chef in or out from the bottom-left."""
        if (
            self.chef is None
            or self.chef_mode == "hidden"
        ):
            return

        progress = (
            self.chef_animation_time
            / CHEF_SLIDE_DURATION
        )

        if self.chef_mode == "exit":
            progress = 1.0 - progress

        elif self.chef_mode == "in":
            progress = 1.0

        progress = max(
            0,
            min(1, progress),
        )

        eased = (
            1 - (1 - progress) ** 3
        )

        start_x = -self.chef.get_width()

        center_x = round(
            start_x
            + (
                ui(CHEF_CENTER_X) - start_x
            ) * eased
        )

        rect = self.chef.get_rect(
            midbottom=(
                center_x,
                HEIGHT + ui(CHEF_BOTTOM_OFFSET),
            )
        )

        target.blit(self.chef, rect)

    @staticmethod
    def _wrap(text, font, width):
        """Wrap text into dialogue lines."""
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

    def _draw_dialogue(self, target):
        """Draw chef dialogue above the oven and switch."""
        if (
            self.chef_mode != "in"
            or not self.dialogue_started
        ):
            return

        width_limit = max(
            ui(250),
            WIDTH - ui(460),
        )

        lines = self._wrap(
            self.dialogue,
            self.popup_font,
            width_limit - ui(42),
        )

        line_height = (
            self.popup_font.get_linesize()
            + ui(3)
        )

        width = min(
            width_limit,
            max(
                self.popup_font.size(line)[0]
                for line in lines
            ) + ui(42),
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
            width_limit - ui(42),
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

        # Bubble pop effect
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
            prompt = (
                "CLICK THE ROTARY SWITCH"
                if self.oven_state == "idle"
                else "PRESS A TO COUNTER"
            )

            hint = self.guide_font.render(
                prompt,
                True,
                PAPER,
            )

            target.blit(
                hint,
                (
                    rect.x + ui(8),
                    rect.bottom + ui(12),
                ),
            )

    def _draw_controls(self, target):
        """Show only A — Counter when the pizza is cooked."""
        if self.oven_state != "cooked":
            return

        x = WIDTH - ui(200)
        y = HEIGHT - ui(47)

        key = pygame.Rect(
            x,
            y,
            ui(34),
            ui(28),
        )

        label = self.guide_font.render(
            "Counter",
            True,
            PAPER,
        )

        outline = pygame.Rect(
            x - ui(9),
            y - ui(7),
            key.width + label.get_width() + ui(34),
            key.height + ui(14),
        )

        pulse = math.sin(
            pygame.time.get_ticks() * 0.005
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
            max(
                ui(3),
                round(ui(4) + pulse),
            ),
            border_radius=ui(11),
        )

        pygame.draw.rect(
            target,
            PAPER,
            key,
            border_radius=ui(6),
        )

        pygame.draw.rect(
            target,
            BROWN,
            key,
            ui(2),
            border_radius=ui(6),
        )

        letter = self.guide_font.render(
            "A",
            True,
            BROWN,
        )

        target.blit(
            letter,
            letter.get_rect(center=key.center),
        )

        target.blit(
            label,
            label.get_rect(
                midleft=(
                    key.right + ui(8),
                    key.centery,
                )
            ),
        )

    def draw(self, target, mouse_pos):
        """Render the oven and guided cooking tutorial."""
        target.fill(CREAM)

        if self.background is not None:
            target.blit(
                self.background,
                (0, 0),
            )

        oven_rect = self._oven_rect()

        if oven_rect is not None:
            # Oven body
            target.blit(
                self.oven,
                oven_rect,
            )

            # Before click: oven_door.png
            # After click: ovenwithpiz.png
            if (
                self.oven_state != "idle"
                and self.oven_with_pizza is not None
            ):
                door = self.oven_with_pizza
            else:
                door = self.oven_door

            self._draw_component(
                target,
                door,
                oven_rect,
                DOOR_POSITION,
            )

            # Timer screen
            self._draw_component(
                target,
                self.screen_timer,
                oven_rect,
                TIMER_POSITION,
            )

            self._draw_timer(
                target,
                oven_rect,
            )

            # Highlighted rotary switch
            self._draw_switch(
                target,
                oven_rect,
            )

            # Indicator
            self._draw_indicator(
                target,
                oven_rect,
            )

            # Cooking completion message at top-right
            if self.oven_state == "cooked":
                banner = self.status_font.render(
                    "COOKED! READY TO SERVE!",
                    True,
                    BROWN,
                )

                panel = pygame.Rect(
                    WIDTH - banner.get_width() - ui(52),
                    ui(23),
                    banner.get_width() + ui(32),
                    banner.get_height() + ui(18),
                )

                pygame.draw.rect(
                    target,
                    CREAM,
                    panel,
                    border_radius=ui(12),
                )

                pygame.draw.rect(
                    target,
                    BROWN,
                    panel,
                    ui(3),
                    border_radius=ui(12),
                )

                target.blit(
                    banner,
                    banner.get_rect(center=panel.center),
                )

        # Draw chef and dialogue above the oven
        self._draw_chef(target)
        self._draw_dialogue(target)

        # Highlight A when cooked
        self._draw_controls(target)
