#!/usr/bin/env python
# -*- coding: utf-8 -*-

from minitel.Minitel import Minitel
from minitel.ImageMinitel import ImageMinitel
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
from time import sleep

# Crée une image avec un texte
fonte = ImageFont.truetype("/home/fred/.fonts/OdaBalloon.ttf", 60)
#fonte.fontmode = 1
largeur, hauteur = fonte.getsize("PyMinitel")
image = Image.new("1", (largeur, hauteur))
draw = ImageDraw.Draw(image)
draw.text((0, 0),"PyMinitel", 255, font = fonte)
image = image.resize((largeur / 3, int(hauteur * 1.35 / 3)), Image.NEAREST)

minitel = Minitel()

minitel.deviner_vitesse()
minitel.identifier()
minitel.definir_vitesse(4800)
minitel.definir_mode('VIDEOTEX')
minitel.configurer_clavier(etendu = True, curseur = False, minuscule = True)
minitel.echo(False)
minitel.efface()
minitel.curseur(False)

# Met à jour la ligne de contrôle
minitel.position(1, 0)
minitel.envoyer(u"PyMinitel v0.1.2 - Frédéric Bisson")
minitel.efface(portee = 'finligne')

image_minitel1 = ImageMinitel(minitel, disjoint = False)
image_minitel1.importer(image)

image_minitel2 = ImageMinitel(minitel, disjoint = True)
image_minitel2.importer(image)

image_minitel1.envoyer(1, 2)
#image_minitel2.envoyer(1, 2)

minitel.position(1, 1)
for j in range(0, 4):
    for i in range(0, 15):
        minitel.insere(nb_ligne = 1)
        # Au-delà de 1200 bauds, le Minitel n’est pas capable d’encaisser une
        # série trop rapide de déplacements de la zone texte. On introduit donc
        # un délai de 3/100e de secondes (déterminé de façon empirique). Les
        # Minitel 1, 1B et 2 présentent tous cette limite.
        sleep(0.03)
        minitel.sortie.join()

    for i in range(0, 15):
        minitel.supprime(nb_ligne = 1)
        # Au-delà de 1200 bauds, le Minitel n’est pas capable d’encaisser une
        # série trop rapide de déplacements de la zone texte. On introduit donc
        # un délai de 3/100e de secondes (déterminé de façon empirique). Les
        # Minitel 1, 1B et 2 présentent tous cette limite.
        sleep(0.03)
        minitel.sortie.join()

minitel.sortie.join()

minitel.close()
