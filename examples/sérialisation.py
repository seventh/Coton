#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Démonstration de la recopie des données entre tâches

Si la donnée `liste` était partagée entre les deux acteurs, la sortie serait :

J'ai reçu : [1, 2]
J'ai reçu : [1, 1, 2]
J'ai reçu : [1, 1, 1, 2]
…
"""

import time

import coton


class Producteur(metaclass=coton.MétaActeur):
    """Générateur
    """

    liste = coton.send_msg("Test trop fort", list(), instantané=True)

    @coton.entry
    def tiens(self):
        # Sans affectation, il n'y aurait pas de production de la donnée !
        # Autre version :
        # self.liste += [1, 2]
        self.liste.extend([1, 2])
        coton.publier(Producteur.liste)

        time.sleep(1)


class Consommateur(metaclass=coton.MétaActeur):

    liste = coton.recv_msg("Tiens gros", list())

    @coton.entry(liste)
    def tructruc(self):
        print("J'ai reçu : {}".format(self.liste))
        self.liste.pop()


if __name__ == "__main__":
    coton.run()
