PyMinitel
=========

PyMinitel contient la classe Minitel qui permet d’envoyer et de recevoir
des séquences de caractères vers et depuis un Minitel dans un programme écrit
en Python. Elle fonctionne via une liaison série entre l’ordinateur
et le Minitel.

PyMinitel contient aussi des classes permettant la création d’une interface
utilisateur rudimentaire.

Installation
============

Pour pouvoir utiliser PyMinitel, vous devez l’installer sur votre système.

PyMinitel utilise distutils. L’installation en est donc simplifiée. Il suffit
d’exécuter la commande suivante sous Linux dans le répertoire de PyMinitel::

   sudo python setup.py install



Démarrage rapide
================

Le cycle de vie d’un objet Minitel consiste en la création, la
détermination de la vitesse du Minitel, de ses capacités, l’utilisation
du Minitel par l’application et la libération des ressources::
  
  from minitel.Minitel import Minitel

  minitel = Minitel()

  minitel.deviner_vitesse()
  minitel.identifier()

  # ...
  # Utilisation de l’objet minitel
  # ...

  minitel.close()


.. toctree::
   :maxdepth: 2



Index et tables
===============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
