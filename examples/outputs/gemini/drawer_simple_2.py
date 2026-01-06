from enum import Enum, auto

class Zustand(Enum):
    """Definition der möglichen Zustände basierend auf dem PlantUML Diagramm."""
    AUF = auto()
    ZU = auto()
    VERRIEGELT = auto()

class Aktion(Enum):
    """Die möglichen Aktionen (Trigger), die Zustandsübergänge auslösen."""
    SCHLIESSEN = auto()
    VERRIEGELN = auto()
    ENTRIEGELN = auto()
    OEFFNEN = auto()

class UngueltigerUebergangError(Exception):
    """Benutzerdefinierte Exception für ungültige Zustandsübergänge."""
    pass

class TuerStateMachine:
    def __init__(self):
        # Initialzustand laut Diagramm: [*] --> Auf
        self._aktueller_zustand = Zustand.AUF
        
        # Definition der Übergangstabelle: (Startzustand, Aktion) -> Zielzustand
        self._uebergaenge = {
            (Zustand.AUF, Aktion.SCHLIESSEN): Zustand.ZU,
            (Zustand.ZU, Aktion.VERRIEGELN): Zustand.VERRIEGELT,
            (Zustand.VERRIEGELT, Aktion.ENTRIEGELN): Zustand.ZU,
            (Zustand.ZU, Aktion.OEFFNEN): Zustand.AUF
        }

    @property
    def zustand(self):
        """Gibt den aktuellen Zustand zurück."""
        return self._aktueller_zustand

    def _fuehre_aktion_aus(self, aktion: Aktion):
        """Interne Methode zur Verarbeitung des Zustandsübergangs."""
        schluessel = (self._aktueller_zustand, aktion)
        
        if schluessel in self._uebergaenge:
            neuer_zustand = self._uebergaenge[schluessel]
            print(f"Aktion: '{aktion.name}' | Übergang: {self._aktueller_zustand.name} -> {neuer_zustand.name}")
            self._aktueller_zustand = neuer_zustand
        else:
            raise UngueltigerUebergangError(
                f"Aktion '{aktion.name}' ist im Zustand '{self._aktueller_zustand.name}' nicht möglich."
            )

    # Öffentliche Methoden, die die API der State Machine darstellen
    
    def schliessen(self):
        self._fuehre_aktion_aus(Aktion.SCHLIESSEN)

    def verriegeln(self):
        self._fuehre_aktion_aus(Aktion.VERRIEGELN)

    def entriegeln(self):
        self._fuehre_aktion_aus(Aktion.ENTRIEGELN)

    def oeffnen(self):
        self._fuehre_aktion_aus(Aktion.OEFFNEN)

# --- Beispielhafte Nutzung ---

if __name__ == "__main__":
    tuer = TuerStateMachine()
    
    try:
        print(f"Startzustand: {tuer.zustand.name}")
        
        # Normaler Ablauf
        tuer.schliessen()   # Auf -> Zu
        tuer.verriegeln()   # Zu -> Verriegelt
        tuer.entriegeln()   # Verriegelt -> Zu
        tuer.oeffnen()      # Zu -> Auf
        
        print("\n--- Teste Fehlerfall ---")
        # Fehlerfall: Versuchen zu verriegeln, wenn die Tür offen ist
        tuer.verriegeln() 
        
    except UngueltigerUebergangError as e:
        print(f"FEHLER: {e}")