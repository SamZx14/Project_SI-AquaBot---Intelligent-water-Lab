"""The paged solution screen with pairs of jugs."""

import math
from rendering import pygame
import widgets
from settings import ACCENT, BG, GLASS_EDGE, MUTED, TEAL, W, WATER_A, WHITE


def jug_glass_card(app, x, y, edge):
    """Draw one solution card and its moving reflection."""
    width, height = 326, 226
    layer = pygame.Surface((width, height), pygame.SRCALPHA)
    mask = pygame.Surface((width, height), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, width, height), border_radius=14)
    for line in range(height):
        t = line/(height-1)
        shine = (1-t)**3
        pygame.draw.line(layer, (int(20+23*shine), int(39+29*shine), int(53+34*shine), 225),
                         (0, line), (width, line))
    reflection = pygame.Surface((width, height), pygame.SRCALPHA)
    center = width*(.5+.65*math.sin(app.time*.45+x*.003+y*.002))
    for band in range(60):
        offset = (band-30)*4
        alpha = round(23*math.exp(-((band-30)/15)**2))
        left = center+offset
        pygame.draw.polygon(reflection, (188, 231, 245, alpha),
                            [(left, 0), (left+5, 0), (left-95, height), (left-100, height)])
    layer.blit(reflection, (0, 0))
    pygame.draw.rect(layer, (218, 246, 255, 35), (4, 4, width-8, height-8), 1, border_radius=11)
    pygame.draw.line(layer, (227, 249, 255, 95), (18, 5), (width-18, 5))
    layer.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    app.canvas.blit(layer, (x, y))
    pygame.draw.rect(app.canvas, edge, (x, y, width, height), 2, border_radius=14)


def draw_jug_view(app):
    """Draw up to six solution states on the current page."""
    app.canvas.fill(BG)
    app.fields = []
    app.buttons.clear()
    app.canvas.blit(app.jug_logo, (32, 10))
    widgets.text(app, "Explained solution in the jugs", (118, 28), 32, ACCENT)
    widgets.button(app, "lab_view", "< Back to lab", (966, 28, 194, 44))
    a, b, target = app.config
    widgets.text(app, f"{app.algorithm}  |  Jug A: {a} L  |  Jug B: {b} L  |  Target: {target} L", (40, 80), 20, TEAL)
    widgets.centered_text(app, "Follow the arrows. Each pair of jugs represents one solution state.", W/2, 116, 18, MUTED)
    n = len(app.result.states)
    start = app.jug_page*6
    count = min(6, n-start)
    positions = [(46+col*390, 174+row*268) for row in range(2)
                 for col in (range(3) if row == 0 else range(2, -1, -1))]
    for slot in range(max(0, count)):
        i = start+slot
        x, y = positions[slot]
        state = app.result.states[i]
        goal = target in state
        edge = ACCENT if goal else TEAL
        jug_glass_card(app, x, y, edge)
        widgets.centered_text(app, f"Step {i}" + ("  /  GOAL" if goal else ""), x+163, y+10, 20, edge)
        widgets.centered_text(app, app.result.actions[i], x+163, y+40, 16, WHITE)
        for jug, (capacity, amount) in enumerate(zip((a, b), state)):
            left, top = x+44+jug*145, y+78
            width, height = 76, 96
            pygame.draw.rect(app.canvas, GLASS_EDGE, (left+width-1, top+18, 19, 48), 3, border_radius=7)
            pygame.draw.rect(app.canvas, BG, (left, top, width, height), border_radius=6)
            filled = round((height-8)*amount/capacity)
            if filled:
                pygame.draw.rect(app.canvas, WATER_A, (left+4, top+height-4-filled, width-8, filled))
                pygame.draw.line(app.canvas, TEAL, (left+4, top+height-4-filled), (left+width-4, top+height-4-filled), 2)
            pygame.draw.lines(app.canvas, GLASS_EDGE, False,
                              [(left, top), (left, top+height), (left+width, top+height), (left+width, top)], 3)
            pygame.draw.line(app.canvas, WHITE, (left-4, top), (left+width+4, top), 2)
            widgets.centered_text(app, f"{'A' if jug == 0 else 'B'}: {amount}/{capacity} L", left+width/2, top+108, 16, WHITE)
        if slot < count-1:
            nx, ny = positions[slot+1]
            if ny != y:
                p, q = (x+163, y+232), (x+163, ny-8)
                head = [(q[0]-7, q[1]-10), q, (q[0]+7, q[1]-10)]
            else:
                direction = 1 if nx > x else -1
                p = (x+334 if direction == 1 else x-8, y+118)
                q = (nx-8 if direction == 1 else nx+334, y+118)
                head = [(q[0]-direction*10, q[1]-7), q, (q[0]-direction*10, q[1]+7)]
            pygame.draw.line(app.canvas, TEAL, p, q, 3)
            pygame.draw.lines(app.canvas, TEAL, False, head, 3)
    if not n:
        widgets.text(app, app.result.message, (48, 220), 24, ACCENT)
        widgets.text(app, "Return to the lab to change the capacities or target.", (48, 264), 20, MUTED)
    widgets.button(app, "jug_prev", "< Previous", (40, 726, 162, 44), enabled=start > 0)
    widgets.button(app, "jug_next", "Next >", (998, 726, 162, 44), enabled=start+6 < n)
    label = f"Steps {start}-{start+count-1} of {n-1}  |  Page {app.jug_page+1}/{max(1, (n+5)//6)}" if n else "No solution to display"
    widgets.centered_text(app, label, W/2, 736, 18, MUTED)
    app.window.fill(BG)
    app.canvas.present(app.window)
    pygame.display.flip()
