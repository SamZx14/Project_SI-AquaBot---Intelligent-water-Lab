"""Continuity, clipping and long-running checks for space travel."""
import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
import unittest
import pygame
from orbit import OrbitalBackdrop, SubpixelSprite, planet_texture


class OrbitTests(unittest.TestCase):
    def setUp(self):
        pygame.display.init()
        pygame.display.set_mode((1, 1))
        self.base = pygame.Surface((1200, 800))
        self.base.fill((17, 24, 31))
        self.orbit = OrbitalBackdrop(self.base)

    def tearDown(self):
        pygame.quit()

    def test_nearby_motion_is_slow_and_continuous(self):
        for body in self.orbit.bodies:
            for time in (0, 30, 90, 600, 3600):
                x, y = self.orbit.position(body, time)
                if -body.radius < x < 1200+body.radius and -body.radius < y < 285+body.radius:
                    xx, yy = self.orbit.position(body, time+1/60)
                    self.assertLess(abs(xx-x), .5)
                    self.assertLess(abs(yy-y), .1)

    def test_all_body_textures_keep_transparency(self):
        for kind in {body.kind for body in self.orbit.bodies}:
            texture = planet_texture(kind)
            self.assertTrue(texture.get_flags() & pygame.SRCALPHA, kind)
            self.assertEqual(texture.get_at((0, 0)).a, 0, kind)

    def test_fractional_motion_moves_light_smoothly_without_brightness_pulses(self):
        source = pygame.Surface((1, 1), pygame.SRCALPHA)
        source.fill((255, 255, 255, 255))
        sprite = SubpixelSprite(source)
        target = pygame.Surface((12, 12), pygame.SRCALPHA)
        for step in range(33):
            x, y = 3+step/16, 4+step/32
            target.fill((0, 0, 0, 0))
            sprite.draw(target, x, y)
            pixels = [(xx, yy, target.get_at((xx, yy)).r)
                      for xx in range(12) for yy in range(12)]
            light = sum(p[2] for p in pixels)
            self.assertEqual(light, 255)
            self.assertAlmostEqual(sum(xx*v for xx, yy, v in pixels)/light, x, delta=.01)
            self.assertAlmostEqual(sum(yy*v for xx, yy, v in pixels)/light, y, delta=.01)

    def test_subpixel_drawing_does_not_accumulate_blur_or_change_artwork(self):
        source = pygame.Surface((4, 4), pygame.SRCALPHA)
        source.fill((30, 120, 230, 180))
        original = pygame.image.tobytes(source, 'RGBA')
        sprite = SubpixelSprite(source)
        target = pygame.Surface((12, 12), pygame.SRCALPHA)
        sprite.draw(target, -.2, .7)
        expected = pygame.image.tobytes(target, 'RGBA')
        for i in range(30):
            target.fill((0, 0, 0, 0))
            sprite.draw(target, i/7, i/11, 128)
        target.fill((0, 0, 0, 0))
        sprite.draw(target, -.2, .7)
        self.assertEqual(pygame.image.tobytes(target, 'RGBA'), expected)
        self.assertEqual(pygame.image.tobytes(source, 'RGBA'), original)

    def test_long_journey_preserves_cabin_and_is_frame_rate_independent(self):
        target = self.base.copy()
        self.orbit.draw(target, 65)
        expected = pygame.image.tobytes(target, 'RGB')
        for time in (0, 12, 126.9, 127, 400, 3600, 36000):
            self.orbit.draw(target, time)
            self.assertEqual(target.get_at((0, 0)), self.base.get_at((0, 0)))
            self.assertEqual(target.get_at((600, 400)), self.base.get_at((600, 400)))
        self.orbit.draw(target, 65)
        self.assertEqual(pygame.image.tobytes(target, 'RGB'), expected)


if __name__ == '__main__':
    unittest.main()
