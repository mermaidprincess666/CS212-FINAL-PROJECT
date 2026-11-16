
"""Interactive oven scene for SLICE."""

import math
import pygame

from settings import ASSETS_DIR, WIDTH, HEIGHT, ui


CREAM = (247, 233, 209)
PAPER = (255, 247, 232)
BROWN = (123, 86, 66)

# Main oven size and position
OVEN_WIDTH = 900
OVEN_CENTER_X = 0.50
OVEN_CENTER_Y = 0.52

# Component sizes relative to oven width
DOOR_SIZE = 0.73
TIMER_SIZE = 0.15
SWITCH_SIZE = 0.095
INDICATOR_SIZE = 0.020

# Component positions relative to oven body
DOOR_POSITION = (0.405, 0.53)
TIMER_POSITION = (0.885, 0.34)
SWITCH_POSITION = (0.875, 0.53)
INDICATOR_POSITION = (0.815, 0.785)

# Oven settings
COOK_TIME_SECONDS = 5
SWITCH_ROTATION = 32  # Original marker turns clockwise toward the right
SWITCH_ROTATION_DURATION = 0.40
INDICATOR_BLINK_INTERVAL = 0.35

# Extra clickable space around the switch
SWITCH_CLICK_PADDING = 55

# Timer position
TIMER_TEXT_OFFSET_X = -8
TIMER_TEXT_OFFSET_Y = 8


class OvenScene:
    """Interactive oven with timer, switch, and indicator."""

    def __init__(self, game):
        self.game = game

        # Load background
        self.background = self._load_image(
            "bg_oven_kitchen.png"
        )

        if self.background is not None:
            self.background = pygame.transform.smoothscale(
                self.background,
                (WIDTH, HEIGHT),
            )

        # Load oven assets
        self.oven = self._load_image(
            "oven.png", crop=True
        )

        self.oven_door = self._load_image(
            "oven_door.png", crop=True
        )

        self.screen_timer = self._load_image(
            "screen_timer.png", crop=True
        )

        self.rotary_switch = self._load_image(
            "rotary_switch.png", crop=True
        )

        self.indicator = self._load_image(
            "indicator.png", crop=True
        )

        self.indicator_blink = self._load_image(
            "indicator_blink.png", crop=True
        )

        # Resize main oven
        self.oven = self._resize(
            self.oven,
            ui(OVEN_WIDTH),
        )

        oven_width = (
            self.oven.get_width()
            if self.oven is not None
            else ui(OVEN_WIDTH)
        )

        # Resize attached components
        self.oven_door = self._resize(
            self.oven_door,
            round(oven_width * DOOR_SIZE),
        )

        self.screen_timer = self._resize(
            self.screen_timer,
            round(oven_width * TIMER_SIZE),
        )

        self.rotary_switch = self._resize(
            self.rotary_switch,
            round(oven_width * SWITCH_SIZE),
        )

        # Center the original knob on a square canvas for stable rotation.
        # The unrotated PNG is still drawn unchanged when the oven is OFF.
        self.switch_rotation_image = self._make_switch_rotation_image()

        self.indicator = self._resize(
            self.indicator,
            round(oven_width * INDICATOR_SIZE),
        )

        self.indicator_blink = self._resize(
            self.indicator_blink,
            round(oven_width * INDICATOR_SIZE),
        )

        # Fonts
        self.guide_font = self._font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(16),
            game.fonts.get("small"),
        )

        self.timer_font = self._font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(24),
            game.fonts.get("small"),
        )

        self.status_font = self._font(
            "Fredoka/static/Fredoka-SemiBold.ttf",
            ui(27),
            game.fonts.get("dialogue"),
        )

        # Oven states: idle, cooking, cooked
        self.oven_state = "idle"

        # Timer
        self.time_remaining = 0.0

        # Switch animation
        self.switch_angle = 0.0
        self.switch_animation_time = 0.0

        # Indicator animation
        self.blink_timer = 0.0

        # Mouse hover
        self.switch_hovered = False

    def _load_image(self, filename, crop=False):
        """Load images from ASSETS/KITCHEN."""
        path = ASSETS_DIR / "KITCHEN" / filename

        try:
            image = pygame.image.load(
                str(path)
            ).convert_alpha()

            if crop:
                bounds = image.get_bounding_rect(
                    min_alpha=10
                )

                if bounds.width > 0 and bounds.height > 0:
                    image = image.subsurface(
                        bounds
                    ).copy()

            return image

        except (OSError, pygame.error) as error:
            print(f"Could not load {filename}: {error}")
            return None

    def _resize(self, image, width):
        """Resize without stretching."""
        if image is None:
            return None

        width = max(1, int(width))

        scale = width / image.get_width()

        height = max(
            1,
            round(image.get_height() * scale),
        )

        return pygame.transform.smoothscale(
            image,
            (width, height),
        )

    def _make_switch_rotation_image(self):
        """Build a centered square pivot so the knob does not wobble."""
        if self.rotary_switch is None:
            return None

        side = max(self.rotary_switch.get_size()) + ui(8)
        canvas = pygame.Surface((side, side), pygame.SRCALPHA)
        canvas.blit(
            self.rotary_switch,
            self.rotary_switch.get_rect(center=(side // 2, side // 2)),
        )
        return canvas

    def _font(self, filename, size, fallback):
        """Load font."""
        try:
            return pygame.font.Font(
                str(ASSETS_DIR / "FONTS" / filename),
                size,
            )

        except (OSError, pygame.error):
            return fallback or pygame.font.Font(
                None, size
            )

    def _oven_rect(self):
        """Return the oven's rectangle."""
        if self.oven is None:
            return None

        return self.oven.get_rect(
            center=(
                round(WIDTH * OVEN_CENTER_X),
                round(HEIGHT * OVEN_CENTER_Y),
            )
        )

    def _component_center(self, oven_rect, position):
        """Find component center relative to the oven."""
        x_ratio, y_ratio = position

        return (
            oven_rect.left
            + round(oven_rect.width * x_ratio),
            oven_rect.top
            + round(oven_rect.height * y_ratio),
        )

    def _component_rect(self, image, oven_rect, position):
        """Return a component's rectangle."""
        if image is None or oven_rect is None:
            return None

        return image.get_rect(
            center=self._component_center(
                oven_rect, position
            )
        )

    def _switch_rect(self):
        """Return the displayed rotary switch rectangle."""
        return self._component_rect(
            self.rotary_switch,
            self._oven_rect(),
            SWITCH_POSITION,
        )

    def _switch_hitbox(self):
        """Make the switch easier to click."""
        rect = self._switch_rect()

        if rect is None:
            return None

        return rect.inflate(
            ui(SWITCH_CLICK_PADDING),
            ui(SWITCH_CLICK_PADDING),
        )

    def _mouse_positions(self, position):
        """
        Return possible mouse coordinates in the
        game's logical resolution.

        Handles normal windows and scaled fullscreen.
        """
        positions = []

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
            x = (
                (position[0] - viewport.x)
                * WIDTH / viewport.width
            )

            y = (
                (position[1] - viewport.y)
                * HEIGHT / viewport.height
            )

            positions.append(
                (round(x), round(y))
            )

        # Fallback if mouse coordinates are already logical
        positions.append(position)

        return positions

    def _is_switch_clicked(self, position):
        """Check if the switch was clicked."""
        hitbox = self._switch_hitbox()

        if hitbox is None:
            return False

        for mouse_pos in self._mouse_positions(position):
            if hitbox.collidepoint(mouse_pos):
                return True

        return False

    def _start_cooking(self):
        """Start with the original knob position, then turn clockwise."""
        if self.oven_state in ("cooking", "resetting"):
            return

        if self.oven_state == "cooked":
            # On a later click, return smoothly to OFF before restarting.
            # This avoids the knob suddenly snapping to its original angle.
            self.oven_state = "resetting"
            self.switch_animation_time = 0.0
            return

        self.oven_state = "cooking"
        self.time_remaining = float(COOK_TIME_SECONDS)
        self.switch_angle = 0.0
        self.switch_animation_time = 0.0
        self.blink_timer = 0.0

        print("Oven switched ON. Cooking started!")

    def _finish_cooking(self):
        """Finish the cooking cycle."""
        self.oven_state = "cooked"
        self.time_remaining = 0.0
        self.switch_angle = SWITCH_ROTATION

        print("Cooking complete!")

    def handle_event(self, event):
        """Handle mouse interaction and navigation."""

        if event.type == pygame.MOUSEMOTION:
            self.switch_hovered = self._is_switch_clicked(
                event.pos
            )

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self._is_switch_clicked(event.pos):
                    self._start_cooking()
                    return

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self.game.scene_manager.go_to(
                    "welcome"
                )

            elif event.key == pygame.K_d:
                self.game.scene_manager.go_to(
                    "kitchen"
                )

    def update(self, delta_time):
        """Turn the knob smoothly and update cooking."""

        if self.oven_state not in ("cooking", "resetting"):
            return

        self.switch_animation_time = min(
            SWITCH_ROTATION_DURATION,
            self.switch_animation_time + delta_time,
        )
        progress = self.switch_animation_time / SWITCH_ROTATION_DURATION
        eased = progress * progress * (3 - 2 * progress)

        if self.oven_state == "resetting":
            self.switch_angle = SWITCH_ROTATION * (1 - eased)
            if progress >= 1.0:
                self.oven_state = "idle"
                self.switch_angle = 0.0
                self._start_cooking()
            return

        # From the original PNG orientation to the clockwise ON position.
        self.switch_angle = SWITCH_ROTATION * eased

        self.blink_timer += delta_time
        self.time_remaining = max(0.0, self.time_remaining - delta_time)
        if self.time_remaining <= 0:
            self._finish_cooking()

    def draw(self, target, mouse_pos):
        """Draw interactive oven."""
        target.fill(CREAM)

        if self.background is not None:
            target.blit(
                self.background,
                (0, 0),
            )

        oven_rect = self._oven_rect()

        if oven_rect is not None:

            # Main oven
            target.blit(
                self.oven,
                oven_rect,
            )

            # Oven door
            self._draw_component(
                target,
                self.oven_door,
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

            # Timer numbers
            self._draw_timer(
                target,
                oven_rect,
            )

            # Rotary switch
            self._draw_rotary_switch(
                target,
                oven_rect,
            )

            # Indicator
            self._draw_indicator(
                target,
                oven_rect,
            )

            # Cooking message
            if self.oven_state == "cooked":
                self._draw_cooked_message(
                    target,
                    oven_rect,
                )

        self._draw_controls(target)

    def _draw_component(
        self,
        target,
        image,
        oven_rect,
        position,
    ):
        """Draw a component relative to the oven."""
        if image is None:
            return

        rect = self._component_rect(
            image,
            oven_rect,
            position,
        )

        target.blit(image, rect)

    def _draw_rotary_switch(self, target, oven_rect):
        """Draw the switch with clockwise rotation."""
        if self.rotary_switch is None:
            return

        center = self._component_center(
            oven_rect,
            SWITCH_POSITION,
        )

        # Hover highlight
        if (
            self.switch_hovered
            and self.oven_state != "cooking"
        ):
            radius = max(
                ui(24),
                self.rotary_switch.get_width() // 2 + ui(5),
            )

            pygame.draw.circle(
                target,
                (245, 221, 164),
                center,
                radius,
                ui(3),
            )

        # Draw the exact original PNG before the player clicks.
        if abs(self.switch_angle) < 0.01:
            image = self.rotary_switch
        else:
            # Pygame's negative angles rotate clockwise.
            image = pygame.transform.rotozoom(
                self.switch_rotation_image,
                -self.switch_angle,
                1.0,
            )

        target.blit(image, image.get_rect(center=center))

    def _draw_indicator(self, target, oven_rect):
        """Show the blinking green indicator."""
        image = self.indicator

        if self.oven_state == "cooking":
            blink_on = (
                int(
                    self.blink_timer
                    / INDICATOR_BLINK_INTERVAL
                ) % 2 == 0
            )

            if blink_on and self.indicator_blink is not None:
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
        """Display countdown centered inside the timer screen."""
        if self.screen_timer is None:
            return

        timer_rect = self._component_rect(
            self.screen_timer,
            oven_rect,
            TIMER_POSITION,
        )

        if timer_rect is None:
            return

        seconds = max(0, math.ceil(self.time_remaining))
        minutes = seconds // 60
        remaining_seconds = seconds % 60

        timer_text = f"{minutes:02d}:{remaining_seconds:02d}"

        timer_image = self.timer_font.render(
            timer_text,
            True,
            BROWN,
        )

        timer_text_rect = timer_image.get_rect(
            center=(
                timer_rect.centerx + ui(TIMER_TEXT_OFFSET_X),
                timer_rect.centery + ui(TIMER_TEXT_OFFSET_Y),
            )
        )

        target.blit(timer_image, timer_text_rect)

    def _draw_cooked_message(self, target, oven_rect):
        """Display cooking completion."""
        message = self.status_font.render(
            "COOKED!",
            True,
            BROWN,
        )

        rect = message.get_rect(
            midbottom=(
                oven_rect.centerx,
                oven_rect.top - ui(18),
            )
        )

        target.blit(message, rect)

    def _draw_controls(self, target):
        """Draw bottom-right navigation guide."""
        y = HEIGHT - ui(47)
        right = WIDTH - ui(30)

        items = [
            ("A", "Counter"),
            ("D", "Kitchen"),
        ]

        x = right - ui(285)

        for index, (key, label) in enumerate(items):
            key_rect = pygame.Rect(
                x,
                y,
                ui(34),
                ui(28),
            )

            pygame.draw.rect(
                target,
                PAPER,
                key_rect,
                border_radius=ui(6),
            )

            pygame.draw.rect(
                target,
                BROWN,
                key_rect,
                ui(2),
                border_radius=ui(6),
            )

            key_image = self.guide_font.render(
                key,
                True,
                BROWN,
            )

            target.blit(
                key_image,
                key_image.get_rect(
                    center=key_rect.center
                ),
            )

            label_image = self.guide_font.render(
                label,
                True,
                PAPER,
            )

            target.blit(
                label_image,
                (
                    key_rect.right + ui(8),
                    key_rect.centery
                    - label_image.get_height() // 2,
                ),
            )

            x += ui(140)

            if index == 0:
                separator_x = x - ui(12)

                pygame.draw.line(
                    target,
                    BROWN,
                    (separator_x, y),
                    (
                        separator_x,
                        y + ui(28),
                    ),
                    ui(2),
                )
