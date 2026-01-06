"""
Kaffeemaschinen State Machine
Basierend auf PlantUML Spezifikation
"""

from abc import ABC, abstractmethod
from enum import Enum, auto
from typing import Optional, Callable
from dataclasses import dataclass, field


class AnSubState(Enum):
    """Unterzustände des 'An'-Zustands"""
    LEERLAUF = auto()
    ZUBEREITUNG = auto()
    AUSGABE = auto()


class MainState(Enum):
    """Hauptzustände der Kaffeemaschine"""
    AUS = auto()
    AN = auto()
    PAUSE = auto()


@dataclass
class KaffeemaschineContext:
    """Kontext-Daten der Kaffeemaschine"""
    wasser: int = 100  # Wassermenge in Prozent
    
    def hat_genug_wasser(self, mindestmenge: int = 20) -> bool:
        """Guard: Prüft ob genügend Wasser vorhanden ist"""
        return self.wasser > mindestmenge


class Aktionen:
    """Sammlung aller Aktionen/Effekte der State Machine"""
    
    @staticmethod
    def piepen():
        """Exit-Aktion: Akustisches Signal"""
        print("🔔 *PIEP*")
    
    @staticmethod
    def wasser_reinigen():
        """Entry-Aktion: Wassersystem reinigen"""
        print("💧 Wasser wird gereinigt...")
    
    @staticmethod
    def wasser_auffuellen(context: KaffeemaschineContext, menge: int = 20):
        """Wasser auffüllen"""
        context.wasser = min(100, context.wasser + menge)
        print(f"💧 Wasser aufgefüllt. Aktueller Stand: {context.wasser}%")
    
    @staticmethod
    def kaffee_zubereiten():
        """Kaffee zubereiten"""
        print("☕ Kaffee wird zubereitet...")
    
    @staticmethod
    def kaffee_ausgeben(context: KaffeemaschineContext):
        """Kaffee ausgeben (verbraucht Wasser)"""
        context.wasser = max(0, context.wasser - 25)
        print(f"☕ Kaffee wird ausgegeben. Wasser verbleibend: {context.wasser}%")


class KaffeemaschineStateMachine:
    """
    State Machine für eine Kaffeemaschine
    
    Zustände:
    - Aus: Maschine ist ausgeschaltet
    - An: Maschine ist eingeschaltet (mit Unterzuständen)
        - Leerlauf: Wartet auf Befehle
        - Zubereitung: Bereitet Kaffee zu
        - Ausgabe: Gibt Kaffee aus
    - Pause: Maschine ist pausiert (merkt sich letzten An-Unterzustand)
    """
    
    def __init__(self):
        # Aktueller Hauptzustand
        self._main_state: MainState = MainState.AUS
        
        # Aktueller Unterzustand (nur relevant wenn main_state == AN)
        self._an_sub_state: AnSubState = AnSubState.LEERLAUF
        
        # History-Zustand für Pause/Fortfahren
        self._history_sub_state: AnSubState = AnSubState.LEERLAUF
        
        # Kontext mit Daten
        self.context = KaffeemaschineContext()
        
        print("🔌 Kaffeemaschine initialisiert im Zustand: AUS")
    
    # ==================== Properties ====================
    
    @property
    def main_state(self) -> MainState:
        """Aktueller Hauptzustand"""
        return self._main_state
    
    @property
    def an_sub_state(self) -> Optional[AnSubState]:
        """Aktueller Unterzustand (nur wenn AN)"""
        if self._main_state == MainState.AN:
            return self._an_sub_state
        return None
    
    @property
    def zustand_info(self) -> str:
        """Lesbare Zustandsbeschreibung"""
        if self._main_state == MainState.AN:
            return f"{self._main_state.name} -> {self._an_sub_state.name}"
        return self._main_state.name
    
    # ==================== Zustandsübergänge ====================
    
    def _enter_an_state(self, sub_state: AnSubState):
        """Betritt den An-Zustand mit einem bestimmten Unterzustand"""
        # Entry-Aktion von An
        Aktionen.wasser_reinigen()
        
        self._main_state = MainState.AN
        self._an_sub_state = sub_state
        print(f"✅ Zustand: {self.zustand_info}")
    
    def _exit_an_state(self):
        """Verlässt den An-Zustand"""
        # History speichern
        self._history_sub_state = self._an_sub_state
        
        # Exit-Aktion von An
        Aktionen.piepen()
    
    def _exit_aus_state(self):
        """Verlässt den Aus-Zustand"""
        Aktionen.piepen()
    
    # ==================== Transitionen (Events) ====================
    
    def anschalten(self) -> bool:
        """
        Transition: Aus --> An
        Schaltet die Maschine ein
        """
        if self._main_state != MainState.AUS:
            print(f"⚠️  Kann nicht anschalten - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: anschalten")
        
        # Exit-Aktion von Aus
        self._exit_aus_state()
        
        # Entry in An-Zustand (startet in Leerlauf)
        self._enter_an_state(AnSubState.LEERLAUF)
        
        return True
    
    def ausschalten(self) -> bool:
        """
        Transition: An --> Aus (implizit, nicht im Diagramm aber sinnvoll)
        Schaltet die Maschine aus
        """
        if self._main_state != MainState.AN:
            print(f"⚠️  Kann nicht ausschalten - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: ausschalten")
        
        # Exit-Aktion von An
        self._exit_an_state()
        
        self._main_state = MainState.AUS
        print(f"✅ Zustand: {self.zustand_info}")
        
        return True
    
    def wasser_auffuellen(self, menge: int = 20) -> bool:
        """
        Transition: Leerlauf --> Leerlauf (Self-Transition)
        Füllt Wasser auf
        """
        if self._main_state != MainState.AN or self._an_sub_state != AnSubState.LEERLAUF:
            print(f"⚠️  Kann Wasser nicht auffüllen - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: wasserAuffüllen")
        Aktionen.wasser_auffuellen(self.context, menge)
        print(f"✅ Zustand: {self.zustand_info}")
        
        return True
    
    def kaffee_machen(self) -> bool:
        """
        Transition: Leerlauf --> Zubereitung [wasser > 20]
        Startet die Kaffeezubereitung (mit Guard)
        """
        if self._main_state != MainState.AN or self._an_sub_state != AnSubState.LEERLAUF:
            print(f"⚠️  Kann keinen Kaffee machen - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: kaffeeMachen")
        
        # Guard prüfen
        if not self.context.hat_genug_wasser(20):
            print(f"⚠️  Guard fehlgeschlagen: Nicht genug Wasser ({self.context.wasser}% ≤ 20%)")
            return False
        
        print(f"✓  Guard erfüllt: Wasser ({self.context.wasser}%) > 20%")
        
        Aktionen.kaffee_zubereiten()
        self._an_sub_state = AnSubState.ZUBEREITUNG
        print(f"✅ Zustand: {self.zustand_info}")
        
        return True
    
    def zubereitung_abschliessen(self) -> bool:
        """
        Transition: Zubereitung --> Ausgabe
        Schließt die Zubereitung ab
        """
        if self._main_state != MainState.AN or self._an_sub_state != AnSubState.ZUBEREITUNG:
            print(f"⚠️  Kann Zubereitung nicht abschließen - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: zubereitungAbschließen")
        
        Aktionen.kaffee_ausgeben(self.context)
        self._an_sub_state = AnSubState.AUSGABE
        print(f"✅ Zustand: {self.zustand_info}")
        
        return True
    
    def kaffee_entnehmen(self) -> bool:
        """
        Transition: Ausgabe --> Leerlauf
        Kaffee wird entnommen
        """
        if self._main_state != MainState.AN or self._an_sub_state != AnSubState.AUSGABE:
            print(f"⚠️  Kann Kaffee nicht entnehmen - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: kaffeeEntnehmen")
        print("☕ Kaffee wurde entnommen. Guten Appetit!")
        
        self._an_sub_state = AnSubState.LEERLAUF
        print(f"✅ Zustand: {self.zustand_info}")
        
        return True
    
    def stop(self) -> bool:
        """
        Transition: An --> Pause
        Pausiert die Maschine (speichert History)
        """
        if self._main_state != MainState.AN:
            print(f"⚠️  Kann nicht pausieren - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: stop")
        
        # Exit An-Zustand (speichert History)
        self._exit_an_state()
        
        self._main_state = MainState.PAUSE
        print(f"✅ Zustand: {self.zustand_info}")
        print(f"   (History gespeichert: {self._history_sub_state.name})")
        
        return True
    
    def fortfahren(self) -> bool:
        """
        Transition: Pause --> An[H]
        Setzt die Maschine fort (stellt History wieder her)
        """
        if self._main_state != MainState.PAUSE:
            print(f"⚠️  Kann nicht fortfahren - Aktueller Zustand: {self.zustand_info}")
            return False
        
        print("\n📍 Event: fortfahren")
        print(f"   (History wird wiederhergestellt: {self._history_sub_state.name})")
        
        # Entry in An-Zustand mit History-Unterzustand
        self._enter_an_state(self._history_sub_state)
        
        return True


# ==================== Demo / Test ====================

def demo():
    """Demonstriert die State Machine"""
    
    print("=" * 60)
    print("KAFFEEMASCHINEN STATE MACHINE - DEMO")
    print("=" * 60)
    
    maschine = KaffeemaschineStateMachine()
    
    # Normaler Ablauf
    print("\n" + "-" * 40)
    print("SZENARIO 1: Normaler Kaffee-Durchlauf")
    print("-" * 40)
    
    maschine.anschalten()
    maschine.wasser_auffuellen(50)
    maschine.kaffee_machen()
    maschine.zubereitung_abschliessen()
    maschine.kaffee_entnehmen()
    
    # Pause mit History
    print("\n" + "-" * 40)
    print("SZENARIO 2: Pause während Zubereitung")
    print("-" * 40)
    
    maschine.kaffee_machen()
    maschine.stop()  # Pausiert während Zubereitung
    maschine.fortfahren()  # Kehrt zu Zubereitung zurück
    maschine.zubereitung_abschliessen()
    maschine.kaffee_entnehmen()
    
    # Guard-Test: Zu wenig Wasser
    print("\n" + "-" * 40)
    print("SZENARIO 3: Guard-Test (zu wenig Wasser)")
    print("-" * 40)
    
    # Mehrere Kaffees machen bis Wasser leer
    for i in range(5):
        print(f"\n--- Versuch {i+1} ---")
        if maschine.kaffee_machen():
            maschine.zubereitung_abschliessen()
            maschine.kaffee_entnehmen()
        else:
            print("Wasser muss aufgefüllt werden!")
            maschine.wasser_auffuellen(50)
    
    # Ausschalten
    print("\n" + "-" * 40)
    print("SZENARIO 4: Ausschalten")
    print("-" * 40)
    
    maschine.ausschalten()
    
    print("\n" + "=" * 60)
    print("DEMO BEENDET")
    print("=" * 60)


if __name__ == "__main__":
    demo()