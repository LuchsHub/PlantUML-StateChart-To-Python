from enum import Enum, auto

class Zustand(Enum):
    """
    Repräsentiert die Zustände aus dem PlantUML Diagramm.
    """
    AUF = auto()
    ZU = auto()
    VERRIEGELT = auto()

    def __str__(self):
        return self.name

class UngueltigerUebergangError(Exception):
    """Wird geworfen, wenn eine Aktion im aktuellen Zustand nicht erlaubt ist."""
    pass

class TuerSteuerung:
    def __init__(self):
        # [*] --> Auf (Initialer Zustand)
        self._aktueller_zustand = Zustand.AUF
        
        # Definition der Übergänge: 
        # { Aktueller_Zustand: { 'aktion': Neuer_Zustand } }
        self._uebergaenge = {
            Zustand.AUF: {
                'schließen': Zustand.ZU
            },
            Zustand.ZU: {
                'verriegeln': Zustand.VERRIEGELT,
                'öffnen': Zustand.AUF
            },
            Zustand.VERRIEGELT: {
                'entriegeln': Zustand.ZU
            }
        }

    @property
    def zustand(self):
        """Gibt den aktuellen Zustand zurück."""
        return self._aktueller_zustand

    def _fuehre_aktion_aus(self, aktions_name: str):
        """
        Interne Methode, um den Zustandsübergang zu prüfen und durchzuführen.
        """
        moegliche_aktionen = self._uebergaenge.get(self._aktueller_zustand, {})
        
        if aktions_name in moegliche_aktionen:
            neuer_zustand = moegliche_aktionen[aktions_name]
            print(f"Übergang: {self._aktueller_zustand} --({aktions_name})--> {neuer_zustand}")
            self._aktueller_zustand = neuer_zustand
        else:
            raise UngueltigerUebergangError(
                f"Aktion '{aktions_name}' ist im Zustand '{self._aktueller_zustand}' nicht möglich."
            )

    # Öffentliche Methoden (API), die den Aktionen im Diagramm entsprechen
    
    def schliessen(self):
        self._fuehre_aktion_aus('schließen')

    def verriegeln(self):
        self._fuehre_aktion_aus('verriegeln')

    def entriegeln(self):
        self._fuehre_aktion_aus('entriegeln')

    def oeffnen(self):
        self._fuehre_aktion_aus('öffnen')

# --- Beispielhafte Nutzung ---

if __name__ == "__main__":
    tuer = TuerSteuerung()
    print(f"Startzustand: {tuer.zustand}")

    try:
        # Glücklicher Pfad (Happy Path)
        tuer.schliessen()   # Auf -> Zu
        tuer.verriegeln()   # Zu -> Verriegelt
        tuer.entriegeln()   # Verriegelt -> Zu
        tuer.oeffnen()      # Zu -> Auf
        
        print("\nVersuche ungültigen Übergang:")
        # Fehlerhafter Pfad: Tür ist Auf, wir versuchen direkt zu verriegeln
        tuer.verriegeln() 

    except UngueltigerUebergangError as e:
        print(f"FEHLER: {e}")