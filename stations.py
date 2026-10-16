"""Supply tank, drain, and wastewater pipe drawing."""

import math
from rendering import pygame
from drone import DRAIN_X, SUPPLY_X
from settings import ACCENT, H, MUTED, W


def render_supply_tank():
    """Build the supply tank image for reuse between frames."""
    def surface():
        art = pygame.Surface((76, 160), pygame.SRCALPHA)
        art.scale = tuple(value*3 for value in art.scale)
        art.raw = pygame.Surface((228, 480), pygame.SRCALPHA).raw
        return art

    tank = surface()
    pygame.draw.ellipse(tank, (0, 8, 13, 90), (2, 146, 72, 10))
    body = surface()
    pygame.draw.rect(body, (54, 92, 104, 52), (6, 8, 64, 140), border_radius=14)
    water = surface()
    for yy in range(41, 144):
        depth = (yy-41)/103
        pygame.draw.line(water, (int(120-62*depth), int(199-46*depth),
                                int(220-30*depth), 158), (11, yy), (65, yy))
    pygame.draw.ellipse(water, (159, 221, 237, 150), (11, 37, 54, 8))
    pygame.draw.ellipse(water, (222, 242, 245, 105), (11, 37, 54, 8), 1)
    water_mask = surface()
    pygame.draw.rect(water_mask, (255, 255, 255, 255), (11, 18, 54, 127), border_radius=12)
    water.blit(water_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    body.blit(water, (0, 0))
    reflection = surface()
    for xx in range(10, 67):
        light = int(95*math.exp(-((xx-19)/4)**2)+36*math.exp(-((xx-57)/5)**2))
        pygame.draw.line(reflection, (219, 241, 242, light), (xx, 20), (xx, 139))
    body.blit(reflection, (0, 0))
    body_mask = surface()
    pygame.draw.rect(body_mask, (255, 255, 255, 255), (6, 8, 64, 140), border_radius=14)
    body.blit(body_mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    tank.blit(body, (0, 0))
    pygame.draw.rect(tank, (86, 117, 131, 190), (7, 12, 62, 134), 2, border_radius=13)
    # Clip the bands to the rounded tank ends.
    for yy in (7, 139):
        collar = surface()
        for row in range(14):
            light = int(66+120*math.exp(-((row-4)/3)**2))
            pygame.draw.line(collar, (light, light+8, min(255, light+12), 245),
                             (3, yy+row), (73, yy+row))
        mask = surface()
        pygame.draw.ellipse(mask, (255, 255, 255, 255), (3, yy, 70, 14))
        collar.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        tank.blit(collar, (0, 0))
        pygame.draw.ellipse(tank, (34, 49, 56, 230), (3, yy, 70, 14), 1)
        pygame.draw.ellipse(tank, (192, 209, 210, 240), (4, yy, 68, 9), 1)
        pygame.draw.ellipse(tank, (233, 239, 230, 150), (8, yy+1, 60, 5), 1)
        for xx in (9, 65):
            pygame.draw.circle(tank, (29, 39, 45), (xx, yy+7), 2)
            pygame.draw.circle(tank, (186, 203, 205), (xx, yy+6), 1)
    pygame.draw.ellipse(tank, (25, 47, 56, 190), (8, 5, 60, 7))
    pygame.draw.ellipse(tank, (211, 231, 232, 210), (7, 4, 62, 9), 1)
    return pygame.transform.smoothscale(tank, (76, 160))


def draw_stations(app):
    if app.supply_tank_art is None:
        app.supply_tank_art = render_supply_tank()
    app.canvas.blit(app.supply_tank_art, (int(SUPPLY_X)-38, 392))
    # The supply water keeps moving while playback is paused.
    surface = pygame.Surface((54, 10), pygame.SRCALPHA)
    for band in range(2):
        wave = [(x, 4+band*2+math.sin(x*.13+app.time*1.5+band)*.65)
                for x in range(2, 52)]
        pygame.draw.lines(surface, (190, 236, 246, 65-band*20), False, wave, 1)
    app.canvas.blit(surface, (int(SUPPLY_X)-27, 429))
    draw_drain_pipe(app)
    drain = pygame.Surface((54, 30), pygame.SRCALPHA)
    pygame.draw.ellipse(drain, (0, 7, 12, 100), (0, 8, 54, 22))
    pygame.draw.ellipse(drain, (30, 39, 45), (2, 5, 50, 22))
    pygame.draw.ellipse(drain, (173, 185, 188), (2, 3, 50, 22))
    pygame.draw.ellipse(drain, (224, 231, 229), (3, 3, 48, 19),1)
    pygame.draw.ellipse(drain, (80, 101, 112), (6, 6, 42, 16))
    pygame.draw.ellipse(drain, (15, 26, 34), (9, 8, 36, 12))
    pygame.draw.ellipse(drain, (124, 147, 156), (10, 8, 34, 11),1)
    for i in range(5):
        pygame.draw.line(drain, (27, 35, 40), (16+i*5, 10), (13+i*5, 18),3)
        pygame.draw.line(drain, (183, 199, 202), (15+i*5, 9), (12+i*5, 17),2)
        pygame.draw.line(drain, (226, 232, 231), (15+i*5, 9), (12+i*5, 16),1)
    for xx, yy in ((8, 13), (46, 13), (27, 5), (27, 22)):
        pygame.draw.circle(drain, (203, 220, 224), (xx, yy), 1)
    app.canvas.blit(drain, (DRAIN_X-27, 522))
    for label, center in (("Supply Tank", SUPPLY_X), ("Drain", DRAIN_X)):
        caption = app.fonts[14].render(label, True, MUTED)
        app.canvas.blit(caption, caption.get_rect(midtop=(center, 558 if label == "Supply Tank" else 566)))
    onboard = app.fonts[14].render(f"Onboard: {app.drone.cargo:.1f} L", True, MUTED)
    app.canvas.blit(onboard, onboard.get_rect(midtop=(SUPPLY_X, 578)))


def draw_drain_pipe(app):
    if not app.pipe_runs and app.empty_pipe is not None:
        app.canvas.blit(app.empty_pipe, (0, 0))
        return
    # Route the pipe around the drain label.
    points = [(DRAIN_X, 540), (DRAIN_X, 546)]
    # Match the curve tangents to the straight pipe sections.
    for i in range(1, 49):
        t = i/48
        u = 1-t
        points.append((DRAIN_X+22*(3*u*t*t+t*t*t),
                       u**3*546+3*u*u*t*559+3*u*t*t*560+t**3*573))
    points.append((DRAIN_X+22, 590))
    for i in range(1, 49):
        angle = i/48*math.pi/2
        points.append((DRAIN_X+8+14*math.cos(angle), 590+14*math.sin(angle)))
    points.append((44, 604))
    pipe = pygame.Surface((W, H), pygame.SRCALPHA)
    def rounded_path(target, color, path, width):
        key = (color, tuple(path), width)
        if key in app.pipe_path_cache:
            art, position = app.pipe_path_cache[key]
            target.blit(art, position)
            return
        # Draw at 3x size, then shrink to smooth the pipe joints.
        left = math.floor(min(x for x, y in path)-width)
        top = math.floor(min(y for x, y in path)-width)
        right = math.ceil(max(x for x, y in path)+width)
        bottom = math.ceil(max(y for x, y in path)+width)
        size = (right-left+1, bottom-top+1)
        detail = pygame.Surface((size[0]*3, size[1]*3), pygame.SRCALPHA)
        scaled = [((x-left)*3, (y-top)*3) for x, y in path]
        pygame.draw.lines(detail, color, False, scaled, width*3)
        for point in scaled[1:-1]:
            pygame.draw.circle(detail, color, point, width*1.5)
        art = pygame.transform.smoothscale(detail, size)
        app.pipe_path_cache[key] = (art, (left, top))
        target.blit(art, (left, top))
    rounded_path(pipe, (19, 25, 30, 240), points, 13)
    rounded_path(pipe, (113, 170, 188, 195), points, 10)
    rounded_path(pipe, (13, 40, 55, 235), points, 7)
    rounded_path(pipe, (180, 212, 224, 80), [(x-2, y-2) for x, y in points], 1)
    distances = [0.0]
    for a, b in zip(points, points[1:]):
        distances.append(distances[-1]+math.dist(a, b))
    def sample(distance):
        for j in range(1, len(points)):
            if distance <= distances[j]:
                a, b = points[j-1], points[j]
                span = max(.001, distances[j]-distances[j-1])
                t = (distance-distances[j-1])/span
                return (a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t,
                        -(b[1]-a[1])/span, (b[0]-a[0])/span)
        return (*points[-1], 0, -1)
    fluid = pygame.Surface((W, H), pygame.SRCALPHA)
    mask = pygame.Surface((W, H), pygame.SRCALPHA)
    rounded_path(mask, (255, 255, 255), points, 7)
    for tail, head in app.pipe_runs:
        low, high = max(0, tail), min(distances[-1], head)
        if high <= low:
            continue
        samples = [sample(low+i*(high-low)/max(1, int((high-low)/2)))
                   for i in range(max(1, int((high-low)/2))+1)]
        centerline = [(x, y) for x, y, _, _ in samples]
        pygame.draw.lines(fluid, (56, 145, 178, 205), False, centerline, 6)
        shimmer = []
        for i, (x, y, nx, ny) in enumerate(samples):
            distance = low+i*(high-low)/max(1, len(samples)-1)
            ripple = .6*math.sin(distance*.12-app.pipe_clock*12)
            shimmer.append((x+nx*(-1.2+ripple), y+ny*(-1.2+ripple)))
        pygame.draw.lines(fluid, (169, 225, 239, 115), False, shimmer, 1)
        for seed in range(7):
            distance = (app.pipe_clock*165+seed*37+11*math.sin(seed*2))%distances[-1]
            if low+3 < distance < high-3:
                x, y, nx, ny = sample(distance)
                offset = math.sin(seed*5)*1.3
                pygame.draw.circle(fluid, (217, 244, 248, 100),
                                   (x+nx*offset, y+ny*offset), 1, 1)
        if tail < distances[-1] < head:
            for seed in range(5):
                t = (app.pipe_clock*2.4+seed*.21)%1
                pygame.draw.circle(pipe, (135, 213, 237, int(130*(1-t))),
                                   (44-5*t, 604+8*t*t), 1)
    fluid.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    pipe.blit(fluid, (0, 0))
    for yy in (582, 588):
        pygame.draw.line(pipe, (169, 183, 191, 220), (DRAIN_X+16, yy), (DRAIN_X+28, yy), 2)
    pygame.draw.line(pipe, (169, 183, 191, 220), (48, 598), (48, 610), 2)
    for cx in (71, 158):
        pygame.draw.rect(pipe, (18, 28, 38), (cx-4, 597, 8, 14), border_radius=2)
        pygame.draw.rect(pipe, (131, 163, 178), (cx-4, 597, 8, 14), 1, border_radius=2)
        pygame.draw.line(pipe, ACCENT, (cx, 600), (cx, 608), 2)
    if not app.pipe_runs:
        app.empty_pipe = pipe
    app.canvas.blit(pipe, (0, 0))
