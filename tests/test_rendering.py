"""Regression checks for fractional scaling and screen proportions."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
import unittest
from rendering import pygame, configure, fit_viewport


class RenderingTests(unittest.TestCase):
    def tearDown(self):
        configure((1200, 800))

    def test_adjacent_gradient_lines_leave_no_transparent_gaps(self):
        for factor in (0.875, 1.26, 1.5, 1.6, 2.25):
            configure((1200*factor, 800*factor))
            for vertical in (False, True):
                surface = pygame.Surface((80, 80), pygame.SRCALPHA)
                for i in range(80):
                    start, end = ((i, 0), (i, 79)) if vertical else ((0, i), (79, i))
                    pygame.draw.line(surface, (100, 150, 200, 255), start, end)
                alpha = pygame.image.tobytes(surface, "RGBA")[3::4]
                self.assertTrue(all(value == 255 for value in alpha), (factor, vertical))

    def test_viewport_preserves_proportions_and_centers_content(self):
        for window in ((1920, 1009), (900, 700), (1200, 800), (800, 1200)):
            size, offset = fit_viewport(window)
            self.assertLessEqual(abs(size[0]-size[1]*1.5), 1)
            for outer, inner, margin in zip(window, size, offset):
                self.assertLessEqual(inner, outer)
                self.assertLessEqual(abs(outer-inner-2*margin), 1)
