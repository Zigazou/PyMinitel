#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..constantes import *
from ..utils import comparer, canon

class Label(UI):
    def __init__(self, minitel, x, y, valeur = '', couleur = None):
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(valeur, str) or isinstance(valeur, unicode)

        # Initialise le champ
        self.valeur = valeur

        UI.__init__(self, minitel, x, y, len(self.valeur), 1, couleur)

    def gereTouche(self, sequence): return False

    def affiche(self):
        # Début du label à l’écran
        self.minitel.position(self.x, self.y)

        # Couleur du label
        if self.couleur != None: self.minitel.couleur(caractere = self.couleur)

        # Affiche le contenu
        self.minitel.envoyer(self.valeur)

