"""
A* (A-Star) Pathfinder for Least-Cost Path on cost surface
Uses heuristic (e.g. Euclidean distance) for faster convergence than plain Dijkstra.
Useful for comparing route results with the existing Dijkstra implementation.
"""
import numpy as np
import heapq
from typing import Tuple, List, Optional


class AStarPathFinder:
    """
    A* algorithm for least-cost path on a cost surface.
    Same 8-directional movement and cost model as Dijkstra for fair comparison.
    """

    def __init__(self, cost_surface: np.ndarray):
        self.cost_surface = cost_surface
        self.height, self.width = cost_surface.shape

        self.directions = [
            (-1, 0), (-1, 1), (0, 1), (1, 1), (1, 0), (1, -1), (0, -1), (-1, -1)
        ]
        self.direction_costs = [1.0, 1.414, 1.0, 1.414, 1.0, 1.414, 1.0, 1.414]

    def _heuristic(self, pos: Tuple[int, int], end: Tuple[int, int]) -> float:
        """Euclidean distance heuristic (admissible for 8-directional movement)."""
        return np.sqrt((pos[0] - end[0]) ** 2 + (pos[1] - end[1]) ** 2)

    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        row, col = pos
        return 0 <= row < self.height and 0 <= col < self.width

    def find_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> Optional[dict]:
        """
        Find least-cost path using A*.
        Returns same structure as LeastCostPathFinder for drop-in comparison.
        Memory-optimized: uses dictionary instead of full array for g_cost.
        """
        if not self._is_valid_position(start) or not self._is_valid_position(end):
            return None

        # Use dictionary instead of full array to save memory
        # Only stores costs for visited nodes instead of all possible nodes
        g_cost = {start: 0}
        parent = {}
        # Priority: f = g + h (heap by f, then by g for tie-breaking)
        open_set = [(0 + self._heuristic(start, end), 0, start[0], start[1])]
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
                new_g = current_cost + (movement * terrain_cost)

                # Use dictionary.get() with infinity as default
                if new_g < g_cost.get(neighbor, np.inf):
                    g_cost[neighbor] = new_g
                    parent[neighbor] = current
                    h = self._heuristic(neighbor, end)
                    heapq.heappush(open_set, (new_g + h, new_g, nr, nc))

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
