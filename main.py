import pygame
import sys
import math   # we use math.sin for the bouncing triangle











# ==================================================
# 1. START PYGAME
# --------------------------------------------------
# This must run first. It turns Pygame on.
# ==================================================
pygame.init()

























# ==================================================
# 2. WINDOW SETTINGS
# --------------------------------------------------
# WIDTH and HEIGHT are the size of the game window
# in pixels. Change them to make the window bigger
# or smaller.
# ==================================================
WIDTH = 1200
HEIGHT = 675































screen = pygame.display.set_mode((WIDTH, HEIGHT))   # the window we draw on
pygame.display.set_caption("SLICE by PyAgustinos")  # text at the top of the window

clock = pygame.time.Clock()   # controls how fast the game runs

























# ==================================================
# 3. COLORS
# --------------------------------------------------
# Each color is (Red, Green, Blue).
# Each number goes from 0 (none) to 255 (full).
# Change a number to change the color.
# ==================================================

# Main colors
BACKGROUND = (221, 201, 170)          # beige background
TITLE_COLOR = (90, 55, 45)            # dark brown text and borders
BUTTON_COLOR = (115, 145, 115)        # green button
BUTTON_HOVER = (90, 120, 90)          # darker green when the mouse is on it
BUTTON_BORDER = (120, 75, 60)         # brown button outline
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)                     # used for the screen fade
CREAM = (252, 243, 225)               # light box color
PLACEHOLDER_COLOR = (235, 220, 195)   # boxes that will become pictures later

# Colors for the story scene
SCENE_WALL = (245, 205, 190)
SCENE_COUNTER = (205, 140, 130)
SCENE_FLOOR = (225, 175, 160)
SCENE_LAMP = (225, 160, 170)

































# ==================================================
# 4. MAIN MENU LAYOUT
# --------------------------------------------------
# The menu is split in two parts:
#   LEFT  = title and buttons
#   RIGHT = character picture (placeholder for now)
# LEFT_WIDTH is where the left part ends.
# ==================================================
LEFT_WIDTH = 540

# --- Title box size and position ---
TITLE_WIDTH = 465
TITLE_HEIGHT = 155
TITLE_X = (LEFT_WIDTH - TITLE_WIDTH) // 2   # puts the box in the middle of the left part
TITLE_Y = 35                                # distance from the top

# --- Menu button size and position ---
BUTTON_X = 110            # distance from the left
BUTTON_START_Y = 270      # where the first button starts (from the top)
BUTTON_WIDTH = 305
BUTTON_HEIGHT = 44
BUTTON_GAP = 9            # space between buttons

# --- Character picture area (right side) ---
CHARACTER_X = LEFT_WIDTH
CHARACTER_Y = 0
CHARACTER_WIDTH = WIDTH - LEFT_WIDTH
CHARACTER_HEIGHT = HEIGHT




































# ==================================================
# 5. FONTS
# --------------------------------------------------
# A font is the style and size of the text.
# The number is the size. Bigger number = bigger text.
# ==================================================
title_font = pygame.font.SysFont("georgia", 40, bold=True)
button_font = pygame.font.SysFont("arial", 22)
label_font = pygame.font.SysFont("arial", 18)
small_font = pygame.font.SysFont("arial", 20)
dialogue_font = pygame.font.SysFont("arial", 24)        # story text
name_font = pygame.font.SysFont("arial", 22, bold=True) # name tag text

































# ==================================================
# 6. TRANSITION AND TYPING SETTINGS
# --------------------------------------------------
# Change these numbers to change how things move.
#
# SCREEN_FADE_SPEED = how fast the screen fades to black
#                     and back when we change screens.
#                     Bigger = faster. Smaller = slower.
#                     10 takes about 1 second in total.
#
# FADE_SPEED = how fast the story text fades in and out
#              between story pieces. Bigger = faster.
#
# TYPE_SPEED = how many letters appear every frame.
#              0.7 is about 40 letters per second.
#
# POP_HEIGHT = how high a new letter hops (in pixels).
# POP_LENGTH = how many letters the hop lasts.
#
# After a letter finishes its hop, it stays still.
# ==================================================
SCREEN_FADE_SPEED = 10

FADE_SPEED = 10

TYPE_SPEED = 0.5
POP_LENGTH = 2
POP_FADE = 0.6
LINE_HEIGHT = 32

# A black picture that covers the whole window.
# We make it see-through (alpha) to fade the screen.
fade_surface = pygame.Surface((WIDTH, HEIGHT))
fade_surface.fill(BLACK)




































# ==================================================
# 7. CREATE THE MENU SHAPES
# --------------------------------------------------
# A Rect is a rectangle: (x, y, width, height)
#   x = distance from the left
#   y = distance from the top
# We use Rects to draw shapes and to check clicks.
# ==================================================
title_area = pygame.Rect(TITLE_X, TITLE_Y, TITLE_WIDTH, TITLE_HEIGHT)

character_area = pygame.Rect(
    CHARACTER_X,
    CHARACTER_Y,
    CHARACTER_WIDTH,
    CHARACTER_HEIGHT
)







































# ==================================================
# 8. CREATE THE MENU BUTTONS
# --------------------------------------------------
# We make a list of button names.
# Then a loop makes one Rect for each name.
# Each button is placed a little lower than the last.
# ==================================================
button_names = [
    "START GAME",
    "CONTINUE",
    "SETTINGS",
    "ABOUT US",
    "EXIT"
]

buttons = []   # will hold pairs of (name, rectangle)

for i, name in enumerate(button_names):
    # i = 0, 1, 2, 3, 4 (the position of the button)
    x = BUTTON_X
    y = BUTTON_START_Y + i * (BUTTON_HEIGHT + BUTTON_GAP)
    rect = pygame.Rect(x, y, BUTTON_WIDTH, BUTTON_HEIGHT)
    buttons.append((name, rect))












































# ==================================================
# 9. SMALL BUTTONS AT THE BOTTOM
# --------------------------------------------------
# BACK  = bottom left
# SKIP  = bottom right (left of NEXT)
# NEXT  = bottom right
# ==================================================
back_button = pygame.Rect(40, HEIGHT - 60, 140, 40)
next_button = pygame.Rect(WIDTH - 180, HEIGHT - 60, 140, 40)
skip_button = pygame.Rect(WIDTH - 340, HEIGHT - 60, 140, 40)






































# ==================================================
# 10. STORY SCENE SHAPES
# --------------------------------------------------
# dialogue_box = the big box with the story text
# name_tag     = the small box that shows who is talking
# scene_characters = three placeholder boxes where
#                    the animal pictures will go later
# ==================================================
dialogue_box = pygame.Rect(60, 440, WIDTH - 120, 160)
name_tag = pygame.Rect(90, 410, 200, 42)

scene_characters = [
    pygame.Rect(150, 110, 240, 360),   # left character
    pygame.Rect(480, 110, 240, 360),   # middle character
    pygame.Rect(810, 110, 240, 360),   # right character
]



































# ==================================================
# 11. HELPER FUNCTIONS
# --------------------------------------------------
# A function is a small tool we can use again and
# again. We write it once, then call it by name.
# ==================================================

def draw_text_center(text, font, color, center, alpha=255):
    """Draw text with its middle at the 'center' point.

    alpha is how visible the text is (0 = invisible, 255 = normal).
    If we do not give an alpha, the text is fully visible.
    """
    image = font.render(text, True, color)       # turn the text into a picture
    image.set_alpha(alpha)                       # set how see-through it is
    rect = image.get_rect(center=center)         # find where to put it
    screen.blit(image, rect)                     # draw it on the window


def draw_button(rect, text, mouse_pos, font=None):
    """Draw one button. It turns darker when the mouse is on it."""
    if font is None:
        font = button_font

    # Check if the mouse is inside the button
    if rect.collidepoint(mouse_pos):
        color = BUTTON_HOVER
    else:
        color = BUTTON_COLOR

    pygame.draw.rect(screen, color, rect, border_radius=12)             # button body
    pygame.draw.rect(screen, BUTTON_BORDER, rect, 3, border_radius=12)  # outline
    draw_text_center(text, font, WHITE, rect.center)                    # button text


def wrap_text(text, font, max_width):
    """Cut a long sentence into lines that fit inside max_width.

    It adds words one at a time. When the line gets too
    wide, it starts a new line.
    """
    words = text.split(" ")
    lines = []
    current = ""

    for word in words:
        test = current + word + " "
        if font.size(test)[0] <= max_width:
            current = test                    # the word fits, keep going
        else:
            lines.append(current)             # line is full, save it
            current = word + " "              # start a new line

    lines.append(current)                     # save the last line
    return lines

def draw_typed_text(text, font, color, x, y, max_width, chars_shown, alpha):
    """Draw the story text one letter at a time.

    Letters do not move at all. Each new letter fades in
    where it belongs, then stays still.
    """
    lines = wrap_text(text, font, max_width)
    count = 0   # how many letters we have passed

    for line in lines:
        for i, letter in enumerate(line):

            # Stop at letters that are not typed yet
            if count >= chars_shown:
                return

            if letter != " ":
                # fade: 0 = just appeared, 1 = finished
                age = chars_shown - count
                progress = min(1.0, age / POP_LENGTH)
                letter_alpha = int(alpha * (1 - (1 - progress) * POP_FADE))

                image = font.render(letter, True, color)
                image.set_alpha(letter_alpha)

                letter_x = x + font.size(line[:i])[0]   # where this letter starts
                screen.blit(image, (int(letter_x), int(y)))

            count += 1

        y += LINE_HEIGHT

def draw_menu(mouse_pos):
    """Draw the main menu."""
    screen.fill(BACKGROUND)

    # Right side: placeholder for the character picture
    pygame.draw.rect(screen, PLACEHOLDER_COLOR, character_area)
    draw_text_center(
        "Character image here",
        label_font,
        TITLE_COLOR,
        character_area.center
    )

    # Title box (cream box with a brown outline)
    pygame.draw.rect(screen, CREAM, title_area, border_radius=20)
    pygame.draw.rect(screen, TITLE_COLOR, title_area, 4, border_radius=20)

    # Game name, and the small line under it
    draw_text_center(
        "SLICE",
        title_font,
        TITLE_COLOR,
        (title_area.centerx, title_area.centery - 15)
    )
    draw_text_center(
        "by PyAgustinos",
        label_font,
        TITLE_COLOR,
        (title_area.centerx, title_area.centery + 30)
    )

    # Draw all five menu buttons
    for name, rect in buttons:
        draw_button(rect, name, mouse_pos)


def draw_info_screen(heading, lines, mouse_pos):
    """Draw a simple screen: a heading, some text, and a BACK button.

    Used for Continue, Settings, About, and Character screens.
    """
    screen.fill(BACKGROUND)
    draw_text_center(heading, title_font, TITLE_COLOR, (WIDTH // 2, 100))

    # Draw each line of text, one under the other
    y = 200
    for line in lines:
        draw_text_center(line, button_font, TITLE_COLOR, (WIDTH // 2, y))
        y += 40

    draw_button(back_button, "BACK", mouse_pos, small_font)


def draw_intro_scene(speaker, text, mouse_pos, text_alpha, chars_shown):
    """Draw the story scene.

    text_alpha  controls the fade (the name and story text fade).
    chars_shown controls the typing (the typing counter).

    Order matters! Things drawn first are at the back.
    Things drawn last are at the front.
    1) Background  2) Characters  3) Dialogue box  4) Buttons
    """













    # ---------- 1) BACKGROUND ----------
    screen.fill(SCENE_WALL)                                               # wall
    pygame.draw.rect(screen, SCENE_COUNTER, (0, 300, WIDTH, 90))          # counter
    pygame.draw.rect(screen, SCENE_FLOOR, (0, 390, WIDTH, HEIGHT - 390))  # floor

    # Two hanging lamps (a line and a circle each)
    for lamp_x in (200, 1000):
        pygame.draw.line(screen, TITLE_COLOR, (lamp_x, 0), (lamp_x, 55), 3)
        pygame.draw.circle(screen, SCENE_LAMP, (lamp_x, 75), 28)

    # Sign at the top
    sign = pygame.Rect(WIDTH // 2 - 90, 20, 180, 55)
    pygame.draw.rect(screen, CREAM, sign, border_radius=10)
    pygame.draw.rect(screen, TITLE_COLOR, sign, 3, border_radius=10)
    draw_text_center("PIZZA", button_font, TITLE_COLOR, sign.center)













    # ---------- 2) CHARACTER PLACEHOLDERS ----------
    for char_rect in scene_characters:
        pygame.draw.rect(screen, PLACEHOLDER_COLOR, char_rect, border_radius=20)
        pygame.draw.rect(screen, TITLE_COLOR, char_rect, 3, border_radius=20)
        draw_text_center(
            "Character",
            label_font,
            TITLE_COLOR,
            (char_rect.centerx, char_rect.y + 40)
        )













    # ---------- 3) DIALOGUE BOX ----------
    pygame.draw.rect(screen, CREAM, dialogue_box, border_radius=18)
    pygame.draw.rect(screen, TITLE_COLOR, dialogue_box, 4, border_radius=18)

    # Name tag (the name does not move)
    pygame.draw.rect(screen, BUTTON_COLOR, name_tag, border_radius=10)
    pygame.draw.rect(screen, BUTTON_BORDER, name_tag, 3, border_radius=10)
    draw_text_center(speaker, name_font, WHITE, name_tag.center, text_alpha)

    # Story text: typed one letter at a time
    draw_typed_text(
        text,
        dialogue_font,
        TITLE_COLOR,
        dialogue_box.x + 40,
        dialogue_box.y + 40,
        dialogue_box.width - 140,
        chars_shown,
        text_alpha
    )

    # Small triangle at the bottom right: "click to continue".
    # It only shows when the text is fully visible AND the last
    # letter has finished its hop (that is why we add POP_LENGTH).
    # It bounces up and down to say "click me!".
    if text_alpha == 255 and chars_shown >= len(text) + POP_LENGTH:   # CHANGED
        now = pygame.time.get_ticks()
        bounce = int(4 * math.sin(now * 0.008))
        tx = dialogue_box.right - 45
        ty = dialogue_box.bottom - 35 + bounce
        pygame.draw.polygon(
            screen,
            TITLE_COLOR,
            [(tx - 10, ty), (tx + 10, ty), (tx, ty + 12)]
        )








    # ---------- 4) BOTTOM BUTTONS ----------
    draw_button(back_button, "BACK", mouse_pos, small_font)
    draw_button(skip_button, "SKIP", mouse_pos, small_font)
    draw_button(next_button, "NEXT", mouse_pos, small_font)































# ==================================================
# 12. GAME TEXT
# --------------------------------------------------
# All the words shown in the game are here.
# You can edit the text without touching the code.
# ==================================================

# The story. Each item is: ("who is talking", "what they say")
# One click shows one item.
intro_dialogue = [
    ("Narrator", "Congratulations, my friend! You survived the University of San Agustin. Your diploma is real, and so are your student loans."),
    ("Narrator", "Your classmates became engineers and nurses. You looked at all that and said no thanks. You wanted to play with dough."),
    ("Narrator", "YOU! Yes, you. The one who can smell fresh dough from three blocks away. That is not a talent. That is a calling."),
    ("Narrator", "So grab your savings, dream big, and trust your gut. Zero backup plan, one very first pizza restaurant!"),
    ("Narrator", "Fair warning: cats will judge you, dogs will love everything, monkeys will steal the olives, and bees will ask for extra honey."),
    ("Narrator", "Ready to bake, serve, and become the best pizza maker in town? Welcome to SLICE — your restaurant, your recipes, your slightly chaotic adventure!"),
]


# Text for the simple screens
character_lines = [
    "Cat, Dog, Monkey, Bee, or Bunny?",
    "(Character selection comes in the next step.)"
]
continue_lines = ["No saved game yet.", "(Saving comes in a later stage.)"]
settings_lines = ["Settings will be added later."]
about_lines = ["SLICE by PyAgustinos", "A cozy pizza restaurant game."]






















# ==================================================
# 13. GAME VARIABLES
# --------------------------------------------------
# These variables remember what the game is doing.
# ==================================================

running = True            # the game stops when this becomes False
current_screen = "menu"   # which screen we are on right now
intro_index = 0           # which piece of the story we are on (0 = first)

# --- Variables for the text fade (between story pieces) ---
text_alpha = 255          # how visible the story text is (0 to 255)
fade_state = "none"       # "none" = no fade, "out" = fading away, "in" = appearing
pending_index = 0         # the story piece we will show after the fade out

# --- Variable for the typing effect ---
chars_shown = 0.0         # the typing counter (letters shown + a little extra at the end)

# --- Variables for the SCREEN fade (the black fade) ---
screen_fade_state = "none"   # "none" = no fade, "out" = going to black, "in" = coming back
screen_fade_alpha = 0        # how black the screen is (0 = clear, 255 = fully black)
next_screen = "menu"         # the screen we will show after the screen goes black


def go_to(screen_name):
    """Start a black fade, then change to another screen.

    Instead of changing the screen right away, we remember
    where we want to go. The screen fades to black first.
    When it is fully black, the main loop changes the screen
    and fades back in.

    We ignore this if a screen fade is already happening.
    """
    global screen_fade_state, next_screen   # 'global' lets this function change these variables

    if screen_fade_state == "none":
        next_screen = screen_name
        screen_fade_state = "out"





































# ==================================================
# 14. MAIN GAME LOOP
# --------------------------------------------------
# The game runs inside this loop, again and again,
# about 60 times every second.
# Each time around, it does these jobs:
#   A) Check what the player did (clicks and keys)
#   B) Update the text fade and the typing
#   C) Update the screen fade (black fade)
#   D) Draw the current screen
#   E) Show the drawing on the window
# ==================================================

while running:
    mouse_pos = pygame.mouse.get_pos()   # where the mouse is right now
    advance_intro = False                # True = show the next story piece


    # ----------------------------------------------
    # 14A. CHECK WHAT THE PLAYER DID
    # ----------------------------------------------
    for event in pygame.event.get():

        # The player clicked the X to close the window
        if event.type == pygame.QUIT:
            running = False

        # While the screen is fading, ignore keys and clicks
        if screen_fade_state != "none":
            continue

        # --- Keyboard ---
        if event.type == pygame.KEYDOWN:

            # ESC: close the game from the menu,
            #      or go back to the menu from other screens
            if event.key == pygame.K_ESCAPE:
                if current_screen == "menu":
                    running = False
                else:
                    go_to("menu")

            # SPACE or ENTER: next story piece
            if current_screen == "intro":
                if event.key == pygame.K_SPACE or event.key == pygame.K_RETURN:
                    advance_intro = True

        # --- Left mouse click ---
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:

            # Clicks on the MAIN MENU
            if current_screen == "menu":
                for name, rect in buttons:
                    if rect.collidepoint(event.pos):   # was this button clicked?
                        if name == "START GAME":
                            go_to("intro")             # black fade, then the story
                        elif name == "CONTINUE":
                            go_to("continue")
                        elif name == "SETTINGS":
                            go_to("settings")
                        elif name == "ABOUT US":
                            go_to("about")
                        elif name == "EXIT":
                            running = False

            # Clicks on the STORY screen
            elif current_screen == "intro":
                if back_button.collidepoint(event.pos):
                    # BACK: go to the previous piece (with a text fade).
                    # If we are on the first piece, go to the menu.
                    if intro_index > 0:
                        if fade_state == "none":        # ignore clicks during a text fade
                            pending_index = intro_index - 1
                            fade_state = "out"
                    else:
                        go_to("menu")
                elif skip_button.collidepoint(event.pos):
                    go_to("character")                 # skip the whole story
                elif next_button.collidepoint(event.pos):
                    advance_intro = True
                elif dialogue_box.collidepoint(event.pos):
                    advance_intro = True               # clicking the box also continues

            # Clicks on the CHARACTER screen
            elif current_screen == "character":
                if back_button.collidepoint(event.pos):
                    go_to("intro")

            # Clicks on Continue, Settings, and About screens
            else:
                if back_button.collidepoint(event.pos):
                    go_to("menu")

    # Move the story forward.
    # We do this after the event loop so it only happens once.
    # We wait until the text fade is finished (fade_state == "none").
    if advance_intro and current_screen == "intro" and fade_state == "none":
        # The typing is finished when the counter reaches the last
        # letter PLUS the extra steps the last letters need to settle.
        typing_end = len(intro_dialogue[intro_index][1]) + POP_LENGTH   # CHANGED

        if chars_shown < typing_end:
            # Still typing: finish the typing right now.
            # Every letter jumps to its final, still position.
            chars_shown = typing_end                                    # CHANGED
        elif intro_index + 1 >= len(intro_dialogue):
            # The story is finished, so go to character selection
            go_to("character")
        else:
            pending_index = intro_index + 1   # remember which piece comes next
            fade_state = "out"                # start fading the old text away

    # ----------------------------------------------
    # 14B. UPDATE THE TEXT FADE AND THE TYPING
    # ----------------------------------------------
    # We pause these while the screen is fading to black,
    # so nothing changes behind the black fade.
    if screen_fade_state == "none":

        # "out": the old text becomes invisible.
        #        When it is gone, we swap to the new piece.
        # "in":  the new text becomes visible.
        if fade_state == "out":
            text_alpha -= FADE_SPEED
            if text_alpha <= 0:
                text_alpha = 0
                intro_index = pending_index   # swap to the new story piece
                chars_shown = 0.0             # the new piece starts with no letters
                fade_state = "in"             # now fade the new text in

        elif fade_state == "in":
            text_alpha += FADE_SPEED
            if text_alpha >= 255:
                text_alpha = 255
                fade_state = "none"           # the text fade is finished

        # Typing: the counter grows a little every frame.
        # We pause the typing while the old text is fading out.
        if current_screen == "intro" and fade_state != "out":
            typing_end = len(intro_dialogue[intro_index][1]) + POP_LENGTH   # CHANGED
            if chars_shown < typing_end:
                chars_shown += TYPE_SPEED
                if chars_shown > typing_end:
                    chars_shown = typing_end   # never go past the end

    # ----------------------------------------------
    # 14C. UPDATE THE SCREEN FADE (BLACK FADE)
    # ----------------------------------------------
    # "out": the screen becomes black.
    #        When it is fully black, we change the screen.
    # "in":  the black goes away and the new screen appears.
    if screen_fade_state == "out":
        screen_fade_alpha += SCREEN_FADE_SPEED
        if screen_fade_alpha >= 255:
            screen_fade_alpha = 255

            # The screen is fully black, so now we can change screens safely.
            # If we go from the menu to the story, start the story from piece 1.
            if next_screen == "intro" and current_screen == "menu":
                intro_index = 0

            current_screen = next_screen
            text_alpha = 255          # reset the text fade
            fade_state = "none"
            chars_shown = 0.0         # the story starts typing from the first letter

            screen_fade_state = "in"  # now the black goes away

    elif screen_fade_state == "in":
        screen_fade_alpha -= SCREEN_FADE_SPEED
        if screen_fade_alpha <= 0:
            screen_fade_alpha = 0
            screen_fade_state = "none"   # the screen fade is finished

    # ----------------------------------------------
    # 14D. DRAW THE CURRENT SCREEN
    # ----------------------------------------------
    if current_screen == "menu":
        draw_menu(mouse_pos)

    elif current_screen == "intro":
        speaker, text = intro_dialogue[intro_index]   # get the current story piece
        draw_intro_scene(speaker, text, mouse_pos, text_alpha, chars_shown)

    elif current_screen == "character":
        draw_info_screen("Choose Your Character", character_lines, mouse_pos)

    elif current_screen == "continue":
        draw_info_screen("Continue", continue_lines, mouse_pos)

    elif current_screen == "settings":
        draw_info_screen("Settings", settings_lines, mouse_pos)

    elif current_screen == "about":
        draw_info_screen("About Us", about_lines, mouse_pos)

    # Draw the black cover on top of everything.
    # It is drawn last, so it covers the whole screen.
    if screen_fade_alpha > 0:
        fade_surface.set_alpha(screen_fade_alpha)
        screen.blit(fade_surface, (0, 0))

    # ----------------------------------------------
    # 14E. SHOW THE DRAWING ON THE WINDOW
    # ----------------------------------------------
    pygame.display.flip()   # show everything we just drew
    clock.tick(60)          # run at most 60 times per second
























# ==================================================
# 15. CLOSE THE GAME
# --------------------------------------------------
# This runs after the loop stops.
# ==================================================
pygame.quit()
sys.exit()