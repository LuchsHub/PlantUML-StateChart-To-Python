from enum import Enum, auto
from typing import Callable


class Zustand(Enum):
    """Mögliche Zustände der Tür."""
    AUF = auto()
    ZU = auto()
    VERRIEGELT = auto()


class UngueltigerUebergangError(Exception):
    """Exception für ungültige Zustandsübergänge."""
    pass


class Tuer:
    """
    State Machine für eine Tür.
    
    Zustandsdiagramm:
    ┌─────────────────────────────────────────────┐
    │  [*] --> Auf                                │
    │   Auf ──schließen──> Zu                     │
    │   Zu  ──öffnen────-> Auf                    │
    │   Zu  ──verriegeln─> Verriegelt             │
    │   Verriegelt ──entriegeln──> Zu             │
    └─────────────────────────────────────────────┘
    """
    
    # Definition aller gültigen Übergänge: (Aktion, VonZustand) -> NachZustand
    _UEBERGAENGE: dict[tuple[str, Zustand], Zustand] = {
        ("schliessen", Zustand.AUF): Zustand.ZU,
        ("oeffnen", Zustand.ZU): Zustand.AUF,
        ("verriegeln", Zustand.ZU): Zustand.VERRIEGELT,
        ("entriegeln", Zustand.VERRIEGELT): Zustand.ZU,
    }
    
    def __init__(self) -> None:
        """Initialisiert die Tür im Zustand 'Auf'."""
        self._zustand = Zustand.AUF
        self._on_zustandswechsel: Callable[[Zustand, Zustand], None] | None = None
    
    @property
    def zustand(self) -> Zustand:
        """Gibt den aktuellen Zustand zurück."""
        return self._zustand
    
    @property
    def ist_offen(self) -> bool:
        return self._zustand == Zustand.AUF
    
    @property
    def ist_verriegelt(self) -> bool:
        return self._zustand == Zustand.VERRIEGELT
    
    def set_zustandswechsel_callback(
        self, 
        callback: Callable[[Zustand, Zustand], None]
    ) -> None:
        """Registriert einen Callback für Zustandswechsel."""
        self._on_zustandswechsel = callback
    
    def _fuehre_uebergang_aus(self, aktion: str) -> None:
        """
        Führt einen Zustandsübergang aus.
        
        Args:
            aktion: Name der auszuführenden Aktion
            
        Raises:
            UngueltigerUebergangError: Wenn der Übergang nicht erlaubt ist
        """
        schluessel = (aktion, self._zustand)
        
        if schluessel not in self._UEBERGAENGE:
            raise UngueltigerUebergangError(
                f"Aktion '{aktion}' ist im Zustand '{self._zustand.name}' "
                f"nicht erlaubt."
            )
        
        alter_zustand = self._zustand
        self._zustand = self._UEBERGAENGE[schluessel]
        
        # Callback ausführen, falls registriert
        if self._on_zustandswechsel:
            self._on_zustandswechsel(alter_zustand, self._zustand)
    
    # === Öffentliche Aktionen ===
    
    def schliessen(self) -> None:
        """Schließt die Tür (Auf -> Zu)."""
        self._fuehre_uebergang_aus("schliessen")
    
    def oeffnen(self) -> None:
        """Öffnet die Tür (Zu -> Auf)."""
        self._fuehre_uebergang_aus("oeffnen")
    
    def verriegeln(self) -> None:
        """Verriegelt die Tür (Zu -> Verriegelt)."""
        self._fuehre_uebergang_aus("verriegeln")
    
    def entriegeln(self) -> None:
        """Entriegelt die Tür (Verriegelt -> Zu)."""
        self._fuehre_uebergang_aus("entriegeln")
    
    def __repr__(self) -> str:
        return f"Tuer(zustand={self._zustand.name})"


### Beispielverwendung ###

def log_zustandswechsel(von: Zustand, nach: Zustand) -> None:
    """Callback zum Loggen von Zustandswechseln."""
    print(f"  📝 Zustand: {von.name} -> {nach.name}")


def main():
    # Tür erstellen
    tuer = Tuer()
    tuer.set_zustandswechsel_callback(log_zustandswechsel)
    
    print(f"Startzustand: {tuer}")
    print()
    
    # Gültige Übergänge durchführen
    aktionen = [
        ("schliessen", tuer.schliessen),
        ("verriegeln", tuer.verriegeln),
        ("entriegeln", tuer.entriegeln),
        ("oeffnen", tuer.oeffnen),
    ]
    
    for name, aktion in aktionen:
        print(f"Aktion: {name}()")
        aktion()
    
    print(f"\nEndzustand: {tuer}")
    print()
    
    # Ungültigen Übergang testen
    print("Test: Verriegeln einer offenen Tür...")
    try:
        tuer.verriegeln()  # Sollte fehlschlagen
    except UngueltigerUebergangError as e:
        print(f"  ❌ Fehler: {e}")


if __name__ == "__main__":
    main()