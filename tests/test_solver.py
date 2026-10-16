import unittest
from collections import deque
from math import gcd
from solver import solve, neighbors


class SolverTests(unittest.TestCase):
    def test_classic_shortest(self):
        r = solve(4, 3, 2)
        self.assertEqual(len(r.actions)-1, 4)
        self.assertIn(2, r.states[-1])

    def test_legal_paths_and_reachability(self):
        for a in range(1, 9):
            for b in range(1, 9):
                for target in range(10):
                    for algorithm in ("BFS", "DFS"):
                        r = solve(a, b, target, algorithm)
                        possible = target <= max(a, b) and target % gcd(a, b) == 0
                        self.assertEqual(bool(r.states), possible)
                        if r.states:
                            self.assertEqual(r.states[0], (0, 0))
                            self.assertIn(target, r.states[-1])
                            self.assertEqual(len(r.states), len(r.actions))
                            for old, new, action in zip(r.states, r.states[1:], r.actions[1:]):
                                self.assertIn((new, action), neighbors(old, a, b))

    def test_zero_target(self):
        self.assertEqual(solve(4, 3, 0).states, [(0, 0)])

    def test_validation(self):
        for args in ((0, 3, 2), (-1, 3, 2), (4, 3, -1), (101, 3, 2), (4.0, 3, 2), (4, 3, 2, "bad")):
            with self.assertRaises(ValueError):
                solve(*args)

    def test_bfs_distances(self):
        for a, b in ((4, 3), (5, 7), (8, 5), (6, 4), (99, 100)):
            distances = {(0, 0): 0}
            queue = deque([(0, 0)])
            while queue:
                state = queue.popleft()
                for nxt, _ in neighbors(state, a, b):
                    if nxt not in distances:
                        distances[nxt] = distances[state]+1
                        queue.append(nxt)
            for target in range(max(a, b)+1):
                expected = min((d for state, d in distances.items() if target in state), default=None)
                r = solve(a, b, target)
                self.assertEqual(len(r.states)-1 if r.states else None, expected)


if __name__ == "__main__":
    unittest.main()
