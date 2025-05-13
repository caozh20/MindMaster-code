from astar import AStar
import sys
sys.path.append(".")
import math
from core.const import WORLD_WIDTH, WORLD_HEIGHT


# changed from the demo
class Astar_Solver(AStar):

    """sample use of the astar algorithm. In this exemple we work on a maze made of ascii characters,
    and a 'node' is just a (x,y) tuple that represents a reachable position"""

    def __init__(self, obstacle):
        self.obstacle = obstacle

    def heuristic_cost_estimate(self, n1, n2):
        """computes the 'direct' distance between two (x,y) tuples"""
        (x1, y1) = n1
        (x2, y2) = n2
        return math.hypot(x2 - x1, y2 - y1)

    def distance_between(self, n1, n2):
        """this method always returns 1, as two 'neighbors' are always adajcent"""
        return 1
    def is_goal_reached(self, current, goal):
        """ returns true when we can consider that 'current' is the goal"""
        if abs(current[0] - goal[0]) <= 5 and abs(current[1] - goal[1]) <= 5:
            return True
        return current == goal

    def neighbors(self, node):
        """ for a given coordinate in the maze, returns up to 4 adjacent(north,east,south,west)
            nodes that can be reached (=any adjacent coordinate that is not a wall)
        """
        x, y = node
        grid = 5
        neighbors = []
        for nx, ny in [(x, y - grid), (x, y + grid), (x - grid, y), (x + grid, y)]:
            flag = True
            if -WORLD_WIDTH <= nx < WORLD_WIDTH and -WORLD_HEIGHT <= ny < WORLD_HEIGHT:
                for entity in self.obstacle:
                    if (entity.position[0] - entity.size[0] / 2 - 50) <= nx < (entity.position[0] + entity.size[0] / 2 + 50) \
                            and (entity.position[1] - entity.size[1] / 2 - 50) <= ny < (entity.position[1] + entity.size[1] / 2 + 50):
                        flag = False
            else:
                flag = False
            if flag:
                neighbors.append((nx, ny))
        return neighbors
