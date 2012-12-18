#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..constantes import *
from ..utils import comparer, canon

class ChampTexte(UI):
    def __init__(self, minitel,x, y, longueurVisible, longueurTotale = None, valeur = u'', couleur = None):
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(longueurVisible, int)
        assert isinstance(longueurTotale, int) or longueurTotale == None
        assert isinstance(valeur, (str, unicode))
        assert x + longueurVisible < 80
        assert longueurVisible >= 1
        if longueurTotale == None: longueurTotale = longueurVisible
        assert longueurVisible <= longueurTotale

        UI.__init__(self, minitel, x, y, longueurVisible, 1, couleur)

        # Initialise le champ
        self.longueurVisible = longueurVisible
        self.longueurTotale = longueurTotale
        self.valeur = u'' + valeur
        self.curseurX = 0
        self.decalage = 0
        self.activable = True
        self.accent = None

    def gereTouche(self, sequence):
        if comparer(sequence, GAUCHE):
            self.accent = None
            self.curseurGauche()
            return True        
        elif comparer(sequence, DROITE):
            self.accent = None
            self.curseurDroite()
            return True        
        elif comparer(sequence, CORRECTION):
            self.accent = None
            if self.curseurGauche():
                self.valeur = self.valeur[0:self.curseurX] + self.valeur[self.curseurX + 1:]
                self.affiche()
            return True        
        elif (comparer(sequence, ACCENT_AIGU) or comparer(sequence, ACCENT_GRAVE) or
             comparer(sequence, ACCENT_CIRCONFLEXE) or comparer(sequence, ACCENT_TREMA)):
            self.accent = sequence
            return True
        elif comparer(sequence, [ACCENT_CEDILLE, 'c']):
            self.accent = None
            self.valeur = self.valeur[0:self.curseurX] + u'ç' + self.valeur[self.curseurX:]
            self.curseurDroite()
            self.affiche()
            return True
        elif chr(sequence[0]) in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ *$!:;,?./&(-_)=+\'@':
            caractere = u'' + chr(sequence[0])
            if self.accent != None:
                if caractere in 'aeiou':
                    if comparer(self.accent, ACCENT_AIGU):
                        caractere = u'áéíóú'['aeiou'.index(caractere)]
                    elif comparer(self.accent, ACCENT_GRAVE):
                        caractere = u'àèìòù'['aeiou'.index(caractere)]
                    elif comparer(self.accent, ACCENT_CIRCONFLEXE):
                        caractere = u'âêîôû'['aeiou'.index(caractere)]
                    elif comparer(self.accent, ACCENT_TREMA):
                        caractere = u'äëïöü'['aeiou'.index(caractere)]

                self.accent = None

            self.valeur = self.valeur[0:self.curseurX] + caractere + self.valeur[self.curseurX:]
            self.curseurDroite()
            self.affiche()
            return True        

        return False

    def curseurGauche(self):
        if self.curseurX == 0:
            self.minitel.bip()
            return False

        self.curseurX = self.curseurX - 1

        if self.curseurX < self.decalage:
            self.decalage = max(0, self.decalage - self.longueurVisible / 2)
            self.affiche()
        else:
            self.minitel.position(self.x + self.curseurX - self.decalage, self.y)

        return True
    
    def curseurDroite(self):
        if self.curseurX == min(len(self.valeur), self.longueurTotale):
            self.minitel.bip()
            return False
    
        self.curseurX = self.curseurX + 1

        if self.curseurX > self.decalage + self.longueurVisible:
            self.decalage = max(0, self.decalage + self.longueurVisible / 2)
            self.affiche()
        else:
            self.minitel.position(self.x + self.curseurX - self.decalage, self.y)

        return True

    def gereArrivee(self):
        self.minitel.position(self.x + self.curseurX - self.decalage, self.y)
        self.minitel.curseur(True)

    def gereDepart(self):
        self.accent = None
        self.minitel.curseur(False)

    def affiche(self):
        # Début du champ texte à l’écran
        self.minitel.position(self.x, self.y)

        # Couleur du label
        if self.couleur != None: self.minitel.couleur(caractere = self.couleur)

        if len(self.valeur) - self.decalage <= self.longueurVisible:
            # Cas valeur plus petite que la longueur visible
            affichage = self.valeur[self.decalage:].ljust(self.longueurVisible, '.')
        else:
            # Cas valeur plus grande que la longueur visible
            affichage = self.valeur[
                self.decalage:
                self.decalage + self.longueurVisible
            ]

        # Affiche le contenu
        self.minitel.envoyer(affichage)

        # Place le curseur visible
        self.minitel.position(
            self.x + self.curseurX - self.decalage,
            self.y
        )

