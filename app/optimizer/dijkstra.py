"""
Dijkstra's Algorithm for Least-Cost Path (LCP) Routing
Optimized for transmission line routing on cost surfaces
"""
import numpy as np
import heapq
from typing import Tuple, List, Optional


class LeastCostPathFinder:
    """
    Implements Dijkstra's algorithm for finding the least-cost path
    on a cost surface raster for transmission line routing
    """
    
    def __init__(self, cost_surface: np.ndarray):
        """
        Initialize the pathfinder
        
        Args:
            cost_surface: 2D numpy array representing traversal costs
        """
        self.cost_surface = cost_surface
        self.height, self.width = cost_surface.shape
        
        # 8-directional movement (including diagonals)
        self.directions = [
            (-1, 0),   # North
            (-1, 1),   # Northeast
            (0, 1),    # East
            (1, 1),    # Southeast
            (1, 0),    # South
            (1, -1),   # Southwest
            (0, -1),   # West
            (-1, -1)   # Northwest
        ]
        
        # Diagonal movement costs more (sqrt(2) ≈ 1.414)
        self.direction_costs = [1.0, 1.414, 1.0, 1.414, 1.0, 1.414, 1.0, 1.414]
    
    def find_path(self, start: Tuple[int, int], end: Tuple[int, int]) -> Optional[dict]:
        """
        Find the least-cost path from start to end using Dijkstra's algorithm
        Memory-optimized: uses dictionary instead of full array for g_cost.

        Args:
            start: (row, col) starting position
            end: (row, col) ending position

        Returns:
            dict containing:
                - path: List of (row, col) coordinates
                - total_cost: Accumulated cost along the path
                - distance: Euclidean distance in pixels
        """
        # Validate inputs
        if not self._is_valid_position(start) or not self._is_valid_position(end):
            return None

        # Initialize data structures
        # Use dictionary instead of full array to save memory
        # Only stores costs for visited nodes instead of all possible nodes
        g_cost = {start: 0}

        # Parent tracking for path reconstruction
        parent = {}

        # Priority queue: (cost, row, col)
        open_set = [(0, start[0], start[1])]

        # Closed set to track visited nodes
        closed_set = set()

        while open_set:
            current_cost, row, col = heapq.heappop(open_set)
            current = (row, col)

            # Skip if already processed
            if current in closed_set:
                continue

            # Mark as visited
            closed_set.add(current)

            # Check if we reached the goal
            if current == end:
                path = self._reconstruct_path(parent, start, end)
                return {
                    'path': path,
                    'total_cost': g_cost[end],
                    'distance': len(path),
                    'euclidean_distance': self._euclidean_distance(start, end)
                }

            # Explore neighbors
            for i, (dr, dc) in enumerate(self.directions):
                neighbor_row = row + dr
                neighbor_col = col + dc
                neighbor = (neighbor_row, neighbor_col)

                # Skip invalid positions
                if not self._is_valid_position(neighbor):
                    continue

                # Skip already visited
                if neighbor in closed_set:
                    continue

                # Calculate cost to reach neighbor
                # Cost = current cost + movement cost * terrain cost
                movement_cost = self.direction_costs[i]
                terrain_cost = self.cost_surface[neighbor_row, neighbor_col]

                # Handle invalid terrain (e.g., water bodies with very high cost)
                if terrain_cost >= 99:  # Threshold for impassable terrain
                    continue

                new_cost = current_cost + (movement_cost * terrain_cost)

                # Update if we found a better path
                # Use dictionary.get() with infinity as default
                if new_cost < g_cost.get(neighbor, np.inf):
                    g_cost[neighbor] = new_cost
                    parent[neighbor] = current
                    heapq.heappush(open_set, (new_cost, neighbor_row, neighbor_col))

        # No path found
        return None
    
    def _is_valid_position(self, pos: Tuple[int, int]) -> bool:
        """Check if position is within bounds"""
        row, col = pos
        return 0 <= row < self.height and 0 <= col < self.width
    
    def _reconstruct_path(self, parent: dict, start: Tuple[int, int], 
                         end: Tuple[int, int]) -> List[Tuple[int, int]]:
        """
        Reconstruct path from parent dictionary
        
        Args:
            parent: Dictionary mapping each node to its parent
            start: Starting position
            end: Ending position
        
        Returns:
            List of (row, col) coordinates from start to end
        """
        path = []
        current = end
        
        while current != start:
            path.append(current)
            current = parent.get(current)
            if current is None:
                return []  # Path reconstruction failed
        
        path.append(start)
        path.reverse()
        
        return path
    
    def _euclidean_distance(self, pos1: Tuple[int, int], pos2: Tuple[int, int]) -> float:
        """Calculate Euclidean distance between two positions"""
        return np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)

    def path_to_coordinates(self, path: List[Tuple[int, int]],
                           bounds: List[float], resolution: float) -> List[Tuple[float, float]]:
        """
        Convert pixel path to geographic coordinates

        Args:
            path: List of (row, col) pixel coordinates
            bounds: [min_lon, min_lat, max_lon, max_lat]
            resolution: Meters per pixel

        Returns:
            List of (lon, lat) geographic coordinates
        """
        min_lon, min_lat, max_lon, max_lat = bounds

        # Calculate pixel to coordinate conversion
        lon_per_pixel = (max_lon - min_lon) / self.width
        lat_per_pixel = (max_lat - min_lat) / self.height

        coordinates = []
        for row, col in path:
            lon = min_lon + (col * lon_per_pixel)
            lat = max_lat - (row * lat_per_pixel)  # Flip Y axis
            coordinates.append((lon, lat))

        return coordinates

    def simplify_path(self, path: List[Tuple[int, int]], tolerance: int = 5) -> List[Tuple[int, int]]:
        """
        Simplify path using Douglas-Peucker algorithm
        Reduces number of points while maintaining path shape

        Args:
            path: List of (row, col) coordinates
            tolerance: Simplification tolerance in pixels

        Returns:
            Simplified path
        """
        if len(path) < 3:
            return path

        # Find the point with maximum distance from line segment
        start = np.array(path[0])
        end = np.array(path[-1])

        max_dist = 0
        max_index = 0

        for i in range(1, len(path) - 1):
            point = np.array(path[i])
            dist = self._perpendicular_distance(point, start, end)

            if dist > max_dist:
                max_dist = dist
                max_index = i

        # If max distance is greater than tolerance, recursively simplify
        if max_dist > tolerance:
            # Recursive call
            left = self.simplify_path(path[:max_index + 1], tolerance)
            right = self.simplify_path(path[max_index:], tolerance)

            # Combine results (remove duplicate middle point)
            return left[:-1] + right
        else:
            # Return endpoints only
            return [path[0], path[-1]]

    def _perpendicular_distance(self, point: np.ndarray, line_start: np.ndarray,
                               line_end: np.ndarray) -> float:
        """Calculate perpendicular distance from point to line segment"""
        if np.array_equal(line_start, line_end):
            return np.linalg.norm(point - line_start)

        # Vector from line_start to line_end
        line_vec = line_end - line_start
        # Vector from line_start to point
        point_vec = point - line_start

        # Project point onto line
        line_len = np.linalg.norm(line_vec)
        line_unitvec = line_vec / line_len
        projection_length = np.dot(point_vec, line_unitvec)

        # Clamp to line segment
        projection_length = max(0, min(line_len, projection_length))
        projection = line_start + line_unitvec * projection_length

        # Return distance from point to projection
        return np.linalg.norm(point - projection)

    # ---------------------------------------------------------------
    # Line-of-sight (LOS) smoothing
    # ---------------------------------------------------------------
    # The 8-connected grid search produces a staircase zigzag whenever the
    # true bearing between two points is not a multiple of 45 deg. The raw
    # path also contains tiny wiggles wherever two neighbours have nearly
    # identical cost. Both are pure artefacts of the grid - they add length
    # and bends without avoiding anything meaningful.
    #
    # smooth_path_los() walks the path and greedily replaces A->B->...->C
    # with the direct line A->C whenever the straight line:
    #   - does not cross any impassable cell (cost >= 99), AND
    #   - has total Dijkstra-style cost not exceeding
    #     max_cost_ratio x the zigzag's original cost.
    # Shortcuts through obstacles or significantly more expensive terrain are
    # rejected automatically, so legitimate detours are preserved.

    @staticmethod
    def _bresenham_line(r0: int, c0: int, r1: int, c1: int) -> List[Tuple[int, int]]:
        """Return the list of integer cells on the line from (r0,c0) to (r1,c1), inclusive."""
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
        """Dijkstra-style cost of the straight line between two cells.
        Returns +inf if the line crosses any impassable cell (cost >= 99)."""
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
        """Dijkstra-style cost along path[i..j]. Grid-adjacent steps use the
        8-neighbour cost; non-adjacent hops (produced by prior smoothing) are
        priced via the Bresenham line integral so iterated passes stay
        mathematically consistent. Returns +inf if any segment is blocked."""
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
        """One greedy forward pass of LOS shortcutting. See smooth_path_los."""
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
        """Collapse grid-staircase zigzag via iterated line-of-sight shortcutting.

        Args:
            path: Raw grid path from find_path(), list of (row, col).
            max_cost_ratio: Shortcut accepted if its cost <= ratio x original.
                Default 1.2 tolerates small cost fluctuations along otherwise
                clear terrain while still rejecting genuine obstacle detours
                (which typically cost 2x+ of the equivalent straight line).
            max_iterations: Re-run the greedy pass up to this many times.
                Later passes find shortcuts that only became evaluable once an
                earlier pass thinned the vertex list. Converges quickly (1-3
                iterations on most real paths).

        Returns:
            A list of (row, col) vertices with the same start/end as path but
            typically far fewer bends. Consecutive vertices are no longer
            required to be grid-adjacent.
        """
        if len(path) < 3:
            return list(path)
        current = list(path)
        for _ in range(max_iterations):
            nxt = self._smooth_los_single_pass(current, max_cost_ratio)
            if len(nxt) == len(current):
                return nxt
            current = nxt
        return current

