import numpy as np
from quadtree import Point
import quadtree
from PIL import Image
import pickle
import math
from egene import pygameTools as pgt
import sys
import pygame
from pathing import astar, SimplePath
import tqdm
import multiprocessing as mp

sys.setrecursionlimit(10000)


class Connection:
    def __init__(self, nodes, length):
        self.nodes = nodes
        self.length = length


class Node:
    def __init__(self, x, y, is_doorway=False):
        self.connections = None
        self.x = x
        self.y = y
        self.connections = []
        self.is_doorway = is_doorway  # Used to ignore doorways if this nodes is being used to represent said door

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        else:
            raise TypeError


def doorway_order(nodes):
    return sorted(nodes, key=lambda n: (n.x, n.y))

def remove_dupes(l):
    newl = []
    for i in l:
        if i not in newl:
            newl.append(i)
    return newl


def is_corner(n, node_map, scale):
    neis = {}
    for dx in range(-1, 2):
        for dy in range(-1, 2):
            if dx != 0 or dy != 0:
                neis[(dx, dy)] = node_map[int(n.y // scale + dy)][int(n.x // scale) + dx] == 0

    if neis[(-1, -1)] and not (neis[(0, -1)] or neis[(-1, 0)]):
        return True
    if neis[(-1, 1)] and not (neis[(0, 1)] or neis[(-1, 0)]):
        return True
    if neis[(1, -1)] and not (neis[(0, -1)] or neis[(1, 0)]):
        return True
    if neis[(1, 1)] and not (neis[(0, 1)] or neis[(1, 0)]):
        return True


def make_connections(nodes, map):
    for i in nodes:  # Connected nodes together if there is no wall inbetween
        i.connections = []
        for j in nodes:
            if not map.line_blocked(Point(i.x, i.y), Point(j.x, j.y), check_doorways=not (i.is_doorway or j.is_doorway)):  # if either of them are not a doorway check for doorways
                i.connections.append(Connection([i, j], pgt.cdistance(i.x, i.y, j.x, j.y)))


class Map:
    def __init__(self, array, scale):
        self.scale = scale
        print("INITIALIZING MAP")
        self.walls = set()
        self.nodes = []
        self.node_map = [[0 for c in range(array.shape[1])] for r in range(array.shape[0])]
        self.node_quadtree = quadtree.QuadTree(quadtree.Rectangle(0, 0, array.shape[1] * scale, array.shape[0] * scale), 4)
        self.paths = {}
        self.doorways = []
        for y in range(array.shape[0]):
            for x in range(array.shape[1]):
                if sum(array[y, x]) == 0:
                    self.walls.add(Point(x * scale, y * scale))
                elif sum(array[y, x]) == 255 * 3:
                    n = Node(x * scale + scale / 2, y * scale + scale / 2)
                    self.nodes.append(n)
                    self.node_map[y][x] = n

        print("Finding the nodes on convex corners")
        # Finding the nodes that are on a corner
        self.corner_nodes = []
        for n in self.nodes:
            if is_corner(n, self.node_map, self.scale):
                self.corner_nodes.append(n)

        self.nodes = self.corner_nodes

        # Remake node map with just the corners
        self.node_map = [[0 for c in range(array.shape[1])] for r in range(array.shape[0])]
        for n in self.nodes:
            self.node_map[int(n.y / scale)][int(n.x / scale)] = n

        # self.nodes = self.corner_nodes
        print("Generating walls quadtree")
        self.quadtree = quadtree.QuadTree(quadtree.Rectangle(0, 0, array.shape[1] * scale, array.shape[0] * scale), 6)
        for wall in self.walls:
            self.quadtree.insert(Point(wall.x, wall.y))


        print("Connecting nodes in view of each other")
        make_connections(self.nodes, self)
        print("Number of connection so far:", sum([len(n.connections) for n in self.nodes]))


        print("Finding Door Ways. Current number of nodes:", len(self.nodes))
        newnodes = []
        removenodes = []
        self.doorways = []
        for i in self.nodes:
            v_nodes = []
            h_nodes = []
            for j in self.nodes:
                if not self.line_blocked(i, j) and pgt.cdistance(i.x, i.y, j.x, j.y) < 100:  # Large doorways should be ignored
                    if i.x == j.x and i.y != j.y:
                        v_nodes.append(j)
                    elif i.y == j.y and i.x != j.x:
                        h_nodes.append(j)

            if len(v_nodes) == 1 and len(h_nodes) == 1:  # Search for the diagonal point to create the doorway
                for j in self.nodes:
                    if j.x == h_nodes[0].x and j.y == v_nodes[0].y and not self.line_blocked(i, j):
                        # We have a doorway
                        # print("Found a doorway")
                        self.doorways.append(doorway_order([i, j, v_nodes[0], h_nodes[0]]))  # Puts all the nodes into a doorway

        # print("Number of doorways found:", len(doorways))
        self.doorways = remove_dupes(self.doorways)
        print("Number of unique doorways found:", len(self.doorways))

        for d in self.doorways: # Iterates through all doorways and finds two points to represent the whole doorway
            for n in d:
                self.nodes.remove(n)
            if not self.line_blocked(Node(d[0].x - 50, (d[0].y + d[1].y) / 2), Node(d[2].x + 50, (d[2].y + d[3].y) / 2)):
                self.nodes.append(Node(d[0].x, (d[0].y + d[1].y) / 2, is_doorway=True))
                self.nodes.append(Node(d[2].x, (d[2].y + d[3].y) / 2, is_doorway=True))
            else:
                self.nodes.append(Node((d[0].x + d[2].x) / 2, d[0].y, is_doorway=True))
                self.nodes.append(Node((d[1].x + d[3].x) / 2, d[1].y, is_doorway=True))

        print("Connecting nodes in view of each other again")
        make_connections(self.nodes, self)
        print("Number of connection after doorways:", sum([len(n.connections) for n in self.nodes]))

        print("num of nodes:", len(self.nodes))
        # Put all the nodes into a quadtree so nearest nodes can be found faster
        print("Generating node quadtree")
        for n in self.nodes:
            self.node_quadtree.insert(n)
        print("Calculating navigation routes")
        self.calc_all_paths()  # Precalculates all the paths between and combination of nodes
        print(self.paths)

    @staticmethod
    def to_paths(args):
        i, nodes, map = args
        d = {}
        for j in range(i, len(nodes)):
            path = astar(Point(nodes[i].x, nodes[i].y), Point(nodes[j].x, nodes[j].y), map)
            # If path times out it equals None so it should not be added to dict
            if path is not None:
                d.update({((nodes[i].x, nodes[i].y),
                           (nodes[j].x, nodes[j].y)): path})
        return d

    def calc_all_paths(self):
        pool = mp.Pool()

        for result in tqdm.tqdm(pool.imap_unordered(Map.to_paths, [(i, self.nodes, self) for i in range(len(self.nodes))]), total=len(self.nodes)):
            self.paths.update(result)
            # print(self.paths)

    def path_lookup(self, start_node, end_node):
        try:
            return self.paths[(start_node.x, start_node.y), (end_node.x, end_node.y)]
        except KeyError:
            try:
                p = self.paths[(end_node.x, end_node.y), (start_node.x, start_node.y)]
                # This is an opposite path so the order must be reversed
                return SimplePath(p.nodes[::-1])
            except KeyError:
                # print("No valid path found in lookup")
                return None

    def line_blocked(self, start, end, check_doorways=False):  # Checks if a straight line through this map is not blocked (used for pathing)
        loc = Point(start.x, start.y)
        d = math.atan2(end.y - start.y, end.x - start.x)

        while pgt.cdistance(loc.x, loc.y, end.x, end.y) > 10:
            if len(self.quadtree.query(quadtree.Rectangle(loc.x - self.scale, loc.y - self.scale, self.scale, self.scale))) > 0:  # It hits a wall
                return True
            elif check_doorways:
                for door in self.doorways:
                    if loc.x > door[0].x and loc.x < door[3].x and loc.y > door[0].y and loc.y < door[3].y:
                        return True  # Treating the doorway as a wall and this line hit it
            loc.x += math.cos(d) * 10
            loc.y += math.sin(d) * 10
        return False

    def draw_nodes(self, surface, cam=(0, 0)):
        for n in self.nodes:
            pygame.draw.circle(surface, (100, 100, 100), (n.x - cam[0], n.y - cam[1]), 4)
            for c in n.connections:
                pygame.draw.line(surface, (100, 100, 100), (c.nodes[0].x - cam[0], c.nodes[0].y - cam[1]), (c.nodes[1].x - cam[0], c.nodes[1].y - cam[1]), 3)
        for n in self.corner_nodes:
            pygame.draw.circle(surface, (0, 100, 100), (n.x - cam[0], n.y - cam[1]), 4)


def convert(image_name):
    im = np.asarray(Image.open("assets\\" + image_name).convert("RGB"))
    return Map(im, 32)


if __name__ == "__main__":
    # pickle.dump(convert("Big.png"), open("big.p", "wb"))
    name = "SchoolPathing"
    pickle.dump(convert(name + ".png"), open(name + ".p", "wb"))
