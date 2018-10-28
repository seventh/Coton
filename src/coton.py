# -*- coding: utf-8 -*-

"""Atelier de prototypage en composants.
"""

import collections
import functools
import pickle
import queue
import threading
import time


Échange = collections.namedtuple("Échange", ["producteurs", "consommateurs"])


class GrandMamamouchi:
    """Contexte d'exécution, ordonnanceur, etc.
    """

    def __init__(self):
        self._types = dict()
        self._échanges = dict()
        self._instances = dict()
        self._files = dict()
        self._tâches = dict()
        self._entrées = dict()
        self._sorties = dict()

    def ajouter(self, typ):
        """Mémorise le type comme faisant partie du système
        """
        self._types[typ.__name__] = typ
        for nom, att in typ.__dict__.items():
            if isinstance(att, recv_msg):
                self._échanges.setdefault(nom, Échange(
                    set(), set())).consommateurs.add(typ.__name__)
            elif isinstance(att, send_msg):
                self._échanges.setdefault(nom, Échange(
                    set(), set())).producteurs.add(typ.__name__)

        # Ajout des files d'entrée et de sortie
        self._files[typ.__name__] = queue.Queue()
        self._sorties[typ.__name__] = FileSortie()

    def publier(self, nom, nom_échange, valeur, instantané):
        h = time.time()
        print("{}: {} → {}".format(h, nom, nom_échange))
        self._sorties[nom].push(nom_échange, valeur, instantané)
        if instantané:
            self.transmettre(nom, nom_échange, valeur)

    def transmettre(self, nom, nom_échange, valeur):
        échange = self._échanges[nom_échange]
        valeur_codée = pickle.dumps(valeur)
        for c in échange.consommateurs:
            print("{}: {} → {}".format(nom_échange, nom, c))
            q = self._files[c]
            q.put((nom_échange, valeur_codée))
        for c in [n for n in échange.producteurs if n != nom]:
            print("{}: {} → {}".format(nom_échange, nom, c))
            q = self._files[c]
            q.put((nom_échange, valeur_codée))

    def instance(self, nom):
        return self._instances[nom]

    def run(self):
        # Création des instances
        for nom, typ in self._types.items():
            self._instances[nom] = typ()

        # Création des tâches
        for nom in self._types:
            if nom in self._entrées:
                t = threading.Thread(target=tâche_autonome, name=nom, args=(
                    nom, self._files[nom], self._entrées[nom]))
            else:
                t = threading.Thread(target=tâche, name=nom,
                                     args=(nom, self._files[nom]))
            self._tâches[nom] = t
            t.start()

        # Démarrage des tâches (envoi d'un message anodin)
        for q in self._files.values():
            q.put(None)

        # … attente infinie (par tranches de 1 seconde)
        while True:
            time.sleep(1.0)


GM = GrandMamamouchi()


class recv_msg:
    """Attribute whose value is updated by framework only
    """

    def __init__(self, doc="", default=None, *,
                 system_name=None):
        self.__doc__ = doc
        self._name = "ça_marche_pas 1"
        self._system_name = system_name
        self._default = default
        self._actions = list()

    def __get__(self, obj, objtype):
        """Preferred way to read attribute (for framework user)
        """
        return getattr(obj, self._name)

    def __set__(self, obj, value):
        """Preferred way to write attribute (for framework user)
        """
        return setattr(obj, self._name, value)

    def __set_name__(self, obj, attribute_name):
        """Allows association of attribute name with descriptor
        """
        self._name = "_" + attribute_name
        if self._system_name is None:
            self._system_name = attribute_name

    @property
    def system_name(self):
        """Identifier, within the whole system, of the exchanged data
        """
        return self._system_name

    def add_callback(self, callback):
        """Register callback method in order to execute it at attribute update
        """
        self._actions.append(callback)

    def update(self, obj, value):
        """Preferred way to write attribute value (for framework)

        Callbacks associated with the attribute are also executed, and their
        outputs transmitted
        """
        # Mise-à-jour de la valeur
        setattr(obj, self._name, value)

        # Appel des points d'entrée
        nom = type(obj).__name__
        sortie = GM._sorties[nom]
        for action in self._actions:
            action(obj)
            # Production des sorties associées
            for donnée in sortie:
                if not donnée.immediate:
                    GM.transmettre(nom, donnée.name, donnée.value)
            sortie.clear()


class send_msg:
    """Attribute whose value can be updated either by user or framework
    """

    def __init__(self, doc="", default=None, *,
                 system_name=None, immediate=False):
        """
        immediate → chaque mise-à-jour provoque l'émission immédiate de la
                     donnée
        """
        self.__doc__ = doc
        self._name = "ça_marche_pas 2"
        self._system_name = system_name
        self._default = default
        self._actions = list()
        self._immediate = immediate

    def __get__(self, obj, objtype):
        """Preferred way to read attribute (for framework user)
        """
        if obj is None:
            return self
        else:
            return getattr(obj, self._name)

    def __set__(self, obj, value):
        retour = setattr(obj, self._name, value)
        GM.publier(type(obj).__name__, self._system_name,
                   value, self._immediate)
        return retour

    def __set_name__(self, obj, attribute_name):
        """Allows association of attribute name with descriptor
        """
        self._name = "_" + attribute_name
        if self._system_name is None:
            self._system_name = attribute_name

    @property
    def system_name(self):
        """Identifier, within the whole system, of the exchanged data
        """
        return self._system_name

    @property
    def is_immediate(self):
        """If true, update of the attribute value is immediately communicated
        """
        return self._immediate

    def add_callback(self, callback):
        """Register callback method in order to execute it at attribute update
        """
        self._actions.append(callback)

    def update(self, obj, value):
        """Preferred way to write attribute value (for framework)

        Callbacks associated with the attribute are also executed, and their
        outputs transmitted
        """
        # Mise-à-jour de la valeur
        setattr(obj, self._name, value)

        # Appel des points d'entrée
        nom = type(obj).__name__
        sortie = GM._sorties[nom]
        for action in self._actions:
            action(obj)
            # Production des sorties associées
            for donnée in sortie:
                if not donnée.immediate:
                    GM.transmettre(nom, donnée.name, donnée.value)
            sortie.clear()


class entry:
    """Annotation de lien entre point d'entrée et modification de donnée

    Soit l'annotation est utilisée seule et le point d'entrée est
    inconditionnel, c'est-à-dire appelé une seule fois au démarrage, soit elle
    liste un ensemble de données reçues dont la modification provoque l'appel.

    Ainsi:

      @entry
      def toto(self):
         …

    définit un point d'entrée incondionnel, quand

      @entry(tata)
      def toto(self):
         …

    provoque l'appelle de `toto` à chaque mise-à-jour de `tata`.

    Évidemment, un Acteur ne peut pas avoir qu'au plus un point d'entrée
    inconditionnel, et seulement si c'est le seul.

    Les send_msg doivent d'ailleurs être marqués `instantané` == True.
    """

    def __init__(self, *données):
        # On doit pouvoir faire mieux. Peut-être même faudrait-il distinguer
        # les points d'entrée inconditionnels avec un marqueur spécifique ?
        if len(données) == 1 and not isinstance(données[0], (recv_msg, send_msg)):
            self.méthode = données[0]
            self.données = list()
        else:
            self.méthode = None
            self.données = données

    def __call__(self, méthode):
        # Il est inutile de copier les attributs classiques pour faire un
        # 'bon' adapteur : __doc__, etc.
        # En effet, les instances seront supprimées lors de la construction du
        # type

        if isinstance(méthode, entry):
            # On fusionne les décors successifs
            self.données.append(méthode.données)
            self.méthode = méthode.méthode
        else:
            self.méthode = méthode
        return self


def décorateur_init(i, champs):
    """Fonction d'initialisation amendée de l'ajout d'attributs
    """
    @functools.wraps(i)
    def init(self, *args, **kwargs):
        i(self, *args, **kwargs)
        for k, v in champs.items():
            try:
                getattr(self, k)
                print("Conflit d'attribut sur {}.{}".format(
                    self.__class__.__name__, k))
            except AttributeError:
                setattr(self, k, v)
    return init


class MétaActeur(type):
    """Lien entre le code utilisateur et le GrandMamamouchi
    """

    def __new__(metacls, nom, bases, attribs):
        champs = dict()

        # Suppression des décorateurs 'entry', tout en conservant les
        # informations qu'ils portent. On en profite de vérifier si l'acteur
        # est un générateur.
        a_entry = False
        est_générateur = False
        for k in attribs:
            v = attribs[k]
            if isinstance(v, entry):
                if len(v.données) == 0:
                    if a_entry:
                        print(
                            "ERREUR : l'Acteur {!r} a plus d'un point d'entrée"
                            " inconditionnel".format(nom))
                    else:
                        est_générateur = True
                        GM._entrées[nom] = v.méthode
                elif est_générateur:
                    print("ERREUR : l'Acteur {!r} ne peut à la fois avoir des"
                          " points d'entrée conditionnels et"
                          " inconditionnels".format(nom))

                # On shunte le décorateur
                attribs[k] = v.méthode

                # On câble l'activation de la méthode dans les descripteurs
                for msg in attribs.values():
                    if msg in v.données:
                        msg.add_callback(v.méthode)

                a_entry = True
        if not a_entry:
            print("AVERTISSEMENT : l'Acteur {!r} n'a aucun point"
                  "d'entrée".format(nom))

        # Pour chaque attribut de classe 'send_msg/recv_msg', on ajoute un
        # attribut d'instance qui permetttra de stocker la valeur
        for k, v in attribs.items():
            if isinstance(v, (recv_msg, send_msg)):
                nom_attribut = "_" + k
                champs[nom_attribut] = v._default

        # L'initialisation des attributs d'instance est faite en même temps
        # que l'instance, avec les valeurs par défaut prévues, via une
        # surcharge de la fonction d'initialisation

        # Surcharge de la fonction d'initialisation
        intérim = super().__new__(metacls, nom, bases, attribs)
        i = intérim.__init__
        attribs["__init__"] = décorateur_init(i, champs)

        # On crée le type final
        retour = super().__new__(metacls, nom, bases, attribs)

        # On l'enregistre auprès du Grand Mamamouchi
        GM.ajouter(retour)

        return retour


DonnéeSystème = collections.namedtuple(
    "DonnéeSystème", ["name", "value", "immediate"])


class FileSortie:
    """File de production d'un point d'entrée
    """

    def __init__(self):
        self._file = list()
        self._indexes = dict()

    def clear(self):
        self._file.clear()
        self._indexes.clear()

    def push(self, nom, valeur, immédiat):
        entrée = DonnéeSystème(nom, valeur, immédiat)
        if not immédiat:
            if nom in self._indexes:
                del self._file[self._indexes[nom]]
            self._indexes[nom] = len(self._file)
        self._file.append(entrée)

    def __iter__(self):
        yield from self._file

    def __len__(self):
        return len(self._file)

    def __getitem__(self, index):
        return self._file[index]


def tâche(nom_instance, queue):
    instance = GM.instance(nom_instance)

    # Attente du point de synchronisation du démarrage
    queue.get()

    # Boucle active
    while True:
        nom_système, valeur_codée = queue.get()

        # Conversion du nom système en nom local
        for nom_attr, attr in type(instance).__dict__.items():
            if (isinstance(attr, (recv_msg, send_msg)) and
                    attr._system_name == nom_système):
                nom = nom_attr
                break
        else:
            print("Erreur : pas de tel échange ({}.{})".format(
                nom_instance, nom_système))
            nom = nom_système

        # Stockage de la donnée, et appel des points d'activations liés
        valeur = pickle.loads(valeur_codée)
        attr.update(instance, valeur)


def tâche_autonome(nom_instance, queue, entrée):
    instance = GM.instance(nom_instance)
    sortie = GM._sorties[nom_instance]

    # Attente du point de synchronisation du démarrage
    queue.get()

    # Ajout de la première auto-activation
    queue.put((None, None))

    # Appel de l'unique point d'activation, en boucle
    while True:
        nom, valeur_codée = queue.get()
        if nom is None and valeur_codée is None:
            # Appel du seul point d'activation
            entrée(instance)

            # Production des sorties associées
            for donnée in sortie:
                if not donnée.immediate:
                    GM.transmettre(nom_instance, donnée.name, donnée.value)
            sortie.clear()

            # Empilement dès la sortie de la prochaine auto-activation
            queue.put((None, None))
        else:
            # Stockage de la donnée
            valeur = pickle.loads(valeur_codée)
            attr = type(instance).__dict__[nom]
            attr.update(instance, valeur)


def run():
    GM.run()


def publier(obj, attr):
    """Si l'utilisateur souhaite déclarer lui-même la publication
    """
    GM.publier(obj.__class__.__name__,
               attr._system_name,
               getattr(obj, attr._system_name),
               attr._immediate)


def sortie(obj):
    """Permet d'obtenir la file de sortie d'un objet donné, à des fins de test
    unitaire
    """
    return GM._sorties[obj.__class__.__name__]
