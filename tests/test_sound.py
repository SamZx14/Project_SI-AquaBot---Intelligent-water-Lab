"""Sound lifecycle and animation mapping checks without speaker playback."""
import os
os.environ["SDL_AUDIODRIVER"] = "dummy"
import unittest
from unittest.mock import Mock, patch
import pygame
from sound import SoundEffects


class AudioTests(unittest.TestCase):
    def setUp(self):
        self.audio = SoundEffects()
        self.assertTrue(self.audio.available)
        self.audio.effect = Mock()
        self.audio.goal = Mock()

    def tearDown(self):
        pygame.mixer.quit()

    def test_all_recordings_decode(self):
        self.assertEqual(len(self.audio.sounds), 8)
        for sound in self.audio.sounds.values():
            self.assertGreater(sound.get_length(), 0)

    def test_phase_changes_switch_sounds_without_restarting_each_frame(self):
        for phase, name in (("fly", "flight"), ("grip", "arm"),
                            ("pour", "fill"), ("transfer", "fill"),
                            ("pour", "fill"), ("refill", "suction"),
                            ("empty", "drain"), ("release", "arm")):
            self.audio.sync(phase)
            self.audio.effect.play.assert_called_with(self.audio.sounds[name], loops=-1)
            count = self.audio.effect.play.call_count
            self.audio.sync(phase)
            self.assertEqual(self.audio.effect.play.call_count, count)
        self.audio.sync("idle")
        self.assertIsNone(self.audio.current)
        self.audio.effect.stop.assert_called()

    def test_arrival_pause_resume_and_reset(self):
        self.audio.sync("idle", arriving=True)
        self.assertEqual(self.audio.current, "flight")
        self.audio.sync("idle", arriving=True, paused=True)
        self.audio.effect.pause.assert_called_once()
        self.audio.sync("idle", arriving=True)
        self.assertEqual(self.audio.effect.play.call_count, 1)
        self.audio.effect.unpause.assert_called()
        self.audio.stop()
        self.audio.effect.stop.assert_called()
        self.audio.goal.stop.assert_called_once()
        self.assertIsNone(self.audio.current)

    def test_goal_only_plays_once_until_reset(self):
        for _ in range(10):
            self.audio.sync("idle", complete=True)
        self.audio.goal.play.assert_called_once_with(self.audio.sounds["complete"])
        self.audio.stop()
        self.audio.sync("idle", complete=True)
        self.assertEqual(self.audio.goal.play.call_count, 2)

    def test_missing_device_does_not_crash_app(self):
        pygame.mixer.quit()
        with patch("sound.pygame.mixer.init", side_effect=pygame.error("No device")):
            with self.assertWarns(UserWarning):
                audio = SoundEffects()
        audio.sync("fly")
        audio.error()
        audio.stop()
        self.assertFalse(audio.available)
