# SLICE

SLICE is a Pygame pizza-restaurant game project. The playable part currently
contains the main menu, an animated gate transition, an opening story, and
simple Continue, Settings, About, and character-selection screens.

The restaurant gameplay is not implemented yet. There is no `game/` or
`systems/` package yet; player movement, customers, orders, baking, and serving
will be added when that work starts.

## Install and Run

Use Python 3 and install the project dependency:

```bash
python -m pip install -r requirements.txt
```

Start the game from the project folder:

```bash
python main.py
```

The game window is 1200 by 675 pixels and targets 60 frames per second. The
window uses Pygame's scaled display mode and vertical sync, as before.

## Project Structure

```text
main.py                 Safe entry point; starts Game
settings.py             Window, color, layout, and timing settings
dev_runner.py           Starts main.py as a child process during development
core/
	__init__.py           Package marker for the core modules
	game.py               Pygame setup and the shared game loop
	scene_manager.py      Active screen, input routing, and screen fades
	asset_loader.py       Cached image loading with helpful missing-file errors
screens/
	menu.py               Main menu and animated gate transition
	gate_light.py         The wandering light and its dust motes
	introduction.py       Opening story, dialogue typing, and story drawing
	characters.py         Current character-selection placeholder
	info.py               Shared Continue, Settings, and About screens
	common.py             Shared text and button drawing helpers
assets/menu/            Background and gate images used by the menu
data/                   Reserved for saved settings and order data
docs/                   Project notes (README.md, algorithms.md, data_structures.md)
tests/                  Automated checks for current screen behavior
```

Edit the root `settings.py` for the live window and menu settings.

## How the Game Runs

`main.py` calls `Game().run()`. `core/game.py` initializes Pygame, creates the
window, loads shared fonts and assets, then repeats the same three steps:

1. Send input events to the scene manager and active screen.
2. Update the active screen and transition timers.
3. Draw the screen and fade layers, then show the frame.

The scene manager owns the screen names and fades. A screen can call
`game.scene_manager.go_to("about")` to change screens with a black fade.
`set_scene` is for an immediate switch, currently used to start the gate
animation. The gate animation switches directly to the story with a white fade
when it finishes.

Each screen has `handle_event(event)`, `update(delta_time)`, and
`draw(target, mouse_pos)` methods. Screens do not import each other; they ask
the scene manager to change the active screen. This keeps menu, dialogue, and
game-loop code separate.

## Controls

- Click a menu button to choose it.
- During the gate animation, click or press Space/Enter to skip it.
- During the story, press Space/Enter or click Next/the dialogue box.
- The first advance completes the current line if it is still typing. Advance
	again to move to the next line.
- Back moves to the previous story line. Skip opens character selection.
- Escape returns to the menu. Escape on the main menu exits the game.

## Add a Scene

1. Create a file in `screens/` and add a screen class.
2. Give it `handle_event`, `update`, and `draw` methods, following
	 `screens/info.py` for a small example.
3. Register an instance in `core/scene_manager.py` under a short name such as
	 `"shop"`.
4. Ask for it with `game.scene_manager.go_to("shop")` from a button or event.

Use `set_scene` only when a transition should happen immediately. For normal
navigation, use `go_to` so the existing black fade is kept.

## Add a Character or Animation

Character and restaurant behavior belongs in a new module under a `game/`
package rather than in `main.py` or the scene manager. The `game/` package does
not exist yet; create it along with an `__init__.py` when this work begins. The
current character screen is only a placeholder, so the first playable character
will need its own data and behavior before it can be selected in the game.

Put image files in an appropriate folder under `assets/`. Load them through the
shared loader so each image is cached:

```python
image = game.assets.load_image("chef.png", subdirectory="characters")
```

For a simple animation, store the animation's elapsed time in the owning
character or screen and update it with the `delta_time` passed to `update`.
Keep the image paths relative to `assets/`; do not repeat absolute paths in
game code. Missing images raise an error that shows the expected full path.

## Settings and Current Limits

Change the window size, colors, button placement, FPS target, and gate/dialogue
timings in the root `settings.py`. The keyboard controls are handled by the
active screen and `core/scene_manager.py`.

The current assets contain menu artwork only. There are no sound files or
audio playback calls in the project yet. Continue, Settings, About, and
character selection are informational placeholders, and there is no playable
restaurant loop or save system yet.

Run the automated screen checks with:

```bash
python -m unittest discover -s tests -v
```