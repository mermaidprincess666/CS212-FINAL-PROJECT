"""The small warm light that wanders the entrance before the gate opens."""

import math
import random
from collections import deque

import pygame

from screens.common import clamp, ease
from settings import (
    GATE_LIGHT_APPEAR_TIME,
    GATE_LIGHT_AURA_COLOR,
    GATE_LIGHT_CORE_COLOR,
    GATE_LIGHT_CORE_RADIUS,
    GATE_LIGHT_DART_ARC,
    GATE_LIGHT_DART_TIME,
    GATE_LIGHT_FLOAT_TIME,
    GATE_LIGHT_FLARE_RADIUS,
    GATE_LIGHT_HALO_COLOR,
    GATE_LIGHT_HALO_RADIUS,
    GATE_LIGHT_MID_COLOR,
    GATE_PARTICLE_CAP,
    GATE_PARTICLE_DART_RATE,
    GATE_PARTICLE_FLOAT_RATE,
    GATE_PARTICLE_LIFE,
    GATE_LIGHT_PRELUDE_TIME,
    GATE_LIGHT_WANDER_AMPLITUDE,
    GATE_LIGHT_WANDER_DRIFT,
    GATE_LIGHT_WANDER_OFFSET,
    GATE_LIGHT_WANDER_SECONDARY,
    GATE_TRAIL_SAMPLES,
    HEIGHT,
    WIDTH,
)


# Prelude stages, walked in order: kindle, drift, dive, then the gate's own
# light takes over and this one is spent.
PHASE_APPEAR = 0
PHASE_FLOAT = 1
PHASE_DART = 2
PHASE_SPENT = 3

# Pre-baked fade steps: one sprite per size/alpha pair, so drawing a mote or a
# trail streak never has to set an alpha at runtime.
DUST_ALPHAS = (70, 130, 190, 235, 255)
TRAIL_SIZES = (34, 28, 22, 17, 13, 9)


def make_glow(diameter, color, plateau=0.0):
    """A soft round of light: solid near the middle, feathered to nothing."""
    diameter = max(4, diameter + diameter % 2)
    surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    centre = diameter // 2
    steps = 32
    for index in range(steps, 0, -1):
        ring = max(1, round(centre * index / steps))
        fraction = index / steps
        if fraction <= plateau:
            alpha = 255
        else:
            alpha = int(255 * ((1 - fraction) / (1 - plateau)) ** 2)
        pygame.draw.circle(surf, (*color, alpha), (centre, centre), ring)
    return surf


def make_streak(diameter, outer_color, inner_color):
    """A gold cloud with a cream heart, so the trail shows on pale and dark art."""
    surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
    outer = make_glow(diameter, outer_color)
    inner = make_glow(round(diameter * 0.6), inner_color)
    surf.blit(outer, (0, 0))
    surf.blit(inner, inner.get_rect(center=surf.get_rect().center))
    return surf


class GateLight:
    """A tiny golden light: it appears, drifts peacefully, then dives in.

    The path is analytic, so the light is positioned from the animation
    clock rather than accumulated per frame. Only the dust motes keep
    their own state, which is why ``update`` takes both a delta time and
    the absolute clock of the cutscene.
    """

    def __init__(self, seed=20261103):
        self.seed = seed
        self.flare = make_glow(GATE_LIGHT_FLARE_RADIUS * 2, GATE_LIGHT_AURA_COLOR)
        self.halo = make_glow(GATE_LIGHT_HALO_RADIUS * 2, GATE_LIGHT_MID_COLOR)
        self.core = make_glow(
            GATE_LIGHT_CORE_RADIUS * 2 + 4, GATE_LIGHT_CORE_COLOR, 0.4
        )
        self.trail_sprites = [
            make_streak(size, GATE_LIGHT_HALO_COLOR, GATE_LIGHT_MID_COLOR)
            for size in TRAIL_SIZES
        ]
        self.dust_sprites = [
            [
                self._faded(make_glow(size, color), alpha)
                for alpha in DUST_ALPHAS
            ]
            for size, color in (
                (10, GATE_LIGHT_MID_COLOR),
                (8, GATE_LIGHT_AURA_COLOR),
            )
        ]
        self.trail = deque(maxlen=GATE_TRAIL_SAMPLES)
        self.particles = []
        self.pos = (0.0, 0.0)
        self.brightness = 0.0
        self.phase = PHASE_APPEAR
        self._wave = ()
        self._spawn_left = 0.0
        self.reset()

    @staticmethod
    def _faded(surf, alpha):
        """Return a copy of ``surf`` with ``alpha`` baked in."""
        copy = surf.copy()
        copy.set_alpha(alpha)
        return copy

    def reset(self):
        """Start the prelude again, rebuilding the wandering path and motes.

        The waves come from a seeded generator, so the light follows the same
        route on every replay instead of drifting differently each time.
        """
        rng = random.Random(self.seed)
        span = GATE_LIGHT_FLOAT_TIME
        # (frequency, phase) sine pairs: four shape the path, the fifth is the
        # brightness pulse used while floating.
        self._wave = tuple(
            (math.tau * cycles / span, rng.uniform(0.0, math.tau))
            for cycles in (
                rng.uniform(0.8, 1.4),
                rng.uniform(2.6, 3.6),
                rng.uniform(0.7, 1.2),
                rng.uniform(2.2, 3.2),
                rng.uniform(1.4, 2.0),
            )
        )
        self.trail.clear()
        self.particles.clear()
        self.pos = (0.0, 0.0)
        self.brightness = 0.0
        self.phase = PHASE_APPEAR
        self._spawn_left = 0.0
        self._rng = rng

    def wander(self, gate_pos, float_time):
        """Position on the wandering path, ``float_time`` seconds in."""
        offset_x, offset_y = GATE_LIGHT_WANDER_OFFSET
        centre_x = clamp(
            gate_pos[0] + offset_x, GATE_LIGHT_WANDER_AMPLITUDE[0] + 60, WIDTH - 160
        )
        centre_y = clamp(
            gate_pos[1] + offset_y, GATE_LIGHT_WANDER_AMPLITUDE[1] + 60, HEIGHT - 120
        )
        amplitude_x, amplitude_y = GATE_LIGHT_WANDER_AMPLITUDE
        minor_x, minor_y = GATE_LIGHT_WANDER_SECONDARY
        drift_x, drift_y = GATE_LIGHT_WANDER_DRIFT
        progress = clamp(float_time / GATE_LIGHT_FLOAT_TIME, 0.0, 1.0)
        primary_x, phase_x = self._wave[0]
        secondary_x, phase_x2 = self._wave[1]
        primary_y, phase_y = self._wave[2]
        secondary_y, phase_y2 = self._wave[3]
        return (
            centre_x
            + amplitude_x * math.sin(primary_x * float_time + phase_x)
            + minor_x * math.sin(secondary_x * float_time + phase_x2)
            + drift_x * progress,
            centre_y
            + amplitude_y * math.sin(primary_y * float_time + phase_y)
            + minor_y * math.sin(secondary_y * float_time + phase_y2)
            + drift_y * progress,
        )

    def update(self, delta_time, clock, gate_pos):
        """Move the light along its phases for the given cutscene clock."""
        if clock >= GATE_LIGHT_PRELUDE_TIME:
            # The gate's own light takes over from here; only the motes the
            # dive left behind stay, so the handover has no hard cut.
            self.phase = PHASE_SPENT
            self.pos = gate_pos
            self.brightness = 1.0
            self.trail.clear()
            self._update_particles(delta_time)
            return

        if clock < GATE_LIGHT_APPEAR_TIME:
            # Kindle: fade in while sitting at the start of the wandering path.
            self.phase = PHASE_APPEAR
            self.pos = self.wander(gate_pos, 0.0)
            self.brightness = ease(clock / GATE_LIGHT_APPEAR_TIME)
        elif clock < GATE_LIGHT_APPEAR_TIME + GATE_LIGHT_FLOAT_TIME:
            # Wander: slow sine drift with a breathing brightness.
            float_time = clock - GATE_LIGHT_APPEAR_TIME
            self.phase = PHASE_FLOAT
            self.pos = self.wander(gate_pos, float_time)
            pulse_frequency, pulse_phase = self._wave[4]
            self.brightness = 0.78 + 0.22 * math.sin(
                pulse_frequency * float_time + pulse_phase
            )
        else:
            # Dive: accelerate into the arch, bowing sideways on the way.
            dart_time = clock - GATE_LIGHT_APPEAR_TIME - GATE_LIGHT_FLOAT_TIME
            progress = clamp(dart_time / GATE_LIGHT_DART_TIME, 0.0, 1.0)
            start = self.wander(gate_pos, GATE_LIGHT_FLOAT_TIME)
            travel = ease(progress)
            delta_x = gate_pos[0] - start[0]
            delta_y = gate_pos[1] - start[1]
            length = max(1.0, math.hypot(delta_x, delta_y))
            arc = math.sin(math.pi * progress) * GATE_LIGHT_DART_ARC
            self.phase = PHASE_DART
            self.pos = (
                start[0] + delta_x * travel - delta_y / length * arc,
                start[1] + delta_y * travel + delta_x / length * arc,
            )
            self.brightness = 0.85 + 0.55 * progress
            self.trail.append(self.pos)

        # Motes are spawned on an average rate, so the leftover fraction carries
        # into the next frame instead of being dropped.
        rate = (
            GATE_PARTICLE_DART_RATE
            if self.phase == PHASE_DART
            else GATE_PARTICLE_FLOAT_RATE
        )
        self._spawn_left += rate * delta_time
        while self._spawn_left >= 1.0:
            self._spawn_left -= 1.0
            self._spawn_particle()
        self._update_particles(delta_time)

    def _spawn_particle(self):
        """Release one dust mote where the light currently is."""
        if len(self.particles) >= GATE_PARTICLE_CAP:
            return
        rng = self._rng
        life = GATE_PARTICLE_LIFE * rng.uniform(0.55, 1.0)
        self.particles.append(
            {
                "x": self.pos[0] + rng.uniform(-5.0, 5.0),
                "y": self.pos[1] + rng.uniform(-5.0, 5.0),
                "vx": rng.uniform(-11.0, 11.0),
                "vy": rng.uniform(-17.0, -3.0),
                "life": life,
                "max": life,
                "kind": rng.randrange(len(self.dust_sprites)),
            }
        )

    def _update_particles(self, delta_time):
        """Drift the motes and drop the ones that have faded out."""
        if not self.particles:
            return
        drag = 1.0 - min(1.0, 1.2 * delta_time)
        alive = []
        for particle in self.particles:
            particle["life"] -= delta_time
            if particle["life"] <= 0.0:
                continue
            particle["x"] += particle["vx"] * delta_time
            particle["y"] += particle["vy"] * delta_time
            particle["vx"] *= drag
            particle["vy"] += 7.0 * delta_time
            alive.append(particle)
        self.particles = alive

    def draw(self, target):
        """Draw the trail, the motes and the light itself."""
        self._draw_trail(target)
        self._draw_particles(target)

        if self.phase == PHASE_SPENT:
            return

        self._blit_glow(target, self.flare, self.pos, 130 * self.brightness)
        self._blit_glow(target, self.halo, self.pos, 235 * self.brightness)
        self._blit_glow(
            target, self.core, self.pos, 255 * clamp(self.brightness, 0.35, 1.0)
        )

    def _draw_particles(self, target):
        """Draw the golden dust, fading each mote out over its own lifetime."""
        for particle in self.particles:
            fraction = particle["life"] / particle["max"]
            sprites = self.dust_sprites[particle["kind"]]
            # The fade is pre-baked into the variants, so no alpha is set here.
            sprite = sprites[min(len(sprites) - 1, int(fraction * len(sprites)))]
            half = sprite.get_width() // 2
            target.blit(
                sprite,
                (round(particle["x"] - half), round(particle["y"] - half)),
            )

    @staticmethod
    def _blit_glow(target, sprite, position, alpha):
        """Draw one cached glow at ``position`` with the given alpha."""
        sprite.set_alpha(int(clamp(alpha, 0.0, 255.0)))
        half = sprite.get_width() // 2
        target.blit(sprite, (round(position[0] - half), round(position[1] - half)))

    def _draw_trail(self, target):
        """A short golden-cream streak behind the diving light."""
        count = len(self.trail)
        if count < 2:
            return
        steps = len(self.trail_sprites)
        for index, position in enumerate(self.trail):
            fraction = (index + 1) / count
            sprite = self.trail_sprites[min(steps - 1, int(fraction * steps))]
            self._blit_glow(target, sprite, position, 200 * fraction**1.5)
