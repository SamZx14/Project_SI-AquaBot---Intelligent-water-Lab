"""Draw logical UI coordinates into native-resolution Pygame surfaces.

UI modules use this wrapper; animation backgrounds use native Pygame.
"""
from types import SimpleNamespace
import pygame as native

_scale = (1.0, 1.0)


def fit_viewport(size, logical=(1200, 800)):
    factor = min(size[0]/logical[0], size[1]/logical[1])
    fitted = tuple(max(1, round(v*factor)) for v in logical)
    return fitted, tuple((outer-inner)//2 for outer, inner in zip(size, fitted))


def configure(size, logical=(1200, 800)):
    global _scale
    _scale = (max(1, size[0])/logical[0], max(1, size[1])/logical[1])


def _point(value, scale):
    return (round(value[0]*scale[0]), round(value[1]*scale[1]))


def _rect(value, scale):
    rect = native.Rect(value)
    return native.Rect(*_point(rect.topleft, scale),
                       max(1, round(rect.width*scale[0])), max(1, round(rect.height*scale[1])))


class Surface:
    def __init__(self, size, flags=0):
        self.logical_size = tuple(map(int, size))
        self.scale = _scale
        self.raw = native.Surface(tuple(max(1, round(v*s)) for v, s in zip(size, self.scale)), flags)

    def get_size(self):
        return self.logical_size

    def get_width(self):
        return self.logical_size[0]

    def get_height(self):
        return self.logical_size[1]

    def get_rect(self, **kwargs):
        return native.Rect((0, 0), self.logical_size).move(0, 0) if not kwargs else self._positioned_rect(kwargs)

    def _positioned_rect(self, kwargs):
        rect = native.Rect((0, 0), self.logical_size)
        for key, value in kwargs.items():
            setattr(rect, key, value)
        return rect

    def fill(self, color):
        self.raw.fill(color)

    def blit(self, source, dest, special_flags=0):
        if isinstance(source, Surface):
            raw = source.raw
            size = tuple(max(1, round(v*s)) for v, s in zip(source.logical_size, self.scale))
            if raw.get_size() != size:
                raw = native.transform.smoothscale(raw, size)
        else:
            size = tuple(max(1, round(v*s)) for v, s in zip(source.get_size(), self.scale))
            raw = native.transform.smoothscale(source, size)
        self.raw.blit(raw, _point(dest[:2], self.scale), special_flags=special_flags)

    def subsurface(self, rect):
        area = native.Rect(rect)
        result = Surface(area.size, native.SRCALPHA)
        result.raw = self.raw.subsurface(_rect(area, self.scale))
        result.scale = self.scale
        return result

    def present(self, window):
        size, offset = fit_viewport(window.get_size(), self.logical_size)
        image = self.raw
        if image.get_size() != size:
            image = native.transform.smoothscale(image, size)
        window.blit(image, offset)


class Draw:
    @staticmethod
    def _width(surface, width):
        return max(1, round(width*min(surface.scale))) if width else 0

    def line(self, surface, color, start, end, width=1):
        # Map adjacent logical rows/columns to shared pixel boundaries.
        # Rounding just the stroke width leaves gaps at fractional scales.
        if width == 1 and (start[1] == end[1] or start[0] == end[0]):
            sx, sy = surface.scale
            left, top = min(start[0], end[0]), min(start[1], end[1])
            right, bottom = max(start[0], end[0])+1, max(start[1], end[1])+1
            x, y = round(left*sx), round(top*sy)
            native.draw.rect(surface.raw, color,
                             (x, y, max(1, round(right*sx)-x), max(1, round(bottom*sy)-y)))
            return
        native.draw.line(surface.raw, color, _point(start, surface.scale), _point(end, surface.scale), self._width(surface, width))

    def lines(self, surface, color, closed, points, width=1):
        native.draw.lines(surface.raw, color, closed, [_point(p, surface.scale) for p in points], self._width(surface, width))

    def polygon(self, surface, color, points, width=0):
        native.draw.polygon(surface.raw, color, [_point(p, surface.scale) for p in points], self._width(surface, width))

    def rect(self, surface, color, rect, width=0, border_radius=0):
        native.draw.rect(surface.raw, color, _rect(rect, surface.scale), self._width(surface, width),
                         border_radius=round(border_radius*min(surface.scale)))

    def ellipse(self, surface, color, rect, width=0):
        native.draw.ellipse(surface.raw, color, _rect(rect, surface.scale), self._width(surface, width))

    def circle(self, surface, color, center, radius, width=0):
        sx, sy = surface.scale
        rect = (round((center[0]-radius)*sx), round((center[1]-radius)*sy),
                max(1, round(radius*2*sx)), max(1, round(radius*2*sy)))
        native.draw.ellipse(surface.raw, color, rect, self._width(surface, width))


class Font:
    def __init__(self, name, size, **kwargs):
        self.name, self.size, self.kwargs = name, size, kwargs
        self.base = native.font.SysFont(name, size, **kwargs)
        self.cache = {}

    def render(self, text, antialias, color):
        # Render text at the display resolution to keep it sharp.
        size = max(1, round(self.size*_scale[1]))
        if size not in self.cache:
            self.cache[size] = native.font.SysFont(self.name, size, **self.kwargs)
        raw = self.cache[size].render(text, antialias, color)
        result = Surface(self.base.size(text), native.SRCALPHA)
        # Empty labels have zero-width glyph surfaces. SDL's smoothscale can
        # crash on those; keep the transparent placeholder instead.
        if raw.get_width() == 0 or raw.get_height() == 0:
            return result
        if raw.get_size() != result.raw.get_size():
            raw = native.transform.smoothscale(raw, result.raw.get_size())
        result.raw = raw
        return result


def smoothscale(source, size):
    result = Surface(size, native.SRCALPHA)
    result.raw = native.transform.smoothscale(source.raw if isinstance(source, Surface) else source, result.raw.get_size())
    return result


class Facade:
    Surface = Surface
    draw = Draw()
    font = SimpleNamespace(init=native.font.init, SysFont=Font)
    transform = SimpleNamespace(smoothscale=smoothscale)
    image = SimpleNamespace(load=native.image.load,
                            save=lambda surface, path: native.image.save(surface.raw if isinstance(surface, Surface) else surface, path),
                            tobytes=lambda surface, fmt: native.image.tobytes(surface.raw if isinstance(surface, Surface) else surface, fmt))

    def __getattr__(self, name):
        return getattr(native, name)


pygame = Facade()
