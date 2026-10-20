import math
import os
import sys

import pygame

from Games import settings

# Opens the game window on the right side of your screen.
# Change the numbers if the window lands in a bad spot.
os.environ["SDL_VIDEO_WINDOW_POS"] = "960,60"


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode(
            (settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT)
        )
        pygame.display.set_caption(settings.GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.time_passed = 0.0
        self.show_coming_soon = False

        self.title_font = pygame.font.Font(None, 130)
        self.subtitle_font = pygame.font.Font(None, 34)
        self.prompt_font = pygame.font.Font(None, 40)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                print("Key pressed:", pygame.key.name(event.key))
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_RETURN:
                    self.show_coming_soon = True

    def update(self, dt):
        self.time_passed += dt

    def draw(self):
        self.draw_floor()
        self.draw_title_panel()
        self.draw_pizza()
        self.draw_prompt()
        pygame.display.flip()

    def draw_floor(self):
        tile = 64
        for row in range(settings.SCREEN_HEIGHT // tile + 1):
            for col in range(settings.SCREEN_WIDTH // tile + 1):
                if (row + col) % 2 == 0:
                    color = settings.FLOOR_LIGHT
                else:
                    color = settings.FLOOR_RED
                pygame.draw.rect(self.screen, color, (col * tile, row * tile, tile, tile))

    def draw_title_panel(self):
        center_x = settings.SCREEN_WIDTH // 2

        panel = pygame.Rect(0, 0, 640, 200)
        panel.center = (center_x, 120)
        pygame.draw.rect(self.screen, settings.CREAM, panel, border_radius=30)
        pygame.draw.rect(self.screen, settings.DARK_BROWN, panel, width=6, border_radius=30)

        shadow = self.title_font.render(settings.GAME_TITLE, True, settings.DARK_BROWN)
        text = self.title_font.render(settings.GAME_TITLE, True, settings.TOMATO_RED)
        self.screen.blit(shadow, shadow.get_rect(center=(center_x + 4, 100 + 4)))
        self.screen.blit(text, text.get_rect(center=(center_x, 100)))

        subtitle = self.subtitle_font.render(
            "A cozy restaurant for furry friends", True, settings.DARK_BROWN
        )
        self.screen.blit(subtitle, subtitle.get_rect(center=(center_x, 170)))

    def draw_pizza(self):
        bob = math.sin(self.time_passed * 2) * 8
        cx = settings.SCREEN_WIDTH // 2
        cy = int(380 + bob)
        radius = 110

        pygame.draw.circle(self.screen, settings.DARK_BROWN, (cx + 6, cy + 10), radius)
        pygame.draw.circle(self.screen, settings.CRUST_TAN, (cx, cy), radius)
        pygame.draw.circle(self.screen, settings.SAUCE_RED, (cx, cy), radius - 12)
        pygame.draw.circle(self.screen, settings.CHEESE_YELLOW, (cx, cy), radius - 24)

        pepperoni_spots = [(-45, -35), (40, -45), (0, 5), (-55, 40), (50, 35), (5, -70)]
        for offset_x, offset_y in pepperoni_spots:
            pos = (cx + offset_x, cy + offset_y)
            pygame.draw.circle(self.screen, settings.PEPPERONI_RED, pos, 17)
            pygame.draw.circle(self.screen, settings.PEPPERONI_DARK, pos, 5)

    def draw_prompt(self):
        center_x = settings.SCREEN_WIDTH // 2
        if self.show_coming_soon:
            message = "Buttons and character selection arrive in Stage 2!"
        else:
            message = "Press ENTER to start    |    ESC to quit"

        text = self.prompt_font.render(message, True, settings.DARK_BROWN)
        box = text.get_rect(center=(center_x, 590)).inflate(40, 20)
        pygame.draw.rect(self.screen, settings.CREAM, box, border_radius=16)
        pygame.draw.rect(self.screen, settings.DARK_BROWN, box, width=3, border_radius=16)
        self.screen.blit(text, text.get_rect(center=(center_x, 590)))

    def run(self):
        while self.running:
            dt = self.clock.tick(settings.FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    Game().run()