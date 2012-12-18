#!/usr/bin/env python
# -*- coding: utf-8 -*-
def canon(liste):
    """Canonise une séquence de caractères

    Arguments:
    liste -- une chaîne de caractères, un entier ou une liste

    Note:
    Si une liste est soumise, quelle que soit sa profondeur, elle sera remise
    à plat. Une liste peut donc contenir des chaînes de caractères, des entiers
    ou des listes. Cette facilité permet la construction de séquences de
    caractères plus aisée.

    Retour:
    Une liste de profondeur 1 de caractères ou d’entiers
    """
    assert isinstance(liste, list) or isinstance(liste, int) or isinstance(liste, str)

    if isinstance(liste, int): return [liste]

    canonise = []
    for element in liste:
        if isinstance(element, str):
            for caractere in element:
                canonise.append(ord(caractere))
        elif isinstance(element, int):
            canonise.append(element)
        elif isinstance(element, list):
            canonise = canonise + canon(element)

    return canonise

def comparer(liste1, liste2):
    """Compare deux séquences de caractères

    Arguments:
    liste1 -- une séquence de caractères
    liste2 -- une séquence de caractères

    Les séquences de caractères s’entendent dans le sens des séquences de
    caractères de la fonction canon.

    Retour:
    True si les deux listes sont identiques une fois canonisées,
    False sinon.
    """
    return canon(liste1) == canon(liste2)

