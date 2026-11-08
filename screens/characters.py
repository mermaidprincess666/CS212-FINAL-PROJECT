"""Character selection screen and its portrait interactions."""

import math

import pygame

from screens.character_data import CHARACTERS
from screens.common import draw_text_center
from settings import CREAM, HEIGHT, TITLE_COLOR, WIDTH


TAN = (194, 151, 116)
TERRACOTTA = (157, 83, 61)
DARK_BROWN = (63, 43, 35)
PANEL_CREAM = (252, 243, 225, 228)
PORTRAIT_SIZE = (82, 58)
CHARACTER_OFFSET = (-57, 98)
CHARACTER_CANVAS_SIZE = (round(WIDTH * 0.8), round(HEIGHT * 0.8))


class CharacterScene:
	"""Let players preview, select, and confirm one of the five characters."""

	def __init__(self, game):
		self.game = game
		self.title_font = game.fonts["title"]
		self.name_font = game.fonts["title"]
		self.body_font = game.fonts["button"]
		self.label_font = game.fonts["small"]
		self.selected_index = 0
		self.elapsed = 0.0
		self.transition_time = 0.0
		self.transition_from = None
		self.confirmed = False

		self.background = self._load_background()
		self.counter = self._load_counter()
		self.artwork = [self._load_character_art(character) for character in CHARACTERS]
		self.portrait_rects = [
			pygame.Rect(220 + index * 152, 500, 136, 94)
			for index in range(len(CHARACTERS))
		]
		self.back_button = pygame.Rect(38, HEIGHT - 62, 150, 44)
		self.confirm_button = pygame.Rect(WIDTH - 208, HEIGHT - 62, 170, 44)
		self._portrait_surfaces = [
			self._fit_image(self._crop_sprite(self.artwork[index][0]), PORTRAIT_SIZE)
			for index in range(len(CHARACTERS))
		]
		self._large_surfaces = [
			(
				self._scale_canvas(base),
				self._scale_canvas(talking),
				self._scale_canvas(hands),
			)
			for base, talking, hands in self.artwork
		]

	def _load_background(self):
		try:
			return self.game.assets.load_image(
				"game bg.png", (WIDTH, HEIGHT), subdirectory="MAIN"
			)
		except (FileNotFoundError, pygame.error):
			return None

	def _load_counter(self):
		try:
			return self.game.assets.load_image(
				"counter.png", (WIDTH, HEIGHT), subdirectory="MAIN"
			)
		except (FileNotFoundError, pygame.error):
			return None

	def _load_character_art(self, character):
		folder = f"MAIN/ANIMAL/{character['folder']}"
		base = self._load_full_sprite(character["portrait"], folder)
		talking = self._load_full_sprite(character["talking"], folder) or base
		hands = self._load_full_sprite(character["hands"], folder)
		if base is None:
			return None, None, None
		return base, talking, hands

	def _load_full_sprite(self, filename, folder):
		try:
			return self.game.assets.load_image(filename, subdirectory=folder)
		except (FileNotFoundError, pygame.error):
			return None

	@staticmethod
	def _crop_sprite(image):
		if image is None:
			return None
		bounds = image.get_bounding_rect(min_alpha=8)
		if bounds.width and bounds.height:
			return image.subsurface(bounds).copy()
		return image

	@staticmethod
	def _scale_canvas(image):
		if image is None:
			return None
		return pygame.transform.smoothscale(image, CHARACTER_CANVAS_SIZE)

	@staticmethod
	def _fit_image(image, available_size):
		if image is None:
			return None
		width, height = image.get_size()
		scale = min(available_size[0] / width, available_size[1] / height)
		return pygame.transform.smoothscale(
			image, (max(1, round(width * scale)), max(1, round(height * scale)))
		)

	def _fit_image_pair(self, base, talking, available_size):
		base_image = self._fit_image(base, available_size)
		if base_image is None:
			return None, None
		talking_image = self._fit_image(talking, available_size)
		return base_image, talking_image or base_image

	def handle_event(self, event):
		if event.type == pygame.KEYDOWN:
			if event.key == pygame.K_LEFT:
				self._select(self.selected_index - 1)
			elif event.key == pygame.K_RIGHT:
				self._select(self.selected_index + 1)
			elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
				self._confirm()
			elif event.key == pygame.K_ESCAPE:
				self._back()
			return

		if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
			for index, rect in enumerate(self.portrait_rects):
				if rect.collidepoint(event.pos):
					self._select(index)
					return
			if self.confirm_button.collidepoint(event.pos):
				self._confirm()
			elif self.back_button.collidepoint(event.pos):
				self._back()

	def _select(self, index):
		index %= len(CHARACTERS)
		if index == self.selected_index:
			return
		self.transition_from = self._current_character_surface()
		self.transition_time = 0.22
		self.selected_index = index
		self.confirmed = False

	def _confirm(self):
		self.game.selected_character = dict(CHARACTERS[self.selected_index])
		self.confirmed = True

	def _back(self):
		self.game.scene_manager.go_to("intro")

	def _current_character_surface(self):
		base, _, _ = self._large_surfaces[self.selected_index]
		return base

	def update(self, delta_time):
		self.elapsed += delta_time
		self.transition_time = max(0.0, self.transition_time - delta_time)
		if self.transition_time == 0:
			self.transition_from = None

	def draw(self, target, mouse_pos):
		if self.background is None:
			target.fill((219, 183, 153))
		else:
			target.blit(self.background, (0, 0))
		self._draw_backdrop_wash(target)
		self._draw_selected_character(target)
		if self.counter is not None:
			target.blit(self.counter, (0, 0))
		self._draw_selected_hands(target)
		self._draw_heading(target)
		self._draw_character_copy(target)
		self._draw_portraits(target, mouse_pos)
		self._draw_button(target, self.back_button, "BACK", mouse_pos)
		confirm_text = "CONFIRMED" if self.confirmed else "CONFIRM"
		self._draw_button(target, self.confirm_button, confirm_text, mouse_pos, primary=True)
		if self.confirmed:
			name = CHARACTERS[self.selected_index]["name"]
			draw_text_center(
				target,
				f"{name} is ready for service!",
				self.label_font,
				DARK_BROWN,
				(WIDTH // 2, 465),
			)

	def _draw_backdrop_wash(self, target):
		wash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
		wash.fill((252, 243, 225, 52))
		target.blit(wash, (0, 0))

	def _draw_heading(self, target):
		pygame.draw.rect(target, PANEL_CREAM, (285, 22, 630, 67), border_radius=13)
		pygame.draw.rect(target, DARK_BROWN, (285, 22, 630, 67), 2, border_radius=13)
		draw_text_center(
			target,
			"CHOOSE YOUR CHARACTER",
			self.title_font,
			TITLE_COLOR,
			(WIDTH // 2, 56),
		)

	def _draw_selected_character(self, target):
		base, talking, _ = self._large_surfaces[self.selected_index]
		bob = round(math.sin(self.elapsed * 2.2) * 2)
		if self.transition_from is not None:
			progress = 1 - self.transition_time / 0.22
			old = self.transition_from.copy()
			old.set_alpha(round(255 * (1 - progress)))
			target.blit(old, (CHARACTER_OFFSET[0], CHARACTER_OFFSET[1] + bob))
		if base is None:
			self._draw_placeholder_character(target, (430, 296 + bob))
			return

		active = self.elapsed % 4.2
		mouth_alpha = 0
		if 3.15 <= active < 3.75:
			mouth_alpha = round(170 * min((active - 3.15) / 0.18, (3.75 - active) / 0.18, 1))
		image = base.copy()
		if mouth_alpha > 0 and talking is not None:
			talking_image = talking.copy()
			talking_image.set_alpha(mouth_alpha)
			image.blit(talking_image, (0, 0))
		image.set_alpha(round(255 * min(1.0, (0.22 - self.transition_time) / 0.22)))
		target.blit(image, (CHARACTER_OFFSET[0], CHARACTER_OFFSET[1] + bob))

	def _draw_selected_hands(self, target):
		_, _, hands = self._large_surfaces[self.selected_index]
		if hands is not None:
			hands.set_alpha(round(255 * min(1.0, (0.22 - self.transition_time) / 0.22)))
			target.blit(hands, CHARACTER_OFFSET)

	def _draw_placeholder_character(self, target, center):
		pygame.draw.ellipse(target, TAN, (center[0] - 112, center[1] - 150, 224, 290))
		pygame.draw.circle(target, CREAM, (center[0] - 42, center[1] - 52), 12)
		pygame.draw.circle(target, CREAM, (center[0] + 42, center[1] - 52), 12)
		draw_text_center(target, "?", self.title_font, DARK_BROWN, center)

	def _draw_character_copy(self, target):
		character = CHARACTERS[self.selected_index]
		panel = pygame.Rect(665, 194, 420, 190)
		pygame.draw.rect(target, PANEL_CREAM, panel, border_radius=16)
		pygame.draw.rect(target, DARK_BROWN, panel, 2, border_radius=16)
		draw_text_center(
			target,
			character["name"],
			self.name_font,
			TERRACOTTA,
			(panel.centerx, panel.y + 57),
		)
		draw_text_center(
			target,
			character["species"],
			self.label_font,
			DARK_BROWN,
			(panel.centerx, panel.y + 105),
		)
		self._draw_wrapped_description(target, character["description"], panel)

	def _draw_wrapped_description(self, target, text, panel):
		words = text.split()
		lines = []
		line = ""
		for word in words:
			candidate = f"{line} {word}".strip()
			if self.body_font.size(candidate)[0] > panel.width - 44 and line:
				lines.append(line)
				line = word
			else:
				line = candidate
		if line:
			lines.append(line)
		for index, line in enumerate(lines):
			draw_text_center(
				target,
				line,
				self.body_font,
				DARK_BROWN,
				(panel.centerx, panel.y + 143 + index * 27),
			)

	def _draw_portraits(self, target, mouse_pos):
		for index, rect in enumerate(self.portrait_rects):
			selected = index == self.selected_index
			hovered = rect.collidepoint(mouse_pos)
			fill = (255, 249, 239) if selected or hovered else (235, 220, 195)
			pygame.draw.rect(target, fill, rect, border_radius=11)
			pygame.draw.rect(
				target,
				TERRACOTTA if selected else DARK_BROWN,
				rect,
				4 if selected else 2,
				border_radius=11,
			)
			image = self._portrait_surfaces[index]
			if image is None:
				pygame.draw.circle(target, TAN, (rect.centerx, rect.y + 37), 23)
			else:
				target.blit(image, image.get_rect(center=(rect.centerx, rect.y + 31)))
			draw_text_center(
				target,
				CHARACTERS[index]["species"],
				self.label_font,
				DARK_BROWN,
				(rect.centerx, rect.bottom - 14),
			)

	def _draw_button(self, target, rect, label, mouse_pos, primary=False):
		hovered = rect.collidepoint(mouse_pos)
		fill = TERRACOTTA if primary else CREAM
		if hovered:
			fill = (177, 97, 72) if primary else (255, 249, 239)
		pygame.draw.rect(target, fill, rect, border_radius=10)
		pygame.draw.rect(target, DARK_BROWN, rect, 2, border_radius=10)
		color = CREAM if primary else DARK_BROWN
		draw_text_center(target, label, self.label_font, color, rect.center)
