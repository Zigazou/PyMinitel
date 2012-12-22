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
    automatiquement par les noyaux Linux et est assigné à /dev/ttyUSB*. Sous
    Android, le noyau Linux ne dispose pas du pilote en standard.

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
                   Sequence (un objet Sequence, une chaîne de caractères ou
                   unicode, une liste, un entier).
        """
        # Convertit toute entrée en objet Sequence
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
        """Lit une séquence en provenance du Minitel

        Retourne un objet Sequence reçu depuis le Minitel. Cette fonction
        analyse les envois du Minitel pour en faire une séquence consistante
        du point de vue du Minitel. Par exemple, si le Minitel envoie un
        caractère SS2, SEP ou ESC, celui-ci ne fait qu’annoncer une suite de
        caractères désignant un résultat ou un caractère non existant dans la
        norme ASCII. Par contre, le nombre de caractères pouvant être reçus
        après des caractères spéciaux est normalisé. Cela permet de savoir
        exactement le nombre de caractères qui vont constituer la séquence.

        C’est cette méthode qui doit être utilisée plutôt que la méthode
        recevoir lorsqu’on dialogue avec le Minitel.
        """
        # Crée une séquence
        sequence = Sequence()

        # Ajoute le premier caractère lu à la séquence en mode bloquant
        sequence.ajoute(self.recevoir(bloque = True))
        assert sequence.longueur != 0

        # Teste le caractère reçu
        if sequence.valeurs[-1] in [SS2, SEP]:
            # Une séquence commençant par SS2 ou SEP aura une longueur de 2
            sequence.ajoute(self.recevoir(bloque = True))
        elif sequence.valeurs[-1] == ESC:
            # Les séquences ESC ont des tailles variables allant de 1 à 4
            try:
                # Essaie de lire un caractère avec un temps d’attente de 1/10s
                # Cela permet de lire la touche la touche Esc qui envoie
                # uniquement le code ESC sans rien après.
                sequence.ajoute(self.recevoir(bloque = True, attente = 0.1))

                # Une séquence CSI commence par ESC, 0x5b
                if sequence.valeurs == CSI:
                    # Une séquence CSI appelle au moins 1 caractère
                    sequence.ajoute(self.recevoir(bloque = True))

                    if sequence.valeurs[-1] in [0x32, 0x34]:
                        # La séquence ESC, 0x5b, 0x32/0x34 appelle un dernier
                        # caractère
                        sequence.ajoute(self.recevoir(bloque = True))
            except Empty:
                # Si aucun caractère n’est survenu après 1/10s, on continue
                pass

        return sequence

    def appeler(self, contenu, attente):
        """Envoie une séquence au Minitel et attend sa réponse.

        Cette méthode permet d’envoyer une commande au Minitel (configuration,
        interrogation d’état) et d’attendre sa réponse. Cette fonction attend
        au maximum 1 seconde avant d’abandonner. Dans ce cas, une séquence
        vide est retournée.

        Avant de lancer la commande, la méthode vide la file d’attente en
        réception.

        Arguments:
        contenu -- Une séquence de caractères interprétable par la classe
                   Sequence (un objet Sequence, une chaîne de caractères ou
                   unicode, une liste, un entier).
        attente -- Nombre de caractères attendu de la part du Minitel en
                   réponse à notre envoi.
        """
        assert isinstance(attente, int)

        # Vide la file d’attente en réception
        self.entree = Queue()

        # Envoie la séquence
        self.envoyer(contenu)

        # Attend que toute la séquence ait été envoyée
        self.sortie.join()

        # Tente de recevoir le nombre de caractères indiqué par le paramètre
        # attente avec un délai d’1 seconde.
        retour = Sequence()
        for i in range(0, attente):
            try:
                # Attend un caractère
                retour.ajoute(self.entree.get(block = True, timeout = 1))
            except Empty:
                # Si un caractère n’a pas été envoyé en moins d’une seconde,
                # on abandonne
                break

        return retour

    def definirMode(self, mode = 'VIDEOTEX'):
        """Définit le mode de fonctionnement du Minitel.

        Le Minitel peut fonctionner selon 3 modes : VideoTex (le mode standard
        du Minitel, celui lors de l’allumage), Mixte ou TéléInformatique (un
        mode 80 colonnes).

        La méthode definirMode prend en compte le mode courant du Minitel pour
        émettre la bonne commande.

        Si le changement de mode n’a pu avoir lieu, la méthode retourne False,
        sinon True.

        Arguments:
        mode -- Une chaîne de caractère pouvant prendre 3 valeurs : VIDEOTEX,
                MIXTE ou TELEINFORMATIQUE (la casse est importante).
        """
        assert isinstance(mode, str)

        # 3 modes sont possibles
        if mode not in ['VIDEOTEX', 'MIXTE', 'TELEINFORMATIQUE']: return False

        # Si le mode demandé est déjà actif, ne fait rien
        if self.mode == mode: return True

        resultat = False

        # Il y a 9 cas possibles, mais seulement 6 sont pertinents. Les cas
        # demandant de passer de VIDEOTEX à VIDEOTEX, par exemple, ne donnent
        # lieu à aucune transaction avec le Minitel
        if self.mode == 'TELEINFORMATIQUE' and mode == 'VIDEOTEX':
            retour = self.appeler([CSI, 0x3f, 0x7b], 2)
            resultat = retour.egale([SEP, 0x5e])
        elif self.mode == 'TELEINFORMATIQUE' and mode == 'MIXTE':
            # Il n’existe pas de commande permettant de passer directement du
            # mode TéléInformatique au mode Mixte. On effectue donc la
            # transition en deux étapes en passant par le mode Videotex
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

        # Si le changement a eu lieu, on garde le nouveau mode en mémoire
        if resultat: self.mode = mode

        return resultat

    def identifier(self):
        """Identifie le Minitel connecté.

        Cette méthode doit être appelée une fois la connexion établie avec le
        Minitel afin de déterminer les fonctionnalités et caractéristiques
        disponibles.

        Aucune valeur n’est retournée. À la place, l’attribut capacite de
        l’objet contient un dictionnaire de valeurs renseignant sur les
        capacités du Minite :
        capacite['nom'] -- Nom du Minitel (ex. Minitel 2)
        capacite['retournable'] -- Le Minitel peut-il être retourné et servir
                                   de modem ? (True ou False)
        capacite['clavier'] -- Clavier (None, ABCD ou Azerty)
        capacite['vitesse'] -- Vitesse maxi en bps (1200, 4800 ou 9600)
        capacite['constructeur'] -- Nom du constructeur (ex. Philips)
        capacite['80colonnes'] -- Le Minitel peut-il afficher 80 colonnes ?
                                  (True ou False)
        capacite['caracteres'] -- Peut-on redéfinir des caractères ? (True ou
                                  False)
        capacite['version'] -- Version du logiciel (une lettre)
        """
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

    def devinerVitesse(self):
        """Deviner la vitesse de connexion avec le Minitel.

        Cette méthode doit être appelée juste après la création de l’objet
        afin de déterminer automatiquement la vitesse de transmission sur
        laquelle le Minitel est réglé.

        Pour effectuer la détection, la méthode devinerVitesse va tester les
        vitesses 9600 bps, 4800 bps, 1200 bps et 300 bps (dans cet ordre) et
        envoyer à chaque fois une commande PRO1 de demande de statut terminal.
        Si le Minitel répond par un acquittement PRO2, on a détecté la vitesse.

        En cas de détection, la vitesse est enregistré dans l’attribut vitesse
        de l’objet.

        La méthode retourne la vitesse en bits par seconde ou -1 si elle n’a
        pas pu être déterminée.
        """
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

        # La vitesse n’a pas été trouvée
        return -1

    def definirVitesse(self, vitesse):
        """Programme le Minitel et le port série pour une vitesse donnée.

        Pour changer la vitesse de communication entre l’ordinateur et le
        Minitel, le développeur doit d’abord s’assurer que la connexion avec
        le Minitel a été établie à la bonne vitesse (voir la méthode
        devinerVitesse).

        Cette méthode ne doit être appelée qu’après que le Minitel ait été
        identifié (voir la méthode identifier) car elle se base sur les
        capacités détectées du Minitel.

        La méthode envoie d’abord une commande de réglage de vitesse au Minitel
        et, si celui-ci l’accepte, configure le port série à la nouvelle
        vitesse.

        Arguments:
        vitesse -- Entier indiquant la vitesse en bits par seconde. Les valeurs
                   acceptées sont 300, 1200, 4800 et 9600. La valeur 9600 n’est
                   autorisée qu’à partir du Minitel 2
        """
        assert isinstance(vitesse, int)

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
        """Configure le fonctionnement du clavier.

        Configure le fonctionnement du clavier du Minitel. Cela impacte les
        codes et caractères que le Minitel peut envoyer à l’ordinateur en
        fonction des touches appuyées (touches alphabétiques, touches de
        fonction, combinaisons de touches etc.).

        La méthode renvoie True si toutes les commandes de configuration ont
        correctement été traitées par le Minitel. Dès qu’une commande échoue,
        la méthode arrête immédiatement et retourne False.

        Arguments:
        etendu -- Booléen indiquant si le clavier fonctionne en mode étendu
                  (True) ou en mode normal (False)
        curseur -- Booléen indiquant si les touches du curseur doivent être
                   gérées (True) ou pas (False)
        minuscule -- Booléen indiquant si l’appui sur une touche alphabétique
                     sans appui simultané sur la touche Maj/Shift génère une
                     minuscule (True) ou une majuscule (False)
        """
        assert etendu in [True, False]
        assert curseur in [True, False]
        assert minuscule in [True, False]

        # Les commandes clavier fonctionnent sur un principe de bascule
        # start/stop
        bascules = { True: START, False: STOP }

        # Crée les séquences des 3 appels en fonction des arguments
        appels = [
            ([PRO3, bascules[etendu   ], RCPT_CLAVIER, ETEN], LONGUEUR_PRO3),
            ([PRO3, bascules[curseur  ], RCPT_CLAVIER, C0  ], LONGUEUR_PRO3),
            ([PRO2, bascules[minuscule], MINUSCULES        ], LONGUEUR_PRO2)
        ]

        # Envoie les commandes une par une
        for appel in appels:
            commande = appel[0] # Premier élément du tuple = commande
            longueur = appel[1] # Second élément du tuple = longueur réponse

            retour = self.appeler(commande, longueur)

            if retour.longueur != longueur: return False

        return True

    def normaliserCouleur(self, couleur):
        """Retourne le numéro de couleur du Minitel.

        À partir d’une couleur fournie sous la forme d’une chaîne avec le
        nom de la couleur en français ou un entier indiquant un niveau de
        gris, cette méthode retourne le numéro de la couleur correspondante
        pour le Minitel.

        Si la couleur n’est pas valide, la méthode retourne None.

        Arguments:
        couleur -- Chaîne de caractères ou entier indiquant la couleur. Les
                   valeurs acceptées sont noir, rouge, vert, jaune, bleu,
                   magenta, cyan, blanc, et les entiers de 0 (noir) à 7 (blanc)
        """
        assert isinstance(couleur, (str, int))

        # Les niveaux de gris s’échelonnent comme suit :
        # nor, bleu, rouge, magenta, vert, cyan, jaune, blanc
        couleurs = {
            'noir': 0, 'rouge': 1, 'vert': 2, 'jaune': 3,
            'bleu': 4, 'magenta': 5, 'cyan': 6, 'blanc': 7,
            '0': 0, '1': 4, '2': 1, '3': 5,
            '4': 2, '5': 6, '6': 3, '7': 7
        }

        # On convertit la couleur en chaîne de caractères pour que l’appelant
        # puisse utiliser indifféremment '0' (str) ou 0 (int).
        if couleur in couleurs: return couleurs[str(couleur)]

        return None

    def couleur(self, caractere = None, fond = None):
        """Définit les couleurs utilisées pour les prochains caractères.

        Les couleurs possibles sont noir, rouge, vert, jaune, bleu, magenta,
        cyan, blanc et un niveau de gris de 0 à 7.        

        Note:
        En Videotex, la couleur de fond ne s’applique qu’aux délimiteurs. Ces
        délimiteurs sont l’espace et les caractères semi-graphiques. Définir
        la couleur de fond et afficher immédiatement après un caractère autre
        qu’un délimiteur (une lettre par exemple) n’aura aucun effet.

        Si une couleur est positionnée à None, la méthode n’émet aucune
        commande en direction du Minitel.

        Si une couleur n’est pas valide, elle est simplement ignorée.

        Arguments:
        caractere -- Chaîne de caractères ou entier indiquant la couleur.
        fond -- Chaîne de caractères ou entier indiquant la couleur.
        """
        assert isinstance(caractere, (str, int)) or caractere == None
        assert isinstance(fond, (str, int)) or fond == None

        # Définit la couleur d’avant-plan (la couleur du caractère)
        if caractere != None:
            couleur = self.normaliserCouleur(caractere)
            if couleur != None:
                self.envoyer([ESC, 0x40 + couleur])

        # Définit la couleur d’arrière-plan (la couleur de fond)
        if fond != None:
            couleur = self.normaliserCouleur(fond)
            if couleur != None:
                self.envoyer([ESC, 0x50 + couleur])

    def position(self, colonne, ligne, relatif = False):
        """Définit la position du curseur du Minitel

        Note:
        Cette méthode optimise le déplacement du curseur, il est donc important
        de se poser la question sur le mode de positionnement (relatif vs
        absolu) car le nombre de caractères générés peut aller de 1 à 5.

        Sur le Minitel, la première colonne a la valeur 1. La première ligne
        a également la valeur 1 bien que la ligne 0 existe. Cette dernière
        correspond à la ligne d’état et possède un fonctionnement différent
        des autres lignes.

        Arguments:
        colonne -- Entier indiquant la colonne
        ligne -- Entier indiquant la ligne
        relatif -- Booléen indiquant si les coordonnées fournies sont relatives
                   (True) par rapport à la position actuelle du curseur ou si
                   elles sont absolues (False, valeur par défaut)
        """
        assert isinstance(colonne, int)
        assert isinstance(ligne, int)
        assert relatif in [True, False]

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
                    # Déplacement court en haut
                    self.envoyer([VT]*-ligne)
                elif ligne >= 1 and ligne <= 4:
                    # Déplacement court en bas
                    self.envoyer([LF]*ligne)
                else:
                    # Déplacement long en haut ou en bas
                    direction = { True: 'B', False: 'A'}
                    self.envoyer([CSI, str(ligne), direction[ligne < 0]])

            if colonne != 0:
                if colonne >= -4 and colonne <= -1:
                    # Déplacement court à gauche
                    self.envoyer([BS]*-colonne)
                elif colonne >= 1 and colonne <= 4:
                    # Déplacement court à droite
                    self.envoyer([TAB]*colonne)
                else:
                    # Déplacement long à gauche ou à droite
                    direction = { True: 'C', False: 'D'}
                    self.envoyer([CSI, str(colonne), direction[colonne < 0]])

    def taille(self, largeur = 1, hauteur = 1):
        """Définit la taille des prochains caractères

        Le Minitel est capable d’agrandir les caractères. Quatres tailles sont
        disponibles :
        - largeur = 1, hauteur = 1: taille normale
        - largeur = 2, hauteur = 1: caractères deux fois plus larges
        - largeur = 1, hauteur = 2: caractères deux fois plus hauts
        - largeur = 2, hauteur = 2: caractères deux fois plus hauts et larges

        Note:
        Cette commande ne fonctionne qu’en mode Videotex.

        Le positionnement avec des caractères deux fois plus hauts se fait par
        rapport au bas du caractère.

        Arguments:
        largeur -- Entier indiquant le coefficient multiplicateur de largeur
        hauteur -- Entier indiquant le coefficient multiplicateur de hauteur
        """
        assert largeur in [1, 2]
        assert hauteur in [1, 2]

        self.envoyer([ESC, 0x4c + (hauteur - 1) + (largeur - 1) * 2])

    def effet(self, soulignement = None, clignotement = None, inversion = None):
        """Active ou désactive des effets

        Le Minitel dispose de 3 effets sur les caractères : soulignement,
        clignotement et inversion vidéo.

        Arguments:
        soulignement -- Booléen indiquant s’il faut activer le soulignement
                        (True) ou le désactiver (False)
        clignotement -- Booléen indiquant s’il faut activer le clignotement
                        (True) ou le désactiver (False)
        inversion -- Booléen indiquant s’il faut activer l’inverson vidéo
                     (True) ou la désactiver (False)
        """
        assert soulignement in [True, False, None]
        assert clignotement in [True, False, None]
        assert inversion in [True, False, None]

        # Gère le soulignement
        soulignements = {True: [ESC, 0x5a], False: [ESC, 0x59], None: None}
        self.envoyer(soulignements[soulignement])

        # Gère le clignotement
        clignotements = {True: [ESC, 0x48], False: [ESC, 0x49], None: None}
        self.envoyer(clignotements[clignotement])

        # Gère l’inversion vidéo
        inversions = {True: [ESC, 0x5d], False: [ESC, 0x5c], None: None}
        self.envoyer(inversions[inversion])

    def curseur(self, visible):
        """Active ou désactive l’affichage du curseur

        Le Minitel peut afficher un curseur clignotant à la position
        d’affichage des prochains caractères.

        Il est intéressant de la désactiver quand l’ordinateur doit envoyer
        de longues séquences de caractères car le Minitel va chercher à
        afficher le curseur pour chaque caractère affiché, générant un effet
        peu agréable.

        Arguments:
        visible -- Booléen indiquant s’il faut activer le curseur (True) ou le
                   rendre invisible (False)
        """
        assert visible in [True, False]

        etats = {True: CON, False: COF}
        self.envoyer([etats[visible]])

    def echo(self, actif):
        """Active ou désactive l’écho clavier

        Par défaut, le Minitel envoie tout caractère tapé au clavier à la fois
        à l’écran et sur la prise péri-informatique. Cette astuce évite à
        l’ordinateur de dévoir renvoyer à l’écran le dernière caractère tapé,
        économisant ainsi de la bande passante.

        Dans le cas où l’ordinateur propose une interface utilisateur plus
        poussée, il est important de pouvoir contrôler exactement ce qui est
        affiché par le Minitel.

        La méthode retourne True si la commande a bien été traitée par le
        Minitel, False sinon.

        Arguments:
        actif -- Booléen indiquant s’il faut activer l’écho (True) ou le
                 désactiver (False)
        """
        assert actif in [True, False]

        actifs = {
            True: [PRO3, AIGUILLAGE_ON, RCPT_ECRAN, EMET_MODEM],
            False: [PRO3, AIGUILLAGE_OFF, RCPT_ECRAN, EMET_MODEM]
        }
        retour = self.appeler(actifs[actif], LONGUEUR_PRO3)
        
        return retour.longueur == LONGUEUR_PRO3

    def efface(self, portee = 'tout'):
        """Efface tout ou partie de l’écran

        Cette méthode permet d’effacer :
        - tout l’écran ('tout'),
        - du curseur jusqu’à la fin de la ligne ('finligne'),
        - du curseur jusqu’au bas de l’écran ('finecran'),
        - du début de l’écran jusqu’au curseur ('debutecran'),
        - du début de la ligne jusqu’au curseur ('debutligne'),
        - la ligne entière ('ligne').

        Arguments:
        portee -- Chaîne de caractères indiquant la portée de l’effacement. Les
                  valeurs possibles sont tout, finligne, finecran, debutecran,
                  debutligne et ligne
        """
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
        """Répéter un caractère

        Arguments:
        caractere -- Caractère à répéter
        longueur -- Entier donnant le nombre de fois où le caractère est répété
        """
        assert isinstance(longueur, int)
        assert longueur > 0 and longueur <= 40
        assert isinstance(caractere, (str, unicode, int, list))
        assert isinstance(caractere, int) or len(caractere) == 1

        self.envoyer([caractere, REP, 0x40 + longueur - 1])

    def bip(self):
        """Émet un bip

        Demande au Minitel d’émettre un bip
        """
        self.envoyer([BEL])

    def debutLigne(self):
        """Retour en début de ligne

        Positionne le curseur au début de la ligne courante.
        """
        self.envoyer([CR])

    def supprime(self, nombre):
        """Supprime des caractères après le curseur

        En supprimant des caractères après le curseur, le Minitel ramène
        les derniers caractères contenus sur la ligne.
        """
        self.envoyer([CSI, str(nombre), 'M'])

    def insere(self, nombre):
        """Insère des caractères après le curseur

        En insérant des caractères après le curseur, le Minitel pousse les
        derniers caractères contenus sur la ligne à droite.
        """
        self.envoyer([CSI, str(nombre), 'L'])

    def semigraphique(self, actif = True):
        """Passe en mode semi-graphique ou en mode alphabétique
        """
        assert actif in [True, False]

        actifs = { True: SO, False: SI}
        self.envoyer(actifs[actif])

    def redefinir(self, depuis, dessins, jeu = 'G0'):
        """Redéfinit des caractères du Minitel

        À partir du Minitel 2, il est possible de redéfinir des caractères.
        Chaque caractère est dessiné à partir d’une matrice 8×10 pixels.

        Note:
        Les dessins des caractères sont données par une suite de 0 et de 1 dans
        une chaîne de caractères. Tout autre caractère est purement et
        simplement ignoré. Cette particularité permet de dessiner les
        caractères depuis un éditeur de texte standard et d’ajouter des
        commentaires.
        
        Ex::
        11111111
        10000001
        10000001
        10000001
        10000001 Ceci est un rectangle !
        10000001
        10000001
        10000001
        10000001
        11111111

        Le Minitel n’insère aucun pixel de séparation entre les caractères,
        il faut donc prendre cela en compte et les inclure dans vos dessins.

        Arguments:
        depuis -- Caractère à partir duquel redéfinir
        dessins -- Chaîne de caractères représentant les dessins des caractères
                   à redéfinir
        jeu -- Chaîne de caractères désignant la palette de caractères à
               modifier (G0 ou G1)
        """
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

