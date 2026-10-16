"""Solve the current inputs and move between solution steps."""

from solver import solve
from drone import DroneController


def compute(app):
    app.audio.stop()
    app.playing = False
    try:
        a, b, target = map(int, app.values)
        result = solve(a, b, target, app.algorithm)
    except ValueError as exc:
        app.error = str(exc) if all(v.isdigit() for v in app.values) else "Enter a whole number in every field."
        app.audio.error()
        return
    app.error = ""
    app.config = (a, b, target)
    app.result = result
    if len(result.states) <= 1:
        app.audio.error()
    app.index = app.scroll = 0
    app.jug_page = 0
    app.water = [0.0, 0.0]
    app.transition, app.hold = 1.0, 0.0
    app.drone = DroneController()
    app.drone_visible = False
    app.entry_elapsed = None
    app.pipe_runs = []
    app.pipe_clock = 0.0
    app.animation_paused = False


def go(app, index):
    if not app.result.states:
        return
    app.audio.stop()
    if app.entry_elapsed is not None:
        app.drone.x = app.entry_target
        app.entry_elapsed = None
    app.index = max(0, min(index, len(app.result.states)-1))
    app.transition = app.hold = 0.0
    app.animation_paused = False
    if app.index == 0:
        app.drone.reset()
        app.drone_visible = False
        app.entry_elapsed = None
        app.pipe_runs = []
        app.pipe_clock = 0.0
        app.water = app.drone.water[:]
        app.transition = 1.0
    else:
        app.drone_visible = True
        app.drone.start(app.result.states[app.index])
    app.scroll = min(max(0, len(app.result.states)-7), max(0, app.index-3))
