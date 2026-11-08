
import pygame

pygame.font.init()


class SettingsScreen:

    def __init__(self):
        self.music_volume = 70
        self.sound_volume = 85
        self.fullscreen = False

        self.title_font = pygame.font.Font(None, 65)
        self.label_font = pygame.font.Font(None, 32)
        self.button_font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 25)

        self.background = (221, 201, 170)
        self.title_color = (90, 55, 45)
        self.button_color = (115, 145, 115)
        self.button_hover = (90, 120, 90)
        self.button_border = (120, 75, 60)
        self.cream = (252, 243, 225)
        self.track_color = (190, 165, 140)

        self.back_button = pygame.Rect(50, 590, 170, 50)
        self.reset_button = pygame.Rect(850, 490, 200, 50)
        self.fullscreen_button = pygame.Rect(850, 370, 200, 50)

        self.music_slider = pygame.Rect(400, 260, 400, 12)
        self.sound_slider = pygame.Rect(400, 340, 400, 12)

        self.dragging_music = False
        self.dragging_sound = False

    def draw(self, screen):

        screen.fill(self.background)

        title = self.title_font.render(
            "Settings", True, self.title_color
        )
        screen.blit(title, title.get_rect(center=(600, 150)))

        self.draw_slider(
            screen, "Music Volume",
            self.music_slider, self.music_volume
        )

        self.draw_slider(
            screen, "Sound Effects Volume",
            self.sound_slider, self.sound_volume
        )

        fullscreen_text = self.label_font.render(
            "Fullscreen", True, self.title_color
        )
        screen.blit(fullscreen_text, (400, 380))

        fullscreen_label = "ON" if self.fullscreen else "OFF"

        self.draw_button(
            screen, self.fullscreen_button, fullscreen_label
        )

        self.draw_button(
            screen, self.reset_button, "RESET SETTINGS"
        )

        self.draw_button(
            screen, self.back_button, "BACK"
        )

    def draw_slider(self, screen, label, rect, value):

        text = self.label_font.render(
            label, True, self.title_color
        )
        screen.blit(text, (400, rect.y - 40))

        pygame.draw.rect(
            screen, self.track_color, rect, border_radius=10
        )

        knob_x = rect.x + int((value / 100) * rect.width)

        pygame.draw.circle(
            screen, self.button_color,
            (knob_x, rect.centery), 13
        )

        value_text = self.small_font.render(
            str(value) + "%", True, self.title_color
        )

        screen.blit(
            value_text, (rect.right + 25, rect.y - 8)
        )

    def draw_button(self, screen, rect, text):

        mouse_position = pygame.mouse.get_pos()

        color = (
            self.button_hover
            if rect.collidepoint(mouse_position)
            else self.button_color
        )

        pygame.draw.rect(
            screen, color, rect, border_radius=12
        )

        pygame.draw.rect(
            screen, self.button_border,
            rect, 3, border_radius=12
        )

        button_text = self.button_font.render(
            text, True, self.cream
        )

        screen.blit(
            button_text,
            button_text.get_rect(center=rect.center)
        )

    def update_slider(self, mouse_x, slider):

        value = (mouse_x - slider.x) / slider.width * 100
        value = max(0, min(100, value))

        if slider == self.music_slider:
            self.music_volume = int(value)

        elif slider == self.sound_slider:
            self.sound_volume = int(value)

    def handle_event(self, event):

        if event.type == pygame.MOUSEBUTTONDOWN:

            if event.button == 1:

                if self.music_slider.inflate(20, 30).collidepoint(event.pos):
                    self.dragging_music = True
                    self.update_slider(event.pos[0], self.music_slider)

                elif self.sound_slider.inflate(20, 30).collidepoint(event.pos):
                    self.dragging_sound = True
                    self.update_slider(event.pos[0], self.sound_slider)

                elif self.fullscreen_button.collidepoint(event.pos):
                    self.fullscreen = not self.fullscreen

                elif self.reset_button.collidepoint(event.pos):
                    self.music_volume = 70
                    self.sound_volume = 85
                    self.fullscreen = False

                elif self.back_button.collidepoint(event.pos):
                    return "back"

        elif event.type == pygame.MOUSEMOTION:

            if self.dragging_music:
                self.update_slider(event.pos[0], self.music_slider)

            elif self.dragging_sound:
                self.update_slider(event.pos[0], self.sound_slider)

        elif event.type == pygame.MOUSEBUTTONUP:

            if event.button == 1:
                self.dragging_music = False
                self.dragging_sound = False

        return None
