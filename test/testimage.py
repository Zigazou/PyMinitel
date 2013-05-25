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

exemples = [
  ('testimage1.jpg', 80, 72, 1, 1),
  ('testimage2.jpg', 36, 72, 11, 1),
  ('testimage3.jpg', 80, 72, 1, 1),
  ('testimage4.jpg', 80, 72, 1, 1),
  ('testimage5.jpg', 80, 72, 1, 1),
  ('testimage6.jpg', 80, 72, 1, 1),
]

for fichier, largeur, hauteur, colonne, ligne in exemples:
	image = Image.open(fichier)
	image = image.resize((largeur, hauteur), Image.ANTIALIAS)

	image_minitel = ImageMinitel(minitel)
	image_minitel.importer(image)
	image_minitel.envoyer(colonne, ligne)

	minitel.sortie.join()
	sleep(3)
	minitel.efface()

minitel.close()
