#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from serial import Serial
from threading import Thread
from Queue import Queue, Empty

from binascii import unhexlify
from time import sleep

from constantes import *
from utils import canon

class Minitel:
    def __init__(self, peripherique = '/dev/ttyUSB0'):
        # Initialise l’état du Minitel
        self.mode = 'VIDEOTEX'
        self.vitesse = 1200

        # Initialise la liste des capacités du Minitel
        self.capacite = {
            'nom': u'Minitel inconnu',
            'retournable': False,
            'clavier': 'ABCD',
            'vitesse': 1200,
            'constructeur': u'Inconnu',
            '80colonnes': False,
            'caracteres': False,
            'version': None
        }

        # Crée les deux files d’attente entrée/sortie
        self.entree = Queue()
        self.sortie = Queue()

        # Initialise la connexion avec le Minitel
        self._minitel = Serial(
            peripherique,
            baudrate = 1200,
            bytesize = 7,
            parity   = 'E',
            stopbits = 1,
            timeout  = 1,
            xonxoff  = 0,
            rtscts   = 0
        )

        # Initialise un drapeau pour l’arrêt des threads
        self._continuer = True

        # Crée les deux threads de lecture/écriture
        self._threads = []
        self._threads.append(Thread(None, self._gestionEntree, None, ()))
        self._threads.append(Thread(None, self._gestionSortie, None, ()))

        # Démarre les deux threads de lecture/écriture
        for t in self._threads:
            t.setDaemon(True)
            try:
                t.start()
            except (KeyboardInterrupt, SystemExit):
                self.close()

    def close(self):
        self._continuer = False

        # Attend que tous les threads aient fini
        for t in self._threads: t.join()

        self._minitel.close()

    def _gestionEntree(self):
        # Ajoute à la file entree tout ce que le Minitel peut envoyer
        while self._continuer:
            # Attend un caractère pendant 1 seconde
            caractere = self._minitel.read()

            if len(caractere) == 1: self.entree.put(caractere)

    def _gestionSortie(self):
        # Envoie au Minitel tout ce qui se trouve dans la file sortie et
        # continue de le faire tant que le drapeau continuer est à vrai
        while self._continuer or not self.sortie.empty():
            # Attend un caractère pendant 1 seconde
            try:
                self._minitel.write(self.sortie.get(block = True, timeout = 1))

                # Attend que le caractère envoyé au minitel ait bien été envoyé
                # car la sortie est bufferisée
                self._minitel.flush()

                # Permet à la méthode join de la file de fonctionner
                self.sortie.task_done()

            except Empty:
                continue

    def envoyer(self, contenu):
        if isinstance(contenu, int):
            self.sortie.put(chr(contenu))
        elif isinstance(contenu, str):
            for caractere in contenu:
                self.sortie.put(caractere)
        elif isinstance(contenu, unicode):
            for caractere in self.normaliserChaine(contenu):
                self.sortie.put(caractere)
        elif isinstance(contenu, list):
            for element in contenu:
                self.envoyer(element)

    def recevoir(self, bloque = False, attente = None):
        return self.entree.get(bloque, attente)

    def recevoirSequence(self):
        sequence = [ord(self.recevoir(bloque = True))]

        if sequence[0] in [SS2, SEP]:
            sequence.append(ord(self.recevoir(bloque = True)))
        elif sequence[0] == ESC:
            try:
                caractere = self.recevoir(bloque = True, attente = 0.1)
                sequence.append(ord(caractere))

                if sequence == CSI:
                    sequence.append(ord(self.recevoir(bloque = True)))
                    if sequence[2] in [0x32, 0x34]:
                        sequence.append(ord(self.recevoir(bloque = True)))
            except Empty:
                pass

        return canon(sequence)

    def appeler(self, contenu, attente):
        self.entree = Queue()
        self.envoyer(contenu)
        self.sortie.join()

        retour = []
        for i in range(0, attente):
            try:
                retour.append(self.entree.get(block = True, timeout = 1))
            except Empty:
                break

        return retour

    def definirMode(self, mode = 'VIDEOTEX'):
        # 3 modes sont possibles
        if mode not in ['VIDEOTEX', 'MIXTE', 'TELEINFORMATIQUE']: return False

        # Si le mode demandé est déjà actif, ne fait rien
        if self.mode == mode: return True

        resultat = False

        if self.mode == 'TELEINFORMATIQUE' and mode == 'VIDEOTEX':
            retour = self.appeler([CSI, 0x3f, 0x7b], 2)
            resultat = comparer(retour, [SEP, 0x5e])
        elif self.mode == 'TELEINFORMATIQUE' and mode == 'MIXTE':
            retour = self.appeler([CSI, 0x3f, 0x7b], 2)
            resultat = comparer(retour, [SEP, 0x5e])
            if not resultat: return False
            retour = self.appeler([PRO2, MIXTE1], 2)
            resultat = comparer(retour, [SEP, 0x70])
        elif self.mode == 'VIDEOTEX' and mode == 'MIXTE':
            retour = self.appeler([PRO2, MIXTE1], 2)
            resultat = comparer(retour, [SEP, 0x70])
        elif self.mode == 'VIDEOTEX' and mode == 'TELEINFORMATIQUE':
            retour = self.appeler([PRO2, TELINFO], 4)
            resultat = comparer(retour, [CSI, 0x3f, 0x7a])
        elif self.mode == 'MIXTE' and mode == 'VIDEOTEX':
            retour = self.appeler([PRO2, MIXTE2], 2)
            resultat = comparer(retour, [SEP, 0x71])
        elif self.mode == 'MIXTE' and mode == 'TELEINFORMATIQUE':
            retour = self.appeler([PRO2, TELINFO], 4)
            resultat = comparer(retour, [CSI, 0x3f, 0x7a])

        if resultat: self.mode = mode

        return resultat

    def identifier(self):
        self.capacite = {
            'nom': u'Minitel inconnu',
            'retournable': False,
            'clavier': 'ABCD',
            'vitesse': 1200,
            'constructeur': u'Inconnu',
            '80colonnes': False,
            'caracteres': False,
            'version': None
        }

        # Émet la commande d’identification
        retour = self.appeler([PRO1, ENQROM], 5)

        # Teste la validité de la réponse
        if len(retour) != 5: return
        if retour[0] != chr(SOH): return
        if retour[4] != chr(EOT): return

        # Extrait les caractères d’identification
        constructeurMinitel = retour[1]
        typeMinitel         = retour[2]
        versionLogiciel     = retour[3]
        identifiant         = retour[1] + retour[2] + retour[3]

        # Constructeurs
        constructeurs = {
            'A': u'Matra',
            'B': u'RTIC',
            'C': u'Telic-Alcatel',
            'D': u'Thomson',
            'E': u'CCS',
            'F': u'Fiet',
            'G': u'Fime',
            'H': u'Unitel',
            'I': u'Option',
            'J': u'Bull',
            'K': u'Télématique',
            'L': u'Desmet'
        }
            
        # Types de Minitel
        typeMinitels = {
            'b': { 'nom': u'Minitel 1', 'retournable': False, 'clavier': 'ABCD', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'c': { 'nom': u'Minitel 1', 'retournable': False, 'clavier': 'Azerty', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'd': { 'nom': u'Minitel 10', 'retournable': False, 'clavier': 'Azerty', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'e': { 'nom': u'Minitel 1 couleur', 'retournable': False, 'clavier': 'Azerty', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'f': { 'nom': u'Minitel 10', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'g': { 'nom': u'Émulateur', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 9600, '80colonnes': True, 'caracteres': True },
            'j': { 'nom': u'Imprimante', 'retournable': False, 'clavier': None, 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'r': { 'nom': u'Minitel 1', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            's': { 'nom': u'Minitel 1 couleur', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            't': { 'nom': u'Terminatel 252', 'retournable': False, 'clavier': None, 'vitesse': 1200, '80colonnes': False, 'caracteres': False },
            'u': { 'nom': u'Minitel 1B', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 4800, '80colonnes': True, 'caracteres': False },
            'v': { 'nom': u'Minitel 2', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 9600, '80colonnes': True, 'caracteres': True },
            'w': { 'nom': u'Minitel 10B', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 4800, '80colonnes': True, 'caracteres': False },
            'y': { 'nom': u'Minitel 5', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 9600, '80colonnes': True, 'caracteres': True },
            'z': { 'nom': u'Minitel 12', 'retournable': True, 'clavier': 'Azerty', 'vitesse': 9600, '80colonnes': True, 'caracteres': True },
        }

        if typeMinitel in typeMinitels:
            self.capacite = typeMinitels[typeMinitel]

        if constructeurMinitel in constructeurs:
            self.capacite['constructeur'] = constructeurs[constructeurMinitel]

        self.capacite['version'] = versionLogiciel

        # Correction du constructeur
        if constructeurMinitel == 'B' and typeMinitel == 'v':
            self.capacite['constructeur'] = u'Philips'
        elif constructeurMinitel == 'C' and versionLogiciel == ['4', '5', ';', '<']:
            self.capacite['constructeur'] = u'Telic ou Matra'

        # Détermine le mode écran dans lequel se trouve le Minitel
        retour = self.appeler([PRO1, STATUS_FONCTIONNEMENT], LONGUEUR_PRO2)

        if len(retour) != LONGUEUR_PRO2:
            # Le Minitel est en mode Téléinformatique car il ne répond pas
            # à une commande protocole
            self.mode = 'TELEINFORMATIQUE'
        elif ord(retour[3]) & 1 == 1:
            # Le bit 1 du status fonctionnement indique le mode 80 colonnes
            self.mode = 'MIXTE'
        else:
            # Par défaut, on considère qu’on est en mode Vidéotex
            self.mode = 'VIDEOTEX'

        return

    def devinerVitesse(self):
        # Vitesses possibles jusqu’au Minitel 2
        vitesses = [9600, 4800, 1200, 300]

        for vitesse in vitesses:
            # Configure le port série à la vitesse à tester
            self._minitel.baudrate = vitesse

            # Envoie une demande de statut terminal
            retour = self.appeler([PRO1, STATUS_TERMINAL], LONGUEUR_PRO2)

            # Le Minitel doit renvoyer un acquittement PRO2
            if len(retour) == LONGUEUR_PRO2:
                self.vitesse = vitesse
                return vitesse

        return -1

    def definirVitesse(self, vitesse):
        # Vitesses possibles jusqu’au Minitel 2
        vitesses = {300: B300, 1200: B1200, 4800: B4800, 9600: B9600}

        # Teste la validité de la vitesse demandée
        if vitesse not in vitesses: return False
        if vitesse > self.capacite['vitesse']: return False

        # Envoie une commande protocole de programmation de vitesse
        retour = self.appeler([PRO2, PROG, vitesses[vitesse]], LONGUEUR_PRO2)

        # Le Minitel doit renvoyer un acquittement PRO2
        if len(retour) == LONGUEUR_PRO2:
            # Si on peut lire un acquittement PRO2 avant d’avoir régler la
            # vitesse du port série, c’est que le Minitel ne peut pas utiliser
            # la vitesse demandée
            return False

        # Configure le port série à la nouvelle vitesse
        self._minitel.baudrate = vitesse
        self.vitesse = vitesse

        return True

    def configurerClavier(self, etendu = False, curseur = False, minuscule = False):
        bascules = { True: START, False: STOP }
        appels = [
            ([PRO3, bascules[etendu], RCPT_CLAVIER, ETEN], LONGUEUR_PRO3),
            ([PRO3, bascules[curseur], RCPT_CLAVIER, C0], LONGUEUR_PRO3),
            ([PRO2, bascules[minuscule], MINUSCULES], LONGUEUR_PRO2)
        ]

        for appel in appels:
            commande = appel[0]
            longueur = appel[1]
            retour = self.appeler(commande, longueur)
            if len(retour) != longueur: return False

        return True

    def normaliserCouleur(self, couleur):
        # Les niveaux de gris s’échelonnent comme suit :
        # nor, bleu, rouge, magenta, vert, cyan, jaune, blanc
        couleurs = {
            'noir': 0, 'rouge': 1, 'vert': 2, 'jaune': 3,
            'bleu': 4, 'magenta': 5, 'cyan': 6, 'blanc': 7,
            '0': 0, '1': 4, '2': 1, '3': 5,
            '4': 2, '5': 6, '6': 3, '7': 7,
            0: 0, 1: 4, 2: 1, 3: 5,
            4: 2, 5: 6, 6: 3, 7: 7
        }

        if couleur in couleurs: return couleurs[couleur]

        return None

    def normaliserChaine(self, chaine):
        if self.mode == 'VIDEOTEX':
            chaine = chaine.replace(u'£', unhexlify('1923'))
            chaine = chaine.replace(u'←', unhexlify('192C'))
            chaine = chaine.replace(u'↑', unhexlify('192D'))
            chaine = chaine.replace(u'→', unhexlify('192E'))
            chaine = chaine.replace(u'↓', unhexlify('192F'))
            chaine = chaine.replace(u'°', unhexlify('1930'))
            chaine = chaine.replace(u'±', unhexlify('1931'))
            chaine = chaine.replace(u'¼', unhexlify('193C'))
            chaine = chaine.replace(u'½', unhexlify('193D'))
            chaine = chaine.replace(u'¾', unhexlify('193E'))
            chaine = chaine.replace(u'ç', unhexlify('194B') + u'c')
            chaine = chaine.replace(u'’', unhexlify('194B') + u"'")

            chaine = chaine.replace(u'à', unhexlify('1941') + u'a')
            chaine = chaine.replace(u'á', unhexlify('1942') + u'a')
            chaine = chaine.replace(u'â', unhexlify('1943') + u'a')
            chaine = chaine.replace(u'ä', unhexlify('1948') + u'a')

            chaine = chaine.replace(u'è', unhexlify('1941') + u'e')
            chaine = chaine.replace(u'é', unhexlify('1942') + u'e')
            chaine = chaine.replace(u'ê', unhexlify('1943') + u'e')
            chaine = chaine.replace(u'ë', unhexlify('1948') + u'e')

            chaine = chaine.replace(u'ì', unhexlify('1941') + u'i')
            chaine = chaine.replace(u'í', unhexlify('1942') + u'i')
            chaine = chaine.replace(u'î', unhexlify('1943') + u'i')
            chaine = chaine.replace(u'ï', unhexlify('1948') + u'i')

            chaine = chaine.replace(u'ò', unhexlify('1941') + u'o')
            chaine = chaine.replace(u'ó', unhexlify('1942') + u'o')
            chaine = chaine.replace(u'ô', unhexlify('1943') + u'o')
            chaine = chaine.replace(u'ö', unhexlify('1948') + u'o')

            chaine = chaine.replace(u'ù', unhexlify('1941') + u'u')
            chaine = chaine.replace(u'ú', unhexlify('1942') + u'u')
            chaine = chaine.replace(u'û', unhexlify('1943') + u'u')
            chaine = chaine.replace(u'ü', unhexlify('1948') + u'u')

            chaine = chaine.replace(u'Œ', unhexlify('196A'))
            chaine = chaine.replace(u'œ', unhexlify('197A'))
            chaine = chaine.replace(u'ß', unhexlify('197B'))
            chaine = chaine.replace(u'β', unhexlify('197B'))
        else:
            chaine = chaine.replace(u'£', unhexlify('0E230F'))
            chaine = chaine.replace(u'←', unhexlify('20'))
            chaine = chaine.replace(u'↑', unhexlify('5E'))
            chaine = chaine.replace(u'→', unhexlify('20'))
            chaine = chaine.replace(u'↓', unhexlify('20'))
            chaine = chaine.replace(u'°', unhexlify('0E5B0F'))
            chaine = chaine.replace(u'±', unhexlify('20'))
            chaine = chaine.replace(u'¼', unhexlify('20'))
            chaine = chaine.replace(u'½', unhexlify('20'))
            chaine = chaine.replace(u'¾', unhexlify('20'))
            chaine = chaine.replace(u'ç', unhexlify('0E5C0F'))
            chaine = chaine.replace(u'’', unhexlify('27'))
            chaine = chaine.replace(u'`', unhexlify('60'))
            chaine = chaine.replace(u'§', unhexlify('0E5D0F'))

            chaine = chaine.replace(u'à', unhexlify('0E400F'))
            chaine = chaine.replace(u'á', u'a')
            chaine = chaine.replace(u'â', u'a')
            chaine = chaine.replace(u'ä', u'a')

            chaine = chaine.replace(u'è', unhexlify('0E7F0F'))
            chaine = chaine.replace(u'é', unhexlify('0E7B0F'))
            chaine = chaine.replace(u'ê', u'e')
            chaine = chaine.replace(u'ë', u'e')

            chaine = chaine.replace(u'ì', u'i')
            chaine = chaine.replace(u'í', u'i')
            chaine = chaine.replace(u'î', u'i')
            chaine = chaine.replace(u'ï', u'i')

            chaine = chaine.replace(u'ò', u'o')
            chaine = chaine.replace(u'ó', u'o')
            chaine = chaine.replace(u'ô', u'o')
            chaine = chaine.replace(u'ö', u'o')

            chaine = chaine.replace(u'ù', unhexlify('0E7C0F'))
            chaine = chaine.replace(u'ú', u'u')
            chaine = chaine.replace(u'û', u'u')
            chaine = chaine.replace(u'ü', u'u')

            chaine = chaine.replace(u'Œ', u'OE')
            chaine = chaine.replace(u'œ', u'oe')
            chaine = chaine.replace(u'ß', u'B')
            chaine = chaine.replace(u'β', u'B')

        return str(chaine)

    def couleur(self, caractere = None, fond = None):
        if caractere != None:
            couleur = self.normaliserCouleur(caractere)
            if couleur != None:
                self.envoyer([ESC, 0x40 + couleur])
        
        if fond != None:
            couleur = self.normaliserCouleur(fond)
            if couleur != None:
                self.envoyer([ESC, 0x50 + couleur])

    def position(self, colonne, ligne, relatif = False):
        assert relatif == True or relatif == False

        if not relatif:
            # Déplacement absolu
            if colonne == 1 and ligne == 1:
                self.envoyer([RS])
            else:
                self.envoyer([US, 0x40 + ligne, 0x40 + colonne])
        else:
            # Déplacement relatif par rapport à la position actuelle
            if ligne != 0:
                if ligne >= -4 and ligne <= -1:
                    self.envoyer([VT]*-ligne)
                elif ligne >= 1 and ligne <= 4:
                    self.envoyer([LF]*ligne)
                else:
                    direction = { True: 'B', False: 'A'}
                    self.envoyer([CSI, str(ligne), direction[ligne < 0]])

            if colonne != 0:
                if colonne >= -4 and colonne <= -1:
                    self.envoyer([BS]*-colonne)
                elif colonne >= 1 and colonne <= 4:
                    self.envoyer([TAB]*colonne)
                else:
                    direction = { True: 'C', False: 'D'}
                    self.envoyer([CSI, str(colonne), direction[colonne < 0]])


    def taille(self, largeur = 1, hauteur = 1):
        assert largeur == 1 or largeur == 2
        assert hauteur == 1 or hauteur == 2

        self.envoyer([ESC, 0x4c + hauteur + largeur * 2])

    def effet(self, soulignement = None, clignotement = None, inversion = None):
        assert soulignement == True or soulignement == False or soulignement == None
        assert clignotement == True or clignotement == False or clignotement == None
        assert inversion == True or inversion == False or inverison == None
    
        soulignements = {True: [ESC, 0x5a], False: [ESC, 0x59], None: None}
        self.envoyer(soulignements[soulignement])

        clignotements = {True: [ESC, 0x48], False: [ESC, 0x49], None: None}
        self.envoyer(clignotements[clignotement])

        inversions = {True: [ESC, 0x5d], False: [ESC, 0x5c], None: None}
        self.envoyer(inversions[inversion])

    def curseur(self, visible):
        assert visible == True or visible == False

        etats = {True: CON, False: COF}
        self.envoyer([etats[visible]])

    def echo(self, actif):
        assert actif == True or actif == False

        actifs = {
            True: [PRO3, AIGUILLAGE_ON, RCPT_ECRAN, EMET_MODEM],
            False: [PRO3, AIGUILLAGE_OFF, RCPT_ECRAN, EMET_MODEM]
        }
        retour = self.appeler(actifs[actif], LONGUEUR_PRO3)
        
        return len(retour) == LONGUEUR_PRO3

    def efface(self, portee = 'tout'):
        portees = {
            'tout': [FF],
            'finligne': [CAN],
            'finecran': [CSI, 0x4a],
            'debutecran': [CSI, 0x31, 0x4a],
            #'tout': [CSI, 0x32, 0x4a],
            'debutligne': [CSI, 0x31, 0x4b],
            'ligne': [CSI, 0x32, 0x4b]
        }

        assert portee in portees

        self.envoyer(portees[portee])

    def repeter(self, caractere, longueur):
        assert isinstance(longueur, int)
        assert longueur > 0 and longueur <= 40
        assert isinstance(caractere, (str, unicode, int, list))
        assert isinstance(caractere, int) or len(caractere) == 1

        self.envoyer([caractere, REP, 0x40 + longueur - 1])

    def bip(self): self.envoyer([BEL])
    def debutLigne(self): self.envoyer([CR])
    def geresupprime(self, nombre): self.envoyer([CSI, str(nombre), 'M'])
    def gereinsere(self, nombre): self.envoyer([CSI, str(nombre), 'L'])

