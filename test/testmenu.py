#!/usr/bin/env python
# -*- coding: utf-8 -*-

from minitel.Minitel import Minitel
from minitel.ui.Menu import Menu
from minitel.constantes import *
from minitel.utils import canon, comparer

minitel = Minitel()

minitel.devinerVitesse()
minitel.identifier()
minitel.definirVitesse(9600)
minitel.definirMode('VIDEOTEX')
minitel.configurerClavier(etendu = True, curseur = False, minuscule = True)
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

