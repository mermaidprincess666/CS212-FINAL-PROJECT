"""Shared window, color, layout, and animation settings for SLICE."""

from pathlib import Path


# Window size, frame rate, and caption.
WIDTH = 1200
HEIGHT = 675
FPS = 60
GAME_TITLE = "SLICE by PyAgustinos"

# Colors are RGB tuples.
BACKGROUND = (221, 201, 170)
TITLE_COLOR = (90, 55, 45)
BUTTON_COLOR = (115, 145, 115)
BUTTON_HOVER = (90, 120, 90)
BUTTON_BORDER = (120, 75, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# Gate glow
GATE_GLOW_COLOR = (255, 232, 198)  # #FFE8C6
# Main transition overlay
SCREEN_FADE_COLOR = (245, 232, 211)  # #F5E8D3
# Brightest transition highlight
GATE_HIGHLIGHT_COLOR = (255, 249, 239)  # #FFF9EF
CREAM = (252, 243, 225)
PLACEHOLDER_COLOR = (235, 220, 195)
ANTIQUE_GOLD = (221, 187, 136)  # #DDBB88
WARM_BEIGE = (200, 169, 137)  # #C8A989

# Flat fills for the hand-drawn backdrop of the story scene.
SCENE_WALL = (245, 205, 190)
SCENE_COUNTER = (205, 140, 130)
SCENE_FLOOR = (225, 175, 160)
SCENE_LAMP = (225, 160, 170)

# Main-menu layout.
MENU_CENTER_X = 900
TITLE_WIDTH = 465
TITLE_HEIGHT = 140
TITLE_X = MENU_CENTER_X - TITLE_WIDTH // 2
TITLE_Y = 30
BUTTON_WIDTH = 305
BUTTON_X = MENU_CENTER_X - BUTTON_WIDTH // 2
BUTTON_START_Y = 210
BUTTON_HEIGHT = 44
BUTTON_GAP = 9

# Font sizes and dialogue pacing.
TITLE_FONT_SIZE = 40
BUTTON_FONT_SIZE = 22
LABEL_FONT_SIZE = 18
SMALL_FONT_SIZE = 20
DIALOGUE_FONT_SIZE = 24
NAME_FONT_SIZE = 22
SCREEN_FADE_SPEED = 10  # alpha/step for the scene-to-scene overlay
FADE_SPEED = 10  # alpha/step for one dialogue line swapping out and in
TYPE_SPEED = 0.5  # characters revealed per frame
POP_LENGTH = 2  # frames a fresh letter takes to reach full opacity
POP_FADE = 0.6  # a new letter starts this much dimmer than a settled one
LINE_HEIGHT = 32

# Gate animation. The artwork is authored at 1920 x 1080 pixels, so every
# position and radius below is in that source space unless noted.
# The phases overlap: MENU_UI_FADE runs during the light's prelude, and each
# gate phase is timed from GATE_LIGHT_PRELUDE_TIME, when the dive lands.
MENU_UI_FADE = 0.35        # seconds for the title and buttons to leave
MENU_UI_SLIDE = 70         # px the button panel slides as it fades
GATE_OPEN_DELAY = 0.05     # pause after the prelude before the doors swing
GATE_OPEN_TIME = 1.1       # seconds the doors take to finish swinging
GATE_OPEN_AMOUNT = 0.9     # doors squash to 10% of their width at full swing
GATE_ZOOM_TIME = 1.25      # seconds for the camera to push into the arch
GATE_ZOOM_END = 4.0        # camera magnification reached at the end of the push
GATE_FADE_START = 0.45     # gate seconds spent igniting before expansion starts
GATE_TOTAL_TIME = 1.15     # gate seconds until the haze fully covers the screen
WHITE_IN_TIME = 0.6        # seconds for the haze to clear off the story
GATE_BLOOM = 110           # peak alpha of the ignition glow before it expands
GATE_GLOW_SOURCE = 768  # px: cached size of the shapeless light mass texture
GATE_LIGHT_START_RADIUS = 80   # px: the size of the light when it ignites
GATE_LIGHT_COVER_FRACTION = 0.55  # light mass grows this far; the haze finishes
GATE_LIGHT_FINGERS = 6         # irregular streams that spread from the gate
GATE_FOCUS = (395, 650)    # px in the source art: the arch the camera aims at
SRC_W = 1920
SRC_H = 1080

# The wandering light that leads into the gate animation above. Its three
# phases run back-to-back from the click on START GAME, and the cutscene clock
# hands over to the gate the moment the dive lands. Each value below is that
# phase's duration, so the gate phases above are timed after their sum.
GATE_LIGHT_APPEAR_TIME = 0.35   # the spark kindles in place
GATE_LIGHT_FLOAT_TIME = 1.1     # it hovers and drifts near the entrance
GATE_LIGHT_DART_TIME = 0.30     # it accelerates into the arch
GATE_LIGHT_PRELUDE_TIME = (
    GATE_LIGHT_APPEAR_TIME + GATE_LIGHT_FLOAT_TIME + GATE_LIGHT_DART_TIME
)
GATE_LIGHT_CORE_COLOR = GATE_HIGHLIGHT_COLOR  # #FFF9EF
GATE_LIGHT_MID_COLOR = GATE_GLOW_COLOR  # #FFE8C6
GATE_LIGHT_HALO_COLOR = ANTIQUE_GOLD
GATE_LIGHT_AURA_COLOR = WARM_BEIGE
# The light is three stacked glows, drawn flare first and core last.
GATE_LIGHT_CORE_RADIUS = 7
GATE_LIGHT_HALO_RADIUS = 24
GATE_LIGHT_FLARE_RADIUS = 42
# Where the light wanders, measured from the gate the camera is looking at.
GATE_LIGHT_WANDER_OFFSET = (150, -110)
GATE_LIGHT_WANDER_AMPLITUDE = (105, 58)   # px the main sine swings
GATE_LIGHT_WANDER_SECONDARY = (42, 22)    # px added on a faster sine
GATE_LIGHT_WANDER_DRIFT = (26, -18)       # px walked across the whole float
GATE_LIGHT_DART_ARC = 46  # px the dive bows sideways instead of running straight
GATE_TRAIL_SAMPLES = 18   # positions kept behind the diving light
# The light itself sheds no dust while it wanders and dives. The pool below is
# only for the final cover: the motes fan out of the arch once the light starts
# expanding, and nothing is drawn before that.
GATE_PARTICLE_CAP = 160            # cover motes alive at once
GATE_PARTICLE_BURST_RATE = 420.0   # motes shed per second at full expansion
GATE_PARTICLE_BURST_SPEED = (520.0, 1150.0)  # px/s outward speeds at spawn
GATE_PARTICLE_BURST_ACCEL = 3.6    # per second: cover motes keep gaining speed
GATE_PARTICLE_LIFE = 1.1  # seconds; each mote draws a share of this on spawn
# The warm-white flash at the moment the light reaches the arch.
GATE_FLASH_TIME = 0.45
GATE_FLASH_ALPHA = 215

# Full length of the menu-to-story cutscene, prelude included.
GATE_ANIMATION_TIME = GATE_LIGHT_PRELUDE_TIME + GATE_TOTAL_TIME

PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"
