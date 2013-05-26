#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""ImageMinitel est une classe permettant de convertir une image lisible par
PIL en semi-graphiques pour le Minitel.

"""

from operator import itemgetter

from minitel.constantes import ESC, SO, DC2, COULEURS_MINITEL
from minitel.Sequence import Sequence
from minitel.Minitel import Minitel
from math import sqrt

def _huit_niveaux(niveau):
    """Convertit un niveau sur 8 bits (256 valeurs possibles) en un niveau
    sur 3 bits (8 valeurs possibles).

    :param niveau:
        Niveau à convertir. Si c’est un tuple qui est fourni, la luminosité de
        la couleur est alors calculée. La formule est issue de la page
        http://alienryderflex.com/hsp.html
    :type niveau:
        un tuple ou un entier

    :returns:
        Un entier compris entre 0 et 7 inclus.
    """
    # Niveau peut soit être un tuple soit un entier
    # Gère les deux cas en testant l’exception
    try:
        return niveau * 8 / 256
    except TypeError:
        return int(
            round(
                sqrt(
                    0.299 * niveau[0] ** 2 +
                    0.587 * niveau[1] ** 2 +
                    0.114 * niveau[2] ** 2
                )
            ) * 8 / 256
        )

def _deux_couleurs(couleurs):
    """Réduit une liste de couleurs à un couple de deux couleurs.

    Les deux couleurs retenues sont les couleurs les plus souvent
    présentes.

    :param couleurs:
        Les couleurs à réduire. Chaque couleur doit être un entier compris
        entre 0 et 7 inclus.
    :type couleurs:
        Une liste d’entiers

    :returns:
        Un tuple de deux entiers représentant les couleurs sélectionnées.
    """
    assert isinstance(couleurs, list)

    # Crée une liste contenant le nombre de fois où un niveau est
    # enregistré
    niveaux = [0, 0, 0, 0, 0, 0, 0, 0]

    # Passe en revue tous les niveaux pour les comptabiliser
    for couleur in couleurs:
        niveaux[couleur] += 1

    # Prépare la liste des niveaux afin de pouvoir la trier du plus
    # utilisé au moins utilisé. Pour cela, on crée une liste de tuples
    # (niveau, nombre d’apparitions)
    niveaux = [(index, valeur) for index, valeur in enumerate(niveaux)]

    # Trie les niveaux par nombre d’apparition
    niveaux = sorted(niveaux, key = itemgetter(1), reverse = True)

    # Retourne les deux niveaux les plus rencontrés
    return (niveaux[0][0], niveaux[1][0])

def _arp_ou_avp(couleur, arp, avp):
    """Convertit une couleur en couleur d’arrière-plan ou d’avant-plan.

    La conversion se fait en calculant la proximité de la couleur avec la
    couleur d’arrière-plan (arp) et avec la couleur d’avant-plan (avp).

    :param couleur:
        La couleur à convertir (valeur de 0 à 7 inclus).
    :type couleur:
        un entier

    :param arp:
        La couleur d’arrière-plan (valeur de 0 à 7 inclus)
    :type arp:
        un entier

    :param avp:
        La couleur d’avant-plan (valeur de 0 à 7 inclus)
    :type avp:
        un entier

    :returns:
        0 si la couleur est plus proche de la couleur d’arrière-plan, 1 si
        la couleur est plus proche de la couleur d’avant-plan.
    """
    assert isinstance(couleur, int)
    assert isinstance(arp, int)
    assert isinstance(avp, int)

    if(abs(arp - couleur) < abs(avp - couleur)):
        return 0

    return 1

def _minitel_arp(niveau):
    """Convertit un niveau en une séquence de codes Minitel définissant la
    couleur d’arrière-plan.

    :param niveau:
        Le niveau à convertir (valeur de 0 à 7 inclus).
    :type niveau:
        un entier

    :returns:
        Un objet de type Sequence contenant la séquence à envoyer au
        Minitel pour avec une couleur d’arrière-plan correspondant au
        niveau.
    """
    assert isinstance(niveau, int)

    try:
        return Sequence([ESC, 0x50 + COULEURS_MINITEL[niveau]])
    except IndexError:
        return Sequence([ESC, 0x50])

def _minitel_avp(niveau):
    """Convertit un niveau en une séquence de codes Minitel définissant la
    couleur d’avant-plan.

    :param niveau:
        Le niveau à convertir (valeur de 0 à 7 inclus).
    :type niveau:
        un entier

    :returns:
        Un objet de type Sequence contenant la séquence à envoyer au
        Minitel pour avec une couleur d’avant-plan correspondant au niveau.
    """
    assert isinstance(niveau, int)

    try:
        return Sequence([ESC, 0x40 + COULEURS_MINITEL[niveau]])
    except IndexError:
        return Sequence([ESC, 0x47])

class ImageMinitel:
    """Une classe de gestion d’images Minitel avec conversion depuis une image
    lisible par PIL.

    Cette classe gère une image au sens Minitel du terme, c’est à dire par
    l’utilisation du mode semi-graphique dans lequel un caractère contient
    une combinaison de 2×3 pixels. Cela donne une résolution maximale de 80×72
    pixels.
    
    Hormis la faible résolution ainsi obtenue, le mode semi-graphique présente
    plusieurs inconvénients par rapport à un véritable mode graphique :

    - il ne peut y avoir que 2 couleurs par bloc de 2×3 pixels,
    - les pixels ne sont pas carrés
    """

    def __init__(self, minitel, disjoint = False):
        """Constructeur

        :param minitel:
            L’objet auquel envoyer les commandes
        :type minitel:
            un objet Minitel
        :param disjoint:
            Active le mode disjoint pour les images.
        :type disjoint:
            un booléen
        """
        assert isinstance(minitel, Minitel)
        assert isinstance(disjoint, bool)

        self.minitel = minitel

        # L’image est stockées sous forme de Sequences afin de pouvoir
        # l’afficher à n’importe quelle position sur l’écran
        self.sequences = []

        self.largeur = 0
        self.hauteur = 0
        self.disjoint = disjoint

    def envoyer(self, colonne = 1, ligne = 1):
        """Envoie l’image sur le Minitel à une position donnée

        Sur le Minitel, la première colonne a la valeur 1. La première ligne
        a également la valeur 1 bien que la ligne 0 existe. Cette dernière
        correspond à la ligne d’état et possède un fonctionnement différent
        des autres lignes.

        :param colonne:
            colonne à laquelle positionner le coin haut gauche de l’image
        :type colonne:
            un entier

        :param ligne:
            ligne à laquelle positionner le coin haut gauche de l’image
        :type ligne:
            un entier
        """
        assert isinstance(colonne, int)
        assert isinstance(ligne, int)

        for sequence in self.sequences:
            self.minitel.position(colonne, ligne)
            self.minitel.envoyer(sequence)
            ligne += 1

    def importer(self, image):
        """Importe une image de PIL et crée les séquences de code Minitel
        correspondantes. L’image fournie doit avoir été réduite à des
        dimensions inférieures ou égales à 80×72 pixels. La largeur doit être
        un multiple de 2 et la hauteur un multiple de 3.

        :param image:
            L’image à importer.
        :type niveau:
            une Image
        """
        assert image.size[0] <= 80
        assert image.size[1] <= 72

        # En mode semi-graphique, un caractère a 2 pixels de largeur
        # et 3 pixels de hauteur
        self.largeur = image.size[0] / 2
        self.hauteur = image.size[1] / 3

        # Initialise la liste des séquences
        self.sequences = []

        for hauteur in range(0, self.hauteur):
            # Variables pour l’optimisation du code généré
            old_arp = -1
            old_avp = -1
            old_alpha = 0
            compte = 0

            # Initialise une nouvelle séquence
            sequence = Sequence()

            # Passe en mode semi-graphique
            sequence.ajoute(SO)

            if self.disjoint:
                sequence.ajoute([ESC, 0x5A])

            for largeur in range(0, self.largeur):
                # Récupère 6 pixels
                pixels = [
                    image.getpixel((largeur * 2 + x, hauteur * 3 + y))
                    for x, y in [(0, 0), (1, 0),
                                  (0, 1), (1, 1),
                                  (0, 2), (1, 2)]
                ]

                if self.disjoint:
                    # Convertit chaque couleur de pixel en deux niveaux de gris
                    pixels = [_huit_niveaux(pixel) for pixel in pixels]

                    arp, avp = _deux_couleurs(pixels)

                    if arp != 0:
                        arp, avp = 0, arp

                else:
                    # Convertit chaque couleur de pixel en huit niveau de gris
                    pixels = [_huit_niveaux(pixel) for pixel in pixels]

                    # Recherche les deux couleurs les plus fréquentes
                    # un caractère ne peut avoir que deux couleurs !
                    arp, avp = _deux_couleurs(pixels)

                # Réduit à deux le nombre de couleurs dans un bloc de 6 pixels
                # Cela peut faire apparaître des artefacts mais est inévitable
                pixels = [_arp_ou_avp(pixel, arp, avp) for pixel in pixels]

                # Convertit les 6 pixels en un caractère mosaïque du minitel
                # Le caractère est codé sur 7 bits
                bits = [
                    '0',
                    str(pixels[5]),
                    '1',
                    str(pixels[4]),
                    str(pixels[3]),
                    str(pixels[2]),
                    str(pixels[1]),
                    str(pixels[0])
                ]

                # Génère l’octet (7 bits) du caractère mosaïque
                alpha = int(''.join(bits), 2)

                # Si les couleurs du précédent caractères sont inversés,
                # inverse le caractère mosaïque. Cela évite d’émettre
                # à nouveau des codes couleurs. Cela fonctionne uniquement
                # lorsque le mode disjoint n’est pas actif
                if not self.disjoint and old_arp == avp and old_avp == arp:
                    # Inverse chaque bit à l’exception du 6e et du 8e
                    alpha = alpha ^ 0b01011111
                    avp, arp = arp, avp
                    
                if old_arp == arp and old_avp == avp and alpha == old_alpha:
                    # Les précédents pixels sont identiques, on le retient
                    # pour utiliser un code de répétition plus tard
                    compte += 1
                else:
                    # Les pixels ont changé, mais il peut y avoir des pixels
                    # qui n’ont pas encore été émis pour cause d’optimisation
                    if compte > 0:
                        if compte == 1:
                            sequence.ajoute(old_alpha)
                        else:
                            sequence.ajoute([DC2, 0x40 + compte])

                        compte = 0

                    # Génère les codes Minitel
                    if old_arp != arp:
                        # L’arrière-plan a changé
                        sequence.ajoute(_minitel_arp(arp))
                        old_arp = arp

                    if old_avp != avp:
                        # L’avant-plan a changé
                        sequence.ajoute(_minitel_avp(avp))
                        old_avp = avp

                    sequence.ajoute(alpha)
                    old_alpha = alpha

            if compte > 0:
                if compte == 1:
                    sequence.ajoute(old_alpha)
                else:
                    sequence.ajoute([DC2, 0x40 + compte])

                compte = 0

            if self.disjoint:
                sequence.ajoute([ESC, 0x59])

            # Une ligne vient d’être terminée, on la stocke dans la liste des
            # séquences
            self.sequences.append(sequence)
