import abc

# -------------------------------------------------------------------------
# 1. Basis-Klassen & State Machine Engine
# -------------------------------------------------------------------------

class State(abc.ABC):
    """Basisklasse für alle Zustände."""
    name = "State"
    parent = None  # Für hierarchische Zustände

    def on_entry(self, context):
        """Wird beim Betreten des Zustands ausgeführt."""
        pass

    def on_exit(self, context):
        """Wird beim Verlassen des Zustands ausgeführt."""
        pass

    def handle_event(self, context, event: str):
        """
        Verarbeitet Events. Gibt den Ziel-Zustand (Klasse) zurück,
        wenn eine Transition ausgelöst wird, sonst None.
        Kann auch ein Tupel (StateClass, use_history: bool) zurückgeben.
        """
        return None

class StateMachineContext:
    """
    Der Context hält die Daten, die aktuelle Zustandsinstanz und
    führt die Aktionen aus (Host der Logik).
    """
    def __init__(self):
        # Technische Verwaltung
        self._current_state_instance = None
        self._history = {}  # Speichert {CompositeStateClass: LastSubStateClass}
        
        # Geschäftsdaten (aus Diagramm-Anforderungen)
        self.wasser = 0

        # Initiale Transition: [*] --> Aus
        self._transition_to(Aus)

    @property
    def current_state_name(self):
        return self._current_state_instance.name if self._current_state_instance else "None"

    def process_event(self, event: str):
        print(f"\n[Event: {event}]")
        
        # Event Bubbling: Suche Handler von unten (Leaf) nach oben (Root)
        handler_state = self._current_state_instance
        target = None
        
        while handler_state:
            result = handler_state.handle_event(self, event)
            if result:
                target = result
                break
            # Gehe eine Ebene höher in der Hierarchie
            if handler_state.parent:
                # Wir instanziieren den Parent hier temporär nur zum Lookup, 
                # in einer optimierten Engine wären Klassenreferenzen besser.
                # Hier nutzen wir die Klasse direkt via parent.
                handler_state = handler_state.parent() 
            else:
                handler_state = None

        if target:
            use_history = False
            if isinstance(target, tuple):
                target_cls, use_history = target
            else:
                target_cls = target
                
            self._execute_transition(target_cls, use_history)
        else:
            print(f"  -> Event '{event}' ignoriert in Zustand {self.current_state_name}.")

    def _execute_transition(self, target_cls, use_history=False):
        """
        Führt die Transition durch: LCA-Berechnung, Exits, Action, Entries.
        """
        # 1. Zielauflösung (History Logik)
        final_target = target_cls
        
        # Wenn History angefordert ist und wir eine History haben, stelle wieder her
        if use_history and target_cls in self._history:
            final_target = self._history[target_cls]
            print(f"  (History wiederhergestellt: {final_target.name})")
        # Wenn wir in einen Composite State springen (ohne History oder keine vorhanden),
        # müssen wir dessen Initial State finden.
        elif hasattr(final_target, 'initial_state') and final_target.initial_state:
             # Rekursiv Initial States auflösen, falls verschachtelt
             temp = final_target
             while hasattr(temp, 'initial_state') and temp.initial_state:
                 temp = temp.initial_state
             final_target = temp

        # 2. Pfad-Berechnung (Lowest Common Ancestor)
        source_cls = self._current_state_instance.__class__
        
        # Abstammungslinien (Lineage) erstellen: [Leaf, Parent, Grandparent...]
        source_lineage = self._get_lineage(source_cls)
        target_lineage = self._get_lineage(final_target)
        
        # Finde LCA (erster gemeinsamer Vorfahre)
        lca = None
        for s in source_lineage:
            if s in target_lineage:
                lca = s
                break
        
        # 3. History speichern (Bevor wir Exits ausführen)
        # Wir prüfen alle States, die wir verlassen, ob sie Composite sind
        idx_lca_source = source_lineage.index(lca) if lca else len(source_lineage)
        states_to_exit = source_lineage[:idx_lca_source] # Von Leaf bis exklusive LCA
        
        # Wenn wir z.B. Leerlauf verlassen und An auch verlassen (weil LCA Root ist),
        # müssen wir für 'An' speichern, dass 'Leerlauf' aktiv war.
        for i, state_cls in enumerate(states_to_exit):
            if state_cls.parent:
                self._history[state_cls.parent] = state_cls

        # 4. Exit Aktionen ausführen (Von Leaf hoch bis LCA)
        # Wir nutzen die aktuelle Instanz für den Leaf, für Parents erstellen wir temp Instanzen
        # oder nutzen Klassenmethoden, wenn actions statisch wären. 
        # Hier pattern-konform: Wir simulieren den Stack.
        
        # Aktuellen State exiten
        self._current_state_instance.on_exit(self)
        
        # Parents exiten bis LCA
        # Hinweis: Der _current_state_instance ist nur der Leaf. 
        # Logisch sind wir aber auch in den Parents.
        # Im PlantUML Modell feuern Exits von innen nach außen.
        # Da wir im Code keine Instanzen für Parents halten, instanziieren wir sie on-the-fly 
        # oder rufen Logik auf. Hier: Instanziierung für sauberen Methodenaufruf.
        
        # states_to_exit[0] ist der aktuelle Leaf (schon erledigt). 
        for parent_cls in states_to_exit[1:]:
            parent_inst = parent_cls()
            parent_inst.on_exit(self)

        # 5. Transition Aktionen (nicht Teil von Entry/Exit, sondern am Pfeil)
        # In diesem vereinfachten Modell sind Pfeil-Aktionen (wie wasserAuffüllen) 
        # direkt im handle_event vor dem return ausgeführt worden oder hier.
        # Da wir saubere Trennung wollen, wurden sie im Handler ausgeführt.
        
        # 6. Entry Aktionen ausführen (Von unterhalb LCA runter bis Leaf)
        idx_lca_target = target_lineage.index(lca) if lca else len(target_lineage)
        states_to_enter = target_lineage[:idx_lca_target][::-1] # Umkehren: Von oben nach unten

        for state_cls in states_to_enter:
            st = state_cls()
            st.on_entry(self)
            # Update Current State Instance (Am Ende ist es der Leaf)
            self._current_state_instance = st
            
    def _transition_to(self, initial_state_cls):
        """Hilfsmethode für den allerersten Start (ohne Exit Logik)."""
        self._current_state_instance = initial_state_cls()
        # Bei Initialisierung: Eventuell Kette von Entries nötig?
        # Im Diagramm: [*] --> Aus. Einfach Aus betreten.
        self._current_state_instance.on_entry(self)

    def _get_lineage(self, state_cls):
        """Gibt Liste der Klassen zurück: [State, Parent, Grandparent...]"""
        chain = []
        current = state_cls
        while current:
            chain.append(current)
            current = current.parent
        return chain

    # --- Actions (Methoden, die in PlantUML definiert sind) ---
    
    def piepen(self):
        print("  [Action] piepen")

    def wasserReinigen(self):
        print("  [Action] wasserReinigen")

    def wasserAuffüllenAction(self):
        # Umbenannt um Konflikt mit Event-Name zu vermeiden, rein kosmetisch
        print("  [Action] wasserAuffüllen (Wasserstand erhöhen)")
        self.wasser = 30 # Setze auf Wert > 20 für Guard Test

    def kaffeeZubereiten(self):
        print("  [Logic] Kaffee wird zubereitet...")


# -------------------------------------------------------------------------
# 2. Zustands-Implementierungen (PlantUML Mapping)
# -------------------------------------------------------------------------

# --- Composite State: An (Deklaration für Referenzen) ---
class An(State):
    name = "An"
    parent = None
    # Initial state wird später gesetzt, da Leerlauf noch nicht definiert ist
    initial_state = None 

    def on_entry(self, context):
        # An: Entry: wasserReinigen
        context.wasserReinigen()

    def on_exit(self, context):
        # An: Exit: piepen
        context.piepen()

    def handle_event(self, context, event):
        # An --> Pause : stop
        if event == "stop":
            return Pause
        return super().handle_event(context, event)


# --- Einfacher Zustand: Aus ---
class Aus(State):
    name = "Aus"
    parent = None

    def on_exit(self, context):
        # Aus: Exit: piepen
        context.piepen()

    def handle_event(self, context, event):
        # Aus --> An : anschalten
        if event == "anschalten":
            return An
        return super().handle_event(context, event)


# --- Einfacher Zustand: Pause ---
class Pause(State):
    name = "Pause"
    parent = None

    def handle_event(self, context, event):
        # Pause --> An[H] : fortfahren
        if event == "fortfahren":
            # Rückgabe Tupel (Ziel, History=True)
            return (An, True)
        return super().handle_event(context, event)


# --- Sub-Zustände von An ---

class Leerlauf(State):
    name = "Leerlauf"
    parent = An

    def handle_event(self, context, event):
        # Leerlauf --> Leerlauf : wasserAuffüllen
        if event == "wasserAuffüllen":
            context.wasserAuffüllenAction()
            return Leerlauf # Self-Transition (führt Exit/Entry aus)
        
        # Leerlauf --> Zubereitung : kaffeeMachen [wasser > 20]
        if event == "kaffeeMachen":
            if context.wasser > 20: # Guard
                return Zubereitung
            else:
                print(f"  [Guard Failed] wasser ({context.wasser}) <= 20")
                return None
        
        return super().handle_event(context, event)


class Zubereitung(State):
    name = "Zubereitung"
    parent = An

    def on_entry(self, context):
        context.kaffeeZubereiten()

    def handle_event(self, context, event):
        # Zubereitung --> Ausgabe : zubereitungAbschließen
        if event == "zubereitungAbschließen":
            return Ausgabe
        return super().handle_event(context, event)


class Ausgabe(State):
    name = "Ausgabe"
    parent = An

    def handle_event(self, context, event):
        # Ausgabe --> Leerlauf : kaffeeEntnehmen
        if event == "kaffeeEntnehmen":
            return Leerlauf
        return super().handle_event(context, event)

# Verknüpfung des Initial State für Composite 'An'
An.initial_state = Leerlauf


# -------------------------------------------------------------------------
# 3. Demonstration / Test
# -------------------------------------------------------------------------

def run_demo():
    sm = StateMachineContext()
    print(f"Startzustand: {sm.current_state_name}")

    # 1. Anschalten -> Aus -> An (Entry Reinigen) -> Leerlauf
    sm.process_event("anschalten")

    # 2. Versuch Kaffee zu machen (Guard fail: Wasser 0)
    sm.process_event("kaffeeMachen")

    # 3. Wasser auffüllen (Self Transition Leerlauf)
    sm.process_event("wasserAuffüllen")

    # 4. Kaffee machen (Guard pass: Wasser 30) -> Zubereitung
    sm.process_event("kaffeeMachen")

    # 5. Stop drücken während Zubereitung -> Pause
    #    (Hier greift History Logik: Wir sind in Zubereitung, An speichert Zubereitung)
    #    Exit Zubereitung -> Exit An (piepen) -> Pause
    sm.process_event("stop")

    # 6. Fortfahren -> An[H]
    #    Exit Pause -> Entry An (Reinigen) -> Entry Zubereitung (History restored)
    sm.process_event("fortfahren")

    # 7. Abschluss -> Ausgabe
    sm.process_event("zubereitungAbschließen")

    # 8. Entnahme -> Leerlauf
    sm.process_event("kaffeeEntnehmen")

    # 9. Ausschalten via stop (Bubbling von Leerlauf zu An) -> Pause
    #    (Anmerkung: Das Diagramm definiert stop nur von An->Pause, nicht zurück zu Aus. 
    #    Daher geht es hier in die Pause, nicht Aus.)
    sm.process_event("stop")

if __name__ == "__main__":
    run_demo()