import logging
from transitions.extensions import HierarchicalMachine

# Optional: Logging konfigurieren, um die Übergänge in der Konsole zu sehen
logging.basicConfig(level=logging.INFO, format='%(message)s')

class KaffeeMaschine(object):
    def __init__(self):
        self.wasser_stand = 0
        self._letzter_an_zustand = None # Speicher für den History State [H]

        # Definition der Zustände (States)
        # Verschachtelte Zustände werden über 'children' definiert.
        states = [
            'Aus',
            'Pause',
            {
                'name': 'An',
                'on_enter': ['_wasser_reinigen'], # Entry: wasserReinigen
                'on_exit': ['_piepen'],           # Exit: piepen (wenn man 'An' komplett verlässt)
                'children': [
                    'Leerlauf',
                    'Zubereitung',
                    'Ausgabe'
                ],
                'initial': 'Leerlauf'
            }
        ]

        # Initialisierung der State Machine
        self.machine = HierarchicalMachine(
            model=self,
            states=states,
            initial='Aus',
            ignore_invalid_triggers=True
        )

        # Definition der Übergänge (Transitions)
        # trigger = Name der Methode, die wir aufrufen (z.B. maschine.anschalten())
        self.machine.add_transition(
            trigger='anschalten', 
            source='Aus', 
            dest='An',
            after='_piepen_aus_exit' # Workaround: Da PlantUML "Aus: Exit: piepen" sagt
        )

        # An --> Pause : stop
        # Wir speichern den aktuellen Unterzustand für das History [H] Feature
        self.machine.add_transition(
            trigger='stop', 
            source='An', 
            dest='Pause', 
            before='_speichere_zustand'
        )

        # Pause --> An[H] : fortfahren
        # Wir springen zurück in den gespeicherten Zustand
        self.machine.add_transition(
            trigger='fortfahren', 
            source='Pause', 
            dest='An', # Wird durch prepare dynamisch überschrieben
            prepare='_wiederherstellen_zustand'
        )

        # Leerlauf --> Leerlauf : wasserAuffüllen
        self.machine.add_transition(
            trigger='wasser_auffuellen',
            source='An_Leerlauf',
            dest='An_Leerlauf',
            after='_wasser_tanken_logik'
        )

        # Leerlauf --> Zubereitung : kaffeeMachen [wasser > 20]
        self.machine.add_transition(
            trigger='kaffee_machen',
            source='An_Leerlauf',
            dest='An_Zubereitung',
            conditions=['ist_wasser_genug'] # Guard
        )

        # Zubereitung --> Ausgabe : zubereitungAbschließen
        self.machine.add_transition(
            trigger='zubereitung_abschliessen',
            source='An_Zubereitung',
            dest='An_Ausgabe'
        )

        # Ausgabe --> Leerlauf : kaffeeEntnehmen
        self.machine.add_transition(
            trigger='kaffee_entnehmen',
            source='An_Ausgabe',
            dest='An_Leerlauf',
            after='_kaffee_serviert'
        )

        # Exit Event für 'Aus' (Manuell, da transitions on_exit beim Verlassen feuert)
        # Wir binden es an den Übergang 'anschalten', siehe oben '_piepen_aus_exit'

    # --- Aktionen & Callbacks ---

    def _piepen(self):
        # Wird ausgeführt beim Verlassen von 'An' (siehe PlantUML: An: Exit: piepen)
        print("BEEP! (An-Modus verlassen)")

    def _piepen_aus_exit(self):
        # Wird ausgeführt beim Verlassen von 'Aus' (siehe PlantUML: Aus: Exit: piepen)
        print("BEEP! (Gerät schaltet ein)")

    def _wasser_reinigen(self):
        print("--> Spülvorgang läuft...")

    def _wasser_tanken_logik(self):
        self.wasser_stand += 50
        print(f"--> Wasser aufgefüllt. Aktueller Stand: {self.wasser_stand}ml")

    def _kaffee_serviert(self):
        print("--> Tasse entnommen. Zurück im Leerlauf.")

    # --- Guards (Bedingungen) ---

    def ist_wasser_genug(self):
        print(f"--> Prüfe Wasserstand: {self.wasser_stand}ml")
        if self.wasser_stand > 20:
            self.wasser_stand -= 20 # Wasser verbrauchen
            return True
        else:
            print("!!! Nicht genug Wasser! Bitte auffüllen.")
            return False

    # --- History State Logik [H] ---

    def _speichere_zustand(self):
        # Speichert z.B. 'An_Zubereitung'
        self._letzter_an_zustand = self.state
        print(f"(Zustand '{self._letzter_an_zustand}' gespeichert für Pause)")

    def _wiederherstellen_zustand(self):
        # Wenn wir einen gespeicherten Zustand haben, nutzen wir diesen als Ziel
        if self._letzter_an_zustand:
            # Hier greifen wir tief in die Library-Logik ein, 
            # um das Ziel der Transition dynamisch zu ändern.
            # Alternativ könnte man hier bedingte Transitionen nutzen.
            # Für die Demo überschreiben wir das Ziel nicht, sondern führen 
            # direkt ein 'to_<state>' aus nach dem Return, aber 'transitions'
            # erlaubt dynamische Ziele via Callbacks schwerer.
            # Einfachste Lösung hier:
            self.machine.get_transitions('fortfahren', 'Pause', 'An')[0].dest = self._letzter_an_zustand
            print(f"(Kehre zurück zu '{self._letzter_an_zustand}')")


# --- Testlauf ---

if __name__ == "__main__":
    k = KaffeeMaschine()
    
    print(f"Startzustand: {k.state}")
    
    # 1. Anschalten
    k.anschalten() 

    # 2. Versuch Kaffee zu machen (zu wenig Wasser)
    k.kaffee_machen()
    
    # 3. Wasser auffüllen
    k.wasser_auffuellen()
    
    # 4. Kaffee machen (Erfolg)
    k.kaffee_machen()
    
    # 5. Mitten in der Zubereitung STOP drücken (Pause testen)
    k.stop()
    
    # 6. Fortfahren (History [H] testen)
    k.fortfahren()
    
    # 7. Prozess abschließen
    k.zubereitung_abschliessen()
    
    k.kaffee_entnehmen()