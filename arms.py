"""Mechanical arms that grip and carry a jug."""

import math

from rendering import pygame
from settings import DRONE_Y, H, W


def draw(app, point, grip):
    arm_layer = pygame.Surface((W, H), pygame.SRCALPHA)
    def metal_link(a, b, width):
        vx, vy = b[0]-a[0], b[1]-a[1]
        length = max(1, math.hypot(vx, vy))
        nx, ny = -vy/length, vx/length
        def offset(p, distance):
            return (p[0]+nx*distance, p[1]+ny*distance)
        pygame.draw.line(arm_layer, (16, 20, 24), a, b, width+3)
        for radius, color in ((width, (63, 69, 72)), (width-2, (110, 117, 119)),
                              (max(2, width-5), (161, 168, 169))):
            pygame.draw.line(arm_layer, color, offset(a, -0.8), offset(b, -0.8), radius)
        pygame.draw.line(arm_layer, (226, 229, 221), offset(a, -width*.25), offset(b, -width*.25), 1)
        pygame.draw.line(arm_layer, (39, 44, 47), offset(a, width*.28), offset(b, width*.28), 2)
    def bearing(center, radius):
        pygame.draw.circle(arm_layer, (20, 24, 27), center, radius+1)
        pygame.draw.circle(arm_layer, (92, 100, 103), center, radius)
        pygame.draw.circle(arm_layer, (194, 199, 194), (center[0]-1, center[1]-1), radius-1)
        pygame.draw.circle(arm_layer, (61, 69, 72), center, max(2, radius-3))
        pygame.draw.circle(arm_layer, (137, 147, 151), center, 2)
        for angle in (0, math.pi):
            bolt = (center[0]+math.cos(angle)*(radius-2), center[1]+math.sin(angle)*(radius-2))
            pygame.draw.circle(arm_layer, (31, 37, 39), bolt, 1)
    lift = min(1, max(0, -app.drone.pose[1]/110))
    body_y = DRONE_Y-58*lift+math.sin(app.time*3)*1.4
    for side in (-1, 1):
        shoulder = (app.drone.x+side*23, body_y+63)
        contact = point(side*80, -12)
        folded = (app.drone.x+side*31, body_y+83)
        hand = tuple(a+(b-a)*grip for a, b in zip(folded, contact))
        elbow = (shoulder[0]+side*(16+15*grip), (shoulder[1]+hand[1])/2)
        pygame.draw.rect(arm_layer, (26, 30, 32), (shoulder[0]-8, shoulder[1]-7, 16, 12), border_radius=3)
        pygame.draw.line(arm_layer, (190, 195, 188), (shoulder[0]-6, shoulder[1]-6), (shoulder[0]+6, shoulder[1]-6), 2)
        metal_link(shoulder, elbow, 10)
        metal_link(elbow, hand, 8)
        start = (shoulder[0]-side*5, shoulder[1]+4)
        end = (elbow[0]-side*5, elbow[1]-3)
        middle = (start[0]+(end[0]-start[0])*.58, start[1]+(end[1]-start[1])*.58)
        metal_link(start, middle, 5)
        pygame.draw.line(arm_layer, (215, 221, 215), middle, end, 2)
        cable = [(shoulder[0]+side*7, shoulder[1]+4),
                 (elbow[0]+side*8, elbow[1]), (hand[0]+side*5, hand[1]-4)]
        pygame.draw.lines(arm_layer, (23, 28, 31), False, cable, 2)
        bearing(shoulder, 7)
        bearing(elbow, 7)
        bearing(hand, 5)
        for finger in (-1, 1):
            local = point(side*(80+finger*(9-5*grip)), -12)
            tip = point(side*(80+finger*(9-5*grip)), 0)
            base = tuple(a+(b-a)*grip for a, b in zip(hand, local))
            end = tuple(a+(b-a)*grip for a, b in zip(hand, tip))
            metal_link(hand, base, 4)
            metal_link(base, end, 4)
            pygame.draw.line(arm_layer, (28, 33, 35), base, end, 2)
    app.canvas.blit(arm_layer, (0, 0))
