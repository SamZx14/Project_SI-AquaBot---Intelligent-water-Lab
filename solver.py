"""Graph search for the two-jug problem, independent of the graphical UI."""
from collections import deque
from dataclasses import dataclass
from math import gcd
from time import perf_counter


@dataclass
class Result:
    states: list[tuple[int, int]]
    actions: list[str]
    explored: int
    elapsed_ms: float
    message: str


def neighbors(state, a, b):
    """Return legal (state, action) pairs; omit operations with no effect."""
    x, y = state
    ab, ba = min(x, b-y), min(y, a-x)
    moves = [((a, y), "Fill jug A"), ((x, b), "Fill jug B"),
             ((0, y), "Empty jug A"), ((x, 0), "Empty jug B"),
             ((x-ab, y+ab), "Pour A into B"), ((x+ba, y-ba), "Pour B into A")]
    return [(s, action) for s, action in moves if s != state]


def solve(a, b, target, algorithm="BFS"):
    """Reach target in either jug. BFS is shortest; DFS is depth first."""
    if any(type(v) is not int for v in (a, b, target)):
        raise ValueError("Use whole numbers.")
    if not (1 <= a <= 100 and 1 <= b <= 100 and 0 <= target <= 100):
        raise ValueError("Jug sizes: 1-100 L. Target: 0-100 L.")
    if algorithm not in ("BFS", "DFS"):
        raise ValueError("Choose BFS or DFS.")
    start = perf_counter()
    if target > max(a, b) or target % gcd(a, b):
        return Result([], [], 0, (perf_counter()-start)*1000, "This target is unreachable")
    frontier = deque([(0, 0)])
    parents = {(0, 0): None}
    explored = 0
    while frontier:
        state = frontier.popleft() if algorithm == "BFS" else frontier.pop()
        explored += 1
        if target in state:
            states, actions = [], []
            while True:
                states.append(state)
                parent = parents[state]
                if parent is None:
                    break
                state, action = parent
                actions.append(action)
            return Result(states[::-1], ["Start with empty jugs"]+actions[::-1], explored,
                          (perf_counter()-start)*1000,
                          "Shortest solution found" if algorithm == "BFS" else "DFS solution found")
        moves = neighbors(state, a, b)
        if algorithm == "DFS":
            moves.reverse()
        for nxt, action in moves:
            if nxt not in parents:
                parents[nxt] = (state, action)
                frontier.append(nxt)
    return Result([], [], explored, (perf_counter()-start)*1000, "No solution found")
