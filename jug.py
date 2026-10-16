"""Jug drawing, glass geometry, and carried water."""

import math

import arms
from rendering import pygame
from drone import DRAIN_X
from settings import H, JUG_BOTTOM, JUG_TOP, JUG_WIDTH, JUG_X, TEAL, W, WHITE


def water_surface(app, jug):
    return JUG_BOTTOM-4-(JUG_BOTTOM-JUG_TOP-8)*app.water[jug]/app.config[jug]


def draw_jug(app, x, capacity, amount, label, color):
    top, bottom, width = JUG_TOP, JUG_BOTTOM, JUG_WIDTH
    caption = app.fonts[14].render(f"{label}  |  {capacity} L capacity", True, color)
    app.canvas.blit(caption, caption.get_rect(midtop=(x+width/2, 566)))
    glass = pygame.Surface((width, bottom-top), pygame.SRCALPHA)
    glass.fill((74, 117, 127, 24))
    level = (bottom-top-8)*max(0, min(1, amount/capacity))
    if level > 0.2:
        y = glass.get_height()-4-level
        motion = 1-app.transition
        amplitude = min(1.4+3*motion, level/4)
        surface = [(i, max(4, min(glass.get_height()-4,
                   y+amplitude*(math.sin(i*0.043+app.time*2.3)
                   +0.35*math.sin(i*0.083-app.time*1.7)))))
                   for i in range(4, width-3, 3)]
        surface.append((width-4, surface[-1][1]))
        mask = pygame.Surface(glass.get_size(), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255),
                            surface+[(width-4, glass.get_height()-4), (4, glass.get_height()-4)])
        water = pygame.Surface(glass.get_size(), pygame.SRCALPHA)
        for yy in range(max(4, int(y-amplitude*2)), glass.get_height()-4):
            depth = max(0, min(1, (yy-y)/max(1, level)))
            tint = (int(125-68*depth), int(202-49*depth), int(223-35*depth), int(92+70*depth))
            pygame.draw.line(water, tint, (4, yy), (width-4, yy))
        reflections = pygame.Surface(glass.get_size(), pygame.SRCALPHA)
        for band in range(4):
            yy = y+level*(band+1)/5
            shimmer = [(xx, yy+2*math.sin(xx*0.055+app.time*1.3+band))
                       for xx in range(5, width-4, 3)]
            pygame.draw.lines(reflections, (180, 226, 238, 24), False, shimmer, 1)
        pygame.draw.line(reflections, (225, 247, 255, 42), (18, 4), (18, glass.get_height()-5), 5)
        pygame.draw.line(reflections, (225, 247, 255, 22), (29, 4), (29, glass.get_height()-5), 2)
        if motion > 0:
            for i in range(4):
                bx = 22+(i*37)%120+math.sin(app.time*2+i)*3
                by = glass.get_height()-5-((app.time*27+i*41)%max(1, level))
                pygame.draw.circle(reflections, (217, 243, 250, int(65*motion)), (int(bx), int(by)), 2, 1)
        water.blit(reflections, (0, 0))
        pygame.draw.ellipse(water,(185,230,240,62),(5,y-3,width-10,7))
        water.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        glass.blit(water, (0, 0))
        pygame.draw.lines(glass, (187, 231, 242, 160), False, surface, 2)
    # Draw the base even when the drone has lifted the jug.
    pygame.draw.rect(app.canvas, (16, 26, 37), (x-6, bottom-1, width+12, 7), border_radius=3)
    pygame.draw.line(app.canvas, TEAL, (x+10, bottom+3), (x+width-10, bottom+3))
    jug_id = 0 if x == JUG_X[0] else 1
    if app.drone.held_jug == jug_id:
        draw_carried_jug(app, jug_id, capacity, amount)
        amount_caption = app.fonts[20].render(f"{amount:.1f} / {capacity} L", True, WHITE)
        app.canvas.blit(amount_caption, amount_caption.get_rect(midtop=(x+width/2, 588)))
        return
    silhouette = pygame.Surface(glass.get_size(), pygame.SRCALPHA)
    pygame.draw.polygon(silhouette, (255, 255, 255, 255),
                        vessel_outline(lambda px, py: (px+82, py+68)))
    glass.blit(silhouette, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    app.canvas.blit(glass, (x, top))
    if app.vessel_frame is None:
        app.vessel_frame = pygame.Surface((214,160),pygame.SRCALPHA)
        draw_vessel_frame(app.vessel_frame,lambda px,py: (84+px,80+py))
    app.canvas.blit(app.vessel_frame,(x-2,top-12))
    amount_caption = app.fonts[20].render(f"{amount:.1f} / {capacity} L", True, WHITE)
    app.canvas.blit(amount_caption, amount_caption.get_rect(midtop=(x+width/2, 588)))


def vessel_outline(point):
    """Return the jug outline after applying the given transform."""
    outline = []
    for cx, cy, radius, start in ((-76, -62, 6, 180), (76, -62, 6, 270),
                                  (64, 50, 18, 0), (-64, 50, 18, 90)):
        for i in range(17):
            angle = math.radians(start+i*90/16)
            outline.append(point(cx+radius*math.cos(angle), cy+radius*math.sin(angle)))
    return outline


def draw_vessel_frame(target, point):
    # Only enlarge the jug bounds; a full-screen buffer costs too much here.
    bounds = [point(x, y) for x in (-88, 115) for y in (-78, 76)]
    left = math.floor(min(p[0] for p in bounds))
    top = math.floor(min(p[1] for p in bounds))
    size = (math.ceil(max(p[0] for p in bounds))-left,
            math.ceil(max(p[1] for p in bounds))-top)
    detail = pygame.Surface(size, pygame.SRCALPHA)
    detail.scale = tuple(value*3 for value in detail.scale)
    detail.raw = pygame.Surface((size[0]*3, size[1]*3), pygame.SRCALPHA).raw
    def local(x, y):
        px, py = point(x, y)
        return px-left, py-top
    paint_vessel_frame(detail, local)
    target.blit(pygame.transform.smoothscale(detail, size), (left, top))


def paint_vessel_frame(target, point):
    """Draw the glass highlights, handle, and rims."""
    for xx in range(-80,81,2):
        alpha = int(55*math.exp(-((xx+62)/9)**2)+23*math.exp(-((xx-66)/7)**2)
                    +8*math.exp(-((xx+28)/24)**2))
        pygame.draw.line(target,(204,232,237,alpha),point(xx,-59),point(xx,59),2)
    pygame.draw.polygon(target,(225,242,242,16),
        [point(-58,-57),point(-40,-57),point(-49,54),point(-66,54)])
    handle = [point(81+25*math.cos(-math.pi/2+i*math.pi/64),
                    37*math.sin(-math.pi/2+i*math.pi/64)) for i in range(65)]
    for color, width in (((15,26,32,190),10), ((124,168,178,170),7),
                         ((218,236,235,185),3)):
        pygame.draw.lines(target,color,False,handle,width)
        for end in (handle[0],handle[-1]):
            pygame.draw.circle(target,color,end,width/2)
    outline = vessel_outline(point)
    for color, width in (((43,75,86,220),4), ((188,218,222,200),1)):
        pygame.draw.lines(target,color,False,outline[17:]+outline[:17],width)
    for side in (-1, 1):
        pygame.draw.line(target,(143,188,199,85),point(side*76,-55),point(side*76,47),2)
    for cy, ry in ((-66,6),(64,4)):
        radius = 80 if cy < 0 else 66
        rim = [point(radius*math.cos(i*math.tau/80),cy+ry*math.sin(i*math.tau/80)) for i in range(81)]
        pygame.draw.lines(target,(17,35,43,225),False,rim,5)
        pygame.draw.lines(target,(147,183,189,210),False,rim,3)
        pygame.draw.lines(target,(226,240,236,220),False,rim[40:],1)
        inner = [point((radius-4)*math.cos(i*math.tau/80),cy+(ry-2)*math.sin(i*math.tau/80)) for i in range(81)]
        pygame.draw.lines(target,(84,129,142,145),False,inner,1)
    pygame.draw.line(target,(200,227,232,100),point(-67,-49),point(-70,44),2)


def carried_geometry(app, jug):
    dx, dy, angle, grip = app.drone.pose
    cx, cy = JUG_X[jug]+JUG_WIDTH/2+dx, (JUG_TOP+JUG_BOTTOM)/2+dy
    radians = math.radians(-angle)
    scale = 1-0.35*min(1, max(0, -dy/110))
    def point(x, y):
        x, y = x*scale, y*scale
        return (cx+x*math.cos(radians)-y*math.sin(radians),
                cy+x*math.sin(radians)+y*math.cos(radians))
    corners = [point(-82, -68), point(82, -68), point(82, 68), point(-82, 68)]
    return corners, point, grip


def draw_carried_jug(app, jug, capacity, amount):
    corners, point, grip = carried_geometry(app, jug)
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    body = vessel_outline(point)
    pygame.draw.polygon(layer, (74, 117, 127, 24), body)
    # Keep the water level horizontal and preserve its area as the jug tilts.
    def clip(height):
        result = []
        for a, b in zip(body, body[1:]+body[:1]):
            if a[1] >= height:
                result.append(a)
            if (a[1] >= height) != (b[1] >= height):
                t = (height-a[1])/(b[1]-a[1])
                result.append((a[0]+t*(b[0]-a[0]), height))
        return result
    def area(poly):
        return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(poly, poly[1:]+poly[:1])))/2
    fraction = max(0, min(1, amount/capacity))
    low, high = min(p[1] for p in corners), max(p[1] for p in corners)
    target = area(body)*fraction
    for _ in range(28):
        height = (low+high)/2
        if area(clip(height)) > target:
            low = height
        else:
            high = height
    if fraction > 0.001:
        wet = clip((low+high)/2)
        mask = pygame.Surface((W, H), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255), wet)
        fluid = pygame.Surface((W, H), pygame.SRCALPHA)
        surface = (low+high)/2
        water_depth = max(1,max(p[1] for p in corners)-surface)
        for yy in range(int(surface), int(max(p[1] for p in corners))+1):
            depth = min(1, (yy-surface)/water_depth)
            pygame.draw.line(fluid, (int(125-68*depth), int(202-49*depth), int(223-35*depth), int(92+70*depth)), (0, yy), (W, yy))
        ripples = pygame.Surface((W,H),pygame.SRCALPHA)
        for band in range(4):
            yy = surface+band*13
            wave = [(xx, yy+2*math.sin(xx*0.06+app.time*3+band)) for xx in range(int(min(p[0] for p in corners)), int(max(p[0] for p in corners))+1, 3)]
            pygame.draw.lines(ripples, (198, 239, 249, 65 if band == 0 else 22), False, wave, 2)
        fluid.blit(ripples,(0,0))
        fluid.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        layer.blit(fluid, (0, 0))
    glass_reflection = pygame.Surface((W,H),pygame.SRCALPHA)
    draw_vessel_frame(glass_reflection, point)
    layer.blit(glass_reflection,(0,0))
    app.canvas.blit(layer, (0, 0))
    arms.draw(app, point, grip)
    if app.drone.phase in ("transfer", "empty"):
        lip = min(corners[:2], key=lambda p: -p[1])
        site = app.drone.stage.site
        end_x = JUG_X[site]+82 if isinstance(site, int) else DRAIN_X
        end_y = water_surface(app, site) if isinstance(site, int) else 535
        draw_pour_arc(app, lip, (end_x, end_y))


def draw_pour_arc(app, lip, destination):
    layer = pygame.Surface((W, H), pygame.SRCALPHA)
    points = []
    for i in range(31):
        t = i/30
        points.append((lip[0]+(destination[0]-lip[0])*t,
                       lip[1]+(destination[1]-lip[1])*t*t))
    pygame.draw.lines(layer, (118, 200, 230, 155), False, points, 6)
    pygame.draw.lines(layer, (221, 248, 255, 200), False, points, 2)
    for i in range(9):
        t = (app.time*1.6+i/9)%1
        x = lip[0]+(destination[0]-lip[0])*t
        y = lip[1]+(destination[1]-lip[1])*t*t
        pygame.draw.circle(layer, (196, 238, 250, 170), (x+math.sin(i*3)*3, y), 2)
    pygame.draw.ellipse(layer, (198, 239, 249, 130), (destination[0]-12, destination[1]-2, 24, 5), 1)
    app.canvas.blit(layer, (0, 0))
