#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import unittest

from antenne import Antenne
from antenne import Horloge
from geo import Vec3


class TestAntenne(unittest.TestCase):

    def test_converger(self):
        a = Antenne()

        x = 101
        while x != 0:
            y = a._converger(x)
            print(x, y)
            self.assertGreater(abs(x), abs(
                y), "Pas de convergence vers 0: {} → {}".format(x, y))
            x = y

    def test_aligner(self):
        a = Antenne()

        o = Vec3(10.0, -200.0, 3000.0)
        a.objectif = o
        while a.position != o:
            a.met_activer()
            print(a.position)

    def test_dériver(self):
        a = Antenne()

        self.assertEqual(a.position, Vec3(1, 2, 3))

        a.met_activer()
        self.assertNotEqual(a.position, Vec3(1, 2, 3))
        print(a.position)

    def test_fonctionnement(self):
        a = Antenne()

        for i in range(10):
            a.met_activer()

        a.objectif = Vec3(-4, 8, -9)
        while a.objectif != a.position:
            a.met_activer()

        a.objectif = None
        for i in range(10):
            a.met_activer()
        self.assertNotEqual(a.position, Vec3(1, 2, 3))
        print(a)


class TestHorloge(unittest.TestCase):

    def test_générer(self):
        H = Horloge()
        t0 = time.time()
        H.générer()
        t1 = time.time()
        self.assertEqual(H.tic, 0)
        self.assertAlmostEqual(t1 - t0, 1.0, 2)
        H.générer()
        t2 = time.time()
        self.assertEqual(H.tic, 1)
        self.assertAlmostEqual(t2 - t1, 1.0, 3)

        for i in range(10):
            H.générer()
        t3 = time.time()
        self.assertAlmostEqual(t3 - t2, 10.0, 4)


if __name__ == "__main__":
    unittest.main()
