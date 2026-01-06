import abc

class KaffeeMaschine:
    """
    Die Kontext-Klasse. Sie hält den aktuellen Zustand und die Daten (Wasserstand).
    """
    def __init__(self):
        self._state = Aus(self)  # Initialzustand
        self.wasser = 0
        self._history_state_cls = None # Speicher für History [H]
        print(f"\n[INIT] Maschine gestartet im Zustand: {self._state}")

    def change_state(self, new_state):
        """Wechselt den Zustand und führt Entry/Exit Aktionen aus."""
        old_state = self._state
        
        # 1. Exit-Aktionen des alten Zustands ausführen
        # Hier prüfen wir Hierarchien (Superstate 'An')
        self._handle_exit_actions(old_state, new_state)

        # 2. Zustand wechseln
        self._state = new_state
        print(f"[TRANSITION] {old_state} -> {new_state}")

        # 3. Entry-Aktionen des neuen Zustands ausführen
        self._handle_entry_actions(old_state, new_state)

    def _handle_exit_actions(self, old_state, new_state):
        # Spezifischer Exit für 'Aus' (laut Diagramm)
        if isinstance(old_state, Aus):
            print("  [ACTION] Aus Exit: piepen")

        # Logik für Superstate 'An':
        # Wenn wir einen 'An'-Unterzustand verlassen und NICHT in einen anderen 'An'-Unterzustand gehen.
        if isinstance(old_state, BaseAnState) and not isinstance(new_state, BaseAnState):
            print("  [ACTION] An Exit: piepen")

    def _handle_entry_actions(self, old_state, new_state):
        # Logik für Superstate 'An':
        # Wenn wir in einen 'An'-Unterzustand eintreten und vorher NICHT in einem waren.
        if not isinstance(old_state, BaseAnState) and isinstance(new_state, BaseAnState):
            print("  [ACTION] An Entry: wasserReinigen")

    def save_history(self, state_class):
        self._history_state_cls = state_class

    def get_history_state(self):
        return self._history_state_cls

    # --- Trigger / Events ---
    # Diese Methoden delegieren an den aktuellen Zustand
    def anschalten(self): self._state.anschalten()
    def stop(self): self._state.stop()
    def fortfahren(self): self._state.fortfahren()
    def wasser_auffuellen(self): self._state.wasser_auffuellen()
    def kaffee_machen(self): self._state.kaffee_machen()
    def zubereitung_abschliessen(self): self._state.zubereitung_abschliessen()
    def kaffee_entnehmen(self): self._state.kaffee_entnehmen()


class State(abc.ABC):
    """Abstrakte Basisklasse für alle Zustände."""
    def __init__(self, machine):
        self.machine = machine

    def __str__(self):
        return self.__class__.__name__

    # Standard-Implementierung: Event wird im aktuellen Zustand ignoriert
    def anschalten(self): print(f"  (Ignoriert: 'anschalten' in {self})")
    def stop(self): print(f"  (Ignoriert: 'stop' in {self})")
    def fortfahren(self): print(f"  (Ignoriert: 'fortfahren' in {self})")
    def wasser_auffuellen(self): print(f"  (Ignoriert: 'wasser_auffuellen' in {self})")
    def kaffee_machen(self): print(f"  (Ignoriert: 'kaffee_machen' in {self})")
    def zubereitung_abschliessen(self): print(f"  (Ignoriert: 'zubereitung_abschliessen' in {self})")
    def kaffee_entnehmen(self): print(f"  (Ignoriert: 'kaffee_entnehmen' in {self})")


class Aus(State):
    def anschalten(self):
        # Aus --> An (Initialzustand von An ist Leerlauf)
        self.machine.change_state(Leerlauf(self.machine))


class BaseAnState(State):
    """
    Hilfsklasse für den Composite State 'An'.
    Alle Zustände innerhalb von 'An' erben hiervon.
    Dadurch können wir den Übergang 'stop' zentral definieren.
    """
    def stop(self):
        # An --> Pause
        # History [H]: Wir merken uns, welche Klasse wir gerade sind
        self.machine.save_history(self.__class__)
        self.machine.change_state(Pause(self.machine))


class Leerlauf(BaseAnState):
    def wasser_auffuellen(self):
        # Leerlauf --> Leerlauf (Interne Transition / Self-Transition)
        self.machine.wasser += 10
        print(f"  [ACTION] Wasser aufgefüllt. Aktuell: {self.machine.wasser}")

    def kaffee_machen(self):
        # Guard Condition: [wasser > 20]
        if self.machine.wasser > 20:
            self.machine.change_state(Zubereitung(self.machine))
        else:
            print(f"  [GUARD FAIL] Nicht genug Wasser ({self.machine.wasser} <= 20).")


class Zubereitung(BaseAnState):
    def zubereitung_abschliessen(self):
        # Konsumiere Wasser
        self.machine.wasser -= 20
        self.machine.change_state(Ausgabe(self.machine))


class Ausgabe(BaseAnState):
    def kaffee_entnehmen(self):
        self.machine.change_state(Leerlauf(self.machine))


class Pause(State):
    def fortfahren(self):
        # Pause --> An[H]
        hist_cls = self.machine.get_history_state()
        if hist_cls:
            # Stelle den letzten Zustand wieder her
            self.machine.change_state(hist_cls(self.machine))
        else:
            # Fallback, falls keine History da ist (sollte laut Diagramm nicht passieren)
            self.machine.change_state(Leerlauf(self.machine))


# ==========================================
# Beispielhafter Ablauf (Test)
# ==========================================
if __name__ == "__main__":
    sm = KaffeeMaschine()

    # 1. Anschalten -> Geht in Leerlauf (Entry An: Reinigen wird getriggert)
    sm.anschalten()

    # 2. Versuch Kaffee zu machen (zu wenig Wasser)
    sm.kaffee_machen()

    # 3. Wasser auffüllen
    sm.wasser_auffuellen() # 10
    sm.wasser_auffuellen() # 20
    sm.wasser_auffuellen() # 30

    # 4. Mitten im Prozess Pause drücken
    sm.stop() # Exit An: Piepen wird getriggert

    # 5. Fortfahren -> Sollte wieder in Leerlauf landen (wegen History)
    sm.fortfahren() # Entry An: Reinigen wird getriggert

    # 6. Kaffee machen (jetzt genug Wasser) -> Zubereitung
    sm.kaffee_machen()

    # 7. Mitten in der Zubereitung Pause drücken
    sm.stop()

    # 8. Fortfahren -> Sollte direkt wieder in Zubereitung landen [History]
    sm.fortfahren()

    # 9. Zubereitung fertig -> Ausgabe
    sm.zubereitung_abschliessen()

    # 10. Entnehmen -> Zurück zu Leerlauf
    sm.kaffee_entnehmen()