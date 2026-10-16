"""Drone artwork, rotors, tube, and water stream drawing."""

import math
from rendering import pygame
import jug
from settings import DRONE_NOZZLE_Y, DRONE_Y, H, JUG_BOTTOM, W


def tube_tip(app):
    if not app.drone.stage:
        return DRONE_NOZZLE_Y
    site = app.drone.stage.site
    bottom = JUG_BOTTOM-8 if isinstance(site, int) else 532
    return DRONE_NOZZLE_Y+(bottom-DRONE_NOZZLE_Y)*app.drone.tube


def draw_drone(app):
    if not app.drone_visible:
        return
    x = app.drone.x
    bob = math.sin(app.time*3)*1.4
    lift = min(1, max(0, -app.drone.pose[1]/110))
    top = DRONE_Y-58*lift+bob
    app.canvas.blit(app.drone_art, (round(x)-93, round(top)))
    cargo = max(0, min(1, app.drone.cargo/max(app.config[:2])))
    if cargo > 0:
        tank = pygame.Surface((28, 26), pygame.SRCALPHA)
        h = max(1, int(24*cargo))
        pygame.draw.rect(tank, (79, 174, 205, 100), (0, 26-h, 28, h), border_radius=3)
        pygame.draw.line(tank, (199, 238, 249, 155), (1, 26-h), (26, 26-h), 1)
        app.canvas.blit(tank, (round(x)-12, round(top)+44))
    rotors = pygame.Surface((W, H), pygame.SRCALPHA)
    for ox, oy, radius in ((-53, 6, 40), (53, 6, 40), (-61, 30, 31), (62, 30, 31)):
        cx, cy = x+ox, top+oy
        pygame.draw.ellipse(rotors, (185, 207, 219, 38), (cx-radius, cy-4, radius*2, 8))
        angle = app.time*95+ox
        dx, dy = math.cos(angle)*radius, math.sin(angle)*3
        pygame.draw.line(rotors, (220, 232, 239, 90), (cx-dx, cy-dy), (cx+dx, cy+dy), 2)
    app.canvas.blit(rotors, (0, 0))
    start = DRONE_NOZZLE_Y+bob
    tip = tube_tip(app)
    if app.drone.tube > 0:
        pygame.draw.line(app.canvas, (31, 37, 44), (x, start), (x, tip), 7)
        pygame.draw.line(app.canvas, (143, 170, 189), (x-1, start), (x-1, tip), 3)
        pygame.draw.rect(app.canvas, (179, 194, 200), (int(x)-4, int(tip)-7, 8, 8), border_radius=2)
        if app.drone.phase == "refill" and not app.animation_paused:
            for i in range(9):
                yy = tip-((app.time*100+i*23)%max(1, tip-start))
                pygame.draw.line(app.canvas, (112, 220, 244), (x, yy), (x, min(yy+7, tip)), 2)
    if app.drone.phase not in ("pour", "drain") or app.animation_paused:
        return
    site = app.drone.stage.site
    surface_y = jug.water_surface(app, site) if isinstance(site, int) else 535
    draw_stream(app, x, start+2, surface_y)


def draw_stream(app, end, start_y, surface_y):
    stream = pygame.Surface((W, H), pygame.SRCALPHA)
    left, right = [], []
    for yy in range(int(start_y), max(int(start_y)+1, int(surface_y))+1, 3):
        sway = math.sin(yy*0.085-app.time*16)*0.8
        left.append((end-3+sway, yy))
        right.append((end+3+sway, yy))
    pygame.draw.polygon(stream, (139, 212, 234, 170), left+right[::-1])
    pygame.draw.lines(stream, (227, 250, 255, 190), False,
                      [(end+math.sin(yy*0.085-app.time*16)*0.8, yy) for _, yy in left], 2)
    pygame.draw.ellipse(stream, (198, 239, 249, 110), (end-12, surface_y-2, 24, 5), 1)
    for i in range(6):
        phase = (app.time*3+i/6)%1
        direction = -1 if i%2 else 1
        dx = direction*(4+phase*17)
        dy = -math.sin(phase*math.pi)*9
        pygame.draw.circle(stream, (198, 239, 249, int(145*(1-phase))),
                           (int(end+dx), int(surface_y+dy)), 1)
    app.canvas.blit(stream, (0, 0))
