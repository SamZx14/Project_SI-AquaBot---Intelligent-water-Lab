"""Window setup, artwork loading, and display scaling."""

import sys
import ctypes
from pathlib import Path
from rendering import configure, fit_viewport, pygame
from orbit import OrbitalBackdrop
from waterfx import AquaLabWater
from settings import H, W


def setup(app):
    if sys.platform == "win32":
        try:
            ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
        except (AttributeError, OSError):
            pass
    configure((W, H))
    pygame.display.init()
    pygame.font.init()
    icon = pygame.image.load(str(Path(__file__).parent / "assets" / "robot-water-icon.png"))
    pygame.display.set_icon(pygame.transform.smoothscale(icon, (64, 64)).raw)
    app.window = pygame.display.set_mode((W, H), pygame.RESIZABLE)
    pygame.display.set_caption("SI AquaBot — Intelligent Water Lab")
    apply_window_transparency()
    app.icon_source = icon.convert_alpha()
    app.jug_logo_source = pygame.image.load(str(Path(__file__).parent / "assets" / "jug-solution-logo.png")).convert_alpha()
    section_atlas = pygame.image.load(str(Path(__file__).parent / "assets" / "section-icons-realistic.png")).convert_alpha()
    app.section_sources = {}
    tile_width = section_atlas.get_width()//2
    for index, kind in enumerate(("lab", "sequence")):
        tile = section_atlas.subsurface((index*tile_width,0,tile_width,section_atlas.get_height()))
        app.section_sources[kind] = tile.subsurface(tile.get_bounding_rect(min_alpha=8)).copy()
    artwork = pygame.image.load(str(Path(__file__).parent / "assets" / "water-drone.png")).convert_alpha()
    app.drone_source = artwork.subsurface(artwork.get_bounding_rect(min_alpha=15)).copy()
    app.lab_source = pygame.image.load(str(Path(__file__).parent / "assets" / "orbital-lab-background.png")).convert()
    app.render_size = None
    resize_rendering(app)
    app.fonts = {s: pygame.font.SysFont("segoeui", s, bold=True) for s in (14, 16, 18, 20, 24, 32)}
    app.clock = pygame.time.Clock()


def apply_window_transparency():
    """Keep the orbital backdrop opaque and legible on Windows."""
    if sys.platform != "win32":
        return
    hwnd = pygame.display.get_wm_info().get("window")
    if not hwnd:
        return
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    get_style = user32.GetWindowLongW
    get_style.argtypes = [ctypes.c_void_p, ctypes.c_int]
    get_style.restype = ctypes.c_long
    set_style = user32.SetWindowLongW
    set_style.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_long]
    set_style.restype = ctypes.c_long
    set_alpha = user32.SetLayeredWindowAttributes
    set_alpha.argtypes = [ctypes.c_void_p, ctypes.c_ulong, ctypes.c_ubyte, ctypes.c_ulong]
    set_alpha.restype = ctypes.c_int
    style = get_style(hwnd, -20)
    set_style(hwnd, -20, style | 0x80000)
    if not set_alpha(hwnd, 0, 255, 2):
        set_style(hwnd, -20, style)


def resize_rendering(app):
    size, _ = viewport(app)
    if size == app.render_size:
        return
    configure(size)
    app.render_size = size
    app.glass_cache = {}
    app.pipe_path_cache = {}
    app.button_face_cache = {}
    app.frost_cache = {}
    app.badge_glow = None
    app.vessel_frame = None
    app.empty_pipe = None
    app.supply_tank_art = None
    app.canvas = pygame.Surface((W, H))
    app.header_logo = pygame.transform.smoothscale(app.icon_source, (86, 86))
    app.jug_logo = pygame.transform.smoothscale(app.jug_logo_source, (72, 72))
    app.section_art = {}
    for kind, source in app.section_sources.items():
        factor = min(24/source.get_width(),28/source.get_height())
        size = (max(1,round(source.get_width()*factor)),max(1,round(source.get_height()*factor)))
        app.section_art[kind] = pygame.transform.smoothscale(source,size)
    app.drone_art = pygame.transform.smoothscale(app.drone_source, (180, 94))
    app.background = pygame.transform.smoothscale(app.lab_source, (W, H))
    atmosphere = pygame.Surface((W, H), pygame.SRCALPHA)
    atmosphere.fill((7, 16, 27, 70))
    app.background.blit(atmosphere, (0, 0))
    app.orbit = OrbitalBackdrop(app.background.raw)
    app.lab_water = AquaLabWater(app.background.raw)
    app.frost_tick = None


def viewport(app):
    return fit_viewport(app.window.get_size(), (W, H))


def mouse(app, pos=None):
    size, offset = viewport(app)
    x, y = pygame.mouse.get_pos() if pos is None else pos
    return ((x-offset[0])*W/size[0], (y-offset[1])*H/size[1])
