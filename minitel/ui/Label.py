#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI

class Label(UI):
    def __init__(self, minitel, posx, posy, valeur = '', couleur = None):
        assert isinstance(posx, int)
        assert isinstance(posy, int)
        assert isinstance(valeur, str) or isinstance(valeur, unicode)

        # Initialise le champ
        self.valeur = valeur

        UI.__init__(self, minitel, posx, posy, len(self.valeur), 1, couleur)

    def gere_touche(self, sequence):
        return False

    def affiche(self):
        # Début du label à l’écran
        self.minitel.position(self.posx, self.posy)

        # Couleur du label
        if self.couleur != None:
            self.minitel.couleur(caractere = self.couleur)

        # Affiche le contenu
        self.minitel.envoyer(self.valeur)

