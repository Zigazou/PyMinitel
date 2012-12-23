#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .UI import UI
from ..Sequence import Sequence
from ..constantes import ENTREE, MAJ_ENTREE

class Conteneur(UI):
    """Classe permettant de regrouper des éléments d’interface utilisateur

    Cette classe permet de regrouper des éléments d’inteface utilisateur afin
    de faciliter leur gestion. Elle est notamment capable d’afficher tous les
    éléments qu’elle contient et de gérer le passage d’un élément à un autre.

    Le passage d’un élément à l’autre se fait au moyen de la touche ENTREE pour
    l’élément suivant et de la combinaison MAJUSCULE+ENTREE pour l’élément
    précédent. Si l’utilisateur veut l’élément suivant alors qu’il est déjà
    sur le dernier élément, le Minitel émettra un bip. Idem pour l’élément
    précédent.

    Le éléments dont l’attribut activable est à False sont purement et
    simplement ignorés lors de la navigation inter-éléments.

    Les attributs suivants sont disponibles :

    - elements : liste des éléments dans leur ordre d’apparition
    - element_actif : objet de classe UI désignant l’élément actif
    - fond : couleur de fond du conteneur
    """
    def __init__(self, minitel, posx, posy, largeur, hauteur, couleur = None,
                 fond = None):
        """Constructeur

        :param minitel:
            L’objet auquel envoyer les commandes et recevoir les appuis de
            touche.
        :type minitel:
            un objet Minitel

        :param posx:
            Coordonnée x de l’élément
        :type posx:
            un entier

        :param posy:
            Coordonnée y de l’élément
        :type posy:
            un entier
        
        :param largeur:
            Largeur de l’élément en caractères
        :type largeur:
            un entier
        
        :param hauteur:
            Hauteur de l’élément en caractères
        :type hauteur:
            un entier
        
        :param couleur:
            Couleur de l’élément
        :type couleur:
            un entier, une chaîne de caractères ou None

        :param fond:
            Couleur de fond du conteneur
        :type couleur:
            un entier, une chaîne de caractères ou None
        """
        assert isinstance(posx, int)
        assert isinstance(posy, int)
        assert isinstance(largeur, int)
        assert isinstance(hauteur, int)
        assert isinstance(couleur, (str, int)) or couleur == None
        assert isinstance(fond, (str, int)) or fond == None

        # Initialisation des attributs
        self.elements = []
        self.element_actif = None
        self.fond = fond

        UI.__init__(self, minitel, posx, posy, largeur, hauteur, couleur)

    def gere_touche(self, sequence):
        assert isinstance(sequence, Sequence)

        # Aucun élement actif ? Donc rien à faire
        if self.element_actif == None:
            return False

        # Fait suivre la séquence à l’élément actif
        touche_geree = self.element_actif.gere_touche(sequence)

        # Si l’élément actif a traité la séquence, c’est fini
        if touche_geree:
            return True

        # Si l’élément actif n’a pas traité la séquence, regarde si le
        # conteneur peut la traiter

        # La touche entrée permet de passer au champ suivant
        if sequence.egale(ENTREE):
            self.element_actif.gere_depart()
            self.suivant()
            self.element_actif.gere_arrivee()
            return True

        # La combinaison Majuscule + entrée permet de passer au champ précédent
        if sequence.egale(MAJ_ENTREE):
            self.element_actif.gere_depart()
            self.precedent()
            self.element_actif.gere_arrivee()
            return True

        return False
            
    def affiche(self):
        # Colorie le fond du conteneur si une couleur de fond a été définie
        if self.fond != None:
            for posy in range(self.posy, self.posy + self.hauteur):
                self.minitel.position(self.posx, posy)
                self.minitel.couleur(fond = self.fond)
                self.minitel.repeter(' ', self.largeur)

        # Demande à chaque élément de s’afficher
        for element in self.elements:
            element.affiche()

        # Si un élément actif a été défini, on lui donne la main
        if self.element_actif != None:
            self.element_actif.gere_arrivee()

    def ajoute(self, element):
        assert isinstance(element, UI)
        assert element not in self.elements

        # Attribue la couleur du conteneur à l’élément par défaut
        if element.couleur == None:
            element.couleur = self.couleur

        # Ajoute l’élément à la liste d’éléments du conteneur
        self.elements.append(element)

        if self.element_actif == None and element.activable == True:
            self.element_actif = element

    def suivant(self):
        # S’il n’y a pas d’éléments, il ne peut pas y avoir d’élément actif
        if len(self.elements) == 0:
            return False

        # Récupère l’index de l’élément actif
        if self.element_actif == None:
            index = -1
        else:
            index = self.elements.index(self.element_actif)

        # Recherche l’élément suivant qui soit activable
        while index < len(self.elements) - 1:
            index += 1
            if self.elements[index].activable == True:
                self.element_actif = self.elements[index]
                return True

        return False

    def precedent(self):
        # S’il n’y a pas d’éléments, il ne peut pas y avoir d’élément actif
        if len(self.elements) == 0:
            return False

        # Récupère l’index de l’élément actif
        if self.element_actif == None:
            index = len(self.elements)
        else:
            index = self.elements.index(self.element_actif)

        # Recherche l’élément suivant qui soit activable
        while index > 0:
            index -= 1
            if self.elements[index].activable == True:
                self.element_actif = self.elements[index]
                return True

        return False

