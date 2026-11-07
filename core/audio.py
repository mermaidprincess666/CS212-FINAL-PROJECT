"""Shared menu music playback state."""

import pygame

from settings import ASSETS_DIR


class MenuMusic:
    """Loop menu music while the player is in a menu-related scene."""

    def __init__(self):
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        music_path = ASSETS_DIR / "MUSIC" / "music bg.mp3"
        pygame.mixer.music.load(str(music_path))
        self.muted = False
        self.active = False

    def set_active(self, active):
        """Start or stop playback only when entering or leaving its scene group."""
        active = bool(active)
        if active == self.active:
            return

        self.active = active
        if active and not self.muted:
            self._play()
        else:
            pygame.mixer.music.stop()
        if active:
            pygame.mixer.music.set_volume(0.0 if self.muted else 1.0)

    def toggle(self):
        """Mute or resume playback immediately, preserving the preference."""
        self.muted = not self.muted
        if self.active:
            pygame.mixer.music.set_volume(0.0 if self.muted else 1.0)
        return self.muted

    @staticmethod
    def _play():
        pygame.mixer.music.play(-1)