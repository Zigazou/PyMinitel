#!/usr/bin/env python
# -*- coding: utf-8 -*-

from serial import Serial      # Liaison physique avec le Minitel
from threading import Thread   # Threads pour l’émission/réception
from Queue import Queue, Empty # Files de caractères pour l’émission/réception

from binascii import unhexlify # Pour créer des chaînes binaires depuis une
                               # chaîne hexa

from constantes import *       # Constantes en rapport avec le Minitel
from Sequence import Sequence  # Gestion des séquences de caractères

class Minitel:
    """Une classe de pilotage du Minitel via un port série

    La classe Minitel permet d’envoyer et de recevoir des séquences de
    caractères vers et depuis un Minitel dans un programme écrit en Python.
    Elle fonctionne via une liaison série entre l’ordinateur et le Minitel.

    Par défaut, elle utilise /dev/ttyUSB0 comme périphérique. En effet, l’une
    des manières les plus simples de relier un Minitel à un ordinateur
    consiste à utiliser un câble USB-TTL 5v (PL2303) car la prise
    péri-informatique du Minitel fonctionne en TTL (0v/5v) et non en RS232
    (-12v/12v). Ce type de câble embarque un composant qui est reconnu
    automatiquement par les noyaux Linux et est assigné à /dev/ttyUSB*.

    Tant que le périphérique sélectionné est un périphérique série, cette
    classe ne devrait pas poser de problème pour communiquer avec le Minitel.
    Par exemple, il est tout à fait possible de créer un proxy série en
    utilisant un Arduino relié en USB à l’ordinateur et dont certaines
    broches seraient relié au Minitel.

    La classe Minitel permet de déterminer la vitesse de fonctionnement du
    Minitel, d’identifier le modèle, de le configurer et d’envoyer et recevoir
    des séquences de caractères.

    Compte tenu de son fonctionnement en threads, le programme principal
    utilisant cette classe n’a pas à se soucier d’être disponible pour recevoir
    les séquences de caractères envoyées par le Minitel.
    """
    def __init__(self, peripherique = '/dev/ttyUSB0'):
        """Constructeur de Minitel

        Arguments:
        peripherique -- une chaîne de caractères identifiant un périphérique.
                        Par défaut, le périphérique est /dev/ttyUSB0

        Note:
        La connexion série est établie selon le standard de base du Minitel.
        À l’allumage le Minitel est configuré à 1200 bps, 7 bits, parité paire,
        mode Vidéotex.

        Cela peut ne pas correspondre à la configuration réelle du Minitel au
        moment de l’exécution. Cela n’est toutefois pas un problème car la
        connexion série peut être reconfigurée à tout moment.
        """
        assert isinstance(peripherique, str)

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
            baudrate = 1200, # vitesse à 1200 bps, le standard Minitel
            bytesize = 7,    # taille de caractère à 7 bits
            parity   = 'E',  # parité paire
            stopbits = 1,    # 1 bit d’arrêt
            timeout  = 1,    # 1 bit de timeout
            xonxoff  = 0,    # pas de contrôle logiciel
            rtscts   = 0     # pas de contrôle matériel
        )

        # Initialise un drapeau pour l’arrêt des threads
        # (les threads partagent les mêmes variables que le code principal)
        self._continuer = True

        # Crée les deux threads de lecture/écriture
        self._threads = []
        self._threads.append(Thread(None, self._gestionEntree, None, ()))
        self._threads.append(Thread(None, self._gestionSortie, None, ()))

        # Démarre les deux threads de lecture/écriture
        for t in self._threads:
            # Configure chaque thread en mode daemon
            t.setDaemon(True)
            try:
                # Lance le thread
                t.start()
            except (KeyboardInterrupt, SystemExit):
                self.close()

    def close(self):
        """Ferme la connexion avec le Minitel

        Indique aux threads d’émission/réception qu’ils doivent s’arrêter et
        attend leur arrêt. Comme les timeouts d’émission et de réception sont
        réglés à 1 seconde, c’est le temps moyen que cette méthode mettra pour
        s’exécuter.
        """
        # Indique aux threads qu’ils doivent arrêter toute activité
        self._continuer = False

        # Attend que tous les threads aient fini
        for t in self._threads: t.join()

        self._minitel.close()

    def _gestionEntree(self):
        """Gestion des séquences de caractères envoyées depuis le Minitel

        Cette méthode ne doit pas être appelée directement, elle est réservée
        exclusivement à la classe Minitel. Elle boucle indéfiniment en tentant
        de lire un caractère sur la connexion série.
        """
        # Ajoute à la file entree tout ce que le Minitel peut envoyer
        while self._continuer:
            # Attend un caractère pendant 1 seconde
            caractere = self._minitel.read()

            if len(caractere) == 1: self.entree.put(caractere)

    def _gestionSortie(self):
        """Gestion des séquences de caractères envoyées vers le Minitel

        Cette méthode ne doit pas être appelée directement, elle est réservée
        exclusivement à la classe Minitel. Elle boucle indéfiniment en tentant
        de lire un caractère sur la file de sortie.
        """
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
        """Envoi de séquence de caractères 

        Envoie une séquence de caractère en direction du Minitel.

        Arguments:
        contenu -- Une séquence de caractères interprétable par la classe
                   Sequence.
        """
        if not isinstance(contenu, Sequence): contenu = Sequence(contenu)

        # Ajoute les caractères un par un dans la file d’attente d’envoi
        for valeur in contenu.valeurs:
            self.sortie.put(chr(valeur))

    def recevoir(self, bloque = False, attente = None):
        """Lit un caractère en provenance du Minitel

        Retourne un caractère présent dans la file d’attente de réception.

        Arguments:
        bloque -- True pour attendre un caractère s’il n’y en a pas dans la
                  file d’attente de réception. False pour ne pas attendre et
                  retourner immédiatement.
        attente -- attente en secondes, valeurs en dessous de la seconde
                   acceptées. Valide uniquement en mode bloque = True
        """
        assert bloque in [True, False]
        assert isinstance(attente, float) or attente == None

        return self.entree.get(bloque, attente)

    def recevoirSequence(self):
        sequence = Sequence()
        sequence.ajoute(self.recevoir(bloque = True))

        if sequence.valeurs[-1] in [SS2, SEP]:
            sequence.ajoute(self.recevoir(bloque = True))
        elif sequence.valeurs[-1] == ESC:
            try:
                sequence.ajoute(self.recevoir(bloque = True, attente = 0.1))

                if sequence.valeurs == CSI:
                    sequence.ajoute(self.recevoir(bloque = True))
                    if sequence.valeurs[-1] in [0x32, 0x34]:
                        sequence.ajoute(self.recevoir(bloque = True))
            except Empty:
                pass

        return sequence

    def appeler(self, contenu, attente):
        self.entree = Queue()
        self.envoyer(contenu)
        self.sortie.join()

        retour = Sequence()
        for i in range(0, attente):
            try:
                retour.ajoute(self.entree.get(block = True, timeout = 1))
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
            resultat = retour.egale([SEP, 0x5e])
        elif self.mode == 'TELEINFORMATIQUE' and mode == 'MIXTE':
            retour = self.appeler([CSI, 0x3f, 0x7b], 2)
            resultat = retour.egale([SEP, 0x5e])
            if not resultat: return False
            retour = self.appeler([PRO2, MIXTE1], 2)
            resultat = retour.egale([SEP, 0x70])
        elif self.mode == 'VIDEOTEX' and mode == 'MIXTE':
            retour = self.appeler([PRO2, MIXTE1], 2)
            resultat = retour.egale([SEP, 0x70])
        elif self.mode == 'VIDEOTEX' and mode == 'TELEINFORMATIQUE':
            retour = self.appeler([PRO2, TELINFO], 4)
            resultat = retour.egale([CSI, 0x3f, 0x7a])
        elif self.mode == 'MIXTE' and mode == 'VIDEOTEX':
            retour = self.appeler([PRO2, MIXTE2], 2)
            resultat = retour.egale([SEP, 0x71])
        elif self.mode == 'MIXTE' and mode == 'TELEINFORMATIQUE':
            retour = self.appeler([PRO2, TELINFO], 4)
            resultat = retour.egale([CSI, 0x3f, 0x7a])

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
        if retour.longueur != 5: return
        if retour.valeurs[0] != SOH: return
        if retour.valeurs[4] != EOT: return

        # Extrait les caractères d’identification
        constructeurMinitel = chr(retour.valeurs[1])
        typeMinitel         = chr(retour.valeurs[2])
        versionLogiciel     = chr(retour.valeurs[3])
        identifiant         = constructeurMinitel + typeMinitel + versionLogiciel

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

        if retour.longueur != LONGUEUR_PRO2:
            # Le Minitel est en mode Téléinformatique car il ne répond pas
            # à une commande protocole
            self.mode = 'TELEINFORMATIQUE'
        elif retour.valeurs[3] & 1 == 1:
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
            if retour.longueur == LONGUEUR_PRO2:
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
        if retour.longueur == LONGUEUR_PRO2:
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
            if retour.longueur != longueur: return False

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

        self.envoyer([ESC, 0x4c + (hauteur - 1) + (largeur - 1) * 2])

    def effet(self, soulignement = None, clignotement = None, inversion = None):
        assert soulignement in [True, False, None]
        assert clignotement in [True, False, None]
        assert inversion in [True, False, None]
    
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
        
        return retour.longueur == LONGUEUR_PRO3

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

    def semigraphique(self, actif = True):
        assert actif == True or actif == False

        actifs = { True: SO, False: SI}
        self.envoyer(actifs[actif])

    def redefinir(self, depuis, dessins, jeu = 'G0'):
        assert jeu == 'G0' or jeu == 'G1'
        assert isinstance(depuis, str) and len(depuis) == 1
        assert isinstance(dessins, str)

        # Deux jeux sont disponible G’0 et G’1
        if jeu == 'G0':
            self.envoyer([US, 0x23, 0x20, 0x20, 0x20, 0x42, 0x49])
        else:
            self.envoyer([US, 0x23, 0x20, 0x20, 0x20, 0x43, 0x49])

        # On indique à partir de quel caractère on veut rédéfinir les dessins
        self.envoyer([US, 0x23, depuis, 0x30])

        octet = ''
        comptePixel = 0
        for pixel in dessins:
            # Seuls les caractères 0 et 1 sont interprétés, les autres sont
            # ignorés. Cela permet de présenter les dessins dans le code
            # source de façon plus lisible
            if pixel != '0' and pixel != '1': continue
            octet = octet + pixel
            comptePixel += 1

            # On regroupe les pixels du caractères par paquets de 6
            # car on ne peut envoyer que 6 bits à la fois
            if len(octet) == 6:
                self.envoyer(0x40 + int(octet, 2))
                octet = ''

            # Quand 80 pixels (8 colonnes × 10 lignes) ont été envoyés
            # on ajoute 4 bits à zéro car l’envoi se fait par paquet de 6 bits
            # (8×10 = 80 pixels, 14×6 = 84 bits, 84-80 = 4)
            if comptePixel == 80:
                self.envoyer(0x40 + int(octet + '0000', 2))
                self.envoyer(0x30)
                octet = ''
                comptePixel = 0

        # Positionner le curseur permet de sortir du mode de définition
        self.envoyer([US, 0x41, 0x41])

        # Sélectionne le jeu de caractère fraîchement modifié (G’0 ou G’1)
        if jeu == 'GO':
            self.envoyer([ESC, 0x28, 0x20, 0x42])
        else:
            self.envoyer([ESC, 0x29, 0x20, 0x43])

