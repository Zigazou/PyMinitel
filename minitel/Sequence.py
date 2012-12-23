#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Sequence est un module permettant de gérer les séquences de caractères
pouvant être envoyées à un Minitel.

"""

from unicodedata import normalize
from binascii import unhexlify

# Tables de conversion des caractères spéciaux
UNICODEVERSVIDEOTEX = {
    u'£': '1923', u'°': '1930', u'±': '1931', 
    u'←': '192C', u'↑': '192D', u'→': '192E', u'↓': '192F', 
    u'¼': '193C', u'½': '193D', u'¾': '193E', 
    u'ç': '194B63', u'’': '194B27', 
    u'à': '194161', u'á': '194261', u'â': '194361', u'ä': '194861', 
    u'è': '194165', u'é': '194265', u'ê': '194365', u'ë': '194865', 
    u'ì': '194169', u'í': '194269', u'î': '194369', u'ï': '194869', 
    u'ò': '19416F', u'ó': '19426F', u'ô': '19436F', u'ö': '19486F', 
    u'ù': '194175', u'ú': '194275', u'û': '194375', u'ü': '194875', 
    u'Œ': '196A', u'œ': '197A', 
    u'ß': '197B', u'β': '197B'
}

UNICODEVERSAUTRE = {
    u'£': '0E230F',
    u'°': '0E5B0F', u'ç': '0E5C0F', u'’': '27', u'`': '60', u'§': '0E5D0F',
    u'à': '0E400F', u'è': '0E7F0F', u'é': '0E7B0F', u'ù': '0E7C0F'
}

class Sequence:
    """Une classe représentant une séquence de valeurs

    Une Séquence est une suite de valeurs prêtes à être envoyées à un Minitel.
    Ces valeurs respectent la norme ASCII.
    """
    def __init__(self, valeur = None, standard = 'VIDEOTEX'):
        """Constructeur de Sequence

        :param valeur:
            valeur à ajouter à la construction de l’objet. Si la valeur est à
            None, aucune valeur n’est ajoutée
        :type valeur:
            une chaîne de caractères, un entier, une liste ou None

        :param standard:
            standard à utiliser pour la conversion unicode vers Minitel. Les
            valeurs possibles sont VIDEOTEX, MIXTE et TELEINFORMATIQUE (la
            casse est importante)
        :type standard:
            une chaîne de caractères
        """
        assert valeur == None or isinstance(valeur, (list, int, str, unicode))
        assert standard in ['VIDEOTEX', 'MIXTE', 'TELEINFORMATIQUE']

        self.valeurs = []
        self.longueur = 0
        self.standard = standard

        if valeur != None:
            self.ajoute(valeur)
        
    def ajoute(self, valeur):
        """Ajoute une valeur ou une séquence de valeurs

        La valeur soumise est d’abord canonisée par la méthode canonise avant
        d’être ajoutée à la séquence. Cela garantit que la séquence ne contient
        que des entiers représentant des caractères de la norme ASCII.

        :param valeur:
            valeur à ajouter
        :type valeur:
            une chaîne de caractères, un entier ou une liste
        """
        assert isinstance(valeur, (list, int, str, unicode))

        self.valeurs += self.canonise(valeur)
        self.longueur = len(self.valeurs)

    def canonise(self, valeur):
        """Canonise une séquence de caractères

        Si une liste est soumise, quelle que soit sa profondeur, elle sera
        remise à plat. Une liste peut donc contenir des chaînes de caractères,
        des entiers ou des listes. Cette facilité permet la construction de
        séquences de caractères plus aisée. Cela facilite également la
        comparaison de deux séquences.

        :param valeur:
            valeur à canoniser
        :type valeur:
            une chaîne de caractères, un entier ou une liste

        :returns:
            Une liste de profondeur 1 d’entiers représentant des valeurs à la
            norme ASCII.

        Exemple::
            canonise(['dd', 32, ['dd', 32]]) retournera
            [100, 100, 32, 100, 100, 32]
        """
        assert isinstance(valeur, (list, int, str, unicode))

        # Si la valeur est juste un entier, on le retient dans une liste
        if isinstance(valeur, int):
            return [valeur]

        # À ce point, le paramètre contient soit une chaîne de caractères, soit
        # une liste. L’une ou l’autre est parcourable par une boucle for ... in
        # Transforme récursivement chaque élément de la liste en entier
        canonise = []
        for element in valeur:
            if isinstance(element, str):
                # Cette boucle traite 2 cas : celui ou liste est une chaîne de
                # caractères et celui ou element est une chaîne de caractères
                for caractere in element:
                    canonise.append(ord(caractere))
            elif isinstance(element, unicode):
                # Cette boucle traite 2 cas : celui ou liste est une chaîne
                # unicode et celui ou element est une chaîne de caractères
                for caractere in element:
                    for ascii in self.unicode_vers_minitel(caractere):
                        canonise.append(ord(ascii))
            elif isinstance(element, int):
                # Un entier a juste besoin d’être ajouté à la liste finale
                canonise.append(element)
            elif isinstance(element, list):
                # Si l’élément est une liste, on la canonise récursivement
                canonise = canonise + self.canonise(element)

        return canonise

    def unicode_vers_minitel(self, caractere):
        """Convertit un caractère unicode en son équivalent Minitel

        :param caractere:
            caractère à convertir
        :type valeur:
            une chaîne de caractères unicode

        :returns:
            une chaîne de caractères contenant une suite de caractères à
            destination du Minitel.
        """
        assert isinstance(caractere, unicode) and len(caractere) == 1

        if self.standard == 'VIDEOTEX':
            if caractere in UNICODEVERSVIDEOTEX:
                return unhexlify(UNICODEVERSVIDEOTEX[caractere])
        else:
            if caractere in UNICODEVERSAUTRE:
                return unhexlify(UNICODEVERSAUTRE[caractere])

        return normalize('NFKD', caractere).encode('ascii', 'replace')

    def egale(self, sequence):
        """Teste l’égalité de 2 séquences

        :param sequence:
            séquence à comparer. Si la séquence n’est pas un objet Sequence,
            elle est d’abord convertie en objet Sequence afin de canoniser ses
            valeurs.
        :type sequence:
            un objet Sequence, une liste, un entier, une chaîne de caractères
            ou une chaîne unicode

        :returns:
            True si les 2 séquences sont égales, False sinon
        """
        assert isinstance(sequence, (Sequence, list, int, str, unicode))

        # Si la séquence à comparer n’est pas de la classe Sequence, alors
        # on la convertit
        if not isinstance(sequence, Sequence):
            sequence = Sequence(sequence)

        return self.valeurs == sequence.valeurs

