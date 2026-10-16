"""Slow, layered deep-space travel behind the stationary cabin window."""
import math
import random
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
import pygame

ASSETS = Path(__file__).parent / 'assets'


class SubpixelSprite:
    """Bilinear translation with premultiplied alpha, without pixel snapping.
    Reuse scratch surfaces and retain the original texture at every frame;
    repeated interpolation would progressively blur a moving object.
    """
    def __init__(self, surface):
        self.source = surface.convert_alpha().premul_alpha()
        self.weighted = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self.blended = pygame.Surface((surface.get_width()+1, surface.get_height()+1), pygame.SRCALPHA)

    def draw(self, target, x, y, opacity=255):
        ix, iy = math.floor(x), math.floor(y)
        fx, fy = x-ix, y-iy
        weights = [round(255*w) for w in
                   ((1-fx)*(1-fy), fx*(1-fy), (1-fx)*fy, fx*fy)]
        # Rounding the weights must not change the sprite's brightness.
        strongest = weights.index(max(weights))
        weights[strongest] += 255-sum(weights)
        self.blended.fill((0,0,0,0))
        for offset, weight in zip(((0,0),(1,0),(0,1),(1,1)), weights):
            if weight:
                self.weighted.fill((weight,)*4)
                self.weighted.blit(self.source,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
                self.blended.blit(self.weighted,offset,special_flags=pygame.BLEND_RGBA_ADD)
        if opacity != 255:
            self.blended.fill((opacity,)*4,special_flags=pygame.BLEND_RGBA_MULT)
        target.blit(self.blended,(ix,iy),special_flags=pygame.BLEND_PREMULTIPLIED)


@lru_cache(maxsize=3)
def atlas_image(name):
    return pygame.image.load(str(ASSETS / name))


@lru_cache(maxsize=9)
def planet_texture(kind):
    """Crop a planet sprite without losing its transparent edges."""
    if kind in ('earth', 'moon', 'mars'):
        atlas = atlas_image('planet-flyby-atlas.png')
        index = ('earth', 'moon', 'mars').index(kind)
        width = atlas.get_width() // 3
        tile = atlas.subsurface((index*width, 0, width, atlas.get_height()))
    else:
        atlas = atlas_image('space-objects-atlas.png')
        # Include rings and solar panels when cropping each sprite.
        bounds = {
            'jupiter': (35, 40, 435, 445),
            'saturn': (470, 65, 620, 385),
            'neptune': (1090, 35, 445, 450),
            'asteroid': (25, 535, 460, 430),
            'satellite': (500, 545, 545, 405),
            'ice': (1080, 525, 455, 440),
        }
        x, y, w, h = bounds[kind]
        sx, sy = atlas.get_width()/1536, atlas.get_height()/1024
        tile = atlas.subsurface((round(x*sx), round(y*sy), round(w*sx), round(h*sy)))
    return tile.subsurface(tile.get_bounding_rect(min_alpha=8)).copy()


@dataclass(frozen=True)
class SpaceBody:
    kind: str
    x: float
    y: float
    radius: float
    depth: float
    angle: float = 0


class OrbitalBackdrop:
    SPEED = 24.0
    FIELD = (7600.0, 2400.0)
    MARGIN = 650.0

    def __init__(self, backdrop):
        self.cabin = backdrop.copy()
        self.size = backdrop.get_size()
        self.sx, self.sy = self.size[0]/1200, self.size[1]/800
        view_size = (self.size[0], max(1, round(285*self.sy)))
        self.layer = pygame.Surface(view_size, pygame.SRCALPHA)
        self.mask = pygame.Surface(view_size, pygame.SRCALPHA)
        # Use one sky across the windows, masked behind the frames.
        def art_point(x, y):
            return round(x*self.size[0]/1536), round(y*self.size[1]/1024)
        panes = [
            [(134,0),(1458,0),(1377,302),(1356,331),(1336,345),
             (1158,360),(698,363),(270,349),(244,336),(225,300)],
            [(0,128),(24,18),(126,320),(0,306)],
            [(1536,124),(1517,185),(1480,321),(1536,310)],
        ]
        for pane in panes:
            pygame.draw.polygon(self.mask, (255,255,255,255), [art_point(x,y) for x,y in pane])
        # Keep foreground equipment outside the sky mask.
        occluders = [
            [(167,249),(191,243),(194,232),(211,229),(247,236),(252,254),
             (272,261),(276,363),(167,363)],
            [(1368,301),(1390,297),(1401,279),(1510,279),(1536,297),(1536,365),(1368,365)],
            [(933,351),(944,345),(974,345),(988,357),(988,365),(933,365)],
        ]
        for shape in occluders:
            pygame.draw.polygon(self.mask, (0,0,0,0), [art_point(x,y) for x,y in shape])
        pipes = [([(0,225),(36,234),(44,282),(165,301)], 14),
                 ([(147,279),(148,257),(161,248),(196,255)], 13),
                 ([(270,329),(294,329),(304,340),(304,363)], 12),
                 ([(1290,357),(1306,327),(1330,315),(1380,315)], 14),
                 ([(1370,298),(1378,275),(1465,263),(1500,252),(1510,281)], 14)]
        for path, width in pipes:
            pygame.draw.lines(self.mask, (0,0,0,0), False, [art_point(x,y) for x,y in path],
                              max(1, round(width*self.size[0]/1536)))
        panorama = atlas_image('deep-space-panorama.png')
        self.sky = pygame.transform.smoothscale(panorama,
                         (round(1650*self.sx), round(550*self.sy))).convert()
        self.sky.fill((145, 151, 168), special_flags=pygame.BLEND_RGB_MULT)
        # Moving only the visible crop saves a large temporary surface.
        self.sky_motion = SubpixelSprite(pygame.Surface((view_size[0]+2,view_size[1]+2)))
        self.sprite_cache = {}
        self.star_cache = {}
        rng = random.Random(28419)
        self.stars = [(rng.uniform(-30,1230), rng.uniform(-30,315),
                       rng.uniform(.12,.75), rng.randrange(60,170)) for _ in range(78)]
        self.bodies = [SpaceBody('earth', 285, 238, 158, .74),
                       SpaceBody('saturn', 865, 67, 91, .27, -9),
                       SpaceBody('ice', 565, 247, 23, .38),
                       SpaceBody('satellite', 1060, 224, 22, .92, 12),
                       SpaceBody('asteroid', 695, 30, 8, .85, 48)]
        kinds = ('earth', 'moon', 'mars', 'jupiter', 'saturn', 'neptune', 'ice')
        for _ in range(70):
            x, y = rng.uniform(-550,6950), rng.uniform(-550,1750)
            if -400 < x < 1450 and -400 < y < 650:
                continue
            depth = rng.uniform(.18,.85)
            self.bodies.append(SpaceBody(rng.choice(kinds), x, y,
                                         rng.uniform(35,175)*(.5+depth), depth))
        for kind, count, radius, depths in (('asteroid', 110, (4,22), (.6,1.2)),
                                           ('satellite', 14, (14,30), (.7,1.05))):
            for _ in range(count):
                self.bodies.append(SpaceBody(kind, rng.uniform(-550,6950),
                    rng.uniform(-550,1750), rng.uniform(*radius),
                    rng.uniform(*depths), rng.uniform(-35,35)))
        self.bodies.sort(key=lambda body: body.depth)
        self.comet = SubpixelSprite(self.comet_sprite())
        self.meteor = SubpixelSprite(self.meteor_sprite())

    def point(self, x, y):
        return round(x*self.sx), round(y*self.sy)

    def position(self, body, time):
        # Wrap objects outside the windows so they do not jump into view.
        camera_x = time*self.SPEED
        camera_y = time*2.1+12*math.sin(time/49)
        x = (body.x-camera_x*body.depth+self.MARGIN)%self.FIELD[0]-self.MARGIN
        y = (body.y-camera_y*body.depth+self.MARGIN)%self.FIELD[1]-self.MARGIN
        return x, y

    def sprite(self, body):
        key = (body.kind, round(body.radius), round(body.angle))
        if key not in self.sprite_cache:
            texture = pygame.transform.rotozoom(planet_texture(body.kind), body.angle, 1)
            scale = 2*body.radius/max(texture.get_size())
            size = (max(1,round(texture.get_width()*scale*self.sx)),
                    max(1,round(texture.get_height()*scale*self.sy)))
            self.sprite_cache[key] = SubpixelSprite(pygame.transform.smoothscale(texture,size))
        return self.sprite_cache[key]

    def comet_sprite(self):
        surface = pygame.Surface(self.point(270,105), pygame.SRCALPHA)
        for i in range(170,0,-1):
            t = i/170
            pygame.draw.circle(surface, (128,166,196,round(30*(1-t)**1.3)),
                self.point(25+i,76-35*t*t), max(1,round((2+12*t)*self.sx)))
        for i in range(145,0,-1):
            t = i/145
            pygame.draw.circle(surface, (162,204,239,round(90*(1-t)**1.8)),
                self.point(25+i,76-i*.31), max(1,round(2*self.sx)))
        for radius, alpha in ((11,8),(7,18),(4,50),(2,200)):
            pygame.draw.circle(surface,(206,227,240,alpha),self.point(25,76),max(1,round(radius*self.sx)))
        return surface

    def meteor_sprite(self):
        surface = pygame.Surface(self.point(60,30),pygame.SRCALPHA)
        for i in range(22,0,-1):
            alpha = round(215*(1-i/23)**1.5)
            pygame.draw.aaline(surface,(255,227,184,alpha),
                self.point(56-i*2.4,26-i*.96),self.point(56-(i-1)*2.4,26-(i-1)*.96))
        return surface

    def draw_star(self, x, y, brightness):
        if brightness not in self.star_cache:
            radius = max(1,round(.65*self.sx))
            surface = pygame.Surface((radius*2+3,radius*2+3),pygame.SRCALPHA)
            pygame.draw.circle(surface,(brightness,brightness,min(255,brightness+17)),
                               (radius+1,radius+1),radius)
            self.star_cache[brightness] = SubpixelSprite(surface)
        sprite = self.star_cache[brightness]
        sprite.draw(self.layer,x*self.sx-sprite.source.get_width()//2,
                    y*self.sy-sprite.source.get_height()//2)

    @staticmethod
    def encounter(time, period, seed):
        """Schedule events from elapsed time, not frame count."""
        cycle = math.floor(time/period)
        rng = random.Random(seed+cycle*7919)
        start = cycle*period+rng.uniform(8,period-14)
        return time-start, rng

    def draw_comet(self, time):
        # An event from the previous window may still be visible.
        for sample in (time, time-127):
            age, rng = self.encounter(sample, 127, 811)
            age += time-sample
            if 0 <= age < 48:
                x = rng.uniform(400,1100)-age*5
                y = rng.uniform(35,230)+age*.32
                fade = min(1, age/5, (48-age)/6)
                self.comet.draw(self.layer,(x-25)*self.sx,(y-76)*self.sy,round(190*fade))

    def draw_meteor(self, time):
        age, rng = self.encounter(time, 43, 412)
        if 0 <= age < 1.35:
            x, y = rng.uniform(280,930)+age*105, rng.uniform(15,120)+age*42
            fade = math.sin(math.pi*age/1.35)
            self.meteor.draw(self.layer,(x-56)*self.sx,(y-26)*self.sy,round(255*fade))

    def draw(self, target, time):
        drift_x = 210+100*math.sin(time/240)
        drift_y = 105+35*math.sin(time/310)
        sky_x, sky_y = drift_x*self.sx, drift_y*self.sy
        whole_x, whole_y = math.floor(sky_x), math.floor(sky_y)
        self.sky_motion.source.blit(self.sky,(0,0),
            (whole_x,whole_y,*self.sky_motion.source.get_size()))
        self.sky_motion.draw(self.layer,whole_x-sky_x,whole_y-sky_y)
        for x,y,depth,brightness in self.stars:
            xx = (x-time*depth*.7+30)%1260-30
            yy = (y-time*depth*.08+30)%345-30
            self.draw_star(xx,yy,brightness)
        self.draw_comet(time)
        for body in self.bodies:
            x,y = self.position(body,time)
            r = body.radius
            if x+r < 0 or x-r > 1200 or y+r < 0 or y-r > 285:
                continue
            sprite = self.sprite(body)
            sprite.draw(self.layer,x*self.sx-sprite.source.get_width()/2,
                        y*self.sy-sprite.source.get_height()/2)
        self.draw_meteor(time)
        self.layer.blit(self.mask,(0,0),special_flags=pygame.BLEND_RGBA_MULT)
        target.blit(self.cabin,(0,0))
        target.blit(self.layer,(0,0))
