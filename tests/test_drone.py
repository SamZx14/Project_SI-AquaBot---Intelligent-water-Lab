"""Water conservation and stage ordering during sequential transfers."""
import unittest
from drone import DroneController, JUG_CENTERS, SUPPLY_X, DRAIN_X


class DroneTests(unittest.TestCase):
    def test_transfer_collects_before_delivering_and_conserves_water(self):
        drone = DroneController()
        drone.water = [0.0, 3.0]
        drone.x = JUG_CENTERS[1]
        drone.start((3, 0))
        phases = set()
        while not drone.finished:
            phase = drone.phase
            phases.add(phase)
            drone.advance(0.01)
            phase = drone.phase
            self.assertAlmostEqual(sum(drone.water)+drone.cargo, 3.0)
            if phase in ("grip", "lift", "carry", "tilt"):
                self.assertEqual(drone.water[0], 0)
            self.assertEqual(drone.cargo, 0)
            self.assertEqual(drone.tube, 0)
        self.assertEqual(drone.water, [3, 0])
        self.assertEqual(drone.cargo, 0)
        self.assertEqual(phases, {"grip", "lift", "carry", "tilt", "transfer", "upright", "return", "land", "release"})

    def test_partial_transfer_leaves_source_remainder(self):
        drone = DroneController()
        drone.water = [3.0, 3.0]
        drone.x = JUG_CENTERS[1]
        drone.start((4, 2))
        peak_cargo = 0
        while not drone.finished:
            drone.advance(0.01)
            peak_cargo = max(peak_cargo, drone.cargo)
            self.assertAlmostEqual(sum(drone.water)+drone.cargo, 6)
        self.assertEqual(drone.water, [4, 2])
        self.assertAlmostEqual(peak_cargo, 0)

    def test_fill_collects_supply_before_flying_and_pouring(self):
        drone = DroneController()
        drone.start((0, 3))
        while not drone.finished:
            drone.advance(0.01)
            phase = drone.phase
            if phase in ("lower", "refill", "retract", "fly"):
                self.assertEqual(drone.water, [0, 0])
            if phase == "fly":
                self.assertEqual(drone.cargo, 3)
                self.assertEqual(drone.tube, 0)
        self.assertEqual(drone.water, [0, 3])
        self.assertEqual(drone.cargo, 0)

    def test_empty_uses_drain_and_does_not_fill_other_jug(self):
        drone = DroneController()
        drone.water = [4.0, 1.0]
        drone.start((0, 1))
        phases = set()
        while not drone.finished:
            phases.add(drone.phase)
            drone.advance(0.01)
            self.assertEqual(drone.water[1], 1)
        self.assertIn("empty", phases)
        self.assertEqual(drone.water, [0, 1])
        self.assertEqual(drone.x, JUG_CENTERS[0])
        self.assertEqual(drone.cargo, 0)

    def test_interrupted_transfer_replans_without_negative_levels(self):
        drone = DroneController()
        drone.water = [0.0, 3.0]
        drone.x = JUG_CENTERS[1]
        drone.start((3, 0))
        drone.advance(0.75)
        self.assertIsNotNone(drone.held_jug)
        self.assertLess(drone.pose[1], 0)
        drone.start((4, 2))
        while not drone.finished:
            drone.advance(0.05)
            self.assertTrue(all(v >= 0 for v in drone.water))
            self.assertGreaterEqual(drone.cargo, 0)
            self.assertGreaterEqual(drone.tube, 0)
            self.assertLessEqual(drone.tube, 1)
        self.assertEqual(drone.water, [4, 2])
        self.assertEqual(drone.cargo, 0)
        drone.reset()
        self.assertEqual(drone.water, [0, 0])
        self.assertEqual(drone.x, SUPPLY_X)


if __name__ == "__main__":
    unittest.main()
