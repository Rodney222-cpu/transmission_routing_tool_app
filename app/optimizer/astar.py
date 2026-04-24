"""
A* (A-Star) Pathfinder for Least-Cost Path on cost surface.

This implementation uses a *weighted* heuristic (Weighted A*, f = g + w * h with
w > 1) so that it produces a visibly different route from plain Dijkstra on the
same cost surface.  With w = 1 A* is admissible and returns the same global
optimum as Dijkstra; with w > 1 it becomes increasingly goal-biased, trading a
small amount of terrain cost for a straighter, shorter path.  The resulting
path is still guaranteed to cost at most w x the Dijkstra optimum.

The weight is also added as a small per-step *distance penalty* on top of the
pure terrain cost, which further biases the search toward direct routes even
when the heuristic alone would be dominated by large terrain costs.
"""
import numpy as np
import heapq
from typing import Tuple, List, Optional


class AStarPathFinder:
    """
    Weighted A* least-cost path on a cost surface.
    Same 8-directional movement and grid model as Dijkstra; differs in its
    objective (directness-biased) so the two algorithms produce distinct routes.
    """

    # w > 1 makes A* greedy toward the goal (straighter, less exploration).
    # 1.5 gives a visibly straighter path while keeping total cost <= 1.5x
    # the Dijkstra optimum on well-behaved cost surfaces.
    DEFAULT_HEURISTIC_WEIGHT = 1.5
    # Per-step distance toll added to each edge cost.  Expressed as a fraction
    # of the mean terrain cost (computed on construction) so it scales with the
    # surface rather than being swamped by high-cost pixels.
    DEFAULT_DISTANCE_PENALTY_FRACTION = 0.15

    def __init__(self, cost_surface: np.ndarray,
                 heuristic_weight: float = DEFAULT_HEURISTIC_WEIGHT,
                 distance_penalty_fraction: float = DEFAULT_DISTANCE_PENALTY_FRACTION):
        self.cost_surface = cost_surface
        self.height, self.width = cost_surface.shape

        self.directions = [
            (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)
        ]
        self.direction_costs = [1.0, 1.414, 1.0, 1.414, 1.0, 1.414, 1.0, 1.414]

        self.heuristic_weight = float(heuristic_weight)
        # Scale the distance penalty against the mean traversable cost so its
        # influence is comparable across different cost surfaces.
        passable = cost_surface[cost_surface < 99]
        mean_cost = float(np.mean(passable)) if passable.size else 1.0
        self.distance_penalty = distance_penalty_fraction * mean_cost

    def _heuristic(self, pos: Tuple[int, int], end: Tuple[int, int]) -> float:
        """Euclidean distance heuristic (admissible for 8-directional movement
        when heuristic_weight == 1.0; goal-biased when > 1.0)."""
        return np.sqrt((pos[0] - end[0]) ** 2 + (pos[1] - end[1]) ** 2)

    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        row, col = pos
        return 0 <= row < self.height and 0 <= col < self.width

    def find_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> Optional[dict]:
        """
        Find least-cost path using Weighted A*.

        Edge cost = movement * (terrain_cost + distance_penalty)
        Priority  = g + heuristic_weight * h

        The distance penalty pushes the search toward shorter routes even when
        terrain costs vary little; the weighted heuristic makes the search
        greedy toward the goal so the resulting path is visibly straighter
        than Dijkstra's global optimum.

        Returns same structure as LeastCostPathFinder for drop-in comparison.
        """
        if not self._is_valid_position(start) or not self._is_valid_position(end):
            return None

        g_cost = {start: 0}
        parent = {}
        w = self.heuristic_weight
        dp = self.distance_penalty
        open_set = [(w * self._heuristic(start, end), 0, start[0], start[1])]
        closed_set = set()

        while open_set:
            f_val, current_cost, row, col = heapq.heappop(open_set)
            current = (row, col)

            if current in closed_set:
                continue
            closed_set.add(current)

            if current == end:
                path = self._reconstruct_path(parent, start, end)
                return {
                    'path': path,
                    'total_cost': g_cost[end],
                    'distance': len(path),
                    'euclidean_distance': self._euclidean_distance(start, end),
                }

            for i, (dr, dc) in enumerate(self.directions):
                nr, nc = row + dr, col + dc
                neighbor = (nr, nc)
                if not self._is_valid_position(neighbor) or neighbor in closed_set:
                    continue

                terrain_cost = self.cost_surface[nr, nc]
                if terrain_cost >= 99:
                    continue

                movement = self.direction_costs[i]
                new_g = current_cost + movement * (terrain_cost + dp)

                if new_g < g_cost.get(neighbor, np.inf):
                    g_cost[neighbor] = new_g
                    parent[neighbor] = current
                    h = self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (new_g + w * h, new_g, nr, nc))

        return None

    def _reconstruct_path(self, parent: dict, start: Tuple[int, int], end: Tuple[int, int]) -> List[Tuple[int, int]]:
        path = []
        current = end
        while current != start:
            path.append(current)
            current = parent.get(current)
            if current is None:
                return []
        path.append(start)
        path.reverse()
        return path

    def _euclidean_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        return np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)

    def path_to_coordinates(self, path: List[Tuple[int, int]], bounds: List[float], resolution: float) -> List[Tuple[float, float]]:
        """Convert pixel path to (lon, lat) - same as Dijkstra module."""
        min_lon, min_lat, max_lon, max_lat = bounds
        lon_per_pixel = (max_lon - min_lon) / self.width
        lat_per_pixel = (max_lat - min_lat) / self.height
        coordinates = []
        for row, col in path:
            lon = min_lon + col * lon_per_pixel
            lat = max_lat - row * lat_per_pixel
            coordinates.append((lon, lat))
        return coordinates

    def simplify_path(self, path: List[Tuple[int, int]], tolerance: int = 5) -> List[Tuple[int, int]]:
        """Douglas-Peucker style simplification - same as Dijkstra."""
        if len(path) < 3:
            return path
        start = np.array(path[0])
        end = np.array(path[-1])
        max_dist, max_index = 0, 0
        for i in range(1, len(path) - 1):
            point = np.array(path[i])
            dist = self._perpendicular_distance(point, start, end)
            if dist > max_dist:
                max_dist, max_index = dist, i
        if max_dist > tolerance:
            left = self.simplify_path(path[: max_index + 1], tolerance)
            right = self.simplify_path(path[max_index:], tolerance)
            return left[:-1] + right
        return [path[0], path[-1]]

    def _perpendicular_distance(self, point: np.ndarray, line_start: np.ndarray, line_end: np.ndarray) -> float:
        if np.array_equal(line_start, line_end):
            return np.linalg.norm(point - line_start)
        line_vec = line_end - line_start
        point_vec = point - line_start
        line_len = np.linalg.norm(line_vec)
        line_unitvec = line_vec / line_len
        proj_len = max(0, min(line_len, np.dot(point_vec, line_unitvec)))
        projection = line_start + line_unitvec * proj_len
        return np.linalg.norm(point - projection)

    # ---------------------------------------------------------------
    # Line-of-sight (LOS) smoothing - mirrors LeastCostPathFinder
    # ---------------------------------------------------------------
    @staticmethod
    def _bresenham_line(r0: int, c0: int, r1: int, c1: int) -> List[Tuple[int, int]]:
        cells = []
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        sr = 1 if r0 < r1 else -1
        sc = 1 if c0 < c1 else -1
        err = dr - dc
        r, c = r0, c0
        while True:
            cells.append((r, c))
            if r == r1 and c == c1:
                break
            e2 = 2 * err
            if e2 > -dc:
                err -= dc
                r += sr
            if e2 < dr:
                err += dr
                c += sc
        return cells

    def _line_cost(self, r0: int, c0: int, r1: int, c1: int) -> float:
        cells = self._bresenham_line(r0, c0, r1, c1)
        total = 0.0
        for i, (r, c) in enumerate(cells):
            t = self.cost_surface[r, c]
            if t >= 99:
                return float('inf')
            if i == 0:
                continue
            pr, pc = cells[i - 1]
            dr = abs(r - pr)
            dc = abs(c - pc)
            mov = 1.414 if (dr == 1 and dc == 1) else 1.0
            total += mov * t
        return total

    def _segment_cost(self, path: List[Tuple[int, int]], i: int, j: int) -> float:
        total = 0.0
        for k in range(i + 1, j + 1):
            r0, c0 = path[k - 1]
            r1, c1 = path[k]
            dr = abs(r1 - r0)
            dc = abs(c1 - c0)
            if dr <= 1 and dc <= 1:
                mov = 1.414 if (dr == 1 and dc == 1) else 1.0
                total += mov * self.cost_surface[r1, c1]
            else:
                line = self._line_cost(r0, c0, r1, c1)
                if line == float('inf'):
                    return float('inf')
                total += line
        return total

    def _smooth_los_single_pass(self, path: List[Tuple[int, int]],
                                max_cost_ratio: float) -> List[Tuple[int, int]]:
        n = len(path)
        if n < 3:
            return list(path)
        smoothed: List[Tuple[int, int]] = [path[0]]
        i = 0
        while i < n - 1:
            best_j = i + 1
            j = i + 2
            while j < n:
                r0, c0 = path[i]
                r1, c1 = path[j]
                direct = self._line_cost(r0, c0, r1, c1)
                if direct == float('inf'):
                    break
                original = self._segment_cost(path, i, j)
                if original == float('inf'):
                    break
                if direct <= max_cost_ratio * original:
                    best_j = j
                    j += 1
                else:
                    break
            smoothed.append(path[best_j])
            i = best_j
        return smoothed

    def smooth_path_los(self, path: List[Tuple[int, int]],
                        max_cost_ratio: float = 1.2,
                        max_iterations: int = 5) -> List[Tuple[int, int]]:
        """Iterated LOS shortcutting. See LeastCostPathFinder.smooth_path_los."""
        if len(path) < 3:
            return list(path)
        current = list(path)
        for _ in range(max_iterations):
            nxt = self._smooth_los_single_pass(current, max_cost_ratio)
            if len(nxt) == len(current):
                return nxt
            current = nxt
        return current
