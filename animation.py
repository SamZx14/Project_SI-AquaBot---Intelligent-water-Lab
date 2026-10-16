"""Playback timing and sound cues."""

import playback


def sync_audio(app):
    complete = (len(app.result.states) > 1 and app.index == len(app.result.states)-1
                and app.transition >= 1 and app.entry_elapsed is None)
    app.audio.sync(app.drone.phase, arriving=app.entry_elapsed is not None,
                    paused=app.animation_paused, complete=complete)


def update(app, dt):
    advance_animation(app, dt)
    sync_audio(app)


def advance_animation(app, dt):
    app.time += dt
    if not app.result.states or app.animation_paused:
        return
    elapsed = max(0, dt*app.speed)
    if app.entry_elapsed is not None:
        used = min(elapsed, 1.6-app.entry_elapsed)
        app.entry_elapsed += used
        t = min(1.0, app.entry_elapsed/1.6)
        eased = t*t*(3-2*t)
        app.drone.x = -120+(app.entry_target+120)*eased
        if t < 1:
            return
        app.entry_elapsed = None
        elapsed -= used
    app.pipe_clock += elapsed
    speed = 165.0
    app.pipe_runs = [(a+speed*elapsed, b+speed*elapsed)
                      for a, b in app.pipe_runs if a+speed*elapsed < 320]
    # Water already in the pipe keeps moving after the jug stops draining.
    start_time = app.drone.total_elapsed
    leftover = app.drone.advance(elapsed)
    end_time = app.drone.total_elapsed
    stage_start = 0.0
    for stage in app.drone.stages:
        stage_end = stage_start+stage.duration
        if stage.kind in ("empty", "drain"):
            begin, end = max(start_time, stage_start), min(end_time, stage_end)
            if end > begin:
                app.pipe_runs.append((speed*(elapsed-(end-start_time)),
                                       speed*(elapsed-(begin-start_time))))
        stage_start = stage_end
    merged = []
    for a, b in sorted(app.pipe_runs):
        if merged and a <= merged[-1][1]+0.01:
            merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
        else:
            merged.append((a, b))
    app.pipe_runs = merged
    app.water = app.drone.water[:]
    app.transition = app.drone.progress
    if app.playing and app.drone.finished:
        app.hold += leftover
        if app.hold >= 0.7:
            if app.index < len(app.result.states)-1:
                playback.go(app, app.index+1)
            else:
                app.playing = False
