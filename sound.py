"""Play the bundled sound effects during matching animation stages."""
from pathlib import Path
import warnings
import pygame


class SoundEffects:
    PHASES = {
        "fly": "flight", "carry": "flight", "return": "flight",
        "grip": "arm", "release": "arm", "lift": "arm",
        "land": "arm", "tilt": "arm", "upright": "arm",
        "pour": "fill", "transfer": "fill",
        "refill": "suction",
        "empty": "drain", "drain": "drain",
    }
    VOLUMES = {"flight": .65, "arm": .65, "fill": .65,
               "suction": .6, "drain": .65, "complete": .75, "click": .6,
               "error": .75}

    def __init__(self):
        self.sounds = {}
        self.current = None
        self.completed = False
        self.available = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            folder = Path(__file__).parent / "assets" / "sounds"
            for name, volume in self.VOLUMES.items():
                sound = pygame.mixer.Sound(str(folder / f"{name}.mp3"))
                sound.set_volume(volume)
                self.sounds[name] = sound
            self.effect = pygame.mixer.Channel(0)
            self.goal = pygame.mixer.Channel(1)
            self.button = pygame.mixer.Channel(2)
            self.alert = pygame.mixer.Channel(3)
            self.available = True
        except (pygame.error, OSError) as exc:
            warnings.warn(f"Sound unavailable; continuing without audio: {exc}")

    def stop(self):
        if self.available:
            self.effect.stop()
            self.goal.stop()
        self.current = None
        self.completed = False

    def click(self):
        if self.available:
            self.button.play(self.sounds["click"])

    def error(self):
        """Play an error sound for each invalid submission."""
        if self.available:
            self.alert.play(self.sounds["error"])

    def sync(self, phase, *, arriving=False, paused=False, complete=False):
        if not self.available:
            return
        if paused:
            self.effect.pause()
            self.goal.pause()
            return
        self.effect.unpause()
        self.goal.unpause()
        wanted = "flight" if arriving else self.PHASES.get(phase)
        if complete:
            wanted = None
        if wanted != self.current:
            self.effect.stop()
            if wanted:
                self.effect.play(self.sounds[wanted], loops=-1)
            self.current = wanted
        if complete and not self.completed:
            self.goal.play(self.sounds["complete"])
        self.completed = complete
