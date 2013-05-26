#!/usr/bin/env python
# -*- coding: utf-8 -*-

from minitel.Minitel import Minitel
from minitel.ImageMinitel import ImageMinitel
from PIL import Image
from time import sleep

minitel = Minitel()

minitel.deviner_vitesse()
minitel.identifier()
minitel.definir_vitesse(4800)
minitel.definir_mode('VIDEOTEX')
minitel.configurer_clavier(etendu = True, curseur = False, minuscule = True)
minitel.echo(False)
minitel.efface()
minitel.curseur(False)

minitel.position(1, 0)
minitel.envoyer(u"PyMinitel v0.1.2 - Frédéric Bisson")
minitel.efface(portee = 'finligne')

image = Image.open('testimage2.jpg')
image = image.resize((36, 72), Image.ANTIALIAS)
image_minitel = ImageMinitel(minitel)
image_minitel.importer(image)
image_minitel.envoyer(23, 1)

minitel.position(3, 8)
minitel.taille(largeur = 2, hauteur = 2)
minitel.couleur(caractere = 'vert')
minitel.envoyer('PyMinitel')
minitel.position(6, 9)
minitel.envoyer('___________')

textes = [
    # ---------------------
    u"  Une bibliothèque",
    u"Python pour contrôler",
    u"un Minitel depuis un",
    u"ordinateur sous Linux"
]

ligne = 12
for texte in textes:
    minitel.position(1, ligne)
    minitel.envoyer(texte)
    ligne += 1

minitel.sortie.join()

minitel.close()
