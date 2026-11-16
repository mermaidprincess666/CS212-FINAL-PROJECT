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
    GATE_PARTICLE_BURST_ACCEL,
    GATE_PARTICLE_BURST_RATE,
    GATE_PARTICLE_BURST_SPEED,
    GATE_PARTICLE_CAP,
    GATE_PARTICLE_LIFE,
    GATE_LIGHT_PRELUDE_TIME,
    GATE_LIGHT_START_RADIUS,
    GATE_LIGHT_WANDER_AMPLITUDE,
    GATE_LIGHT_WANDER_DRIFT,
    GATE_LIGHT_WANDER_OFFSET,
    GATE_LIGHT_WANDER_SECONDARY,
    GATE_TRAIL_SAMPLES,
    HEIGHT,
    ui,
    WIDTH,
)


PHASE_APPEAR = 0
PHASE_FLOAT = 1
PHASE_DART = 2
PHASE_SPENT = 3

# Cached alpha variants avoid per-particle alpha updates.
DUST_ALPHAS = (70, 130, 190, 235, 255)
TRAIL_SIZES = tuple(ui(size) for size in (34, 28, 22, 17, 13, 9))


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
    clock rather than accumulated per frame. Only the cover motes keep
    their own state, which is why ``update`` takes both a delta time and
    the absolute clock of the cutscene. They are the one particle system in
    the transition, and they stay asleep until the gate's light expands.
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
            # Larger warm sprites stand out against the cover.
            for size, color in (
                (ui(10), GATE_LIGHT_MID_COLOR),
                (ui(8), GATE_LIGHT_AURA_COLOR),
                (ui(18), GATE_LIGHT_AURA_COLOR),
                (ui(28), GATE_LIGHT_HALO_COLOR),
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
        """Start the prelude again, rebuilding the wandering path.

        Any motes left from the last replay are dropped here, so a restart
        never carries light into the next cutscene. The waves come from a
        seeded generator, so the light follows the same route on every replay
        instead of drifting differently each time.
        """
        rng = random.Random(self.seed)
        span = GATE_LIGHT_FLOAT_TIME
        # Four sine waves shape the path; the fifth controls brightness.
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
            gate_pos[0] + offset_x,
            GATE_LIGHT_WANDER_AMPLITUDE[0] + ui(60),
            WIDTH - ui(160),
        )
        centre_y = clamp(
            gate_pos[1] + offset_y,
            GATE_LIGHT_WANDER_AMPLITUDE[1] + ui(60),
            HEIGHT - ui(120),
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

    def update(self, delta_time, clock, gate_pos, expansion=0.0):
        """Move the light along its phases for the given cutscene clock.

        ``expansion`` is how far the gate's own light has progressed into
        covering the screen, and it is what arms the particles: nothing is
        spawned while the menu fades out, while the doors swing, or while the
        camera pushes in.
        """
        if clock >= GATE_LIGHT_PRELUDE_TIME:
            # The gate glow takes over; particles start during expansion.
            self.phase = PHASE_SPENT
            self.pos = gate_pos
            self.brightness = 1.0
            self.trail.clear()
            self._emit_cover(delta_time, gate_pos, expansion)
            self._update_particles(delta_time)
            return

        if clock < GATE_LIGHT_APPEAR_TIME:
            self.phase = PHASE_APPEAR
            self.pos = self.wander(gate_pos, 0.0)
            self.brightness = ease(clock / GATE_LIGHT_APPEAR_TIME)
        elif clock < GATE_LIGHT_APPEAR_TIME + GATE_LIGHT_FLOAT_TIME:
            float_time = clock - GATE_LIGHT_APPEAR_TIME
            self.phase = PHASE_FLOAT
            self.pos = self.wander(gate_pos, float_time)
            pulse_frequency, pulse_phase = self._wave[4]
            self.brightness = 0.78 + 0.22 * math.sin(
                pulse_frequency * float_time + pulse_phase
            )
        else:
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

    def _emit_cover(self, delta_time, arch, expansion):
        """Feed the final particle transition, and only that transition.

        The pool is emptied whenever the light has not started to expand yet,
        so no mote from an earlier phase or an abandoned replay can carry into
        the burst. The rate thickens with ``expansion``, so the cloud gathers
        as the light swells rather than arriving all at once.
        """
        if expansion <= 0.0:
            self.particles.clear()
            self._spawn_left = 0.0
            return

        # Carry fractional spawns into the next frame.
        self._spawn_left += (
            GATE_PARTICLE_BURST_RATE * (0.25 + 0.75 * expansion) * delta_time
        )
        while self._spawn_left >= 1.0:
            self._spawn_left -= 1.0
            if len(self.particles) >= GATE_PARTICLE_CAP:
                self._spawn_left = 0.0
                break
            self._spawn_cover_particle(arch, expansion)

    def _spawn_cover_particle(self, arch, expansion):
        """Send one mote out of the arch, fanning in a random direction."""
        rng = self._rng
        angle = rng.uniform(0.0, math.tau)
        # Spawn inside the glow to avoid a visible edge.
        offset = rng.uniform(0.0, GATE_LIGHT_START_RADIUS * 0.4)
        # Early particles need enough speed to cross the screen.
        speed = rng.uniform(*GATE_PARTICLE_BURST_SPEED) * (0.7 + 0.3 * expansion)
        life = GATE_PARTICLE_LIFE * rng.uniform(0.55, 1.0)
        self.particles.append(
            {
                "x": arch[0] + math.cos(angle) * offset,
                "y": arch[1] + math.sin(angle) * offset,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "life": life,
                "max": life,
                "kind": rng.randrange(len(self.dust_sprites)),
            }
        )

    def _update_particles(self, delta_time):
        """Fan the motes outward and drop the ones that have faded out."""
        if not self.particles:
            return
        # Exponential velocity growth is frame-rate independent.
        gain = math.exp(GATE_PARTICLE_BURST_ACCEL * delta_time)
        # Integrate displacement over the same acceleration interval.
        travel = (gain - 1.0) / GATE_PARTICLE_BURST_ACCEL
        alive = []
        for particle in self.particles:
            particle["life"] -= delta_time
            if particle["life"] <= 0.0:
                continue
            particle["x"] += particle["vx"] * travel
            particle["y"] += particle["vy"] * travel
            particle["vx"] *= gain
            particle["vy"] *= gain
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
