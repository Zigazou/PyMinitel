#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..constantes import *
from ..Sequence import Sequence

class Menu(UI):
    def __init__(self, minitel, options, x, y, selection = 0, couleur = None):
        self.options = options
        self.selection = selection

        # Détermine la largeur du menu
        self.largeurLigne = 0
        for option in self.options:
            self.largeurLigne = max(self.largeurLigne, len(option))

        # Détermine la largeur et la hauteur de la zone d’affichage du menu
        largeur = self.largeurLigne + 2
        hauteur = len(self.options) + 2

        UI.__init__(self, minitel, x, y, largeur, hauteur, couleur)

        self.activable = True

    def gereTouche(self, sequence):
        assert isinstance(sequence, Sequence)

        if sequence.egale(HAUT):
            selection = self.optionPrecedente(self.selection)
            if selection == None:
                self.minitel.bip()
            else:
                self.changeSelection(selection)

            return True

        if sequence.egale(BAS):
            selection = self.optionSuivante(self.selection)
            if selection == None:
                self.minitel.bip()
            else:
                self.changeSelection(selection)

            return True

        return False

    def affiche(self):
        i = 0
        self.minitel.position(self.x + 1, self.y)
        if self.couleur != None: self.minitel.couleur(caractere = self.couleur)
        self.minitel.repeter(0x5f, self.largeurLigne)

        for option in self.options:
            if self.couleur != None: self.minitel.couleur(caractere = self.couleur)
            self.afficheLigne(i, self.selection == i)
            i += 1

        self.minitel.position(self.x + 1, self.y + len(self.options) + 1)
        if self.couleur != None: self.minitel.couleur(caractere = self.couleur)
        self.minitel.repeter(0x7e, self.largeurLigne)

    def afficheLigne(self, selection, etat = False):
        self.minitel.position(self.x, self.y + selection + 1)
        if self.couleur != None: self.minitel.couleur(caractere = self.couleur)
        self.minitel.envoyer([0x7d])

        if self.options[selection] == u'-':
            self.minitel.repeter(0x60, self.largeurLigne)
        else:
            if etat: self.minitel.effet(inversion = True)
            self.minitel.envoyer(self.options[selection].ljust(self.largeurLigne))

        if etat: self.minitel.effet(inversion = False)

        self.minitel.envoyer([0x7b])
        
    def changeSelection(self, selection):
        if self.selection == selection: return
        if selection < 0 or selection >= len(self.options): return

        self.afficheLigne(self.selection, False)
        self.afficheLigne(selection, True)

        self.selection = selection

    def optionSuivante(self, numero):
        for i in range(numero + 1, len(self.options)):
            if self.options[i] != u'-': return i

        return None
    
    def optionPrecedente(self, numero):
        for i in range(numero - 1, -1, -1):
            if self.options[i] != u'-': return i

        return None

