# SI AquaBot — Intelligent Water Jug Lab

A Python/Pygame water-jug solver with BFS and DFS, adjustable capacities, and
animated solution playback. A drone collects water from the supply tank, fills
the jugs, and uses mechanical arms to lift and pour them. The lab includes a
clickable solution timeline, a separate jug-state view, moving space scenery,
and sound effects. Pause freezes the current operation; Reset clears playback
and returns the drone to the supply station.

## Run

On this computer, double-click **Run Water Lab.cmd**. The prepared environment is already installed in the working folder.

For a fresh installation, use Python **3.10–3.13** (3.12 recommended; the pinned Pygame release may lack wheels for newer Python versions):

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

On macOS/Linux, use `python3 -m venv .venv`, then `.venv/bin/python -m pip install -r requirements.txt` and `.venv/bin/python main.py`.

## Controls

The main and side cabin windows share one continuous, slow space journey with layered parallax.
The aqua laboratory has independently animated aquarium bubbles, gentle water ripples,
refractive movement, and circulation highlights following the transparent plumbing.
Ambient lab water continues while solution playback is paused and does not change
with playback speed. Foreground equipment remains in front of the window view.
Earth, Mars, rocky and icy moons, gas giants, ringed planets, satellites and
asteroids occupy an irregular field at varied depths. Distant galaxies and
nebulae drift almost imperceptibly; occasional comets and brief meteor streaks
have separate, irregular timing. The scenery runs independently of simulation
playback speed. Space artwork is bundled in `assets`.

The eight bundled recordings in `assets/sounds` accompany draining, drone flight,
robotic arm movement, filling jugs from the drone, jug-to-jug pouring, suction at
the supply, goal completion, clicks on enabled buttons, and red error banners.
The error clip plays once per invalid submission or zero-step result, including
unreachable targets, target zero, and repeated attempts. Zero-step results do not
also play the goal-completion sound.
Drone-to-jug and jug-to-jug pouring share the same water-falling recording.
Operation sounds loop only during their matching animation. Pause suspends audio;
Reset and timeline changes stop the previous sound. The goal sound plays once per
completion. If no audio device is available, the simulation continues silently.


1. Enter jug capacities (1–100 liters) and a target (0–100 liters). Click a field and use Backspace to replace its value. Tab moves between fields.
2. Select **BFS** or **DFS**, then click **Find solution** or press Enter.
3. Press **Play** to animate, or use **Back**, **Next**, and the timeline to inspect states. Scroll to view long solutions. The target is shown below the workspace.
4. Change playback speed between 0.5x, 1x and 2x. Resize the window as needed.
5. Click **Jug view >** beside **Solution Sequence** to open a separate page showing solution states as pairs of jugs with proportional water levels instead of dots. Arrows connect the steps and gold highlights the goal. Longer paths have Previous/Next pages (also available with the mouse wheel or arrow keys). **Back to lab** or Escape returns to the workspace. Opening this view pauses playback.

Keyboard: **Space** plays/pauses, **Left/Right** step, **R** resets playback, **Escape** leaves a field. Playback shortcuts apply when no field is focused.

## Algorithm

A state `(x, y)` stores the amount in each jug. Search starts at `(0, 0)` and succeeds when **either jug** contains the target, not the combined amount. Legal moves are filling either jug, emptying either jug, and pouring one into the other until the source empties or destination fills. Assume unlimited water and a drain.

- **BFS** uses a FIFO queue and guarantees the fewest operations because every edge costs one step.
- **DFS** uses a LIFO stack; it finds a valid solution but need not find the shortest one.
- A discovered-state map prevents cycles and stores parent links for path reconstruction.
- A target is reachable exactly when it fits a jug and is divisible by `gcd(a, b)`. Target zero is already solved.
- There are at most `(a+1)(b+1)` states and six moves per state. Time and memory are bounded by `O(a*b)`.

Example: capacities 4 L and 3 L, target 2 L. BFS finds four operations: fill B → pour B into A → fill B → pour B into A, finishing at `(4, 2)`.

The explored count measures states removed from the queue/stack. The timeline shows the reconstructed solution, not every explored state. Search timing excludes animation. Edited fields leave the previous solution visible until you apply the values.

## Project files

`main.py` starts `WaterLab` from `app.py`. The application holds the current state
and calls the modules below. Drawing and control functions receive that state as
`app`, so playback, sounds, and both screens use the same values.

| File | Responsibility |
| --- | --- |
| `main.py` | Launch the app and read command-line options. |
| `app.py` | Application state and the main event loop. |
| `settings.py` | Shared colors and layout measurements. |
| `window.py` | Window setup, artwork loading, resizing, and mouse coordinates. |
| `controls.py` | Keyboard, mouse, and button actions. |
| `playback.py` | Run the solver, reset playback, and select solution steps. |
| `animation.py` | Advance playback and synchronize sound cues. |
| `sound.py` | Load recordings and play, pause, or stop sound effects. |
| `lab_view.py` | Main lab screen, input fields, and solution timeline. |
| `jug_view.py` | Separate page showing solution states as pairs of jugs. |
| `widgets.py` | Shared buttons, text, icons, and glass panels. |
| `jug.py` | Upright and carried jugs, water levels, and pouring arcs. |
| `drone.py` | Plan and advance drone movements and water operations. |
| `drone_view.py` | Draw the drone, rotors, tube, and water stream. |
| `arms.py` | Draw the mechanical arms gripping a jug. |
| `stations.py` | Draw the supply tank, drain, and wastewater pipe. |
| `orbit.py` | Moving space scenery behind the cabin windows. |
| `waterfx.py` | Ambient aquarium and plumbing effects. |
| `rendering.py` | Scale drawing coordinates to the current display size. |
| `solver.py` | Independent BFS/DFS search. |

`assets/` contains the required artwork, recordings, and sound source notes.
`tests/` checks the solver, controls, playback, rendering, water effects, and sounds.
`requirements.txt` pins the Pygame dependency. `Run Water Lab.cmd` starts the app
using a virtual environment in this folder or its parent.

## Verification

Run these from the folder containing `main.py`. The prepared environment is in
the parent folder; a fresh installation may instead have `.venv` in this folder.

```powershell
$labPython = '.\.venv\Scripts\python.exe'
if (!(Test-Path $labPython)) { $labPython = '..\.venv\Scripts\python.exe' }
& $labPython -B -m unittest discover -s tests -v
& $labPython -B main.py --smoke-test
```

For a display-free smoke test set `$env:SDL_VIDEODRIVER='dummy'` first.

Pygame API reference: [official documentation](https://www.pygame.org/docs/).

© Samira Ibrahim. All rights reserved.
