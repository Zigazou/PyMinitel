#!/usr/bin/env python
# -*- coding: utf-8 -*-

from minitel.Minitel import Minitel
from minitel.ui.UI import UI
from minitel.ui.Menu import Menu
from minitel.constantes import *
from minitel.utils import canon, comparer
from random import choice

from plateau import Plateau, INEXPLORE, DRAPEAU, DECOUVERT

CASEVIERGE  = 'a'
CASEDRAPEAU = 'b'
CASEMINE    = 'c'

class Demineur(UI):
    def __init__(self, minitel, difficulte = 0):
        assert isinstance(difficulte, int)
        assert difficulte >= 0 and difficulte <= 3

        UI.__init__(self, minitel, 1, 1, 40, 24, 'blanc')
        self.activable = True
        self.perdu = False

        # Définit les caractères nécessaires au jeu
        dessins = """
            00000000
            00000000
            00000000
            00000000
            00011000
            00011000 Zone non explorée
            00000000
            00000000
            00000000
            00000000

            00000000
            01111110
            11010110
            10101010
            11010110 Drapeau pour indiquer une mine trouvée
            01111110
            00000010
            00000010
            00000010
            00000010

            10010010
            01010100
            00111000
            00111000
            11111110 Mine
            00111000
            00111000
            01010100
            10010010
            00000000
        """

        minitel.redefinir('a', dessins, 'G1')

        # Initialise le plateau
        self.plateau = Plateau(40,24)
        self.plateau.nouveau(difficulte)

        # Place le curseur au centre
        self.curseurX = self.largeur / 2
        self.curseurY = self.hauteur / 2

    def gereTouche(self, sequence):
        x = self.curseurX - self.x
        y = self.curseurY - self.y

        # Si le démineur a perdu, toute touche le ramène au menu principal
        if self.perdu: return False        

        # Déplacement du curseur vers le haut
        if comparer(sequence, HAUT):
            if self.curseurY > self.y:
                self.curseurY -= 1
                self.placeCurseur()
            else:
                self.minitel.bip()
            return True

        # Déplacement du curseur vers le bas
        if comparer(sequence, BAS):
            if self.curseurY < self.hauteur:
                self.curseurY += 1
                self.placeCurseur()
            else:
                self.minitel.bip()
            return True

        # Déplacement du curseur vers la gauche
        if comparer(sequence, GAUCHE):
            if self.curseurX > self.x:
                self.curseurX -= 1
                self.placeCurseur()
            else:
                self.minitel.bip()
            return True

        # Déplacement du curseur vers la droite
        if comparer(sequence, DROITE):
            if self.curseurX < self.largeur:
                self.curseurX += 1
                self.placeCurseur()
            else:
                self.minitel.bip()
            return True

        # Creuse à l’emplacement courant
        if comparer(sequence, ' '):
            # Si le démineur creuse là où il a déjà creusé, on ignore
            if self.plateau.visibilite(x, y) == DECOUVERT:
                return True

            # Si le démineur creuse sur une mine, il a perdu !
            if self.plateau.aUneMine(x, y):
                self.minitel.curseur(False)
                self.montreMines()
                grosTitre(self.minitel, u'Boom !!!', 10, 10)
                self.perdu = True
                return True

            # Aucun souci pour le démineur, on creuse
            couleurs = [0, 1, 1, 2, 3, 4, 5, 6, 7]

            self.minitel.curseur(False)

            for case in self.plateau.decouvre(x, y):
                alentours = self.plateau.alentours(case[0], case[1])
                self.minitel.position(case[0] + self.x, case[1] + self.y)
                self.minitel.couleur(caractere = couleurs[alentours])
                self.minitel.envoyer(str(alentours))

            self.placeCurseur()
            self.minitel.curseur(True)

            return True

        # Pose un drapeau
        if comparer(sequence, ENTREE):
            self.minitel.semigraphique()
            self.minitel.envoyer(CASEDRAPEAU)
            self.placeCurseur()
            return True

        return False

    def placeCurseur(self):
        self.minitel.position(self.curseurX, self.curseurY)

    def affiche(self):
        self.minitel.curseur(False)
        self.minitel.position(1, 1)
        self.minitel.semigraphique()
        self.minitel.couleur(caractere = 'rouge', fond = 'noir')

        for ligne in range(self.y, self.hauteur + 1):
            for colonne in range(self.x, self.largeur + 1):
                self.minitel.envoyer(CASEVIERGE)

        self.placeCurseur()
        self.minitel.curseur(True)

    def montreMines(self):
        for ligne in range(self.y, self.hauteur + 1):
            for colonne in range(self.x, self.largeur + 1):
                x = colonne - self.x
                y = ligne - self.y

                if self.plateau.aUneMine(x, y):
                    self.minitel.position(colonne, ligne)
                    self.minitel.semigraphique()
                    self.minitel.envoyer(CASEMINE)
        

def grosTitre(minitel, texte, colonne, ligne):
    minitel.position(colonne, ligne)
    minitel.taille(largeur = 2, hauteur = 1)
    minitel.couleur(caractere = 'noir', fond = 'rouge')
    minitel.repeter(u' ', len(texte) + 2)

    minitel.position(colonne, ligne + 2)
    minitel.taille(largeur = 2, hauteur = 2)
    minitel.couleur(caractere = 'noir', fond = 'rouge')
    minitel.envoyer(u' ' + texte + u' ')

    minitel.position(colonne, ligne + 3)
    minitel.taille(largeur = 2, hauteur = 1)
    minitel.couleur(caractere = 'noir', fond = 'rouge')
    minitel.repeter(u' ', len(texte) + 2)

# Initialisation du Minitel
minitel = Minitel()

minitel.devinerVitesse()
minitel.identifier()
minitel.definirVitesse(9600)
minitel.definirMode('VIDEOTEX')
minitel.configurerClavier(etendu = True, curseur = False, minuscule = True)
minitel.echo(False)
minitel.efface()
minitel.curseur(False)

# Création des widgets
options = [
  u'Débutant',
  u'Intermédiaire',
  u'Expert',
  u'-',
  u'A propos',
  u'Quitter'
]

# Sélection du niveau de difficulté
menu = Menu(minitel, options, 13, 5)

while True:
    # Grand titre
    grosTitre(minitel, u'Déminitéleur', 7, 1)

    menu.affiche()
    menu.executer()

    if menu.selection == 5: break

    # Prépare le terrain de jeu
    minitel.efface()

    demineur = Demineur(minitel)
    demineur.affiche()
    demineur.executer()

minitel.close()

