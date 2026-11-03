"""Placeholder for the character-selection screen."""

from screens.info import InfoScene


class CharacterScene(InfoScene):
	"""List the planned cast until choosing one is actually implemented."""

	def __init__(self, game):
		super().__init__(
			game,
			"Choose Your Character",
			[
				"Cat, Dog, Monkey, Bee, or Bunny?",
				"(Character selection comes in the next step.)",
			],
			back_target="intro",
		)
