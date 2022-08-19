import pygame
from egene import pygameTools as pgt


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __getitem__(self, item):
        if item == 0:
            return self.x
        elif item == 1:
            return self.y
        else:
            raise TypeError


class Rectangle:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, point):
        return self.x <= point.x < self.x + self.w and self.y <= point.y < self.y + self.h

    def intersects(self, interval):
        return (self.x + self.w > interval.x and self.y + self.h > interval.y and
                self.x < interval.x + interval.w and self.y < interval.y + interval.h)

    def __str__(self):
        return "x: " + str(self.x) + " y: " + str(self.y) + " width: " + str(self.w) + " height: " + str(self.h)


class QuadTree:
    def __init__(self, boundary, n):
        self.boundary = boundary
        self.capacity = n
        self.points = []
        self.divided = False
        self.subquads = []

    def give_to_children(self, p):
        for q in self.subquads:
            if q.boundary.contains(p):
                q.insert(p)
                break  # The first quads get prioty to prevent a point from being duplicated

    def subdivide(self):
        hw = self.boundary.w / 2
        hh = self.boundary.h / 2
        x, y = self.boundary.x, self.boundary.y
        self.subquads = [QuadTree(Rectangle(x + hw, y, hw, hh), self.capacity),
                         QuadTree(Rectangle(x, y, hw, hh), self.capacity),
                         QuadTree(Rectangle(x, y + hh, hw, hh), self.capacity),
                         QuadTree(Rectangle(x + hw, y + hh, hw, hh), self.capacity)]

        # Dividing the parent's points amongst the children
        for p in self.points:
            self.give_to_children(p)

        self.points = []  # Clears all the points because the parent has given them to their children
        self.divided = True

    def insert(self, point):
        if not self.boundary.contains(point):
            return

        if self.divided:
            self.give_to_children(point)
            return

        self.points.append(point)  # Adds the point to the quad
        # print(point.x, point.y, "Put in boundary:", str(self.boundary))

        if len(self.points) > self.capacity:  # If there are now too many points, divide the tree
            # print("Caused subdivison")
            self.subdivide()

    def query(self, interval, found=None):
        if found is None:
            # print("MADE FOUND")
            found = []
        if not self.boundary.intersects(interval):  # This boundary does not intersect the interval
            # print(self.boundary, "No overlap")
            return found
        else:
            if not self.divided:
                for p in self.points:
                    if interval.contains(p):
                        # print("APPEND")
                        found.append(p)
                return found
            else:  # This quad is divided so children must be queried instead
                for q in self.subquads:
                    found = q.query(interval, found)  # found should just keep growing as more points are appended
        return found


    def show(self, surface):
        # print(self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h)
        pygame.draw.rect(surface, (0, 255, 0), [self.boundary.x, self.boundary.y, self.boundary.w, self.boundary.h], 2)
        pgt.text(surface, (self.boundary.x + self.boundary.w / 2, self.boundary.y + self.boundary.h / 2), str(len(self.points)), (0, 0, 255), 20)
        pgt.text(surface, (self.boundary.x + self.boundary.w / 2, self.boundary.y + self.boundary.h / 2 + 20), str(len(self.subquads)), (100, 50, 100), 20)
        for q in self.subquads:
            q.show(surface)
