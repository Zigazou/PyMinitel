#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..Sequence import Sequence
from ..constantes import *

class Conteneur(UI):
    def __init__(self, minitel, x, y, largeur, hauteur, couleur = None, fond = None):
        assert isinstance(x, int)
        assert isinstance(y, int)
        assert isinstance(largeur, int)
        assert isinstance(hauteur, int)

        self.elements = []
        self.elementActif = None
        self.fond = fond

        #super(Menu, self).__init__(minitel, x, y, largeur, hauteur)
        UI.__init__(self, minitel, x, y, largeur, hauteur, couleur)

    def gereTouche(self, sequence):
        assert isinstance(sequence, Sequence)

        # Aucun élement actif ? Donc rien à faire
        if self.elementActif == None: return False

        # Fait suivre la séquence à l’élément actif
        toucheGeree = self.elementActif.gereTouche(sequence)

        # Si l’élément actif a traité la séquence, c’est fini
        if toucheGeree: return True

        # Si l’élément actif n’a pas traité la séquence, regarde si le
        # conteneur peut la traiter

        # La touche entrée permet de passer au champ suivant
        if sequence.egale(ENTREE):
            self.elementActif.gereDepart()
            self.suivant()
            self.elementActif.gereArrivee()
            return True

        # La combinaison Majuscule + entrée permet de passer au champ précédent
        if sequence.egale(MAJ_ENTREE):
            self.elementActif.gereDepart()
            self.precedent()
            self.elementActif.gereArrivee()
            return True

        return False
            
    def affiche(self):
        # Colorie le fond du conteneur si une couleur de fond a été définie
        if self.fond != None:
            for y in range(self.y, self.y + self.hauteur):
                self.minitel.position(self.x, y)
                self.minitel.couleur(fond = self.fond)
                self.minitel.repeter(' ', self.largeur)

        # Demande à chaque élément de s’afficher
        for element in self.elements:
            element.affiche()

        # Si un élément actif a été défini, on lui donne la main
        if self.elementActif != None: self.elementActif.gereArrivee()

    def ajoute(self, element):
        assert isinstance(element, UI)
        assert element not in self.elements

        # Attribue la couleur du conteneur à l’élément par défaut
        if element.couleur == None: element.couleur = self.couleur

        # Ajoute l’élément à la liste d’éléments du conteneur
        self.elements.append(element)

        if self.elementActif == None and element.activable == True:
            self.elementActif = element

    def suivant(self):
        # S’il n’y a pas d’éléments, il ne peut pas y avoir d’élément actif
        if len(self.elements) == 0: return False

        # Récupère l’index de l’élément actif
        if self.elementActif == None:
            index = -1
        else:
            index = self.elements.index(self.elementActif)

        # Recherche l’élément suivant qui soit activable
        while index < len(self.elements) - 1:
            index += 1
            if self.elements[index].activable == True:
                self.elementActif = self.elements[index]
                return True

        return False

    def precedent(self):
        # S’il n’y a pas d’éléments, il ne peut pas y avoir d’élément actif
        if len(self.elements) == 0: return False

        # Récupère l’index de l’élément actif
        if self.elementActif == None:
            index = len(self.elements)
        else:
            index = self.elements.index(self.elementActif)

        # Recherche l’élément suivant qui soit activable
        while index > 0:
            index -= 1
            if self.elements[index].activable == True:
                self.elementActif = self.elements[index]
                return True

        return False

