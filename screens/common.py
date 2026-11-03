"""Small drawing helpers shared by the game's screens."""

import pygame

from settings import BUTTON_BORDER, BUTTON_COLOR, BUTTON_HOVER, WHITE


def ease(progress):
    """Smoothstep: ease a 0-1 value so it starts and ends slowly."""
    progress = max(0.0, min(1.0, progress))
    return progress**3 * (progress * (progress * 6 - 15) + 10)


def clamp(value, low, high):
    """Keep ``value`` inside the inclusive range ``low`` to ``high``."""
    return low if value < low else (high if value > high else value)


def draw_text_center(target, text, font, color, center, alpha=255):
    """Draw text centered on a surface, optionally making it transparent."""
    image = font.render(text, True, color)
    image.set_alpha(alpha)
    target.blit(image, image.get_rect(center=center))


def draw_button(target, rect, text, mouse_pos, font):
    """Draw a menu button, darkening while the pointer sits on it."""
    color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR
    pygame.draw.rect(target, color, rect, border_radius=12)
    pygame.draw.rect(target, BUTTON_BORDER, rect, 3, border_radius=12)
    draw_text_center(target, text, font, WHITE, rect.center)