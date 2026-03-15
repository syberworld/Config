import json
import os
import copy
from typing import Any, Dict, Optional, TYPE_CHECKING
import threading

if TYPE_CHECKING:
    from PyQt6.QtCore import QObject


class Config:
    """Gestore di configurazione singleton thread-safe basato su file JSON.

    Implementa il pattern Singleton per garantire un'unica istanza della configurazione
    in tutta l'applicazione. Supporta chiavi annidate con notazione dot (es. "ui.theme.color").

    La classe è thread-safe grazie all'utilizzo di un lock a livello di classe durante
    la creazione dell'istanza.

    Note:
        - Il file viene caricato automaticamente al primo utilizzo
        - Il salvataggio avviene in modo automatico ad ogni modifica (set)
        - Gestisce file corrotti o vuoti resettandoli silenziosamente
        - Non emette segnali Qt (nessun QObject ereditato)

    Esempi:
        # Utilizzo base
        config = Config("settings.json")
        config["window.size"] = [1280, 720]
        print(config.get("window.size"))          # [1280, 720]
        print(config["window.size"])              # [1280, 720]

        # Utilizzo con valore di default
        theme = config.get("ui.theme", "light")

        # Verifica esistenza
        if "recent_files" in config:
            print(config["recent_files"])

        # Accesso diretto come dizionario
        config["audio.volume"] = 0.75
        volume = config["audio.volume"]
    """

    _instance = None
    _class_lock = threading.Lock()

    def __new__(cls, filename=""):
        """Crea o restituisce l'unica istanza della classe Config (Singleton).

        Args:
            filename: Percorso del file JSON di configurazione (default: "")

        Returns:
            Config: L'istanza unica della classe
        """
        with cls._class_lock:
            if cls._instance is None:
                cls._instance = super(Config, cls).__new__(cls)
                cls._instance._initialize(filename)
            return cls._instance

    def _initialize(self, filename):
        """Inizializza l'istanza singleton (chiamato una sola volta).

        Args:
            filename: Percorso del file di configurazione
        """
        self._config_path = filename
        self._data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        """Carica i dati dal file JSON.

        Gestisce i casi di:
        - file inesistente → dizionario vuoto
        - file vuoto → dizionario vuoto
        - file corrotto → reset a dizionario vuoto con warning in console
        """
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                    if content:  # Solo se non è vuoto
                        self._data = json.loads(content)
                    else:
                        self._data = {}  # File vuoto → config vuota
            except (json.JSONDecodeError, UnicodeDecodeError):
                print(f"Attenzione: {self._config_path} corrotto. File resettato")
                self._data = {}
                self._save()
        else:
            self._data = {}

    def _save(self):
        """Salva i dati correnti nel file JSON con indentazione leggibile."""
        with open(self._config_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def _get_nested(self, key: str) -> Any:
        """Recupera un valore annidato usando la notazione dot.

        Args:
            key: Chiave nella forma "sezione.sottosezione.valore"

        Returns:
            Il valore corrispondente

        Raises:
            KeyError: Se la chiave (o parte di essa) non esiste
            TypeError: Se uno dei segmenti intermedi non è un dizionario
        """
        parts = key.split(".")
        d = self._data
        for k in parts:
            d = d[k]
        return d

    def _set_nested(self, key: str, value: Any):
        """Imposta un valore in una chiave annidata creando le sezioni intermedie se necessario.

        Args:
            key: Chiave nella forma "sezione.sottosezione.valore"
            value: Valore da impostare (qualsiasi tipo serializzabile in JSON)

        Note:
            Salva automaticamente il file dopo la modifica
        """
        parts = key.split(".")
        d = self._data

        # 1. inserisci/aggiorna il valore
        for k in parts[:-1]:
            d = d.setdefault(k, {})
        d[parts[-1]] = value

        # 2. estrai il ramo a partire dalla root (es. "Prova")
        root_key = parts[0]
        if root_key not in self._data:
            self._data[root_key] = {}
        # crea {"Prova": {...}}
        root_subtree = {root_key: copy.deepcopy(self._data[root_key])}

        self._save()

    def get(self, key: str, default: Any = None) -> Any:
        """Recupera un valore dalla configurazione con possibilità di default.

        Args:
            key: Chiave da cercare (anche annidata con ".")
            default: Valore restituito se la chiave non esiste

        Returns:
            Il valore trovato oppure il default

        Esempi:
            config.get("player.volume", 1.0)
            config.get("debug.enabled", False)
        """
        try:
            return self._get_nested(key)
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Imposta un valore nella configurazione (crea sezioni se necessario).

        Args:
            key: Chiave (anche annidata con ".")
            value: Valore da salvare

        Note:
            Salva immediatamente su file

        Esempi:
            config.set("ui.scale", 1.25)
            config.set("recent_files.0", "/home/user/progetto.mp4")
        """
        self._set_nested(key, value)

    def __getitem__(self, key: str) -> Any:
        """Consente l'accesso con sintassi dizionario: config["chiave"]

        Args:
            key: Chiave da leggere

        Returns:
            Il valore corrispondente

        Raises:
            KeyError: Se la chiave non esiste
        """
        return self.get(key)

    def __setitem__(self, key: str, value: Any):
        """Consente l'assegnazione con sintassi dizionario: config["chiave"] = valore

        Args:
            key: Chiave da impostare
            value: Valore da assegnare
        """
        self.set(key, value)

    def __str__(self) -> str:
        """Rappresentazione leggibile della configurazione."""
        return str(self._data)

    def __repr__(self) -> str:
        """Rappresentazione per sviluppatori."""
        return f"Config(data={self._data!r})"
