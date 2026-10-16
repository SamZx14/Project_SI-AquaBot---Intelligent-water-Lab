"""Application state and the main event loop."""

import animation
import controls
import drone_view
import lab_view
import playback
import window
from rendering import pygame
from sound import SoundEffects


class WaterLab:
    def __init__(self):
        window.setup(self)
        self.values = ["4", "3", "2"]
        self.focus = None
        self.algorithm = "BFS"
        self.speed = 1
        self.buttons, self.fields = {}, []
        self.time = 0.0
        self.running = True
        self.audio = SoundEffects()
        self.page = "lab"
        self.jug_page = 0
        self.compute()

    def compute(self):
        playback.compute(self)

    def go(self, index):
        playback.go(self, index)

    def action(self, key):
        controls.action(self, key)

    def event(self, event):
        controls.event(self, event)

    def update(self, dt):
        animation.update(self, dt)

    def draw(self):
        lab_view.draw(self)

    def viewport(self):
        return window.viewport(self)

    def tube_tip(self):
        return drone_view.tube_tip(self)

    def run(self, smoke=False, screenshot=None):
        frames = 0
        while self.running:
            dt = min(self.clock.tick(60)/1000, 0.05)
            for event in pygame.event.get():
                self.event(event)
            self.update(dt)
            self.draw()
            frames += 1
            if smoke and frames >= 3:
                if screenshot:
                    pygame.image.save(self.canvas, screenshot)
                self.running = False
        self.audio.stop()
        pygame.quit()

