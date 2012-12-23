#!/usr/bin/env python
# -*- coding: utf-8 -*-

from minitel.Minitel import Minitel
from minitel.ui.Menu import Menu

minitel = Minitel()

minitel.deviner_vitesse()
minitel.identifier()
minitel.definir_vitesse(9600)
minitel.definir_mode('VIDEOTEX')
minitel.configurer_clavier(etendu = True, curseur = False, minuscule = True)
minitel.echo(False)
minitel.efface()
minitel.curseur(False)

options = [
  u'Nouveau',
  u'Ouvrir',
  u'-',
  u'Enregistrer',
  u'Enreg. sous...',
  u'Rétablir',
  u'-',
  u'Aperçu',
  u'Imprimer...',
  u'-',
  u'Fermer',
  u'Quitter'
]

menu = Menu(minitel, options, 5, 3)
menu.affiche()

menu.executer()

minitel.close()

