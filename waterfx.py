"""Continuous ambient water motion mapped to the aqua laboratory artwork."""
import math
import random
import pygame
from orbit import SubpixelSprite


class BubbleSprite:
    """Cache bubble positions in eighth-pixel steps to keep drawing cheap."""
    def __init__(self, radius, scale):
        r = max(3, round(radius*scale*8))
        size = math.ceil((r*4+24)/8)
        source = pygame.Surface((size*8, size*8), pygame.SRCALPHA)
        center = (r*2+8, r*2+8)
        pygame.draw.circle(source, (87, 189, 220, 28), center, r*2)
        pygame.draw.circle(source, (97, 204, 230, 48), center, round(r*1.4))
        pygame.draw.circle(source, (12, 65, 83, 75), center, r)
        pygame.draw.circle(source, (169, 235, 250, 215), center, r, max(1, r//4))
        pygame.draw.circle(source, (241, 253, 255, 255),
                           (center[0]-r//3, center[1]-r//3), max(1, r//4))
        self.size = size
        self.frames = []
        for y in range(8):
            for x in range(8):
                shifted = pygame.Surface(source.get_size(), pygame.SRCALPHA)
                shifted.blit(source, (x, y))
                self.frames.append(pygame.transform.smoothscale(shifted, (size, size)))

    def draw(self, target, x, y, opacity):
        x -= self.size/2
        y -= self.size/2
        ix, iy = math.floor(x), math.floor(y)
        frame = self.frames[min(7, int((y-iy)*8))*8+min(7, int((x-ix)*8))]
        frame.set_alpha(opacity)
        target.blit(frame, (ix, iy))


class AquaLabWater:
    # These regions use the original artwork's 1536 x 1024 coordinates.
    VESSELS = (
        (181, 294, 79, 157, 30), (285, 387, 43, 65, 10),
        (391, 391, 128, 60, 24), (569, 423, 29, 27, 4),
        (701, 424, 108, 23, 10), (938, 378, 34, 72, 10),
        (1079, 425, 86, 28, 8), (1378, 338, 113, 128, 32),
        (1510, 326, 25, 151, 9), (49, 465, 23, 37, 4),
        (89, 460, 21, 43, 4), (1278, 455, 16, 33, 3),
        (1303, 455, 13, 33, 3), (1328, 455, 14, 33, 3),
        (1454, 466, 18, 37, 3), (1481, 463, 16, 40, 3),
        (10, 706, 42, 76, 20), (0, 790, 133, 142, 34),
        (1480, 682, 51, 118, 28), (1446, 812, 88, 19, 18),
        (0, 347, 14, 128, 12), (2, 477, 31, 31, 9),
    )
    CIRCUITS = (
        ((2, 231), (30, 238), (36, 280), (48, 289), (172, 301)),
        ((155, 290), (155, 261), (162, 255), (192, 261)),
        ((270, 332), (292, 332), (299, 340), (299, 379)),
        ((607, 441), (614, 410), (628, 405), (878, 405), (886, 413), (886, 448)),
        ((963, 376), (963, 358), (979, 354), (990, 359), (990, 424)),
        ((1292, 384), (1299, 349), (1316, 329), (1334, 320), (1376, 320)),
        ((1377, 301), (1384, 279), (1466, 269), (1499, 259), (1505, 281)),
    )

    def __init__(self, backdrop):
        self.sx = backdrop.get_width()/1536
        self.sy = backdrop.get_height()/1024
        self.layer = pygame.Surface(backdrop.get_size(), pygame.SRCALPHA)
        self.vessels = []
        self.refraction = []
        self.effects = []
        rng = random.Random(3827)
        for index, (x, y, width, height, count) in enumerate(self.VESSELS):
            rect = pygame.Rect(round(x*self.sx), round(y*self.sy),
                               max(2, round(width*self.sx)), max(2, round(height*self.sy)))
            texture = backdrop.subsurface(rect).copy()
            mask = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(),
                             border_radius=max(2, round(4*self.sx)))
            if index == 17:
                # Lower-left water channel.
                mask.fill((0, 0, 0, 0))
                pygame.draw.polygon(mask, (255, 255, 255, 255),
                    [(round(px*self.sx), round(py*self.sy)) for px, py in
                     ((0, 37), (111, 0), (131, 20), (0, 135))])
            # Soften the mask edges to hide the refraction seams.
            edge = max(1, round(3*self.sx))
            for inset in range(edge):
                pygame.draw.rect(mask, (255,255,255,round(255*(inset+1)/(edge+1))),
                                 mask.get_rect().inflate(-inset*2,-inset*2), 1)
            bubbles = [(rng.choice((.23, .52, .76))+rng.uniform(-.09,.09),
                        rng.random(), rng.uniform(15, 34)/height,
                        rng.choice((1.0, 1.6, 2.3, 3.0)), rng.random()*math.tau)
                       for _ in range(round(count*1.5))]
            self.vessels.append((rect, texture, mask,
                                 pygame.Surface(rect.size, pygame.SRCALPHA), bubbles))
            strips = []
            step = max(2, round(4*self.sy))
            for yy in range(0, rect.height, step):
                strip = texture.subsurface((0, yy, rect.width, min(step, rect.height-yy)))
                strips.append((yy, SubpixelSprite(strip)))
            self.refraction.append(strips)
            self.effects.append(pygame.Surface(rect.size, pygame.SRCALPHA))
        self.bubbles = {radius: BubbleSprite(radius, self.sx)
                        for radius in (1.0, 1.6, 2.3, 3.0)}
        self.paths = []
        for path in self.CIRCUITS:
            points = [(x*self.sx, y*self.sy) for x, y in path]
            lengths = [math.dist(a,b) for a,b in zip(points, points[1:])]
            self.paths.append((points, lengths, sum(lengths)))

    @staticmethod
    def path_point(points, lengths, distance):
        for a, b, length in zip(points, points[1:], lengths):
            if distance <= length:
                t = distance/max(.001, length)
                return a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t
            distance -= length
        return points[-1]

    def draw(self, target, time):
        self.layer.fill((0, 0, 0, 0))
        for index, (rect, texture, mask, water, bubbles) in enumerate(self.vessels):
            water.fill((0, 0, 0, 0))
            # Interpolate between pixels so slow water movement stays smooth.
            water.blit(texture, (0, 0))
            for y, strip in self.refraction[index]:
                offset = (math.sin(time*1.3+y*.075+index)
                          + .35*math.sin(time*.73-y*.12))*1.15*self.sx
                strip.draw(water, offset, y)
            effects = self.effects[index]
            effects.fill((0, 0, 0, 0))
            channel = index in (4, 6, 17, 19, 21)
            for band in range(4):
                points = []
                for xx in range(0, rect.width, 2):
                    yy = (rect.height*(band+.5)/4
                          + math.sin(xx*.075-time*1.7+band+index)*2*self.sy
                          + math.sin(xx*.16+time*.8+band)*self.sy)
                    points.append((xx, yy))
                if len(points)>1:
                    brightness = round(27+15*math.sin(time*1.1+band+index)**2)
                    pygame.draw.aalines(effects, (124, 223, 245, brightness), False, points)
            for x, phase, speed, radius, sway in bubbles:
                progress = (phase+time*speed)%1
                travel = .78*progress+.22*progress*progress
                if channel:
                    xx = travel*(rect.width+8)-4
                    yy = rect.height*(.2+.65*x)+math.sin(time*1.6+sway)*2*self.sy
                    if index == 17:
                        yy = rect.height*(.65-.55*progress)+math.sin(sway)*14*self.sy
                else:
                    yy = (1-travel)*(rect.height-5)+2
                    xx = x*(rect.width-9)+4+math.sin(time*1.8+sway+progress*6)*2.5*self.sx
                sprite = self.bubbles[radius]
                fade = min(1, progress*10, (1-progress)*10)
                fade = fade*fade*(3-2*fade)
                sprite.draw(effects, xx, yy, round(255*fade))
            if not channel:
                for band in range(2):
                    points = [(xx, (3+band*2)*self.sy
                               + math.sin(xx*.12-time*2.1+index)*.85*self.sy
                               + math.sin(xx*.23+time*1.3)*.3*self.sy)
                              for xx in range(2, rect.width-1)]
                    if len(points)>1:
                        pygame.draw.aalines(effects, (190, 240, 250, 115-band*40), False, points)
            water.blit(effects, (0, 0))
            water.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
            self.layer.blit(water, rect)
        for index, (points, lengths, total) in enumerate(self.paths):
            spacing = 32*self.sx
            for particle in range(max(2, int(total/spacing))):
                distance = (time*(36+index*2)*self.sx+particle*spacing)%total
                fade = min(1, distance/(9*self.sx), (total-distance)/(9*self.sx))
                for tail in range(7):
                    d = distance-tail*1.25*self.sx
                    if d<0:
                        continue
                    a = self.path_point(points, lengths, d)
                    b = self.path_point(points, lengths, min(total, d+1.5*self.sx))
                    pygame.draw.aaline(self.layer, (164, 235, 252, round(195*fade*(1-tail/8))), a, b)
        target.blit(self.layer, (0, 0))
