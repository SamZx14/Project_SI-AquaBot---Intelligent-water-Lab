"""Headless integration checks for drone playback, input and rendering."""
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
import unittest
from unittest.mock import Mock
import pygame
from main import WaterLab
from drone import SUPPLY_X


class UITests(unittest.TestCase):
    def setUp(self):
        self.app = WaterLab()

    def tearDown(self):
        pygame.quit()

    def test_empty_labels_render_at_native_and_resized_dimensions(self):
        for size in ((1200, 800), (900, 700), (1800, 1200)):
            self.app.window = pygame.display.set_mode(size, pygame.RESIZABLE)
            self.app.draw()
            self.assertIn("step:0", self.app.buttons)
            label = self.app.fonts[16].render("", True, (255, 255, 255))
            self.assertEqual(label.get_width(), 0)
            self.assertEqual(label.raw.get_at((0, 0)).a, 0)

    def test_jug_view_navigation_and_pause(self):
        self.app.action("play")
        self.app.update(.3)
        self.app.draw()
        rect, enabled = self.app.buttons["jug_view"]
        self.assertTrue(enabled)
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.app.draw()
        self.assertEqual(self.app.page, "jugs")
        before = self.app.drone.x
        self.app.update(1)
        self.assertEqual(self.app.drone.x, before)
        self.assertFalse(self.app.fields)
        self.assertNotIn("play", self.app.buttons)
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.app.draw()
        self.assertEqual(self.app.page, "lab")
        self.assertIn("play", self.app.buttons)

    def test_jug_view_long_empty_and_zero_solutions(self):
        for values in (["99", "100", "50"], ["6", "4", "3"], ["4", "3", "0"]):
            self.app.values = values
            self.app.compute()
            self.app.action("jug_view")
            last = max(0, (len(self.app.result.states)-1)//6)
            for _ in range(last+2):
                self.app.action("jug_next")
            self.assertEqual(self.app.jug_page, last)
            self.app.window = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
            self.app.draw()
            self.assertFalse(self.app.buttons["jug_next"][1])
            self.app.action("lab_view")

    def test_play_enters_from_left_and_pause_freezes_arrival(self):
        self.assertFalse(self.app.drone_visible)
        self.app.update(2)
        self.assertFalse(self.app.drone_visible)
        self.app.action("play")
        self.assertEqual(self.app.drone.x, -120)
        self.app.update(.6)
        self.assertGreater(self.app.drone.x, -120)
        self.assertLess(self.app.drone.x, SUPPLY_X)
        self.assertEqual(self.app.water, [0, 0])
        self.app.action("play")
        position = self.app.drone.x
        self.app.update(3)
        self.assertEqual(self.app.drone.x, position)
        self.app.action("play")
        self.app.update(1)
        self.assertIsNone(self.app.entry_elapsed)
        self.assertEqual(self.app.drone.x, SUPPLY_X)
        self.app.action("reset")
        self.assertFalse(self.app.drone_visible)

    def test_play_applies_new_inputs_before_arrival(self):
        self.app.values = ["9", "7", "3"]
        self.app.action("play")
        self.assertEqual(self.app.config, (9, 7, 3))
        self.assertTrue(self.app.playing)
        self.assertEqual(self.app.entry_elapsed, 0)
        self.app.action("reset")
        self.app.values = ["", "7", "3"]
        self.app.action("play")
        self.assertTrue(self.app.error)
        self.assertFalse(self.app.drone_visible)

    def test_playback_reaches_goal(self):
        self.app.action("play")
        for _ in range(600):
            self.app.update(0.05)
        self.assertFalse(self.app.playing)
        self.assertEqual(tuple(self.app.water), self.app.result.states[-1])
        self.assertEqual(self.app.drone.cargo, 0)
        self.app.draw()

    def test_dfs_and_timeline_jump(self):
        self.app.action("DFS")
        self.app.action("step:2")
        self.app.update(30)
        self.assertEqual(tuple(self.app.water), self.app.result.states[2])
        self.assertTrue(self.app.drone.finished)
        self.app.draw()

    def test_pause_freezes_flight_and_pumping(self):
        self.app.go(1)
        self.app.action("play")
        self.app.update(0.5)
        self.app.action("play")
        before = (self.app.drone.x, self.app.drone.tube, self.app.drone.cargo, self.app.water[:])
        self.app.update(10)
        self.assertEqual(before, (self.app.drone.x, self.app.drone.tube, self.app.drone.cargo, self.app.water))
        self.app.action("play")
        self.app.update(0.3)
        self.assertNotEqual(before[:3], (self.app.drone.x, self.app.drone.tube, self.app.drone.cargo))
        self.app.action("reset")
        self.assertEqual(self.app.drone.x, SUPPLY_X)
        self.assertEqual(self.app.water, [0, 0])
        self.assertEqual(self.app.drone.cargo, 0)
        self.assertEqual(self.app.drone.tube, 0)

    def test_render_every_drone_phase_without_text_overlap(self):
        self.app.go(1)
        for _ in range(85):
            self.app.update(0.1)
            self.app.draw()
        self.app.go(2)
        phases = set()
        for _ in range(85):
            self.app.update(0.1)
            phases.add(self.app.drone.phase)
            self.app.draw()
            self.assertLess(self.app.tube_tip()+8, 566)
        self.assertTrue({"grip", "lift", "carry", "tilt", "transfer", "return", "land", "release"}.issubset(phases))
        self.assertEqual(tuple(self.app.water), self.app.result.states[2])

    def test_invalid_and_impossible(self):
        self.app.values = ["", "3", "2"]
        self.app.compute()
        self.assertTrue(self.app.error)
        self.app.draw()
        self.app.values = ["6", "4", "3"]
        self.app.compute()
        self.assertFalse(self.app.result.states)
        self.app.action("play")
        self.app.draw()

    def test_red_errors_sound_once_per_attempt_across_controls(self):
        self.app.audio.alert = Mock()
        for values in (["", "3", "2"], ["0", "3", "2"], ["4", "3", "101"]):
            for control in ("solve", "play", "BFS", "DFS"):
                with self.subTest(values=values, control=control):
                    self.app.values = values
                    self.app.audio.alert.reset_mock()
                    self.app.action(control)
                    self.assertTrue(self.app.error)
                    for _ in range(2):
                        self.app.update(.01)
                        self.app.draw()
                    self.app.audio.alert.play.assert_called_once_with(self.app.audio.sounds["error"])
                    self.app.action(control)
                    self.assertEqual(self.app.audio.alert.play.call_count, 2)
        self.app.audio.alert.reset_mock()
        self.app.values = ["4", "3", "2"]
        self.app.action("solve")
        self.assertFalse(self.app.error)
        self.app.audio.alert.play.assert_not_called()

    def test_zero_step_results_play_error_without_completion_sound(self):
        self.app.audio.alert = Mock()
        self.app.audio.goal = Mock()
        for values in (["6", "4", "3"], ["4", "3", "5"], ["4", "3", "0"]):
            for control in ("solve", "BFS", "DFS"):
                with self.subTest(values=values, control=control):
                    self.app.values = values
                    self.app.audio.alert.reset_mock()
                    self.app.audio.goal.reset_mock()
                    self.app.action(control)
                    self.assertLessEqual(len(self.app.result.states), 1)
                    self.assertFalse(self.app.error)
                    for _ in range(2):
                        self.app.update(.01)
                        self.app.draw()
                    self.app.audio.alert.play.assert_called_once_with(self.app.audio.sounds["error"])
                    self.app.audio.goal.play.assert_not_called()
                    self.app.action(control)
                    self.assertEqual(self.app.audio.alert.play.call_count, 2)

    def test_field_keyboard_and_zero(self):
        self.app.focus = 2
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE, unicode=""))
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_0, unicode="0"))
        self.app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r"))
        self.assertEqual(self.app.result.states, [(0, 0)])
        self.app.draw()

    def test_large_path_and_resized_click(self):
        self.app.values = ["99", "100", "50"]
        self.app.compute()
        self.app.go(len(self.app.result.states)-1)
        self.app.update(30)
        self.assertEqual(tuple(self.app.water), self.app.result.states[-1])
        self.app.draw()
        self.app.window = pygame.display.set_mode((900, 700), pygame.RESIZABLE)
        self.app.draw()
        size, offset = self.app.viewport()
        px = offset[0]+260*size[0]/1200
        py = offset[1]+765*size[1]/800
        self.app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(px, py)))
        self.assertTrue(self.app.playing)


if __name__ == "__main__":
    unittest.main()
