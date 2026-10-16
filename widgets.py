"""Shared buttons, labels, and glass panels."""

import math
from rendering import pygame
import window
from settings import ACCENT, BG, GLASS_EDGE, PANEL, TEAL, WHITE


def text(app, value, pos, size=18, color=WHITE):
    app.canvas.blit(app.fonts[size].render(str(value), True, color), pos)


def centered_text(app, value, center_x, y, size=18, color=WHITE):
    lettering = app.fonts[size].render(str(value), True, color)
    app.canvas.blit(lettering, (round(center_x-lettering.get_width()/2), y))


def neon_text(app, value, pos, size=24, color=ACCENT):
    key = (value, size, color, app.render_size)
    if getattr(app, "_neon_key", None) != key:
        lettering = app.fonts[size].render(value, True, color)
        padding = 12
        glow = pygame.Surface((lettering.get_width()+padding*2,
                               lettering.get_height()+padding*2), pygame.SRCALPHA)
        # Layer faint copies around the text for the glow.
        for radius, alpha in ((8, 5), (5, 9), (2, 16)):
            lettering.raw.set_alpha(alpha)
            for i in range(16):
                angle = i*math.tau/16
                glow.blit(lettering, (padding+math.cos(angle)*radius,
                                      padding+math.sin(angle)*radius))
        lettering.raw.set_alpha(255)
        glow.blit(lettering, (padding, padding))
        app._neon_key, app._neon_art = key, glow
    app.canvas.blit(app._neon_art, (pos[0]-12, pos[1]-12))


def glass_panel(app, rect, color, radius):
    key = (tuple(rect), color, radius)
    if key not in app.glass_cache:
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
        # The panel tint stays cached while the background changes.
        base = pygame.Surface(rect.size, pygame.SRCALPHA)
        base.fill((*color, 125))
        sheen = pygame.Surface(rect.size, pygame.SRCALPHA)
        for y in range(rect.height):
            alpha = int(23*(1-y/max(1, rect.height-1))**3)
            pygame.draw.line(sheen, (*GLASS_EDGE, alpha), (0, y), (rect.width-1, y))
        base.blit(sheen, (0, 0))
        base.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        app.glass_cache[key] = base, mask
    base, mask = app.glass_cache[key]
    if key not in app.frost_cache:
        scene = app.background.subsurface(rect)
        softened = pygame.transform.smoothscale(scene, (max(1, rect.width//14), max(1, rect.height//14)))
        frosted = pygame.transform.smoothscale(softened, rect.size)
        frosted.raw = frosted.raw.convert_alpha()
        frosted.blit(base, (0, 0))
        frosted.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        app.frost_cache[key] = frosted
    frosted = app.frost_cache[key]
    app.canvas.blit(frosted, rect)
    reflection = pygame.Surface(rect.size, pygame.SRCALPHA)
    center = rect.width*(.5+.38*math.sin(app.time*.22+rect.y*.004))
    spread = max(70, rect.width*.19)
    for i in range(32):
        t = (i-15.5)/16
        left = center+t*spread
        right = left+spread/16+1
        alpha = round(10*math.exp(-4*t*t))
        slant = rect.height*.32
        pygame.draw.polygon(reflection, (*GLASS_EDGE, alpha),
                            [(left, 0), (right, 0), (right-slant, rect.height), (left-slant, rect.height)])
    hover = rect.collidepoint(window.mouse(app))
    pygame.draw.rect(reflection, (*GLASS_EDGE, 145 if hover else 100),
                     reflection.get_rect(), 1, border_radius=radius)
    pygame.draw.rect(reflection, (*WHITE, 22), (2, 2, rect.width-4, rect.height-4),
                     1, border_radius=max(1, radius-2))
    pygame.draw.line(reflection, (*WHITE, 66), (radius, 1), (rect.width-radius, 1))
    reflection.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    app.canvas.blit(reflection, rect)
    moving_border_accent(app, rect, radius)
    for x in (rect.left+9, rect.right-10):
        for y in (rect.top+9, rect.bottom-10):
            pygame.draw.circle(app.canvas, (106, 131, 141), (x, y), 2)


def moving_border_accent(app, rect, radius):
    # Wrap each point separately so the highlight stays joined at the seam.
    left, top = rect.left+1, rect.top+1
    right, bottom = rect.right-2, rect.bottom-2
    r = max(1, min(radius-1, (right-left)/2, (bottom-top)/2))
    horizontal, vertical = right-left-2*r, bottom-top-2*r
    arc = math.pi*r/2
    lengths = (horizontal, arc, vertical, arc, horizontal, arc, vertical, arc)
    perimeter = sum(lengths)

    def point(distance):
        distance %= perimeter
        for side, length in enumerate(lengths):
            if distance <= length:
                t = distance/length if length else 0
                if side == 0:
                    return left+r+distance, top
                if side == 2:
                    return right, top+r+distance
                if side == 4:
                    return right-r-distance, bottom
                if side == 6:
                    return left, bottom-r-distance
                cx, cy, angle = {
                    1: (right-r, top+r, -math.pi/2),
                    3: (right-r, bottom-r, 0),
                    5: (left+r, bottom-r, math.pi/2),
                    7: (left+r, top+r, math.pi),
                }[side]
                angle += t*math.pi/2
                return cx+r*math.cos(angle), cy+r*math.sin(angle)
            distance -= length
        return left+r, top

    start = app.time*160
    points = [point(start+i*2) for i in range(25)]
    pygame.draw.lines(app.canvas, ACCENT, False, points, 2)


def box(app, rect, color=PANEL, radius=16, border=0):
    rect = pygame.Rect(rect)
    if border:
        pygame.draw.rect(app.canvas, color, rect, border, border_radius=radius)
        return
    if rect.width >= 450 and rect.height >= 100:
        glass_panel(app, rect, color, radius)
        return
    glass = pygame.Surface(rect.size, pygame.SRCALPHA)
    opacity = 224 if rect.width > 450 else 235
    pygame.draw.rect(glass, (*color, opacity), glass.get_rect(), border_radius=radius)
    reflection = pygame.Surface(rect.size, pygame.SRCALPHA)
    for y in range(rect.height):
        alpha = int(12*(1-y/max(1, rect.height-1)))
        pygame.draw.line(reflection, (*WHITE, alpha), (0, y), (rect.width-1, y))
    mask = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    reflection.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    glass.blit(reflection, (0, 0))
    pygame.draw.rect(glass, (*GLASS_EDGE, 89), glass.get_rect(), 1, border_radius=radius)
    app.canvas.blit(glass, rect)
    if rect.width > 450:
        pygame.draw.line(app.canvas, ACCENT, (rect.left+18, rect.top), (rect.left+65, rect.top), 2)
        for xx in (rect.left+10, rect.right-11):
            pygame.draw.circle(app.canvas, (106, 131, 141), (xx, rect.top+10), 2)


def button(app, key, label, rect, active=False, enabled=True):
    rect = pygame.Rect(rect)
    app.buttons[key] = (rect, enabled)
    hover = rect.collidepoint(window.mouse(app)) and enabled
    pressed = hover and pygame.mouse.get_pressed()[0]
    primary = key in ("solve", "play") and enabled
    face = (220, 161, 77) if primary else ((61, 49, 35) if active else ((30, 52, 65) if hover else (18, 34, 47)))
    edge = ACCENT if active or primary else (TEAL if hover else (64, 94, 111))
    if not enabled:
        face, edge = (25, 29, 37), (57, 66, 78)
    if pressed:
        face = (179, 126, 54) if primary else (12, 27, 40)
    pygame.draw.rect(app.canvas, (9, 14, 22), rect.move(0, 3), border_radius=8)
    face_key = (rect.size, face)
    if face_key not in app.button_face_cache:
        surface = pygame.Surface(rect.size, pygame.SRCALPHA)
        for yy in range(rect.height):
            shine = int(12*(1-yy/max(1, rect.height-1)))
            pygame.draw.line(surface, tuple(min(255, v+shine) for v in face),
                             (0, yy), (rect.width-1, yy))
        mask = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(mask, (255, 255, 255), mask.get_rect(), border_radius=8)
        surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        app.button_face_cache[face_key] = surface
    surface = app.button_face_cache[face_key]
    app.canvas.blit(surface, rect)
    pygame.draw.rect(app.canvas, edge, rect, 2 if active or hover else 1, border_radius=8)
    pygame.draw.line(app.canvas, (94, 129, 145) if enabled else edge,
                     (rect.left+10, rect.top+3), (rect.right-10, rect.top+3))
    if active:
        pygame.draw.line(app.canvas, ACCENT, (rect.left+12, rect.bottom-4),
                         (rect.right-12, rect.bottom-4), 2)
    ink = (20, 29, 35) if primary else (WHITE if enabled else (99, 116, 129))
    rendered = app.fonts[16].render(label, True, ink)
    icon = ("pause" if app.playing else "play") if key == "play" else ("search" if key == "solve" else None)
    content_width = rendered.get_width()+(26 if icon else 0)
    left = rect.centerx-content_width//2
    cy = rect.centery+int(pressed)
    if icon:
        draw_control_icon(app, icon, left, cy, ink)
    app.canvas.blit(rendered, (left+(26 if icon else 0), cy-rendered.get_height()//2))


def draw_control_icon(app, icon, x, y, color):
    """Draw icons directly so missing font symbols are not a problem."""
    if icon == "play":
        pygame.draw.polygon(app.canvas, color, [(x+3, y-8), (x+3, y+8), (x+16, y)])
    elif icon == "pause":
        for dx in (3, 12):
            pygame.draw.rect(app.canvas, color, (x+dx, y-8, 5, 16), border_radius=1)
    elif icon == "search":
        pygame.draw.circle(app.canvas, color, (x+8, y-2), 6, 2)
        pygame.draw.line(app.canvas, color, (x+12, y+3), (x+18, y+9), 3)


def shortcut_row(app, items, y):
    rendered = [(app.fonts[14].render(key, True, TEAL),
                 app.fonts[14].render(description, True, WHITE)) for key, description in items]
    widths = [glyph.get_width()+17+label.get_width() for glyph, label in rendered]
    gap = (420-sum(widths))/max(1,len(items)-1)
    x = 730
    for (glyph, label), item_width in zip(rendered, widths):
        width = glyph.get_width()+12
        box(app, (x, y, width, 23), BG, 4)
        app.canvas.blit(glyph, (x+6, y+2))
        app.canvas.blit(label, (x+width+5, y+2))
        x += item_width+gap


def section_icon(app, kind, x, y):
    icon = app.section_art[kind]
    app.canvas.blit(icon,icon.get_rect(center=(x+9,y+10)))


def draw_shortcuts(app):
    glass_panel(app, pygame.Rect(712, 723, 456, 70), BG, 8)
    if app.focus is None:
        first = (("Space", "Play / pause"), ("Left", "Back"), ("Right", "Next"), ("R", "Reset"))
    else:
        first = (("0-9", "Enter digits"), ("Backspace", "Delete last digit"))
    shortcut_row(app, first, 731)
    shortcut_row(app, (("Enter", "Find solution"), ("Tab", "Next field"), ("Esc", "Leave field")), 761)


def draw_mode_badge(app):
    if app.badge_glow is None:
        app.badge_glow = pygame.Surface((237, 63), pygame.SRCALPHA)
        for spread in range(12, 0, -1):
            pygame.draw.rect(app.badge_glow, (*TEAL, 3+(12-spread)*2),
                             (14-spread, 14-spread, 209+spread*2, 35+spread*2),
                             2, border_radius=8+spread)
    app.canvas.blit(app.badge_glow, (945, 15))
    box(app, (959, 29, 209, 35), BG, 8)
    pygame.draw.rect(app.canvas, (76, 156, 160), (959, 29, 209, 35), 1, border_radius=8)
    pygame.draw.circle(app.canvas, TEAL, (977, 46), 3)
    text(app, "BFS / DFS / AI SIMULATOR", (989, 36), 14, (183, 231, 231))
