
import pygame

from settings import (
    WIDTH,
    HEIGHT,
    BACKGROUND,
    TITLE_COLOR,
    BUTTON_COLOR,
    BUTTON_HOVER,
    BUTTON_BORDER,
    CREAM,
)


class SettingsScreen:

    def __init__(self, game):
        self.game = game

        self.music_volume = 100
        self.sound_volume = 100
        self.fullscreen = game.fullscreen

        self.title_font = game.fonts["title"]
        self.label_font = game.fonts["label"]
        self.button_font = game.fonts["button"]
        self.small_font = game.fonts["small"]

        self.music_slider = pygame.Rect(450, 220, 300, 12)
        self.sound_slider = pygame.Rect(450, 320, 300, 12)

        self.fullscreen_button = pygame.Rect(400, 400, 400, 50)
        self.reset_button = pygame.Rect(400, 475, 190, 50)
        self.back_button = pygame.Rect(610, 475, 190, 50)

        self.dragging = None

    def update(self, delta_time):
        pass

    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            if self.music_slider.inflate(20, 30).collidepoint(event.pos):
                self.dragging = "music"
                self.change_slider(event.pos)

            elif self.sound_slider.inflate(20, 30).collidepoint(event.pos):
                self.dragging = "sound"
                self.change_slider(event.pos)

            elif self.fullscreen_button.collidepoint(event.pos):
                self.game.toggle_fullscreen()
                self.fullscreen = self.game.fullscreen

            elif self.reset_button.collidepoint(event.pos):
                self.music_volume = 70
                self.sound_volume = 85
                self.game.menu_music.set_volume(0.70)

                if self.game.fullscreen:
                    self.game.toggle_fullscreen()

                self.fullscreen = False

            elif self.back_button.collidepoint(event.pos):
                self.game.scene_manager.go_to("menu")

        elif event.type == pygame.MOUSEMOTION:

            if self.dragging:
                self.change_slider(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:
                self.dragging = None

    def change_slider(self, mouse_pos):

        if self.dragging == "music":
            slider = self.music_slider
            value = "music"

        elif self.dragging == "sound":
            slider = self.sound_slider
            value = "sound"

        else:
            return

        percentage = (mouse_pos[0] - slider.x) / slider.width
        percentage = max(0, min(1, percentage))
        volume = int(percentage * 100)

        if value == "music":
            self.music_volume = volume
            self.game.menu_music.set_volume(volume / 100)
        else:
            self.sound_volume = volume

    def draw_slider(self, screen, slider, volume):

        pygame.draw.rect(
            screen,
            BUTTON_BORDER,
            slider,
            border_radius=10
        )

        fill_width = int(slider.width * volume / 100)

        fill_rect = pygame.Rect(
            slider.x,
            slider.y,
            fill_width,
            slider.height
        )

        pygame.draw.rect(
            screen,
            BUTTON_COLOR,
            fill_rect,
            border_radius=10
        )

        pygame.draw.circle(
            screen,
            CREAM,
            (slider.x + fill_width, slider.centery),
            12
        )

    def draw_button(self, screen, rect, text, mouse_pos):

        color = (
            BUTTON_HOVER
            if rect.collidepoint(mouse_pos)
            else BUTTON_COLOR
        )

        pygame.draw.rect(
            screen,
            color,
            rect,
            border_radius=12
        )

        pygame.draw.rect(
            screen,
            BUTTON_BORDER,
            rect,
            2,
            border_radius=12
        )

        text_surface = self.button_font.render(text, True, CREAM)
        text_rect = text_surface.get_rect(center=rect.center)

        screen.blit(text_surface, text_rect)

    def draw(self, screen, mouse_pos):

        screen.fill(BACKGROUND)

        title = self.title_font.render(
            "SETTINGS",
            True,
            TITLE_COLOR
        )

        title_rect = title.get_rect(center=(WIDTH // 2, 100))
        screen.blit(title, title_rect)

        music_text = self.label_font.render(
            f"Music Volume: {self.music_volume}%",
            True,
            TITLE_COLOR
        )

        screen.blit(music_text, (450, 180))

        sound_text = self.label_font.render(
            f"Sound Effects: {self.sound_volume}%",
            True,
            TITLE_COLOR
        )

        screen.blit(sound_text, (450, 280))

        self.draw_slider(screen, self.music_slider, self.music_volume)
        self.draw_slider(screen, self.sound_slider, self.sound_volume)

        fullscreen_text = (
            "Fullscreen: ON"
            if self.game.fullscreen
            else "Fullscreen: OFF"
        )

        self.draw_button(
            screen,
            self.fullscreen_button,
            fullscreen_text,
            mouse_pos
        )

        self.draw_button(
            screen,
            self.reset_button,
            "RESET",
            mouse_pos
        )

        self.draw_button(
            screen,
            self.back_button,
            "BACK",
            mouse_pos
        )
