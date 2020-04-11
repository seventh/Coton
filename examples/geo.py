# -*- coding: utf-8 -*-

import math


class Vec3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = x
        self.y = y
        self.z = z

    def __str__(self):
        retour = "{}(x={:.2f}, y={:.2f}, z={:.2f})".format(
            self.__class__.__name__, self.x, self.y, self.z)
        return retour

    def __repr__(self):
        retour = "{}[0x{:x}](x={:.2f}, y={:.2f}, z={:.2f})".format(
            self.__class__.__name__, id(self), self.x, self.y, self.z)
        return retour

    def __eq__(self, autre):
        retour = (self.x == autre.x and self.y == autre.y
                  and self.z == autre.z)
        return retour

    def __iadd__(self, autre):
        self.x += autre.x
        self.y += autre.y
        self.z += autre.z

        return self

    def __sub__(self, autre):
        retour = self.__class__(self.x - autre.x, self.y - autre.y,
                                self.z - autre.z)
        return retour

    def norme(self):
        retour = math.sqrt(self.norme2())
        return retour

    def norme2(self):
        retour = self.x * self.x + self.y * self.y + self.z * self.z
        return retour

    def distance(self, autre):
        retour = (self - autre).norme()
        return retour
