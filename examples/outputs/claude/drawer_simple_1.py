from enum import Enum, auto
from typing import Callable


class Zustand(Enum):
    """Mögliche Zustände der Tür."""
    AUF = auto()
    ZU = auto()
    VERRIEGELT = auto()


class UngueltigerUebergangError(Exception):
    """Wird ausgelöst bei ungültigem Zustandsübergang."""
    pass


class TuerStateMachine:
    """
    State Machine für eine Tür.
    
    Zustände:
        - AUF: Tür ist offen
        - ZU: Tür ist geschlossen (aber nicht verriegelt)
        - VERRIEGELT: Tür ist geschlossen und verriegelt
    
    Übergänge:
        - schließen:   AUF → ZU
        - öffnen:      ZU → AUF
        - verriegeln:  ZU → VERRIEGELT
        - entriegeln:  VERRIEGELT → ZU
    """
    
    # Übergangs-Tabelle: {(aktueller_zustand, aktion): neuer_zustand}
    _UEBERGAENGE: dict[tuple[Zustand, str], Zustand] = {
        (Zustand.AUF, "schließen"): Zustand.ZU,
        (Zustand.ZU, "öffnen"): Zustand.AUF,
        (Zustand.ZU, "verriegeln"): Zustand.VERRIEGELT,
        (Zustand.VERRIEGELT, "entriegeln"): Zustand.ZU,
    }
    
    def __init__(self) -> None:
        """Initialisiert die State Machine im Startzustand AUF."""
        self._zustand: Zustand = Zustand.AUF
        self._observer: list[Callable[[Zustand, str, Zustand], None]] = []
    
    @property
    def zustand(self) -> Zustand:
        """Gibt den aktuellen Zustand zurück."""
        return self._zustand
    
    @property
    def ist_offen(self) -> bool:
        """Prüft, ob die Tür offen ist."""
        return self._zustand == Zustand.AUF
    
    @property
    def ist_verriegelt(self) -> bool:
        """Prüft, ob die Tür verriegelt ist."""
        return self._zustand == Zustand.VERRIEGELT
    
    def add_observer(self, callback: Callable[[Zustand, str, Zustand], None]) -> None:
        """Fügt einen Observer hinzu, der bei Zustandsänderungen benachrichtigt wird."""
        self._observer.append(callback)
    
    def _fuehre_uebergang_aus(self, aktion: str) -> None:
        """
        Führt einen Zustandsübergang durch.
        
        Args:
            aktion: Name der auszuführenden Aktion
            
        Raises:
            UngueltigerUebergangError: Wenn der Übergang nicht erlaubt ist
        """
        schluessel = (self._zustand, aktion)
        
        if schluessel not in self._UEBERGAENGE:
            raise UngueltigerUebergangError(
                f"Aktion '{aktion}' nicht möglich im Zustand '{self._zustand.name}'"
            )
        
        alter_zustand = self._zustand
        self._zustand = self._UEBERGAENGE[schluessel]
        
        # Observer benachrichtigen
        for observer in self._observer:
            observer(alter_zustand, aktion, self._zustand)
    
    def kann_ausfuehren(self, aktion: str) -> bool:
        """Prüft, ob eine Aktion im aktuellen Zustand ausgeführt werden kann."""
        return (self._zustand, aktion) in self._UEBERGAENGE
    
    # === Öffentliche Aktionen ===
    
    def schliessen(self) -> None:
        """Schließt die Tür (AUF → ZU)."""
        self._fuehre_uebergang_aus("schließen")
    
    def oeffnen(self) -> None:
        """Öffnet die Tür (ZU → AUF)."""
        self._fuehre_uebergang_aus("öffnen")
    
    def verriegeln(self) -> None:
        """Verriegelt die Tür (ZU → VERRIEGELT)."""
        self._fuehre_uebergang_aus("verriegeln")
    
    def entriegeln(self) -> None:
        """Entriegelt die Tür (VERRIEGELT → ZU)."""
        self._fuehre_uebergang_aus("entriegeln")
    
    def __repr__(self) -> str:
        return f"TuerStateMachine(zustand={self._zustand.name})"


# === Beispielverwendung ===

if __name__ == "__main__":
    
    # Observer-Funktion für Logging
    def log_uebergang(alt: Zustand, aktion: str, neu: Zustand) -> None:
        print(f"  [{alt.name}] --{aktion}--> [{neu.name}]")
    
    # State Machine erstellen
    tuer = TuerStateMachine()
    tuer.add_observer(log_uebergang)
    
    print(f"Startzustand: {tuer.zustand.name}\n")
    
    # Gültiger Ablauf durchspielen
    print("Gültiger Ablauf:")
    tuer.schliessen()      # AUF → ZU
    tuer.verriegeln()      # ZU → VERRIEGELT
    tuer.entriegeln()      # VERRIEGELT → ZU
    tuer.oeffnen()         # ZU → AUF
    
    print(f"\nEndzustand: {tuer.zustand.name}")
    
    # Ungültigen Übergang testen
    print("\nUngültiger Übergang testen:")
    try:
        tuer.verriegeln()  # Nicht möglich im Zustand AUF
    except UngueltigerUebergangError as e:
        print(f"  Fehler: {e}")
    
    # Prüfen, ob Aktion möglich ist
    print(f"\nKann 'schließen' ausführen? {tuer.kann_ausfuehren('schließen')}")
    print(f"Kann 'verriegeln' ausführen? {tuer.kann_ausfuehren('verriegeln')}")