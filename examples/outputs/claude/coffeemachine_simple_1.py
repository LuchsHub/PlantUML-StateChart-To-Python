"""
Kaffeemaschine State Machine
Basierend auf PlantUML-Spezifikation

Zustände:
- Aus (Hauptzustand)
- An (Composite-Zustand mit Unterzuständen: Leerlauf, Zubereitung, Ausgabe)
- Pause (mit History-Rückkehr zu An)
"""

from enum import Enum, auto
from typing import Callable, Optional
from dataclasses import dataclass, field


class HauptZustand(Enum):
    """Hauptzustände der Kaffeemaschine"""
    AUS = auto()
    AN = auto()
    PAUSE = auto()


class AnUnterZustand(Enum):
    """Unterzustände innerhalb des 'An'-Zustands"""
    LEERLAUF = auto()
    ZUBEREITUNG = auto()
    AUSGABE = auto()


@dataclass
class KaffeemaschineKontext:
    """Kontext/Daten der Kaffeemaschine"""
    wasser: int = 100  # Wassermenge in Einheiten
    
    def wasser_auffuellen(self, menge: int = 50) -> None:
        """Füllt Wasser auf"""
        self.wasser = min(self.wasser + menge, 100)
        print(f"  💧 Wasser aufgefüllt. Aktueller Stand: {self.wasser}")
    
    def wasser_verbrauchen(self, menge: int = 25) -> None:
        """Verbraucht Wasser bei der Zubereitung"""
        self.wasser = max(self.wasser - menge, 0)
        print(f"  💧 Wasser verbraucht. Aktueller Stand: {self.wasser}")


class KaffeemaschineStateMachine:
    """
    State Machine für eine Kaffeemaschine
    
    Implementiert:
    - Hierarchische Zustände (An mit Unterzuständen)
    - Entry/Exit-Aktionen
    - Guard-Bedingungen
    - History-State (für Pause -> Fortfahren)
    """
    
    def __init__(self) -> None:
        # Aktueller Zustand
        self._haupt_zustand: HauptZustand = HauptZustand.AUS
        self._unter_zustand: Optional[AnUnterZustand] = None
        
        # History für den An-Zustand (merkt sich letzten Unterzustand)
        self._history_unter_zustand: AnUnterZustand = AnUnterZustand.LEERLAUF
        
        # Kontext mit Daten
        self.kontext = KaffeemaschineKontext()
        
        print("🔌 Kaffeemaschine initialisiert im Zustand: AUS")
    
    # ==================== Properties ====================
    
    @property
    def zustand(self) -> str:
        """Gibt den aktuellen Zustand als lesbaren String zurück"""
        if self._haupt_zustand == HauptZustand.AN and self._unter_zustand:
            return f"{self._haupt_zustand.name}.{self._unter_zustand.name}"
        return self._haupt_zustand.name
    
    @property
    def ist_an(self) -> bool:
        return self._haupt_zustand == HauptZustand.AN
    
    # ==================== Entry/Exit Aktionen ====================
    
    def _piepen(self) -> None:
        """Exit-Aktion: Piep-Ton ausgeben"""
        print("  🔔 *PIEP*")
    
    def _wasser_reinigen(self) -> None:
        """Entry-Aktion für 'An'-Zustand: Wasser reinigen"""
        print("  🚿 Wasser wird gereinigt...")
    
    # ==================== Zustandsübergänge ====================
    
    def _betrete_an_zustand(self, unter_zustand: AnUnterZustand) -> None:
        """Betritt den 'An'-Zustand mit dem angegebenen Unterzustand"""
        self._haupt_zustand = HauptZustand.AN
        self._unter_zustand = unter_zustand
        # Entry-Aktion für 'An'
        self._wasser_reinigen()
        print(f"  ➡️ Betrete Unterzustand: {unter_zustand.name}")
    
    def _verlasse_an_zustand(self) -> None:
        """Verlässt den 'An'-Zustand und speichert History"""
        if self._unter_zustand:
            self._history_unter_zustand = self._unter_zustand
        # Exit-Aktion für 'An'
        self._piepen()
        self._unter_zustand = None
    
    # ==================== Ereignisse/Transitionen ====================
    
    def anschalten(self) -> bool:
        """
        Transition: Aus --> An
        
        Returns:
            True wenn Transition erfolgreich, False sonst
        """
        if self._haupt_zustand != HauptZustand.AUS:
            print(f"❌ Kann nicht anschalten - aktueller Zustand: {self.zustand}")
            return False
        
        print("\n⚡ Anschalten...")
        # Exit-Aktion für 'Aus'
        self._piepen()
        # Betrete 'An' mit initialem Unterzustand 'Leerlauf'
        self._betrete_an_zustand(AnUnterZustand.LEERLAUF)
        print(f"✅ Neuer Zustand: {self.zustand}")
        return True
    
    def wasser_auffuellen(self, menge: int = 50) -> bool:
        """
        Transition: Leerlauf --> Leerlauf (Selbstübergang)
        
        Args:
            menge: Wassermenge zum Auffüllen
            
        Returns:
            True wenn erfolgreich
        """
        if not (self._haupt_zustand == HauptZustand.AN and 
                self._unter_zustand == AnUnterZustand.LEERLAUF):
            print(f"❌ Wasser auffüllen nur im Leerlauf möglich - aktuell: {self.zustand}")
            return False
        
        print("\n💧 Wasser auffüllen...")
        self.kontext.wasser_auffuellen(menge)
        print(f"✅ Zustand bleibt: {self.zustand}")
        return True
    
    def kaffee_machen(self) -> bool:
        """
        Transition: Leerlauf --> Zubereitung [wasser > 20]
        
        Returns:
            True wenn Transition erfolgreich
        """
        if not (self._haupt_zustand == HauptZustand.AN and 
                self._unter_zustand == AnUnterZustand.LEERLAUF):
            print(f"❌ Kaffee machen nur im Leerlauf möglich - aktuell: {self.zustand}")
            return False
        
        # Guard-Bedingung prüfen
        if self.kontext.wasser <= 20:
            print(f"❌ Nicht genug Wasser! (Aktuell: {self.kontext.wasser}, benötigt: >20)")
            return False
        
        print("\n☕ Kaffee wird zubereitet...")
        self._unter_zustand = AnUnterZustand.ZUBEREITUNG
        self.kontext.wasser_verbrauchen(25)
        print(f"✅ Neuer Zustand: {self.zustand}")
        return True
    
    def zubereitung_abschliessen(self) -> bool:
        """
        Transition: Zubereitung --> Ausgabe
        
        Returns:
            True wenn erfolgreich
        """
        if not (self._haupt_zustand == HauptZustand.AN and 
                self._unter_zustand == AnUnterZustand.ZUBEREITUNG):
            print(f"❌ Nur während Zubereitung möglich - aktuell: {self.zustand}")
            return False
        
        print("\n✨ Zubereitung abgeschlossen!")
        self._unter_zustand = AnUnterZustand.AUSGABE
        print(f"✅ Neuer Zustand: {self.zustand}")
        return True
    
    def kaffee_entnehmen(self) -> bool:
        """
        Transition: Ausgabe --> Leerlauf
        
        Returns:
            True wenn erfolgreich
        """
        if not (self._haupt_zustand == HauptZustand.AN and 
                self._unter_zustand == AnUnterZustand.AUSGABE):
            print(f"❌ Kein Kaffee zur Entnahme - aktuell: {self.zustand}")
            return False
        
        print("\n☕ Kaffee entnommen!")
        self._unter_zustand = AnUnterZustand.LEERLAUF
        print(f"✅ Neuer Zustand: {self.zustand}")
        return True
    
    def stop(self) -> bool:
        """
        Transition: An --> Pause
        
        Returns:
            True wenn erfolgreich
        """
        if self._haupt_zustand != HauptZustand.AN:
            print(f"❌ Stop nur im An-Zustand möglich - aktuell: {self.zustand}")
            return False
        
        print("\n⏸️ Pause...")
        self._verlasse_an_zustand()
        self._haupt_zustand = HauptZustand.PAUSE
        print(f"✅ Neuer Zustand: {self.zustand} (History: {self._history_unter_zustand.name})")
        return True
    
    def fortfahren(self) -> bool:
        """
        Transition: Pause --> An[H] (History-State)
        
        Returns:
            True wenn erfolgreich
        """
        if self._haupt_zustand != HauptZustand.PAUSE:
            print(f"❌ Fortfahren nur aus Pause möglich - aktuell: {self.zustand}")
            return False
        
        print(f"\n▶️ Fortfahren (History: {self._history_unter_zustand.name})...")
        # Betrete 'An' mit dem gespeicherten History-Unterzustand
        self._betrete_an_zustand(self._history_unter_zustand)
        print(f"✅ Neuer Zustand: {self.zustand}")
        return True
    
    # ==================== Hilfsmethoden ====================
    
    def status(self) -> None:
        """Gibt den aktuellen Status der Maschine aus"""
        print(f"\n{'='*50}")
        print(f"📊 KAFFEEMASCHINE STATUS")
        print(f"{'='*50}")
        print(f"  Zustand: {self.zustand}")
        print(f"  Wasser:  {self.kontext.wasser}%")
        if self._haupt_zustand == HauptZustand.PAUSE:
            print(f"  History: {self._history_unter_zustand.name}")
        print(f"{'='*50}\n")


# ==================== Demo/Test ====================

def demo():
    """Demonstriert die Funktionalität der State Machine"""
    
    print("=" * 60)
    print("   KAFFEEMASCHINE STATE MACHINE DEMO")
    print("=" * 60)
    
    # Initialisierung
    maschine = KaffeemaschineStateMachine()
    maschine.status()
    
    # Szenario 1: Normaler Kaffee-Zyklus
    print("\n📍 SZENARIO 1: Normaler Kaffee-Zyklus")
    print("-" * 40)
    
    maschine.anschalten()
    maschine.kaffee_machen()
    maschine.zubereitung_abschliessen()
    maschine.kaffee_entnehmen()
    maschine.status()
    
    # Szenario 2: Wasser auffüllen
    print("\n📍 SZENARIO 2: Wasser auffüllen")
    print("-" * 40)
    
    maschine.wasser_auffuellen(30)
    maschine.status()
    
    # Szenario 3: Pause mit History
    print("\n📍 SZENARIO 3: Pause während Zubereitung (mit History)")
    print("-" * 40)
    
    maschine.kaffee_machen()  # Geht in Zubereitung
    maschine.stop()           # Pause (speichert History: ZUBEREITUNG)
    maschine.fortfahren()     # Zurück zu ZUBEREITUNG
    maschine.zubereitung_abschliessen()
    maschine.kaffee_entnehmen()
    maschine.status()
    
    # Szenario 4: Guard-Bedingung testen
    print("\n📍 SZENARIO 4: Guard-Bedingung (zu wenig Wasser)")
    print("-" * 40)
    
    # Wasser auf niedriges Level setzen
    maschine.kontext.wasser = 15
    print(f"  ⚠️ Wasserlevel auf {maschine.kontext.wasser} gesetzt")
    maschine.kaffee_machen()  # Sollte fehlschlagen
    maschine.wasser_auffuellen(50)
    maschine.kaffee_machen()  # Jetzt sollte es funktionieren
    
    maschine.status()
    
    print("\n✅ Demo abgeschlossen!")


if __name__ == "__main__":
    demo()