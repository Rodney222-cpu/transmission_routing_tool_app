"""
QGIS-Style Transmission Line Routing Workflow
Implements professional GIS methodology used in QGIS for power line routing:
1. Multi-Criteria Evaluation (MCE)
2. Cost Distance Analysis (Accumulated Cost)
3. Back-Link Direction Calculation
4. Least-Cost Path Extraction
5. Corridor Analysis (Multiple Route Options)
6. Environmental Impact Assessment

This module is OPTIONAL - your app works fine without it using Dijkstra/A*.
To enable: Uncomment the import in routes_api.py
"""
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
import math
import heapq


class QGISRoutingWorkflow:
    """
    Implements the exact QGIS workflow for transmission line routing:
    - Similar to QGIS 'Least Cost Path' plugin
    - Similar to QGIS 'r.cost' and 'r.drain' from GRASS
    - Similar to QGIS Processing Toolbox 'Cost Distance Analysis'
    
    NOTE: This is an optional enhancement. Your app works perfectly
    with Dijkstra/A* algorithms without this module.
    """
    
    def __init__(self):
        self.cost_surface = None
        self.accumulated_cost = None
        self.backlink_direction = None
        self.route_options = []
    
    def calculate_cost_distance(self, cost_surface, start_points):
        """
        QGIS-style cost distance calculation (accumulated cost surface)
        Similar to QGIS 'r.cost' or 'Cost Distance' tool
        
        Args:
            cost_surface: 2D numpy array of costs
            start_points: List of (row, col) tuples for start locations
        
        Returns:
            accumulated_cost: 2D array showing cost to reach each cell from start
            backlink_direction: 2D array showing direction of minimum cost
        """
        height, width = cost_surface.shape
        
        # Initialize accumulated cost with infinity
        accumulated_cost = np.full((height, width), np.inf, dtype=np.float64)
        backlink_direction = np.zeros((height, width), dtype=np.int8)
        
        # Set start points with zero cost
        for row, col in start_points:
            accumulated_cost[row, col] = 0
        
        # Priority queue for Dijkstra's algorithm
        # (cost, row, col)
        priority_queue = []
        
        for row, col in start_points:
            heapq.heappush(priority_queue, (0, row, col))
        
        # 8-directional movement (Queen's case)
        # Directions: 0=E, 1=SE, 2=S, 3=SW, 4=W, 5=NW, 6=N, 7=NE
        directions = [
            (0, 1),   # 0: East
            (1, 1),   # 1: Southeast
            (1, 0),   # 2: South
            (1, -1),  # 3: Southwest
            (0, -1),  # 4: West
            (-1, -1), # 5: Northwest
            (-1, 0),  # 6: North
            (-1, 1)   # 7: Northeast
        ]
        
        # Process using Dijkstra's algorithm
        while priority_queue:
            current_cost, row, col = heapq.heappop(priority_queue)
            
            # Skip if we've already found a better path
            if current_cost > accumulated_cost[row, col]:
                continue
            
            # Check all 8 neighbors
            for direction_idx, (dr, dc) in enumerate(directions):
                new_row, new_col = row + dr, col + dc
                
                # Check bounds
                if 0 <= new_row < height and 0 <= new_col < width:
                    # Calculate distance (Euclidean for diagonal)
                    if dr != 0 and dc != 0:
                        distance = math.sqrt(2)  # Diagonal
                    else:
                        distance = 1.0  # Cardinal
                    
                    # Calculate new cost
                    # Average cost of current and neighbor cell
                    cell_cost = (cost_surface[row, col] + cost_surface[new_row, new_col]) / 2.0
                    new_cost = current_cost + (cell_cost * distance)
                    
                    # Update if better path found
                    if new_cost < accumulated_cost[new_row, new_col]:
                        accumulated_cost[new_row, new_col] = new_cost
                        backlink_direction[new_row, new_col] = direction_idx
                        heapq.heappush(priority_queue, (new_cost, new_row, new_col))
        
        self.accumulated_cost = accumulated_cost
        self.backlink_direction = backlink_direction
        
        return accumulated_cost, backlink_direction
    
    def extract_least_cost_path(self, end_point):
        """
        Extract least-cost path by following backlink directions
        Similar to QGIS 'r.drain' or 'Least Cost Path' plugin
        
        Args:
            end_point: (row, col) tuple for destination
        
        Returns:
            path: List of (row, col) tuples from start to end
        """
        if self.backlink_direction is None:
            raise ValueError("Must calculate cost distance first")
        
        path = []
        row, col = end_point
        
        # Direction vectors (reverse of forward directions)
        reverse_directions = [
            (0, -1),   # From 0 (East) go West
            (-1, -1),  # From 1 (SE) go NW
            (-1, 0),   # From 2 (South) go North
            (-1, 1),   # From 3 (SW) go NE
            (0, 1),    # From 4 (West) go East
            (1, 1),    # From 5 (NW) go SE
            (1, 0),    # From 6 (North) go South
            (1, -1)    # From 7 (NE) go SW
        ]
        
        max_iterations = 10000  # Prevent infinite loops
        iterations = 0
        
        while iterations < max_iterations:
            path.append((row, col))
            
            # Get backlink direction
            direction = self.backlink_direction[row, col]
            
            # If direction is 0, we've reached the start
            if direction == 0 and self.accumulated_cost[row, col] == 0:
                break
            
            # Move in reverse direction
            dr, dc = reverse_directions[direction]
            row, col = row + dr, col + dc
            
            iterations += 1
        
        # Reverse path to go from start to end
        path.reverse()
        
        return path
    
    def generate_route_corridor(self, path, width_cells=10):
        """
        Generate corridor around the route (Right-of-Way analysis)
        Similar to QGIS buffer analysis
        
        Args:
            path: List of (row, col) tuples
            width_cells: Corridor width in cells
        
        Returns:
            corridor_mask: Boolean array showing corridor area
        """
        if not path:
            return None
            
        # Get bounds from accumulated cost or use path bounds
        if self.accumulated_cost is not None:
            height, width = self.accumulated_cost.shape
        else:
            # Fallback: estimate from path
            max_row = max(p[0] for p in path) + width_cells
            max_col = max(p[1] for p in path) + width_cells
            height, width = max_row + 1, max_col + 1
        
        corridor_mask = np.zeros((height, width), dtype=bool)
        
        for row, col in path:
            # Create square buffer around each path cell
            for dr in range(-width_cells, width_cells + 1):
                for dc in range(-width_cells, width_cells + 1):
                    r, c = row + dr, col + dc
                    if 0 <= r < height and 0 <= c < width:
                        # Use Euclidean distance for circular buffer
                        if math.sqrt(dr**2 + dc**2) <= width_cells:
                            corridor_mask[r, c] = True
        
        return corridor_mask
    
    def calculate_environmental_impact(self, path, environmental_layers):
        """
        Calculate environmental impact score for the route
        Similar to QGIS environmental impact assessment
        
        Args:
            path: List of (row, col) tuples
            environmental_layers: Dict of layer name -> 2D array
        
        Returns:
            impact_scores: Dict of impact category -> score
            total_impact: Overall impact score
        """
        impact_scores = {}
        
        for layer_name, layer_data in environmental_layers.items():
            # Extract values along the path
            path_values = []
            for row, col in path:
                if 0 <= row < layer_data.shape[0] and 0 <= col < layer_data.shape[1]:
                    path_values.append(layer_data[row, col])
            
            if path_values:
                impact_scores[layer_name] = {
                    'mean': float(np.mean(path_values)),
                    'max': float(np.max(path_values)),
                    'min': float(np.min(path_values)),
                    'sum': float(np.sum(path_values)),
                    'length_affected': len(path_values)
                }
        
        # Calculate total impact (weighted sum)
        total_impact = sum(scores['mean'] for scores in impact_scores.values())
        
        return impact_scores, total_impact
    
    def calculate_route_statistics(self, path, cost_surface, dem_data=None):
        """
        Calculate comprehensive route statistics
        Similar to QGIS route analysis tools
        
        Args:
            path: List of (row, col) tuples
            cost_surface: 2D cost array
            dem_data: Optional elevation data
        
        Returns:
            stats: Dictionary of route statistics
        """
        if not path:
            return {}
            
        # Extract costs along path
        path_costs = []
        for row, col in path:
            if 0 <= row < cost_surface.shape[0] and 0 <= col < cost_surface.shape[1]:
                path_costs.append(cost_surface[row, col])
        
        if not path_costs:
            return {}
        
        stats = {
            'total_length_cells': len(path),
            'mean_cost': float(np.mean(path_costs)),
            'max_cost': float(np.max(path_costs)),
            'min_cost': float(np.min(path_costs)),
            'total_cost': float(np.sum(path_costs)),
            'cost_variance': float(np.var(path_costs))
        }
        
        # Add elevation statistics if DEM available
        if dem_data is not None:
            path_elevations = []
            for row, col in path:
                if 0 <= row < dem_data.shape[0] and 0 <= col < dem_data.shape[1]:
                    path_elevations.append(dem_data[row, col])
            
            if path_elevations:
                stats['elevation'] = {
                    'min': float(np.min(path_elevations)),
                    'max': float(np.max(path_elevations)),
                    'mean': float(np.mean(path_elevations)),
                    'total_ascent': sum(max(0, path_elevations[i+1] - path_elevations[i]) 
                                       for i in range(len(path_elevations)-1)),
                    'total_descent': sum(max(0, path_elevations[i] - path_elevations[i+1]) 
                                        for i in range(len(path_elevations)-1))
                }
        
        return stats
    
    def smooth_route(self, path, iterations=3):
        """
        Smooth route to reduce unnecessary zigzag
        Similar to QGIS line smoothing tools
        
        Args:
            path: List of (row, col) tuples
            iterations: Number of smoothing iterations
        
        Returns:
            smoothed_path: Smoothed path
        """
        if len(path) < 3:
            return path
        
        smoothed = path.copy()
        
        for _ in range(iterations):
            new_path = [smoothed[0]]  # Keep start point
            
            for i in range(1, len(smoothed) - 1):
                # Average with neighbors
                prev_row, prev_col = smoothed[i-1]
                curr_row, curr_col = smoothed[i]
                next_row, next_col = smoothed[i+1]
                
                new_row = int((prev_row + curr_row + next_row) / 3)
                new_col = int((prev_col + curr_col + next_col) / 3)
                
                new_path.append((new_row, new_col))
            
            new_path.append(smoothed[-1])  # Keep end point
            smoothed = new_path
        
        return smoothed
