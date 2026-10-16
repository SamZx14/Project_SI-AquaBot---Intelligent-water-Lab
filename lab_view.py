"""The main lab screen and solution timeline."""

from rendering import pygame
import widgets
import window
import stations
import drone_view
import jug
import jug_view
from settings import ACCENT, BG, JUG_X, MUTED, TEAL, WATER_A, WATER_B, WHITE


def draw(app):
    window.resize_rendering(app)
    if app.page == "jugs":
        jug_view.draw_jug_view(app)
        return
    app.orbit.draw(app.background.raw, app.time)
    app.lab_water.draw(app.background.raw, app.time)
    # Refresh the frosted background 12 times a second.
    tick = int(app.time*12)
    if tick != app.frost_tick:
        app.frost_cache.clear()
        app.frost_tick = tick
    app.buttons.clear()
    app.canvas.blit(app.background, (0, 0))
    app.canvas.blit(app.header_logo, (20, 2))
    title = app.fonts[32].render("SI AquaBot — Intelligent Water Lab", True, WHITE)
    gold = pygame.Surface(title.get_size(), pygame.SRCALPHA)
    for yy in range(title.get_height()):
        t = yy/max(1, title.get_height()-1)
        pygame.draw.line(gold, (255, int(230-58*t), int(163-86*t), 255), (0, yy), (title.get_width(), yy))
    title.blit(gold, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    widgets.text(app, "SI AquaBot — Intelligent Water Lab", (111, 20), 32, (39, 26, 13))
    app.canvas.blit(title, (110, 18))
    widgets.text(app, "Created by Samira-Ibrahim", (112, 59), 14, (210, 221, 224))
    widgets.draw_mode_badge(app)
    pygame.draw.line(app.canvas, (73, 105, 119), (32, 91), (1168, 91))
    widgets.box(app, (32, 108, 1136, 111))
    app.fields = []
    for i, (label, x) in enumerate(zip(("Jug A (liters)", "Jug B (liters)", "Target (liters)"), (52, 188, 324))):
        widgets.text(app, label, (x, 124), 14, MUTED)
        rect = pygame.Rect(x, 148, 116, 48)
        app.fields.append(rect)
        widgets.box(app, rect, BG, 9)
        pygame.draw.rect(app.canvas, (67, 102, 120), rect, 1, border_radius=9)
        pygame.draw.line(app.canvas, (67, 102, 120), (x+12, 191), (x+104, 191))
        widgets.text(app, "L", (x+91, 164), 14, MUTED)
        if app.focus == i:
            widgets.box(app, rect, ACCENT, 9, 2)
        widgets.text(app, app.values[i]+("|" if app.focus == i and int(app.time*2)%2 == 0 else ""), (x+15, 153), 24)
    widgets.text(app, "Choose a search method", (476, 124), 14, MUTED)
    widgets.button(app, "BFS", "BFS (shortest)", (476, 148, 153, 48), app.algorithm == "BFS")
    widgets.button(app, "DFS", "DFS (depth first)", (638, 148, 160, 48), app.algorithm == "DFS")
    widgets.button(app, "solve", "Find solution", (928, 148, 218, 48), True)
    widgets.section_icon(app, "lab",52,239)
    widgets.text(app, "SI AQUA WORKSPACE", (79, 241), 14, ACCENT)
    widgets.box(app, (32, 274, 656, 343))
    stations.draw_stations(app)
    jug.draw_jug(app, JUG_X[0], app.config[0], app.water[0], "Jug A", WATER_A)
    jug.draw_jug(app, JUG_X[1], app.config[1], app.water[1], "Jug B", WATER_B)
    drone_view.draw_drone(app)
    widgets.box(app, (32, 627, 656, 104), BG, 12)
    widgets.text(app, f"Target: {app.config[2]} liters in either jug", (52, 636), 20, ACCENT)
    action = app.result.actions[app.index] if app.result.states else "No reachable goal"
    if app.entry_elapsed is not None:
        action = "Drone arriving from the left"
    elif not app.drone.finished:
        action = app.drone.description
    complete = bool(app.result.states) and app.index == len(app.result.states)-1 and app.transition >= 1
    if complete:
        if int(app.time / 0.6) % 2 == 0:
            widgets.neon_text(app, "Goal reached!", (52, 668), 24, ACCENT)
    else:
        widgets.text(app, action, (52, 668), 24)
    state = app.result.states[app.index] if app.result.states else None
    widgets.text(app, f"State: {state}" if state else "Try another target or jug capacity.", (52, 706), 16, MUTED)
    widgets.box(app, (712, 239, 456, 474))
    widgets.section_icon(app, "sequence",734,256)
    widgets.text(app, "SOLUTION SEQUENCE", (762, 258), 14, TEAL)
    widgets.button(app, "jug_view", "Jug view >", (1034, 249, 112, 32))
    n = len(app.result.states)
    widgets.text(app, f"{max(0, n-1)} steps", (734, 285), 32)
    widgets.text(app, f"{app.result.explored} states | {app.result.elapsed_ms:.2f} ms", (906, 300), 14, MUTED)
    widgets.text(app, app.result.message, (734, 331), 16, ACCENT if n else (255, 177, 120))
    for row, i in enumerate(range(app.scroll, min(n, app.scroll+7))):
        y = 365+row*43
        active = i == app.index
        widgets.button(app, f"step:{i}", "", (730, y, 416, 38), active)
        ink = WHITE if active else MUTED
        widgets.text(app, f"{i:02}", (742, y+8), 14, ink)
        widgets.text(app, app.result.actions[i], (782, y+7), 16, WHITE)
        widgets.text(app, str(app.result.states[i]), (1056, y+8), 14, ink)
    if not n:
        widgets.text(app, "A target is possible when it fits", (736, 386), 18, MUTED)
        widgets.text(app, "a jug and is divisible by the GCD", (736, 416), 18, MUTED)
        widgets.text(app, "of the two jug capacities.", (736, 446), 18, MUTED)
    widgets.button(app, "reset", "Reset", (32, 746, 83, 38), enabled=bool(n))
    widgets.button(app, "prev", "< Back", (124, 746, 86, 38), enabled=app.index > 0)
    widgets.button(app, "play", "Pause" if app.playing else "Play", (219, 746, 105, 38), True, bool(n) or tuple(app.values) != tuple(str(v) for v in app.config))
    widgets.button(app, "next", "Next >", (333, 746, 86, 38), enabled=bool(n) and app.index < n-1)
    widgets.button(app, "speed", f"{app.speed:g}x speed", (429, 746, 102, 38))
    widgets.draw_shortcuts(app)
    if app.error:
        widgets.box(app, (32, 710, 656, 31), (91, 48, 65), 7)
        widgets.text(app, app.error, (42, 715), 14, (255, 217, 197))
    elif tuple(app.values) != tuple(str(v) for v in app.config):
        widgets.text(app, "Values changed. Click Find solution.", (290, 710), 14, (255, 194, 110))
    pointer = any(rect.collidepoint(window.mouse(app)) and enabled
                  for rect, enabled in app.buttons.values())
    try:
        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if pointer else pygame.SYSTEM_CURSOR_ARROW)
    except pygame.error:
        pass  # The dummy display has no cursor.
    app.window.fill(BG)
    app.canvas.present(app.window)
    pygame.display.flip()
