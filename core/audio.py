
"""Shared menu music playback state."""

import pygame

from settings import ASSETS_DIR


class MenuMusic:

    def __init__(self):
        if pygame.mixer.get_init() is None:
            pygame.mixer.init()

        music_path = ASSETS_DIR / "MUSIC" / "music bg.mp3"
        pygame.mixer.music.load(str(music_path))

        self.muted = False
        self.active = False
        self.volume = 1.0

    def set_volume(self, volume):
        self.volume = max(0.0, min(1.0, volume))

        if self.active:
            if self.muted:
                pygame.mixer.music.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(self.volume)

    def set_active(self, active):
        active = bool(active)

        if active == self.active:
            return

        self.active = active

        if active and not self.muted:
            self._play()
            pygame.mixer.music.set_volume(self.volume)
        else:
            pygame.mixer.music.stop()

    def toggle(self):
        self.muted = not self.muted

        if self.active:
            if self.muted:
                pygame.mixer.music.set_volume(0.0)
            else:
                pygame.mixer.music.set_volume(self.volume)

        return self.muted

    @staticmethod
    def _play():
        pygame.mixer.music.play(-1)
