#!/usr/bin/env python
# -*- coding: utf-8 -*-

from random import randint

# Index pour les tuples des cases
SURFACE   = 0
SOUSSOL   = 1
ALENTOURS = 2

# Etat de surface
INEXPLORE = 0
DRAPEAU   = 1
DECOUVERT = 2

# Etat souterrain
BOMBE = 1
VIDE  = 0

class Plateau:
    def __init__(self, largeur, hauteur):
        assert isinstance(largeur, int) and largeur > 0
        assert isinstance(hauteur, int) and hauteur > 0

        self.largeur = largeur
        self.hauteur = hauteur

    def nouveau(self, difficulte):
        assert isinstance(difficulte, int)
        assert difficulte >= 0 and difficulte <= 2

        # Initialise le plateau avec des cases vides inexplorées
        self.plateau = [
            [[INEXPLORE, VIDE, 0] for colonne in range(0, self.largeur)]
            for ligne in range(0, self.hauteur)
        ]

        # En fonction de la difficulté, ajoute des bombes
        nbBombe = (difficulte + 1) * (self.largeur * self.hauteur) / 10

        assert nbBombe < (self.hauteur * self.largeur)
        for index in range(0, nbBombe):
            # Prend une case au hasard jusqu'à tomber sur une case sans bombe
            while True:
                y = randint(0, self.hauteur - 1)
                x = randint(0, self.largeur - 1)

                if self.plateau[y][x][SOUSSOL] == VIDE: break

            # Ajoute une bombe à la case
            self.plateau[y][x][SOUSSOL] = BOMBE

        # Précalcule le nombre de bombes autour de chaque case
        for y in range(0, self.hauteur):
            for x in range(0, self.largeur):
                cases = [
                    (x-1, y-1), (x, y-1), (x+1, y-1),
                    (x-1, y  ),           (x+1, y  ),
                    (x-1, y+1), (x, y+1), (x+1, y+1)
                ]

                alentours = 0
                for case in cases:
                    if not self.valide(case[0], case[1]): continue
                    alentours += self.plateau[case[1]][case[0]][SOUSSOL]

                self.plateau[y][x][ALENTOURS] = alentours

    def decouvre(self, colonne, ligne): pass
    
    def poseDrapeau(self, colonne, ligne):
        self.plateau[y][x][SURFACE] = DRAPEAU

    def aUneMine(self, x, y):
        return self.plateau[y][x][SOUSSOL] == BOMBE

    def visibilite(self, x, y):
        return self.plateau[y][x][SURFACE]

    def alentours(self, x, y):
        return self.plateau[y][x][ALENTOURS]

    def valide(self, x, y):
        return x >= 0 and x < self.largeur and y >= 0 and y < self.hauteur

    def decouvre(self, x, y):
        self.plateau[y][x][SURFACE] = DECOUVERT
        decouvres = [(x, y)]

        if self.alentours(x, y) > 0: return decouvres

        cases = [
            (x-1, y-1), (x, y-1), (x+1, y-1),
            (x-1, y  ),           (x+1, y  ),
            (x-1, y+1), (x, y+1), (x+1, y+1)
        ]

        for case in cases:
            if not self.valide(case[0], case[1]): continue
            if self.visibilite(case[0], case[1]) == DECOUVERT: continue

            decouvres = decouvres + self.decouvre(case[0], case[1])

        return decouvres
