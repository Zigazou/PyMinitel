#!/usr/bin/env python
# -*- coding: utf-8 -*-

from ..Minitel import Minitel

class UI:
    def __init__(self, minitel, x, y, largeur, hauteur, couleur):
        assert isinstance(minitel, Minitel)
        assert x > 0 and x <= 40
        assert y > 0 and y <= 24
        assert largeur > 0 and largeur + x - 1 <= 40
        assert hauteur > 0 and hauteur + y - 1 <= 40

        # Un élément UI est toujours rattaché à un objet Minitel
        self.minitel = minitel

        # Un élément UI occupe une zone rectangulaire de l’écran du Minitel
        self.x = x
        self.y = y
        self.largeur = largeur
        self.hauteur = hauteur
        self.couleur = couleur

        # Un élément UI peut recevoir ou non les événements clavier
        # Par défaut, il ne les reçoit pas
        self.activable = False

    def executer(self):
        while self.gereTouche(self.minitel.recevoirSequence()): pass

    def affiche(self): pass

    def efface(self):
        for ligne in range(self.y, self.y + self.hauteur):
            self.minitel.position(self.x, ligne)
            self.minitel.repeter(' ', self.largeur)

    def gereTouche(self, sequence): return False

    def gereArrivee(self): pass
    def gereDepart(self): pass

