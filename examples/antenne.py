#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Prototypage des API
"""

import enum
import math
import random
import time

from geo import Vec3
from coton import MétaActeur, send_msg, recv_msg, entry, run


class StatutAlignement(enum.Enum):

    REPOS = 0
    EN_COURS = 1
    ACTIF = 2


class État:

    def __init__(self):
        self.position = Vec3(0, 0, 0)
        self.est_aligné = False
        self.statut = StatutAlignement.REPOS


class Antenne(metaclass=MétaActeur):
    """Simulateur d'une antenne

    L'Équipement émet périodiquement un message de statut. L'absence répétée
    d'une telle émission peut être un indicateur de son non-fonctionnement.
    """

    _PAS = 1.45

    objectif = recv_msg("Position à atteindre, ou 'None' sinon")
    position = send_msg("Direction actuelle de l'Antenne", Vec3(1, 2, 3))
    tic = recv_msg("Heure, en nombre de tics d'horloge", 0)

    def __init__(self):
        """Meilleur constructeur de la terre
        """
        pass

    def __str__(self):
        retour = "Antenne(objectif={}, position={})".format(
            self.objectif, self.position)
        return retour

    @property
    def état(self):
        """Synthèse
        """
        retour = StatutAlignement.ACTIF
        if self.objectif is None:
            retour = StatutAlignement.REPOS
        return retour

    @entry(tic)
    def met_activer(self):
        """Activation périodique
        """
        if self.état is StatutAlignement.ACTIF:
            # Convergence
            écart = self.objectif - self.position
            écart.x = self._converger(écart.x)
            écart.y = self._converger(écart.y)
            écart.z = self._converger(écart.z)
            self.position = self.objectif - écart
        else:
            # Dérive
            delta = Vec3(x=self._dériver(),
                         y=self._dériver(),
                         z=self._dériver())
            self.position += delta
        print("Position : {}".format(self.position))

    def _converger(self, valeur):
        """Assure la convergence vers 0 en respectant un nombre maximal
        de pas
        """
        if -Antenne._PAS <= valeur <= Antenne._PAS:
            retour = 0.0
        elif valeur >= 0:
            retour = math.pow(valeur, 1 / Antenne._PAS)
        else:
            retour = -math.pow(-valeur, 1 / Antenne._PAS)
        return retour

    def _dériver(self):
        retour = random.uniform(-Antenne._PAS, Antenne._PAS)
        return retour


class Gestionnaire(metaclass=MétaActeur):

    # L'objectif visé par l'Antenne ne peut pas être représenté par une seule
    # et même donnée système. Sinon, le Gestionnaire ne sert à rien : une
    # mise-à-jour de l'objectif se ferait via le cadriciel sans passer par le
    # Gestionnaire.

    cible = recv_msg(
        "Commande de position à atteindre par l'antenne, ou 'None'")
    objectif = send_msg("Position à atteindre par l'antenne, ou 'None'")

    état = send_msg("État de l'Antenne gérée", État())

    position = recv_msg("Position publiée par l'Antenne", Vec3(0, 0, 0))

    _TOLÉRANCE = 10.0
    _PREMIER_ALIGNEMENT = 5
    _CONSERVATION = 3

    def __init__(self):
        self._compteur = 0

    @entry(cible)
    def commander(self):
        self.objectif = self.cible
        self.état.est_aligné = False
        if self.objectif is None:
            self.état.statut = StatutAlignement.REPOS
        else:
            self.état.statut = StatutAlignement.EN_COURS

    @entry(position)
    def maj_position(self):
        self.état.position = self.position

        if self.objectif is not None:
            d = self.état_antenne.position.distance(self.objectif)
            if d <= Gestionnaire._TOLÉRANCE:
                self.état.est_aligné = True
                self._compteur = 0
            else:
                self._compteur += 1
                if ((self.état.est_aligné and
                     self._compteur > Gestionnaire._CONSERVATION) or
                    (not self.état.est_aligné and
                     self._compteur > Gestionnaire._PREMIER_ALIGNEMENT)):
                    self._état.est_aligné = False
                    self._objectif = None


class Horloge(metaclass=MétaActeur):
    """Produit un événement périodique d'activation
    """

    tic = send_msg("Heure du système, en nombre d'activations", 0,
                   instantané=True)

    PÉRIODE = 1.0  # en secondes

    def __init__(self):
        self._échéance = None

    @entry
    def générer(self):
        heure = time.time()
        if self._échéance is None:
            attente = Horloge.PÉRIODE
            self._échéance = heure + Horloge.PÉRIODE
            self.tic = 0
        elif heure < self._échéance:
            attente = self._échéance - heure
        else:
            self.tic += 1
            self._échéance += Horloge.PÉRIODE
            attente = max(self._échéance - heure, 0.0)
        if attente > 0.0:
            time.sleep(attente)


if __name__ == "__main__":
    run()
