#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
import unittest

from coton import FileSortie


class TestFileSortie(unittest.TestCase):

    def test_push_différé(self):
        f = FileSortie()
        f.push("toto", "15", False)
        self.assertEqual(len(f), 1)
        f.push("tata", 15, False)
        self.assertEqual(len(f), 2)
        f.push("toto", "14", False)
        self.assertEqual(len(f), 2)

    def test_push_immédiat(self):
        f = FileSortie()
        f.push("toto", "15", True)
        self.assertEqual(len(f), 1)
        f.push("tata", 15, False)
        self.assertEqual(len(f), 2)
        f.push("toto", "15", True)
        self.assertEqual(len(f), 3)


if __name__ == "__main__":
    unittest.main()
