"""The opening story scene and its typewriter-style dialogue."""

import math

import pygame

from screens.common import draw_button, draw_text_center
from settings import (
	BUTTON_BORDER,
	BUTTON_COLOR,
	CREAM,
	FADE_SPEED,
	HEIGHT,
	LINE_HEIGHT,
	PLACEHOLDER_COLOR,
	POP_FADE,
	POP_LENGTH,
	SCENE_COUNTER,
	SCENE_FLOOR,
	SCENE_LAMP,
	SCENE_WALL,
	TITLE_COLOR,
	TYPE_SPEED,
	WIDTH,
)


# Each entry is a speaker and dialogue line.
INTRO_DIALOGUE = [
	(
		"Narrator",
		"Congratulations, my friend! You survived the University of San Agustin. "
		"Your diploma is real, and so are your student loans.",
	),
	(
		"Narrator",
		"Your classmates became engineers and nurses. You looked at all that and "
		"said no thanks. You wanted to play with dough.",
	),
	(
		"Narrator",
		"YOU! Yes, you. The one who can smell fresh dough from three blocks away. "
		"That is not a talent. That is a calling.",
	),
	(
		"Narrator",
		"So grab your savings, dream big, and trust your gut. Zero backup plan, "
		"one very first pizza restaurant!",
	),
	(
		"Narrator",
		"Fair warning: cats will judge you, dogs will love everything, monkeys "
		"will steal the olives, and bees will ask for extra honey.",
	),
	(
		"Narrator",
		"Ready to bake, serve, and become the best pizza maker in town? Welcome "
		"to SLICE — your restaurant, your recipes, your slightly chaotic adventure!",
	),
]


class IntroScene:
	"""Handle dialogue input, typing, transitions, and story-scene drawing."""

	def __init__(self, game):
		self.game = game
		self.dialogue_font = game.fonts["dialogue"]
		self.label_font = game.fonts["label"]
		self.name_font = game.fonts["name"]

		self.back_button = pygame.Rect(40, HEIGHT - 60, 140, 40)
		self.next_button = pygame.Rect(WIDTH - 180, HEIGHT - 60, 140, 40)
		self.skip_button = pygame.Rect(WIDTH - 340, HEIGHT - 60, 140, 40)
		self.dialogue_box = pygame.Rect(60, 440, WIDTH - 120, 160)
		self.name_tag = pygame.Rect(90, 410, 200, 42)
		self.character_boxes = [
			pygame.Rect(150, 110, 240, 360),
			pygame.Rect(480, 110, 240, 360),
			pygame.Rect(810, 110, 240, 360),
		]

		self.index = 0
		self.text_alpha = 255
		self.fade_state = "none"
		self.pending_index = 0
		self.characters_shown = 0.0
		self.advance_requested = False

	def reset(self):
		"""Start the story from its first line."""
		self.reset_for_transition(reset_story=True)

	def reset_for_transition(self, reset_story=False):
		"""Clear typing/fade state and optionally restart the dialogue."""
		if reset_story:
			self.index = 0
		self.text_alpha = 255
		self.fade_state = "none"
		self.pending_index = self.index
		self.characters_shown = 0.0
		self.advance_requested = False

	def handle_event(self, event):
		"""Record keyboard or mouse input for the current dialogue line."""
		if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
			self.advance_requested = True
			return

		if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
			return

		if self.back_button.collidepoint(event.pos):
			if self.index > 0:
				# Don't start another fade mid-transition.
				if self.fade_state == "none":
					self.pending_index = self.index - 1
					self.fade_state = "out"
			else:
				self.game.scene_manager.go_to("menu")
		elif self.skip_button.collidepoint(event.pos):
			self.game.scene_manager.go_to("character")
		elif self.next_button.collidepoint(event.pos) or self.dialogue_box.collidepoint(
			event.pos
		):
			# The dialogue box also advances.
			self.advance_requested = True

	def update(self, delta_time):
		"""Advance typing and fade between dialogue lines."""
		# Consume each press once; fade-time presses are dropped.
		advance_requested = self.advance_requested
		self.advance_requested = False
		manager = self.game.scene_manager

		if manager.screen_fade_state != "none":
			return

		if advance_requested and self.fade_state == "none":
			typing_end = len(INTRO_DIALOGUE[self.index][1]) + POP_LENGTH
			if self.characters_shown < typing_end:
				# Finish typing before advancing.
				self.characters_shown = typing_end
			elif self.index + 1 >= len(INTRO_DIALOGUE):
				# The last line leads to character selection.
				manager.go_to("character")
			else:
				self.pending_index = self.index + 1
				self.fade_state = "out"

		if self.fade_state == "out":
			self.text_alpha -= FADE_SPEED
			if self.text_alpha <= 0:
				self.text_alpha = 0
				self.index = self.pending_index
				self.characters_shown = 0.0
				self.fade_state = "in"
		elif self.fade_state == "in":
			self.text_alpha += FADE_SPEED
			if self.text_alpha >= 255:
				self.text_alpha = 255
				self.fade_state = "none"

		# Pause typing during fades and the gate reveal.
		if (
			self.fade_state != "out"
			and manager.white_in_alpha < 0.4
			and self.characters_shown < len(INTRO_DIALOGUE[self.index][1]) + POP_LENGTH
		):
			self.characters_shown = min(
				self.characters_shown + TYPE_SPEED,
				len(INTRO_DIALOGUE[self.index][1]) + POP_LENGTH,
			)

	def draw(self, target, mouse_pos):
		"""Draw the restaurant backdrop, character placeholders, and dialogue."""
		speaker, text = INTRO_DIALOGUE[self.index]
		# Placeholder restaurant background.
		target.fill(SCENE_WALL)
		pygame.draw.rect(target, SCENE_COUNTER, (0, 300, WIDTH, 90))
		pygame.draw.rect(target, SCENE_FLOOR, (0, 390, WIDTH, HEIGHT - 390))

		for lamp_x in (200, 1000):
			pygame.draw.line(target, TITLE_COLOR, (lamp_x, 0), (lamp_x, 55), 3)
			pygame.draw.circle(target, SCENE_LAMP, (lamp_x, 75), 28)

		sign = pygame.Rect(WIDTH // 2 - 90, 20, 180, 55)
		pygame.draw.rect(target, CREAM, sign, border_radius=10)
		pygame.draw.rect(target, TITLE_COLOR, sign, 3, border_radius=10)
		draw_text_center(
			target,
			"PIZZA",
			self.game.fonts["button"],
			TITLE_COLOR,
			sign.center,
		)

		for character_box in self.character_boxes:
			pygame.draw.rect(target, PLACEHOLDER_COLOR, character_box, border_radius=20)
			pygame.draw.rect(target, TITLE_COLOR, character_box, 3, border_radius=20)
			draw_text_center(
				target,
				"Character",
				self.label_font,
				TITLE_COLOR,
				(character_box.centerx, character_box.y + 40),
			)

		pygame.draw.rect(target, CREAM, self.dialogue_box, border_radius=18)
		pygame.draw.rect(target, TITLE_COLOR, self.dialogue_box, 4, border_radius=18)
		pygame.draw.rect(target, BUTTON_COLOR, self.name_tag, border_radius=10)
		pygame.draw.rect(target, BUTTON_BORDER, self.name_tag, 3, border_radius=10)
		draw_text_center(
			target,
			speaker,
			self.name_font,
			(255, 255, 255),
			self.name_tag.center,
			self.text_alpha,
		)
		self._draw_typed_text(
			target,
			text,
			self.dialogue_box.x + 40,
			self.dialogue_box.y + 40,
			self.dialogue_box.width - 140,
		)

		typing_finished = len(text) + POP_LENGTH
		if self.text_alpha == 255 and self.characters_shown >= typing_finished:
			bounce = int(4 * math.sin(pygame.time.get_ticks() * 0.008))
			triangle_x = self.dialogue_box.right - 45
			triangle_y = self.dialogue_box.bottom - 35 + bounce
			pygame.draw.polygon(
				target,
				TITLE_COLOR,
				[
					(triangle_x - 10, triangle_y),
					(triangle_x + 10, triangle_y),
					(triangle_x, triangle_y + 12),
				],
			)

		button_font = self.game.fonts["small"]
		draw_button(target, self.back_button, "BACK", mouse_pos, button_font)
		draw_button(target, self.skip_button, "SKIP", mouse_pos, button_font)
		draw_button(target, self.next_button, "NEXT", mouse_pos, button_font)

	def _draw_typed_text(self, target, text, x, y, max_width):
		"""Reveal letters in place, each fading up over the last POP_LENGTH ones.

		Every letter is drawn at its final position; only its alpha changes, so
		the text never reflows while it types out.
		"""
		lines = self._wrap_text(text, max_width)
		character_index = 0

		for line in lines:
			for letter_index, letter in enumerate(line):
				if character_index >= self.characters_shown:
					return

				# Spaces count toward the reveal but are not drawn.
				if letter != " ":
					age = self.characters_shown - character_index
					progress = min(1.0, age / POP_LENGTH)
					alpha = int(
						self.text_alpha * (1 - (1 - progress) * POP_FADE)
					)
					image = self.dialogue_font.render(letter, True, TITLE_COLOR)
					image.set_alpha(alpha)
					letter_x = x + self.dialogue_font.size(line[:letter_index])[0]
					target.blit(image, (int(letter_x), int(y)))
				character_index += 1
			y += LINE_HEIGHT

	def _wrap_text(self, text, max_width):
		"""Wrap dialogue on word boundaries to fit the dialogue box."""
		lines = []
		current_line = ""
		for word in text.split(" "):
			candidate = current_line + word + " "
			if self.dialogue_font.size(candidate)[0] <= max_width:
				current_line = candidate
			else:
				if current_line:
					lines.append(current_line)
				current_line = word + " "
		lines.append(current_line)
		return lines
