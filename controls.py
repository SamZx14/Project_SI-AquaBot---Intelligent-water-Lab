"""Mouse, keyboard, and button actions."""

from rendering import pygame
import window
import playback
import animation


def action(app, key):
    if key in ("jug_view", "lab_view"):
        app.page = "jugs" if key == "jug_view" else "lab"
        app.focus = None
        app.playing = False
        app.animation_paused = True
        app.audio.stop()
        if app.page == "jugs":
            app.jug_page = app.index//6
        app.buttons.clear()
        app.fields = []
        return
    if key in ("jug_prev", "jug_next"):
        last = max(0, (len(app.result.states)-1)//6)
        app.jug_page = max(0, min(last, app.jug_page + (1 if key == "jug_next" else -1)))
        return
    if key in ("BFS", "DFS"):
        old = app.algorithm
        app.algorithm = key
        playback.compute(app)
        if app.error:
            app.algorithm = old
    elif key == "solve":
        app.focus = None
        playback.compute(app)
    elif key == "play":
        if tuple(app.values) != tuple(str(v) for v in app.config):
            playback.compute(app)
            if app.error:
                return
        if not app.result.states:
            return
        app.focus = None
        if app.index == len(app.result.states)-1 and app.drone.finished and not app.playing:
            playback.go(app, 0)
        app.playing = not app.playing
        app.animation_paused = not app.playing
        if app.playing and not app.drone_visible:
            app.drone_visible = True
            app.entry_target = app.drone.x
            app.entry_elapsed = 0.0
            app.drone.x = -120.0
    elif key in ("prev", "next", "reset"):
        app.playing = False
        playback.go(app, 0 if key == "reset" else app.index+(1 if key == "next" else -1))
    elif key == "speed":
        app.speed = {1: 2, 2: 0.5, 0.5: 1}[app.speed]
    elif key.startswith("step:"):
        app.playing = False
        playback.go(app, int(key.split(":")[1]))
    animation.sync_audio(app)


def event(app, event):
    if event.type == pygame.QUIT:
        app.running = False
    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        pos = window.mouse(app, event.pos)
        app.focus = next((i for i, r in enumerate(app.fields) if r.collidepoint(pos)), None)
        for key, (rect, enabled) in list(app.buttons.items()):
            if enabled and rect.collidepoint(pos):
                action(app, key)
                app.audio.click()
                break
    elif event.type == pygame.MOUSEWHEEL:
        if app.page == "jugs":
            action(app, "jug_next" if event.y < 0 else "jug_prev")
            return
        app.scroll = max(0, min(max(0, len(app.result.states)-7), app.scroll-event.y))
    elif event.type == pygame.KEYDOWN:
        if app.page == "jugs":
            if event.key == pygame.K_ESCAPE:
                action(app, "lab_view")
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                action(app, "jug_prev" if event.key == pygame.K_LEFT else "jug_next")
            return
        if event.key == pygame.K_ESCAPE:
            app.focus = None
        elif event.key == pygame.K_TAB:
            app.focus = 0 if app.focus is None else (app.focus+1)%3
        elif event.key == pygame.K_RETURN:
            action(app, "solve")
        elif app.focus is not None:
            if event.key == pygame.K_BACKSPACE:
                app.values[app.focus] = app.values[app.focus][:-1]
            elif event.unicode and event.unicode in "0123456789" and len(app.values[app.focus]) < 3:
                app.values[app.focus] += event.unicode
            app.playing = False
        elif event.key == pygame.K_SPACE:
            action(app, "play")
        elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
            action(app, "prev" if event.key == pygame.K_LEFT else "next")
        elif event.key == pygame.K_r:
            action(app, "reset")
