from quadtree import Point, Rectangle
from egene import pygameTools as pgt
import pygame
import time
import bisect


def remove_list_items(L, black_list):
    newL = []
    for v in L:
        if v not in black_list:
            newL.append(v)
    return newL


# Desired connection can be used so the nearest node that can be pathed to some other node is returned
def nearest_node_by_cansee_and_distance(point, map, desired_connection=None):
    t1 = time.time()
    search_size = 100
    wh = len(map.node_map) * map.scale
    ww = len(map.node_map[0]) * map.scale

    points_checked = []

    while True:
        cansee = []
        search_area = Rectangle(point.x - search_size / 2, point.y - search_size / 2, search_size, search_size)
        # Trimming search_area to map limits
        search_area.x = max(search_area.x, 0)
        search_area.y = max(search_area.y, 0)
        search_area.w = min(search_area.x + search_area.w, ww) - search_area.x
        search_area.h = min(search_area.y + search_area.h, wh) - search_area.y

        ps = map.node_quadtree.query(Rectangle(point.x - search_size / 2, point.y - search_size / 2, search_size, search_size))

        # Removing points that have already been checked because they continue to show up in the expanding search area
        ps = remove_list_items(ps, points_checked)
        points_checked += ps
        for p in ps:
            if not map.line_blocked(point, p):
                cansee.append(p)
        if len(cansee) > 0:
            cansee.sort(key=lambda n: pgt.cdistance(point.x, point.y, n.x, n.y))
            if desired_connection is not None:  # If this point must be pathable to another point
                # print("checking for if pathable")
                for c in cansee:  # Check all nodes to see if a path can be made
                    if map.path_lookup(c, desired_connection) is not None:
                        # print("Found a cansee point with path with search size of:", search_size)
                        # print("Took this much time:", time.time() - t1)
                        return c
                # At this point all nodes failed so search size must increase
            else:
                return cansee[0]

        if (search_area.w == ww and search_area.h == wh) or time.time() - t1 > .1:
            print("SEARCH SIZE MAX HIT or Timelimit hit DOING DISTANCE ONLY:", search_size)
            t2 = time.time()
            print("Time to get here:", t2 - t1)
            p = nearest_node_by_distance(point, map, desired_connection)  # Give up on line of sight
            print("Time to sort:", time.time() - t2)
            print("Total Time:", time.time() - t1)
            return p

        search_size += map.scale * 4
        # print("Search size:", search_size)


def nearest_node_by_distance(point, map, desired_connection):
    # When n is not 0 we are searching for the nearest node, so line of sight is less important
    # print("map nodes:", [(n.x, n.y) for n in map.nodes])
    if desired_connection is not None:
        return sorted(map.nodes, key=lambda n: pgt.cdistance(n.x, n.y, point.x, point.y) if map.path_lookup(n, desired_connection) is not None else float("inf"))[0]
    else:
        return sorted(map.nodes, key=lambda n: pgt.cdistance(n.x, n.y, point.x, point.y))[0]


class SimplePath:
    def __init__(self, points):
        self.points = points
        self.nodes = points
        self._length = None

    def __len__(self):
        return len(self.points)

    def __getitem__(self, path_num):
        return self.points[path_num]

    def draw(self, surface):
        for i, n in enumerate(self.points):
            pygame.draw.circle(surface, (0, 0, 255), (n.x, n.y), 3)

            try:
                pygame.draw.line(surface, (0, 0, 255), (n.x, n.y), (self.points[i + 1].x, self.points[i + 1].y), 2)
            except IndexError:
                pass
            pgt.text(surface, (n.x, n.y), str(i), (0, 0, 0), 30)

    def get_path_length(self):  # Calculates the distance needed to be travled to follow this path
        self._length = 0
        for i, p in enumerate(self.points[:-1]):  # Don't do last point b/c no point in front of it
            self._length += pgt.cdistance(p.x, p.y, self.points[i + 1].x, self.points[i + 1].y)
        return self._length


class Path:
    def __init__(self, old_path, node_to_attach, end_node):  # Creating a new path must start with an existing path with a new node being added
        if old_path is not None:  # The initial path won't have an old path
            self.length = old_path.length + pgt.cdistance(old_path.nodes[-1].x, old_path.nodes[-1].y, node_to_attach.x, node_to_attach.y)
            self.nodes = old_path.nodes + [node_to_attach]
        else:
            self.length = 0
            self.nodes = [node_to_attach]

        self.distance_to_goal = pgt.cdistance(node_to_attach.x, node_to_attach.y, end_node.x, end_node.y)
        self.score = self.length + self.distance_to_goal

        self.potential_paths = None
        self.end_point = end_node

    def expand(self):  # Explores all options a path could take
        self.potential_paths = []
        for c in self.nodes[-1].connections:  # Explore all of the last's nodes connections
            if c.nodes[1] not in self.nodes:  # To prevent going to the same spot twice
                self.potential_paths.append(Path(self, c.nodes[1], self.end_point))

    def get_path_length(self):
        return self.length

    def __lt__(self, other):
        return self.score < other.score



# Because nearest nodes had to be found this helps allow some inital nodes to be skipped
def trim_start_end(check, start, end, map):  # Finds furthest nodes in paths that can be moved to directly
    # Find furthest one the start point can still see
    si = 0
    for i in range(len(check.nodes) - 1, -1, -1):
        # print("i:", i)
        if not map.line_blocked(start, check.nodes[i]):
            # print("not blocked from", start.x / 25, start.y / 25, "to", check.nodes[i].x / 25, check.nodes[i].y / 25)
            si = i
            # print("si:", si)
            break

    ei = len(check.nodes) - 1
    # Find earliest point the end point can still see

    for i in range(0, len(check.nodes)):
        if not map.line_blocked(end, check.nodes[i]):
            ei = i
            break

    # time.sleep(2)
    # print("SI EI:", si, ei)
    # return check
    if (si == len(check.nodes) - 1 or ei == 0) and not map.line_blocked(start, end):
        # print("Straight")
        # print("line blocked:", map.line_blocked(start, end))
        return SimplePath([start, end])

    final = SimplePath([start] + check.nodes[si:max(si, ei) + 1])  # Makes first and last node approximates the actual points

    final.points += [end]
    return final


# Uses A* to find the shortest path between two nodes in the path
# This is only used for the precalclation of routes so all points will be right on nodes
def astar(start: Point, end: Point, map):
    if not map.line_blocked(start, end):
        # print("CAN SEE")
        return SimplePath([start, end])
    start_time = time.time()
    end_node = nearest_node_by_cansee_and_distance(end, map)
    i_path = Path(None, nearest_node_by_cansee_and_distance(start, map), end_node)
    priority = [i_path]

    # print("priortiy:", priority)
    while True:
        # print("tick")
        # print("length", len(priority))
        # print(priority[0].nodes[-1].x, priority[0].nodes[-1].y)
        # print(priority[0].potential_paths)
        try:
            check = priority[0]
        except IndexError:
            return None
        # print(len(priority), check.nodes[-1].x, check.nodes[-1].y)
        if time.time() - start_time > .25:  # More than 10 seconds, the path is too complicated
            return None

        # time.sleep(1)
        # timeout = time.time() - start_time > 10
        if check.nodes[-1] == end_node:  # Found the end
            return check  # No trimming is needed because the start and end points are on nodes

        else:
            priority.pop(0)  # If it is completly expanded then the parent is no longer needed
            check.expand()
            for p in check.potential_paths:
                bisect.insort(priority, p)
            # print([p.score for p in priority])


def find_path(start, end, map):  # Should be used by all persons for navigation
    # Find nearest nodes to calculate path from
    # print("looking for a path")
    s_node = nearest_node_by_cansee_and_distance(start, map)
    e_node = nearest_node_by_cansee_and_distance(end, map, desired_connection=s_node)

    # print("FOUND NEAREST NODES")

    # Ask the map for the precalculated path between those two nodes
    p = map.path_lookup(s_node, e_node)
    # print("PATH LOOKEDUP")
    if p is None:
        print("DESIRED CONNECTION MUST HAVE FAILED")
    # print("e_node:", e_node.x, e_node.y, "end:", end.x, end.y)
    # Trim this path if nodes can be skipped based on starting/ending points
    p = trim_start_end(p, start, end, map)
    if map.line_blocked(p.points[-2], end):
        p.points = p.points[:-1]
    # p = SimplePath(p.nodes)

    return p  # Returns the final path
