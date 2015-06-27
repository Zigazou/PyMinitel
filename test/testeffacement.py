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
minitel.efface('vraimenttout')
minitel.curseur(False)

n = 5 

minitel.envoyer(u'Ce texte sera effacé dans {} secondes'.format(n) )
minitel.sortie.join()

for i in range(n) :
	minitel.position(1,i+2)
	minitel.envoyer( str(n-i) ) 
	sleep(1)

minitel.efface('vraimenttout')
minitel.envoyer('Hello world !')
minitel.sortie.join()

minitel.close()
