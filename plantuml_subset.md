## Our Chosen PlantUML Subset
Listed below are the features selected for our custom PlantUML subset. This includes the exact syntax that must be strictly followed to ensure stable parsing.

### Simple State
```puml
@startuml
state Simple_State

[*] --> Simple_State
@enduml
```
<img src="./static/simple_state_plantuml.png" alt="Simple State PlantUML example graphic" width="400"/>

### Composite State
**Keep in mind:** We only allow shallow composite state, which means you can only put simple states into composite states, not other composite states.
```puml
@startuml
state Composite_State

[*] --> Composite_State

state Composite_State {
  state Substate_A
  state Substate_B

  [*] --> Substate_A
  Substate_A --> Substate_B
}
@enduml
```
<img src="./static/composite_state_plantuml.png" alt="Composite State PlantUML example" width="400"/>

### History State
```puml
@startuml
state State_A
state Composite_State

[*] --> State_A
State_A --> Composite_State: Start
Composite_State --> State_A : Pause

state Composite_State {
  state Substate_A
  state Substate_B

  [*] --> Substate_A
  Substate_A --> Substate_B

  State_A --> [H]: Resume
}
@enduml
```
<img src="./static/history_state_plantuml.png" alt="History State PlantUML example" width="400"/>

### Transition + Guards
```puml
@startuml
state State_A
state State_B

[*] --> State_A
State_A --> State_B: Transition [x > 100]
@enduml
```
<img src="./static/transition_guard_plantuml.png" alt="Entry + Exit PlantUML example" width="400"/>

### Entry/Exit Action
```puml
@startuml
state State_A

[*] --> State_A
State_A: entry: do_something
State_A: exit: do_something_else
@enduml
```
<img src="./static/entry_exit_plantuml.png" alt="Entry + Exit PlantUML example" width="400"/>

### Example State Machine Using PlantUML

```puml
@startuml
scale 350 width
[*] --> Tür_offen
state Tür_offen
Tür_offen --> Tür_geschlossen: Event: Tür wird geschlossen

state Tür_geschlossen {
  Tür_geschlossen: Exit: Tür entsperren

  [*] --> Vorspülen: Event: Spülvorgang gestartet

  state Vorspülen {
    Vorspülen: Entry: Tür verriegeln
    Vorspülen: Exit: Wasser abpumpen
    Vorspülen --> Hauptreinigung: Time Event: nach 10min
  }

  state Hauptreinigung {
    Hauptreinigung: Entry: Heizung starten
    Hauptreinigung: Exit: Wasser abpumpen
    Hauptreinigung --> Hauptreinigung: Event: Geschirrspültab freigegeben
    Hauptreinigung --> Trocknen: Time Event: nach 60min
  }

  state Trocknen {
    Trocknen: Entry: Gebläse starten    
    Trocknen: Exit: Wasser abpumpen
  }
}

Tür_geschlossen --> [*]: Spülvorgang beendet
@enduml
```
<img src="./static/dishwasher_plantuml.png" alt="Dishwasher PlantUML example" width="400"/>
