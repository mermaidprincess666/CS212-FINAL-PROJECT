"""Main menu and the gate-opening transition animation."""

import math
import random

import pygame

from screens.common import draw_button, draw_text_center, ease
from screens.gate_light import make_glow, GateLight
from settings import (
    BUTTON_GAP,
    BUTTON_HEIGHT,
    BUTTON_START_Y,
    BUTTON_WIDTH,
    BUTTON_X,
    CREAM,
    GATE_ANIMATION_TIME,
    GATE_BLOOM,
    GATE_FADE_START,
    GATE_FLASH_ALPHA,
    GATE_FLASH_TIME,
    GATE_FOCUS,
    GATE_GLOW_SOURCE,
    GATE_HIGHLIGHT_COLOR,
    GATE_LIGHT_PRELUDE_TIME,
    GATE_LIGHT_START_RADIUS,
    GATE_LIGHT_COVER_FRACTION,
    GATE_LIGHT_FINGERS,
    GATE_OPEN_AMOUNT,
    GATE_OPEN_DELAY,
    GATE_OPEN_TIME,
    GATE_TOTAL_TIME,
    GATE_ZOOM_END,
    GATE_ZOOM_TIME,
    GATE_GLOW_COLOR,
    HEIGHT,
    MENU_UI_FADE,
    MENU_UI_SLIDE,
    SRC_H,
    SRC_W,
    TITLE_COLOR,
    TITLE_HEIGHT,
    TITLE_WIDTH,
    TITLE_X,
    TITLE_Y,
    WHITE,
    WIDTH,
)


MENU_BUTTON_NAMES = ("START GAME", "CONTINUE", "SETTINGS", "ABOUT US", "EXIT")

GATE_FLASH_DIAMETER = 900


class MenuScene:
    """Draw and handle the main menu and its gate artwork."""

    def __init__(self, game):
        self.game = game
        self.title_font = game.fonts["title"]
        self.button_font = game.fonts["button"]
        self.label_font = game.fonts["label"]

        self.title_area = pygame.Rect(TITLE_X, TITLE_Y, TITLE_WIDTH, TITLE_HEIGHT)
        self.buttons = []
        for index, name in enumerate(MENU_BUTTON_NAMES):
            button_y = BUTTON_START_Y + index * (BUTTON_HEIGHT + BUTTON_GAP)
            self.buttons.append(
                (name, pygame.Rect(BUTTON_X, button_y, BUTTON_WIDTH, BUTTON_HEIGHT))
            )

        panel_height = (
            len(self.buttons) * (BUTTON_HEIGHT + BUTTON_GAP) - BUTTON_GAP + 44
        )
        self.button_panel = pygame.Rect(
            BUTTON_X - 28, BUTTON_START_Y - 22, BUTTON_WIDTH + 56, panel_height
        )
        self.ui_layer = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        self._compose_key = None
        self._camera_key = None
        self._camera_frame = None
        self._load_gate_artwork()
        self.gate_glow = self._make_gate_glow()
        self.light_fingers = self._make_light_fingers()
        self.gate_flash = make_glow(GATE_FLASH_DIAMETER, GATE_HIGHLIGHT_COLOR, 0.25)
        self.gate_light = GateLight()

    @staticmethod
    def _feather(size, color):
        """A soft round of light: solid in the middle, fading to nothing.

        The same shape as ``gate_light.make_glow`` with its solid core fixed
        at 0.35, which is what these menu masses want.
        """
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        centre = size // 2
        steps = 32
        for index in range(steps, 0, -1):
            ring = max(1, round(centre * index / steps))
            fraction = index / steps
            if fraction <= 0.35:
                alpha = 255
            else:
                alpha = int(255 * ((1 - fraction) / 0.65) ** 2)
            pygame.draw.circle(surf, (*color, alpha), (centre, centre), ring)
        return surf

    def _make_gate_glow(self):
        """Pre-render the shapeless light mass that grows out of the gate.

        It is a union of overlapping soft rounds, so its outline stays
        irregular at every size and never reads as a circle. Built once at
        a modest source size: resampling a smaller texture is several times
        cheaper per frame and the mass is soft enough not to lose anything.
        """
        radius = int(math.hypot(WIDTH, HEIGHT) * 0.8)
        self.gate_glow_radius = radius
        rng = random.Random(20261103)
        glow = self._feather(96, GATE_GLOW_COLOR)
        highlight = self._feather(56, GATE_HIGHLIGHT_COLOR)
        base = pygame.Surface((160, 160), pygame.SRCALPHA)
        for _ in range(12):
            piece = highlight if rng.random() < 0.4 else glow
            size = round(rng.uniform(0.4, 1.0) * piece.get_width())
            if size != piece.get_width():
                piece = pygame.transform.smoothscale(piece, (size, size))
            x = rng.uniform(0.0, 160 - size)
            y = rng.uniform(0.0, 160 - size)
            base.blit(piece, (round(x), round(y)))
        return pygame.transform.smoothscale(base, (GATE_GLOW_SOURCE, GATE_GLOW_SOURCE))

    def _make_light_fingers(self):
        """Small irregular clouds that will stream out of the gate.

        Each finger stores (image, angle, reach, delay): evenly spaced but
        jittered directions, how far it travels (as a fraction of the
        corner distance) and when it starts moving during the expansion.
        """
        rng = random.Random(31415)
        template = self._feather(48, GATE_GLOW_COLOR)
        core = self._feather(30, GATE_HIGHLIGHT_COLOR)
        fingers = []
        for index in range(GATE_LIGHT_FINGERS):
            base = pygame.Surface((96, 96), pygame.SRCALPHA)
            for _ in range(5):
                piece = core if rng.random() < 0.25 else template
                size = round(rng.uniform(0.35, 0.95) * piece.get_width())
                if size != piece.get_width():
                    piece = pygame.transform.smoothscale(piece, (size, size))
                x = rng.uniform(0.0, 96 - size)
                y = rng.uniform(0.0, 96 - size)
                base.blit(piece, (round(x), round(y)))
            diameter = round(self.gate_glow_radius * rng.uniform(0.18, 0.34))
            image = pygame.transform.smoothscale(base, (diameter, diameter))
            angle = index / GATE_LIGHT_FINGERS * math.tau + rng.uniform(-0.45, 0.45)
            fingers.append(
                (image, angle, rng.uniform(0.15, 0.45), rng.uniform(0.0, 0.3))
            )
        return fingers

    def _load_gate_artwork(self):
        """Load the four gate images and prepare the still menu background."""
        self.gate_bg = self.game.assets.load_image("BG.png", (SRC_W, SRC_H))
        self.gate_frame = self.game.assets.load_image("gate_fence.png", (SRC_W, SRC_H))
        left_full = self.game.assets.load_image("left_gate.png", (SRC_W, SRC_H))
        right_full = self.game.assets.load_image("right_gate.png", (SRC_W, SRC_H))

        self.left_rect = left_full.get_bounding_rect()
        self.right_rect = right_full.get_bounding_rect()
        # Trim each door to its opaque pixels, so swinging it open squashes the
        # door itself and not the transparent padding around it.
        self.left_gate = left_full.subsurface(self.left_rect).copy()
        self.right_gate = right_full.subsurface(self.right_rect).copy()
        self.gate_canvas = pygame.Surface((SRC_W, SRC_H)).convert()
        self.compose_scene(0)
        self.menu_background = pygame.transform.smoothscale(
            self.gate_canvas, (WIDTH, HEIGHT)
        )

    def handle_event(self, event):
        """Handle clicks on the main menu."""
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        for name, rect in self.buttons:
            if not rect.collidepoint(event.pos):
                continue

            if name == "START GAME":
                self.game.scene_manager.set_scene("gate")
            elif name == "EXIT":
                self.game.running = False
            else:
                destinations = {
                    "CONTINUE": "continue",
                    "SETTINGS": "settings",
                    "ABOUT US": "about",
                }
                self.game.scene_manager.go_to(destinations[name])
            return

    def update(self, delta_time):
        """The menu background is still, so it has no per-frame updates."""

    def draw(self, target, mouse_pos):
        """Draw the still gate background and menu controls."""
        target.blit(self.menu_background, (0, 0))
        self.draw_menu_ui(target, mouse_pos)

    def draw_menu_ui(self, target, mouse_pos, alpha=1.0, x_offset=0):
        """Draw the title and buttons on a transparent layer.

        They are composed on one scratch surface so the fade and the slide
        apply to the whole menu as a unit during the gate animation.
        """
        if alpha <= 0:
            return

        self.ui_layer.fill((0, 0, 0, 0))
        # CREAM at 170 alpha, so the gate art still reads through the panel.
        pygame.draw.rect(
            self.ui_layer, (252, 243, 225, 170), self.button_panel, border_radius=22
        )
        pygame.draw.rect(self.ui_layer, CREAM, self.title_area, border_radius=20)
        pygame.draw.rect(
            self.ui_layer, TITLE_COLOR, self.title_area, 4, border_radius=20
        )
        draw_text_center(
            self.ui_layer,
            "SLICE",
            self.title_font,
            TITLE_COLOR,
            (self.title_area.centerx, self.title_area.centery - 15),
        )
        draw_text_center(
            self.ui_layer,
            "by PyAgustinos",
            self.label_font,
            TITLE_COLOR,
            (self.title_area.centerx, self.title_area.centery + 30),
        )

        for name, rect in self.buttons:
            draw_button(self.ui_layer, rect, name, mouse_pos, self.button_font)

        self.ui_layer.set_alpha(int(255 * alpha))
        target.blit(self.ui_layer, (round(x_offset), 0))

    def compose_scene(self, open_amount):
        """Build the gate artwork, with the doors swung open by ``open_amount``.

        The result is cached, so the doors are only rescaled on the frames
        where their swing actually changes. Compositing invalidates the camera
        cache too, since the surface it crops from has just changed.
        """
        key = round(open_amount, 3)
        if key == self._compose_key:
            return
        self._compose_key = key

        swing = ease(open_amount)
        self.gate_canvas.blit(self.gate_bg, (0, 0))

        squash = 1 - swing * GATE_OPEN_AMOUNT
        left_width = max(1, round(self.left_rect.width * squash))
        right_width = max(1, round(self.right_rect.width * squash))
        if left_width == self.left_rect.width:
            left_image = self.left_gate
            right_image = self.right_gate
        else:
            left_image = pygame.transform.smoothscale(
                self.left_gate, (left_width, self.left_rect.height)
            )
            right_image = pygame.transform.smoothscale(
                self.right_gate, (right_width, self.right_rect.height)
            )

        self.gate_canvas.blit(left_image, (self.left_rect.x, self.left_rect.y))
        self.gate_canvas.blit(
            right_image, (self.right_rect.right - right_width, self.right_rect.y)
        )
        self.gate_canvas.blit(self.gate_frame, (0, 0))
        self._camera_key = None

    def draw_camera(self, target, zoom_progress):
        """Render the gate canvas through the same smooth zooming camera.

        Returns where the arch (``GATE_FOCUS``) lands on the screen, so the
        glow can sit on the gate while the camera drifts toward the center.
        """
        zoom = GATE_ZOOM_END**zoom_progress
        view_width = SRC_W / zoom
        view_height = SRC_H / zoom

        focus_x = GATE_FOCUS[0] / SRC_W
        focus_y = GATE_FOCUS[1] / SRC_H
        screen_focus_x = focus_x + (0.5 - focus_x) * zoom_progress
        screen_focus_y = focus_y + (0.5 - focus_y) * zoom_progress
        view_x = GATE_FOCUS[0] - screen_focus_x * view_width
        view_y = GATE_FOCUS[1] - screen_focus_y * view_height
        view_x = max(0.0, min(SRC_W - view_width, view_x))
        view_y = max(0.0, min(SRC_H - view_height, view_y))

        crop_x = int(math.floor(view_x))
        crop_y = int(math.floor(view_y))
        crop_width = min(SRC_W - crop_x, int(math.ceil(view_x + view_width)) - crop_x)
        crop_height = min(SRC_H - crop_y, int(math.ceil(view_y + view_height)) - crop_y)
        scale = WIDTH / view_width
        crop_width_px = max(1, round(crop_width * scale))
        crop_height_px = max(1, round(crop_height * scale))
        key = (crop_x, crop_y, crop_width, crop_height, crop_width_px, crop_height_px)
        if key != self._camera_key:
            # The camera only resamples when its crop or size changes, which
            # keeps the long still prelude as cheap as a single blit.
            self._camera_key = key
            crop = self.gate_canvas.subsurface(
                pygame.Rect(crop_x, crop_y, crop_width, crop_height)
            )
            self._camera_frame = pygame.transform.smoothscale(
                crop, (crop_width_px, crop_height_px)
            )
        target.blit(
            self._camera_frame,
            (round((crop_x - view_x) * scale), round((crop_y - view_y) * scale)),
        )
        return ((GATE_FOCUS[0] - view_x) * scale, (GATE_FOCUS[1] - view_y) * scale)

    def _cover_radius(self, x, y):
        """Distance from the arch to the farthest corner of the screen."""
        return max(
            math.hypot(x - corner_x, y - corner_y)
            for corner_x, corner_y in (
                (0, 0),
                (WIDTH, 0),
                (0, HEIGHT),
                (WIDTH, HEIGHT),
            )
        )

    def draw_gate(self, target, elapsed, delta_time):
        """Draw one frame of the menu-to-story cutscene.

        Phases, all read off ``elapsed`` since the START GAME click:

        Prelude (the first GATE_LIGHT_PRELUDE_TIME seconds): a small warm
        light kindles near the university entrance, wanders peacefully over
        the fence, then accelerates into the center of the gate opening. The
        scene stays closed and still while this happens.
        Ignition: the light that entered the arch brightens and flashes warm
        white, while the doors begin to swing and the camera starts its zoom.
        Expansion: the light swells outward from the arch until it reaches
        every corner, blending into the ivory overlay underneath.

        The handover is not done here. Once the haze fully covers the last
        frame, GateScene switches to the story and the scene manager fades the
        overlay out over WHITE_IN_TIME to reveal it.
        """
        gate_elapsed = max(0.0, elapsed - GATE_LIGHT_PRELUDE_TIME)

        open_amount = (gate_elapsed - GATE_OPEN_DELAY) / GATE_OPEN_TIME
        self.compose_scene(open_amount)
        arch = self.draw_camera(target, ease(gate_elapsed / GATE_ZOOM_TIME))

        ui_progress = ease(elapsed / MENU_UI_FADE)
        self.draw_menu_ui(
            target,
            (-1, -1),
            (1 - ui_progress) ** 1.5,
            MENU_UI_SLIDE * ui_progress,
        )

        cover = self._cover_radius(*arch)
        if gate_elapsed < GATE_FADE_START:
            # Ignition: a small irregular light brightens at the center of the
            # gate while the scene around it stays visible.
            ignition = ease(gate_elapsed / GATE_FADE_START)
            radius = GATE_LIGHT_START_RADIUS * (0.7 + 0.3 * ignition)
            glow_alpha = int(GATE_BLOOM * ignition)
            light = 0.0
            overlay = 0.0
        else:
            # Expansion: the light mass grows from the arch, streams of soft
            # light race outward in several directions, and the whole thing
            # dissolves into a warm ivory haze that keeps the gate readable
            # early and fully covers the last frame.
            light = ease(
                (gate_elapsed - GATE_FADE_START)
                / (GATE_TOTAL_TIME - GATE_FADE_START)
            )
            # The mass itself stops short of the corners; the ivory haze
            # finishes the cover. That keeps the biggest per-frame resample
            # far below full-screen size.
            reach = cover * GATE_LIGHT_COVER_FRACTION
            radius = GATE_LIGHT_START_RADIUS + (reach - GATE_LIGHT_START_RADIUS) * light
            glow_alpha = int(GATE_BLOOM + (255 - GATE_BLOOM) * min(1.0, light * 1.8))
            overlay = light * light

        # Once the haze is at 90% it leaves only a tenth of the light beneath
        # it visible, so the last frames skip the resample.
        if glow_alpha > 0 and overlay < 0.9:
            # Resampled from one cached source surface per frame, like the
            # door and camera already do; the size change is the expansion.
            diameter = max(2, round(radius * 2))
            mass = pygame.transform.smoothscale(self.gate_glow, (diameter, diameter))
            mass.set_alpha(glow_alpha)
            target.blit(
                mass,
                (round(arch[0] - radius), round(arch[1] - radius)),
            )

            # The irregular fingers keep the frontier from ever looking like
            # an expanding circle. They only move; their images are fixed.
            for image, angle, reach, delay in self.light_fingers:
                stream = ease((light - delay) / (1.0 - delay))
                if stream <= 0.0:
                    continue
                distance = cover * reach * stream
                half = image.get_width() / 2
                x = arch[0] + math.cos(angle) * distance - half
                y = arch[1] + math.sin(angle) * distance - half
                image.set_alpha(int(glow_alpha * (0.5 + 0.5 * stream)))
                target.blit(image, (round(x), round(y)))

        # Coverage: the overlay reaches full cover exactly at
        # GATE_TOTAL_TIME, which is when the scene manager hands over.
        if overlay > 0:
            self.game.warm_surface.set_alpha(int(255 * overlay))
            target.blit(self.game.warm_surface, (0, 0))

        # The wandering light sits on top of the still entrance, and dives
        # into the exact point the camera is framing the arch at.
        self.gate_light.update(delta_time, elapsed, arch)
        self.gate_light.draw(target)

        # The arrival: one brief warm-white flash as the light enters, which
        # the spreading mass above immediately takes over.
        arrival = GATE_LIGHT_PRELUDE_TIME
        if arrival <= elapsed < arrival + GATE_FLASH_TIME:
            spike = 1.0 - ease((elapsed - arrival) / GATE_FLASH_TIME)
            half = GATE_FLASH_DIAMETER // 2
            self.gate_flash.set_alpha(int(GATE_FLASH_ALPHA * spike))
            target.blit(self.gate_flash, (round(arch[0] - half), round(arch[1] - half)))
            self.game.warm_surface.set_alpha(int(GATE_FLASH_ALPHA * 0.45 * spike))
            target.blit(self.game.warm_surface, (0, 0))


class GateScene:
    """Advance and draw the short animation between menu and story."""

    def __init__(self, game, menu_scene):
        self.game = game
        self.menu_scene = menu_scene
        self.covered = False
        self.restart()

    def restart(self):
        """Play the animation from the start, armed to hand over once."""
        self.elapsed = 0.0
        self.covered = False
        self.menu_scene.gate_light.reset()

    def handle_event(self, event):
        """A click or Enter/Space skips ahead, fading over to the story."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.game.scene_manager.go_to("intro")
        elif event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self.game.scene_manager.go_to("intro")

    def update(self, delta_time):
        """Advance the cutscene clock, so its timing holds at any frame rate."""
        if self.game.scene_manager.screen_fade_state != "none" or self.covered:
            return

        self.elapsed += delta_time
        if self.elapsed >= GATE_ANIMATION_TIME:
            # The screen is fully covered at this instant; hand over exactly
            # once and let the overlay fade out over the story.
            self.covered = True
            self.game.scene_manager.show_scene("intro", white_fade=True)

    def draw(self, target, mouse_pos):
        """Draw the current frame of the gate animation."""
        self.menu_scene.draw_gate(target, self.elapsed, self.game.delta_time)