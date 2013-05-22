PyMinitel
=========

PyMinitel est une bibliothèque Python permettant de piloter un Minitel
depuis un PC sous Linux. Pour cela, la bibliothèque PySerial est
nécessaire car elle est utilisée pour dialoguer avec le Minitel, en
émission comme en réception.

Le module de base utilise deux threads (émission + réception) offrant
ainsi une communication asynchrone. Cette particularité permet au
script de ne pas être tenu à une grande réactivité vis-à-vis du
Minitel.

En plus du module de base, PyMinitel est livrée avec une interface
utilisateur basique.

Documentation
-------------

Pour générer la documentation, il faut se placer dans le
sous-répertoire doc et taper la commande "make html". Les fichiers
générés se trouveront alors dans _build/html.

Installation
------------

sudo python setup.py install

Exemples
--------

Le sous-répertoire test contient quelques exemples d’utilisation de la bibliothèque.
