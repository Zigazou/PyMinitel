#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..constantes import (
    GAUCHE, DROITE, CORRECTION, ACCENT_AIGU, ACCENT_GRAVE, ACCENT_CIRCONFLEXE, 
    ACCENT_TREMA, ACCENT_CEDILLE
)

CARACTERES_MINITEL = (
    'abcdefghijklmnopqrstuvwxyz' +
    'ABCDEFGHIJKLMNOPQRSTUVWXYZ' +
    ' *$!:;,?./&(-_)=+\'@'
)

class ChampTexte(UI):
    def __init__(self, minitel, posx, posy, longueur_visible,
                 longueur_totale = None, valeur = u'', couleur = None):
        assert isinstance(posx, int)
        assert isinstance(posy, int)
        assert isinstance(longueur_visible, int)
        assert isinstance(longueur_totale, int) or longueur_totale == None
        assert isinstance(valeur, (str, unicode))
        assert posx + longueur_visible < 80
        assert longueur_visible >= 1
        if longueur_totale == None:
            longueur_totale = longueur_visible
        assert longueur_visible <= longueur_totale

        UI.__init__(self, minitel, posx, posy, longueur_visible, 1, couleur)

        # Initialise le champ
        self.longueur_visible = longueur_visible
        self.longueur_totale = longueur_totale
        self.valeur = u'' + valeur
        self.curseur_x = 0
        self.decalage = 0
        self.activable = True
        self.accent = None

    def gere_touche(self, sequence):
        if sequence.egale(GAUCHE):
            self.accent = None
            self.curseur_gauche()
            return True        
        elif sequence.egale(DROITE):
            self.accent = None
            self.curseur_droite()
            return True        
        elif sequence.egale(CORRECTION):
            self.accent = None
            if self.curseur_gauche():
                self.valeur = (self.valeur[0:self.curseur_x] +
                               self.valeur[self.curseur_x + 1:])
                self.affiche()
            return True        
        elif (sequence.egale(ACCENT_AIGU) or
              sequence.egale(ACCENT_GRAVE) or
              sequence.egale(ACCENT_CIRCONFLEXE) or
              sequence.egale(ACCENT_TREMA)):
            self.accent = sequence
            return True
        elif sequence.egale([ACCENT_CEDILLE, 'c']):
            self.accent = None
            self.valeur = (self.valeur[0:self.curseur_x] +
                           u'ç' +
                           self.valeur[self.curseur_x:])
            self.curseur_droite()
            self.affiche()
            return True
        elif chr(sequence.valeurs[0]) in CARACTERES_MINITEL:
            caractere = u'' + chr(sequence.valeurs[0])
            if self.accent != None:
                if caractere in 'aeiou':
                    if self.accent.egale(ACCENT_AIGU):
                        caractere = u'áéíóú'['aeiou'.index(caractere)]
                    elif self.accent.egale(ACCENT_GRAVE):
                        caractere = u'àèìòù'['aeiou'.index(caractere)]
                    elif self.accent.egale(ACCENT_CIRCONFLEXE):
                        caractere = u'âêîôû'['aeiou'.index(caractere)]
                    elif self.accent.egale(ACCENT_TREMA):
                        caractere = u'äëïöü'['aeiou'.index(caractere)]

                self.accent = None

            self.valeur = (self.valeur[0:self.curseur_x] +
                           caractere +
                           self.valeur[self.curseur_x:])
            self.curseur_droite()
            self.affiche()
            return True        

        return False

    def curseur_gauche(self):
        if self.curseur_x == 0:
            self.minitel.bip()
            return False

        self.curseur_x = self.curseur_x - 1

        if self.curseur_x < self.decalage:
            self.decalage = max(0, self.decalage - self.longueur_visible / 2)
            self.affiche()
        else:
            self.minitel.position(
                self.posx + self.curseur_x - self.decalage,
                self.posy
            )

        return True
    
    def curseur_droite(self):
        if self.curseur_x == min(len(self.valeur), self.longueur_totale):
            self.minitel.bip()
            return False
    
        self.curseur_x = self.curseur_x + 1

        if self.curseur_x > self.decalage + self.longueur_visible:
            self.decalage = max(0, self.decalage + self.longueur_visible / 2)
            self.affiche()
        else:
            self.minitel.position(
                self.posx + self.curseur_x - self.decalage,
                self.posy
            )

        return True

    def gere_arrivee(self):
        self.minitel.position(
            self.posx + self.curseur_x - self.decalage,
            self.posy
        )
        self.minitel.curseur(True)

    def gere_depart(self):
        self.accent = None
        self.minitel.curseur(False)

    def affiche(self):
        # Début du champ texte à l’écran
        self.minitel.position(self.posx, self.posy)

        # Couleur du label
        if self.couleur != None:
            self.minitel.couleur(caractere = self.couleur)

        if len(self.valeur) - self.decalage <= self.longueur_visible:
            # Cas valeur plus petite que la longueur visible
            affichage = self.valeur[self.decalage:]
            affichage = affichage.ljust(self.longueur_visible, '.')
        else:
            # Cas valeur plus grande que la longueur visible
            affichage = self.valeur[
                self.decalage:
                self.decalage + self.longueur_visible
            ]

        # Affiche le contenu
        self.minitel.envoyer(affichage)

        # Place le curseur visible
        self.minitel.position(
            self.posx + self.curseur_x - self.decalage,
            self.posy
        )

