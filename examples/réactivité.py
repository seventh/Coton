#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""Démonstration de réception sur une interface d'émission
"""

import time
import coton


class Horloge(metaclass=coton.MétaActeur):
    """Générateur 1 Hz
    """

    tic = coton.send_msg("Heure système", 0)

    @coton.entry
    def émettre(self):
        """Produit un tic à 1Hz
        """
        time.sleep(1)
        self.tic += 1


class Perturbateur3(metaclass=coton.MétaActeur):
    """Propose un incrément
    """

    tic = coton.recv_msg("Heure système", 0)

    partage = coton.send_msg("Donnée multi-écrivains", 0)

    SAUT = 3

    @coton.entry(tic)
    def activer(self):
        print("Perturbateur3 ← {}".format(self.tic))
        if self.tic % self.SAUT == 0:
            self.partage += self.SAUT
            print("Perturbateur3 → {}".format(self.partage))


class Perturbateur5(metaclass=coton.MétaActeur):
    """Propose un incrément
    """

    tic = coton.recv_msg("Heure système", 0)

    partage = coton.send_msg("Donnée multi-écrivains", 0)

    SAUT = 5

    @coton.entry(tic)
    def activer(self):
        print("Perturbateur5 ← {}".format(self.tic))
        if self.tic % self.SAUT == 0:
            self.partage += self.SAUT
            print("Perturbateur5 → {}".format(self.partage))


if __name__ == "__main__":
    coton.run()
