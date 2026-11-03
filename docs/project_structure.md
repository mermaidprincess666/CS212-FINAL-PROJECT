# SLICE — Project Structure and Developer Guide

This guide explains how the SLICE codebase is organized, where each feature
lives, and which files you should edit when you want to change something.
It describes the project **as it exists today**. Restaurant gameplay
(customers, orders, cooking, scoring) is not implemented yet, so this guide
also points out where that work is expected to go.

---

## 1. Project Tree

```text
SLICE/
│
├── main.py                  # Entry point. Creates Game() and runs it.
├── settings.py              # ALL window sizes, colors, layout, fonts and animation timings.
├── dev_runner.py            # Dev helper: runs main.py as a child process (Ctrl+C stops it).
├── requirements.txt         # Dependencies (pygame-ce).
├── README.md                # Short project overview.
│
├── core/                    # Game infrastructure (not screen-specific code).
│   ├── __init__.py          #   Package marker.
│   ├── game.py              #   Game class: window, clock, fonts, assets, main loop.
│   ├── scene_manager.py     #   SceneManager: holds all screens, routes input, fades between them.
│   └── asset_loader.py      #   AssetLoader: loads and caches images from assets/.
│
├── screens/                 # One file per screen (there is no __init__.py; Python finds the package automatically).
│   ├── menu.py              #   MenuScene (main menu) + GateScene (gate cutscene).
│   ├── gate_light.py        #   GateLight: the little wandering light, its trail and dust particles.
│   ├── introduction.py      #   IntroScene: opening story with typewriter dialogue.
│   ├── characters.py        #   CharacterScene: placeholder character-selection page.
│   ├── info.py              #   InfoScene: generic text page used for Continue / Settings / About.
│   └── common.py            #   Shared drawing helpers: ease(), clamp(), draw_button(), draw_text_center().
│
├── assets/
│   └── menu/                # BG.png, gate_fence.png, left_gate.png, right_gate.png (1920x1080 source art).
│
├── data/
│   ├── settings.json        # Empty placeholder — reserved for saved settings. Not loaded by any code yet.
│   └── order.json           # Empty placeholder — reserved for future order data. Not loaded by any code yet.
│
├── docs/
│   ├── README.md            # Empty placeholder.
│   ├── algorithms.md        # Empty placeholder.
│   ├── data_structures.md   # Empty placeholder.
│   └── PROJECT_STRUCTURE.md # This guide.
│
└── tests/
    └── test_scene_flow.py   # Headless unittest checks for menu buttons, gate, and dialogue flow.
```

Files not listed (`.gitignore`, `env/`, `__pycache__/`, `.qoder/`) are tooling
and generated files. Never commit changes to `env/` or `__pycache__/`.

---

## 2. How the Game Works (the actual flow)

```text
python main.py
   └─> Game().run()                      # core/game.py
         ├─ pygame display + clock + fonts + AssetLoader created once
         └─ SceneManager created          # core/scene_manager.py
               └─ starts on screen "menu"
```

1. **Startup.** `main.py` calls `Game().run()`. `Game.__init__` (core/game.py)
   opens a 1200x675 scaled window, builds the shared `fonts` dict, creates one
   `AssetLoader` and one `SceneManager`. The manager's `scenes` dict already
   contains every screen, so all screens are constructed at startup.

2. **Main loop.** `Game.run()` repeats: read events → `scene_manager.handle_event`
   → `scene_manager.update(delta_time)` → `scene_manager.draw(screen, mouse_pos)`
   → flip. Frame time is smoothed with a running average so animation stays
   steady even on a slow frame.

3. **Main menu.** `MenuScene` (screens/menu.py) draws the gate artwork composed
   by `compose_scene()` and five buttons from `MENU_BUTTON_NAMES`.
   `MenuScene.handle_event` decides what each click does.

4. **Scene transitions.** Three ways, all through the scene manager:
   - `go_to(name)` — fade out, switch, fade in. Used by CONTINUE / SETTINGS /
     ABOUT US, BACK buttons, and Escape.
   - `set_scene(name)` — instant switch. Used only by START GAME to enter `GateScene`.
   - `show_scene(name, white_fade=True)` — switch under a full-screen cover.
     Used by the gate when its light has filled the screen.

5. **Gate cutscene.** `GateScene` ticks `elapsed` each frame and calls
   `MenuScene.draw_gate()`. Phases (all timings in settings.py): the
   `GateLight` prelude (appear → float → dart into the arch), door swing +
   camera zoom (`compose_scene` + `draw_camera`), then an expanding light mass
   until `GATE_ANIMATION_TIME`, when it calls
   `show_scene("intro", white_fade=True)`. Click / Space / Enter skips it.

6. **Story.** `IntroScene` (screens/introduction.py) types out lines from
   `INTRO_DIALOGUE` with a per-character reveal (`_draw_typed_text`). The first
   Space/click finishes the current line; the next advances. After the last
   line (or the SKIP button) it calls `go_to("character")`.

7. **Character selection.** `CharacterScene` (screens/characters.py) is only a
   placeholder page (it subclasses `InfoScene`). Real selection is not
   implemented yet.

8. **Back-to-menu / exit.** Escape returns to `"menu"` from any screen; Escape
   on the menu sets `game.running = False` and the loop ends.

There is currently **no gameplay loop**: no customers, orders, pizza building,
cooking, serving, scoring, or win/lose state. Those screens and systems have
to be created when that stage begins (see section 4).

---

## 3. Important Files and Functions

### `main.py`
- **Responsibility:** start the game. Nothing else lives here.
- **Key function:** `main()` → `Game().run()`.
- **Depends on:** `core/game.py`.
- **Edit it when:** you need new startup steps only. Almost never.

### `settings.py`
- **Responsibility:** single source of truth for window (WIDTH/HEIGHT/FPS),
  colors, menu layout (BUTTON_X, TITLE_Y…), fonts sizes, dialogue pacing
  (TYPE_SPEED, FADE_SPEED…), and every gate animation timing
  (GATE_LIGHT_*, GATE_OPEN_*, GATE_ZOOM_*, GATE_TOTAL_TIME…). Also defines
  `ASSETS_DIR`.
- **Depends on:** nothing (pure constants).
- **Edit it when:** changing any size, color, position, or animation speed.

### `core/game.py` — class `Game`
- **Responsibility:** own the window, clock, shared `warm_surface` fade layer,
  the `fonts` dict (`"title"`, `"button"`, `"label"`, `"small"`, `"dialogue"`,
  `"name"`), `assets`, `scene_manager`, and the main loop.
- **Key functions:** `__init__` (setup), `run` (event → update → draw loop).
- **Depends on:** `core/asset_loader.py`, `core/scene_manager.py`, `settings.py`.
- **Edit it when:** adding a globally shared resource (new font size, audio
  mixer, save-file object).

### `core/scene_manager.py` — class `SceneManager`
- **Responsibility:** the screen registry `self.scenes` (keys: `menu`, `gate`,
  `intro`, `character`, `continue`, `settings`, `about`), input routing, Escape
  handling, and the two fade systems (`screen_fade_state` "out"/"in", and
  `white_in_alpha` for the story reveal).
- **Key functions:** `handle_event`, `go_to` (fade), `set_scene` (instant),
  `show_scene` (under cover), `update`, `draw`.
- **Depends on:** every screen in `screens/`, `settings.py`.
- **Edit it when:** adding a new screen to the registry, or changing transition
  behavior.

### `core/asset_loader.py` — class `AssetLoader`
- **Responsibility:** load each image once and cache it. Cache key is
  `(subdirectory, filename, size)`. Raises a clear `FileNotFoundError` showing
  the expected path.
- **Key function:** `load_image(filename, size=None, subdirectory="menu")`.
- **Edit it when:** you need a new asset type (sounds, fonts from file).

### `screens/menu.py` — classes `MenuScene`, `GateScene`
- **Responsibility:** main menu buttons/layout, gate artwork composition
  (`_load_gate_artwork`, `compose_scene`), the zoom camera (`draw_camera`), the
  full cutscene frame (`draw_gate`), and the animation clock (`GateScene.update`).
- **Key functions:** `MenuScene.handle_event` (where button destinations are
  decided), `compose_scene` (door swing), `draw_camera` (zoom),
  `draw_gate` (one cutscene frame), `GateScene.restart`.
- **Depends on:** `screens/common.py`, `screens/gate_light.py`, `core/asset_loader`
  (via `game.assets`), `settings.py`.
- **Edit it when:** changing menu buttons/layout or gate animation behavior.

### `screens/gate_light.py` — class `GateLight` + helpers
- **Responsibility:** the small light in the cutscene prelude: kindle →
  wander → dive, with a fading trail and dust motes. Position is *analytic* —
  computed from the cutscene clock, not accumulated per frame.
- **Key functions:** `make_glow` / `make_streak` (soft light sprites),
  `reset` (rebuilds seeded sine path), `wander` (sine path position),
  `update` (phase switching + particles), `draw`.
- **Depends on:** `screens/common.py`, `settings.py`.
- **Edit it when:** changing the light's path, colors, or particles.

### `screens/introduction.py` — class `IntroScene`
- **Responsibility:** the opening story: backdrop rectangles, character
  placeholders, dialogue box, typewriter text, and BACK/SKIP/NEXT handling.
- **Key data:** `INTRO_DIALOGUE` — list of `(speaker, line)` tuples. Add or
  edit story lines here.
- **Key functions:** `handle_event` (records `advance_requested`), `update`
  (typing + fade state machine, line advance, ends with `go_to("character")`),
  `draw`, `_draw_typed_text` (per-letter fade-up), `_wrap_text` (word wrapping).
- **Depends on:** `screens/common.py`, `settings.py`.
- **Edit it when:** story content, dialogue pacing, or dialogue-box layout.

### `screens/info.py` — class `InfoScene`
- **Responsibility:** one reusable "heading + lines + BACK button" page.
  Instantiated three times in `scene_manager.py` (continue/settings/about)
  with different text and `back_target`.
- **Edit it when:** changing the look of those placeholder pages.

### `screens/characters.py` — class `CharacterScene`
- **Responsibility:** placeholder extending `InfoScene`. Replace with a real
  selection screen when character gameplay starts.

### `screens/common.py`
- **Responsibility:** shared helpers so screens don't duplicate drawing code:
  `ease` (smoothstep), `clamp`, `draw_text_center`, `draw_button`.
- **Edit it when:** you add a helper genuinely used by more than one screen.

### `tests/test_scene_flow.py`
- **Responsibility:** headless (SDL dummy driver) unittest checks that menu
  buttons go to the right screens, the gate finishes into the intro, the light
  wanders then dives, and dialogue advance finishes typing first.
- **Run with:** `python -m unittest discover -s tests -v`.
- **Edit it when:** you change screen behavior, and add tests for new systems.

---

## 4. Where to Make Changes

The gameplay rows are marked **"not implemented yet"** rather than pointing at
files that don't exist. Follow the README's plan: new gameplay code belongs in
a future `game/` package, not inside screens or `main.py`.

| If you want to... | Edit this file/folder | What to change |
|---|---|---|
| Change the main menu buttons | `screens/menu.py` | `MENU_BUTTON_NAMES`, button rects in `MenuScene.__init__`, click logic in `handle_event` |
| Move/resize menu elements | `settings.py` | `MENU_CENTER_X`, `TITLE_*`, `BUTTON_*` constants |
| Change menu colors | `settings.py` | `BACKGROUND`, `BUTTON_COLOR`, `BUTTON_HOVER`, `TITLE_COLOR` |
| Change a menu button's destination | `screens/menu.py` + `core/scene_manager.py` | The `destinations` dict in `MenuScene.handle_event`; the screen must exist in `SceneManager.scenes` |
| Change gate animation speed/phases | `settings.py` | `GATE_LIGHT_*`, `GATE_OPEN_*`, `GATE_ZOOM_*`, `GATE_TOTAL_TIME` |
| Change the wandering light's path | `screens/gate_light.py` | `wander()` sines; offsets/amplitudes in `settings.py` (`GATE_LIGHT_WANDER_*`) |
| Change story text | `screens/introduction.py` | `INTRO_DIALOGUE` list |
| Change dialogue typing speed | `settings.py` | `TYPE_SPEED`, `POP_LENGTH`, `POP_FADE`, `FADE_SPEED` |
| Change how scene fades look | `core/scene_manager.py` (+ `settings.py`) | `go_to` / `update` fade logic; `SCREEN_FADE_COLOR`, `SCREEN_FADE_SPEED` |
| Add a new screen | `screens/` + `core/scene_manager.py` | New class with `handle_event`/`update`/`draw`; register it in the `scenes` dict; reach it via `go_to("name")` |
| Change window resolution / FPS | `settings.py` | `WIDTH`, `HEIGHT`, `FPS` (layout uses `pygame.SCALED`, so constants stay logical) |
| Add fonts (sizes) | `core/game.py` | Entries in the `Game.fonts` dict; sizes in `settings.py` |
| Add images | `assets/<folder>/` | Put the file there, load via `game.assets.load_image("name.png", subdirectory="folder")` |
| Add sound / music | new code needed | **Not implemented yet** — no audio files or mixer code exist. Start in `core/game.py` and add files under `assets/audio/` |
| Add customers | new code needed | **Not implemented yet.** Create the customer logic as a module in a new `game/` package; show it through a new gameplay screen in `screens/` |
| Add customer patience timers | new code needed | **Not implemented yet.** Belongs with the future customer logic in `game/` |
| Add pizza toppings / ingredients | new code needed | **Not implemented yet.** `data/order.json` is an empty placeholder reserved for order data; wire it with a loader when gameplay starts |
| Change cooking time / pizza states | new code needed | **Not implemented yet.** Future cooking logic in `game/` |
| Change scoring, tips, satisfaction | new code needed | **Not implemented yet.** Future scoring logic in `game/` |
| Add save/load (Continue) | new code needed | **Not implemented yet.** Continue is a placeholder `InfoScene`; `data/settings.json` is reserved for it |
| Change shared button/text look | `screens/common.py` | `draw_button`, `draw_text_center` |

---

## 5. Contribution Guidelines

- **Put code in the right layer.** Infrastructure → `core/`, screens and their
  UI → `screens/`, future gameplay logic → a new `game/` package (create it
  with an `__init__.py` when gameplay starts). Do not put gameplay logic inside
  `scene_manager.py` or a screen file.
- **Screens stay independent.** A screen never imports another screen. Ask for
  a change with `game.scene_manager.go_to("name")`. Keep input, update, and
  draw inside `handle_event` / `update` / `draw`.
- **No magic numbers.** Sizes, colors, timings go in `settings.py`, not inline.
- **Reuse first.** Check `screens/common.py` before writing a new drawing
  helper, and `AssetLoader` before calling `pygame.image.load` yourself.
- **Assets:** reference them only through `game.assets.load_image(...)` so the
  cache works and missing files raise a helpful error. Keep paths relative to
  `assets/`.
- **Style:** match the file you are editing (PEP 8-ish, docstrings on modules
  and public functions, `snake_case` functions, `PascalCase` classes,
  `UPPER_CASE` settings constants). Note: `screens/introduction.py` and
  `screens/characters.py` use tabs; other files use 4 spaces — do not mix
  inside one file.
- **Don't touch unrelated systems** while adding a feature, and don't refactor
  working code in a feature PR.
- **Test:** run `python -m unittest discover -s tests -v` and play the affected
  screen manually before pushing. Add a test when you add screen behavior.

---

## 6. Data Structures and Algorithms Used

These are the structures/algorithms that actually exist in the code today.
Each one is real, small, and easy to point at in a CS 212a writeup.

| Name | Where | What it does in the game | Why it's useful |
|---|---|---|---|
| **Hash map (dict) scene registry** | `SceneManager.scenes` (core/scene_manager.py) | Maps screen name → screen object; `current_scene` looks up the active one. | O(1) screen switching and input routing without if-chains over screen names. |
| **Memoization / cache with composite key** | `AssetLoader._images` keyed by `(subdirectory, filename, size)` (core/asset_loader.py) | Each image is decoded and scaled once; later requests return the stored surface. | Avoids repeated disk reads and expensive `smoothscale` per frame. The same idea appears in `MenuScene._compose_key` and `_camera_key` (cache the last door/camera render and skip re-rendering until the key changes). |
| **Fixed-capacity ring buffer (`collections.deque(maxlen=…)`)** | `GateLight.trail` (screens/gate_light.py) | Keeps the last `GATE_TRAIL_SAMPLES` positions of the diving light; old positions fall off automatically. | Perfect sliding window for a fading trail — O(1) append, no manual trimming, bounded memory. |
| **Bounded particle list (simple object pool)** | `GateLight.particles`, cap `GATE_PARTICLE_CAP` (screens/gate_light.py) | Dust motes with position/velocity/life; dead ones are filtered out each frame in `_update_particles`. | Caps worst-case draw work per frame so the effect cannot slow the animation. |
| **State machines** | `GateLight` phases (`PHASE_APPEAR/FLOAT/DART/SPENT`); `SceneManager.screen_fade_state` ("none"/"out"/"in"); `IntroScene.fade_state` | Each frame the object reads its state, transitions by explicit rules, and behaves accordingly. | Makes complex timed sequences (cutscene, fades, dialogue) deterministic and testable. |
| **Smoothstep easing function** | `ease()` (screens/common.py), reused by `SceneManager._ease` | Maps linear 0–1 progress to an S-curve: `6t⁵ − 15t⁴ + 10t³`. | Gives doors, zoom, fades and the light a natural accelerate/decelerate feel instead of robotic linear motion. |
| **Layered sine wave (superposition) motion** | `GateLight.wander()` + seeded `_wave` pairs (frequency, phase) (screens/gate_light.py) | The light's wandering path is computed analytically as sums of sines plus a linear drift. | Position at any time is computed directly from the clock (no per-frame accumulation), so the cutscene is frame-rate independent and skippable/replayable exactly. |
| **Deterministic seeded PRNG** | `random.Random(seed)` in `GateLight.reset`, `MenuScene._make_gate_glow/_make_light_fingers` | Generates the light path, glow shape, and finger sprites from a fixed seed. | Every replay of the cutscene looks identical — important for reproducible tests (`tests/test_scene_flow.py` asserts on light positions). |
| **Greedy word-wrap algorithm** | `IntroScene._wrap_text` (screens/introduction.py) | Adds word by word until the line exceeds the box width, then breaks. | Fits dialogue into the box without hyphenation; simple and adequate for short lines. |
| **Exponential smoothing (moving average)** | `Game.run`: `delta_time = 0.8*prev + 0.2*raw` (core/game.py) | Blends the raw frame time into the game's delta time. | One slow frame no longer jerks the whole animation. |
| **Rectangle hit testing** | `pygame.Rect.collidepoint` in every button handler | Decides which button a click landed on. | Constant-time, standard UI interaction test. |
| **Rate accumulator (fractional carry)** | `GateLight._spawn_left` in `update` | Accumulates `rate * delta_time` motes and spawns whole ones. | Particle emission stays correct at any frame rate instead of "N per frame". |

Structures that are planned but **not yet implemented**: order queues,
customer/patience scheduling, recipe data, scoring — keep this table honest by
only adding entries when the code exists.

---

## 7. Quick Orientation Checklist for New Contributors

1. Run it: `pip install -r requirements.txt && python main.py`.
2. Open `settings.py` — this tells you what the game is made of (window, colors, timings).
3. Read `core/scene_manager.py` — 150 lines that explain every screen and every transition.
4. Read `screens/menu.py` `MenuScene.handle_event` — the one place clicks turn into screen changes.
5. Run the tests: `python -m unittest discover -s tests -v` — they show which behaviors are considered stable.
6. Want to add gameplay? Create the `game/` package first and keep screens as thin UI layers over it.
