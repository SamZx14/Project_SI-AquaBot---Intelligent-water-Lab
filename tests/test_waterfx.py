"""Ambient water remains bounded, repeatable, and independent of playback."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'
import unittest
from pathlib import Path
import pygame
from waterfx import AquaLabWater
from orbit import OrbitalBackdrop


class AquaLabTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.art = pygame.image.load(str(Path(__file__).resolve().parents[1] / 'assets' / 'orbital-lab-background.png')).convert()

    def tearDown(self):
        pygame.quit()

    def test_water_moves_without_changing_floor_or_window(self):
        for size in ((900, 600), (1200, 800), (1800, 1200)):
            base = pygame.transform.smoothscale(self.art, size)
            water = AquaLabWater(base)
            first, second = base.copy(), base.copy()
            water.draw(first, 1)
            water.draw(second, 3)
            for rect, _, _, _, _ in water.vessels:
                self.assertNotEqual(pygame.image.tobytes(first.subsurface(rect), 'RGB'),
                                    pygame.image.tobytes(second.subsurface(rect), 'RGB'))
            for x, y in ((.5, .1), (.5, .7), (.3, .9)):
                point = (int(size[0]*x), int(size[1]*y))
                self.assertEqual(first.get_at(point), base.get_at(point))
            replay = base.copy()
            water.draw(replay, 1)
            self.assertEqual(pygame.image.tobytes(first, 'RGB'), pygame.image.tobytes(replay, 'RGB'))

    def test_side_panes_share_sky_and_preserve_equipment(self):
        orbit = OrbitalBackdrop(pygame.transform.smoothscale(self.art, (1200, 800)))
        for point in ((30, 170), (1190, 220), (500, 100)):
            self.assertEqual(orbit.mask.get_at(point).a, 255)
        for point in ((170, 240), (1120, 265), (100, 100)):
            self.assertEqual(orbit.mask.get_at(point).a, 0)
        a, b = orbit.cabin.copy(), orbit.cabin.copy()
        orbit.draw(a, 0)
        orbit.draw(b, 60)
        self.assertNotEqual(pygame.image.tobytes(a.subsurface((10, 160, 30, 55)), 'RGB'),
                            pygame.image.tobytes(b.subsurface((10, 160, 30, 55)), 'RGB'))


if __name__ == '__main__':
    unittest.main()
