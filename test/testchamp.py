#!/usr/bin/env python
# -*- coding: utf-8 -*-

from minitel.Minitel import Minitel
from minitel.ui.ChampTexte import ChampTexte
from minitel.constantes import *

minitel = Minitel()

minitel.devinerVitesse()
minitel.identifier()
minitel.definirVitesse(9600)
minitel.definirMode('VIDEOTEX')
minitel.configurerClavier(etendu = True, curseur = False, minuscule = True)
minitel.echo(False)
minitel.efface()
minitel.curseur(False)

champ = ChampTexte(minitel, 10, 10, 20, 60, 'Hello world')
champ.affiche()
champ.gereArrivee()

champ.executer()

minitel.close()

