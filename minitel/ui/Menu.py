#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..constantes import HAUT, BAS
from ..Sequence import Sequence

class Menu(UI):
    def __init__(self, minitel, options, posx, posy, selection = 0,
                 couleur = None):
        self.options = options
        self.selection = selection

        # Détermine la largeur du menu
        self.largeur_ligne = 0
        for option in self.options:
            self.largeur_ligne = max(self.largeur_ligne, len(option))

        # Détermine la largeur et la hauteur de la zone d’affichage du menu
        largeur = self.largeur_ligne + 2
        hauteur = len(self.options) + 2

        UI.__init__(self, minitel, posx, posy, largeur, hauteur, couleur)

        self.activable = True

    def gere_touche(self, sequence):
        assert isinstance(sequence, Sequence)

        if sequence.egale(HAUT):
            selection = self.option_precedente(self.selection)
            if selection == None:
                self.minitel.bip()
            else:
                self.change_selection(selection)

            return True

        if sequence.egale(BAS):
            selection = self.option_suivante(self.selection)
            if selection == None:
                self.minitel.bip()
            else:
                self.change_selection(selection)

            return True

        return False

    def affiche(self):
        i = 0
        self.minitel.position(self.posx + 1, self.posy)

        if self.couleur != None:
            self.minitel.couleur(caractere = self.couleur)

        self.minitel.repeter(0x5f, self.largeur_ligne)

        for _ in self.options:
            if self.couleur != None:
                self.minitel.couleur(caractere = self.couleur)

            self.affiche_ligne(i, self.selection == i)
            i += 1

        self.minitel.position(self.posx + 1, self.posy + len(self.options) + 1)

        if self.couleur != None:
            self.minitel.couleur(caractere = self.couleur)

        self.minitel.repeter(0x7e, self.largeur_ligne)

    def affiche_ligne(self, selection, etat = False):
        self.minitel.position(self.posx, self.posy + selection + 1)

        if self.couleur != None:
            self.minitel.couleur(caractere = self.couleur)

        self.minitel.envoyer([0x7d])

        if self.options[selection] == u'-':
            self.minitel.repeter(0x60, self.largeur_ligne)
        else:
            if etat:
                self.minitel.effet(inversion = True)

            option = self.options[selection]
            self.minitel.envoyer(option.ljust(self.largeur_ligne))

        if etat:
            self.minitel.effet(inversion = False)

        self.minitel.envoyer([0x7b])
        
    def change_selection(self, selection):
        if self.selection == selection:
            return

        if selection < 0 or selection >= len(self.options):
            return

        self.affiche_ligne(self.selection, False)
        self.affiche_ligne(selection, True)

        self.selection = selection

    def option_suivante(self, numero):
        for i in range(numero + 1, len(self.options)):
            if self.options[i] != u'-':
                return i

        return None
    
    def option_precedente(self, numero):
        for i in range(numero - 1, -1, -1):
            if self.options[i] != u'-':
                return i

        return None

