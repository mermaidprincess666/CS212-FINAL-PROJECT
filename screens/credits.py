
"""Display the scrolling credits screen."""

import pygame

from settings import WIDTH, HEIGHT


class CreditsScreen:

    def __init__(self, game):
        self.game = game

        self.background = (220, 240, 230)
        self.mint = (170, 215, 195)
        self.dark_mint = (105, 155, 130)
        self.chocolate = (95, 65, 50)
        self.cream = (255, 248, 230)

        self.scroll_y = 0
        self.scroll_speed = 25

        self.back_button = pygame.Rect(
            WIDTH // 2 - 100,
            HEIGHT - 85,
            200,
            55
        )

        self.credits = [
            ("SLICE", "title"),
            ("BY PYAGUSTINOS", "button"),
            ("", "small"),

            ("GAME DEVELOPERS", "button"),
            ("Adelantar, Chloe Kaye Isabelle", "label"),
            ("Cortel, Roehla", "label"),
            ("Cawaling, Divine Joy", "label"),
            ("Galve, Hanna Sophia", "label"),
            ("Solis, Charleign Kim", "label"),
            ("", "small"),

            ("LEAD DEVELOPERS", "button"),
            ("Cortel, Roehla", "label"),
            ("Galve, Hanna Sophia", "label"),
            ("Adelantar, Chloe Kaye Isabelle", "label"),
            ("", "small"),

            ("ARTISTS", "button"),
            ("Solis, Charleign Kim", "label"),
            ("Cawaling, Divine Joy", "label"),
            ("", "small"),

            ("SPECIAL THANKS", "button"),
            ("Ms. Trixie Ann Depra", "label"),
            ("For the guidance, patience, and knowledge", "small"),
            ("shared with us throughout this project.", "small"),
            ("", "small"),

            ("A MESSAGE TO OUR MEMBERS", "button"),
            ("To every member of our team, thank you for your", "small"),
            ("time, effort, creativity, and dedication.", "small"),
            ("Creating this game was not always easy, and", "small"),
            ("we faced challenges along the way.", "small"),
            ("But through every line of code, every design,", "small"),
            ("and every improvement, we continued moving", "small"),
            ("forward together.", "small"),
            ("", "small"),
            ("This project is more than just a game.", "small"),
            ("It represents our teamwork, patience,", "small"),
            ("and determination.", "small"),
            ("Thank you for being part of this journey", "small"),
            ("and for making SLICE possible!", "small"),
            ("", "small"),

            ("THANK YOU FOR PLAYING!", "title"),
            ("Made with love by PyAgustinos", "small"),
        ]

        self.text_height = 0

    def handle_event(self, event):

        if event.type == pygame.MOUSEWHEEL:
            self.scroll_y -= event.y * 35

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.back_button.collidepoint(event.pos):
                    self.game.scene_manager.go_to("menu")

        self.scroll_y = max(0, self.scroll_y)

    def update(self, delta_time):

        self.scroll_y += self.scroll_speed * delta_time

        if self.text_height > 0 and self.scroll_y > self.text_height:
            self.scroll_y = 0

    def draw(self, target, mouse_pos):

        target.fill(self.background)

        title_font = self.game.fonts["title"]
        button_font = self.game.fonts["button"]
        small_font = self.game.fonts["small"]
        label_font = self.game.fonts["label"]

        title_font.set_bold(True)
        button_font.set_bold(True)
        small_font.set_bold(False)
        label_font.set_bold(False)

        title = title_font.render(
            "OUR CREDITS",
            True,
            self.chocolate
        )

        target.blit(
            title,
            title.get_rect(center=(WIDTH // 2, 65))
        )

        content_area = pygame.Rect(
            100,
            125,
            WIDTH - 200,
            HEIGHT - 230
        )

        pygame.draw.rect(
            target,
            self.cream,
            content_area,
            border_radius=20
        )

        previous_clip = target.get_clip()
        target.set_clip(content_area)

        y = content_area.top + 25 - self.scroll_y

        for text, font_type in self.credits:

            if font_type == "title":
                font = title_font
                color = self.dark_mint
                gap = 12

            elif font_type == "button":
                font = button_font
                color = self.chocolate
                gap = 10

            elif font_type == "label":
                font = label_font
                color = self.chocolate
                gap = 7

            else:
                font = small_font
                color = self.dark_mint
                gap = 8

            if text:
                rendered = font.render(text, True, color)

                target.blit(
                    rendered,
                    rendered.get_rect(
                        center=(WIDTH // 2, y)
                    )
                )

                y += rendered.get_height() + gap

            else:
                y += 15

        self.text_height = y - content_area.top

        target.set_clip(previous_clip)

        button_color = (
            self.dark_mint
            if self.back_button.collidepoint(mouse_pos)
            else self.mint
        )

        pygame.draw.rect(
            target,
            button_color,
            self.back_button,
            border_radius=15
        )

        pygame.draw.rect(
            target,
            self.chocolate,
            self.back_button,
            2,
            border_radius=15
        )

        back_text = button_font.render(
            "BACK",
            True,
            self.chocolate
        )

        target.blit(
            back_text,
            back_text.get_rect(
                center=self.back_button.center
            )
        )
