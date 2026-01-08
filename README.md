
# PlantUML-StateChart-To-Python

Kurzes Uni-Projekt im Rahmen der Vorlesung *Model Driven Software Development* (MDSD).
Das Tool liest ein PlantUML-Statechart (`.puml`), baut daraus einen abstrakten Syntaxbaum (AST)
und generiert einfachen Python-Code für eine Zustandsmaschine.

> Hinweis: Nur zu Lern- und Demonstrationszwecken, **nicht** für den produktiven Einsatz gedacht.

## Projektaufbau

- `src/` – Kernlogik
  - `parser.py`: PlantUML-Statechart → AST (treelib-Tree)
  - `generator.py`: AST → Python-State-Machine
  - `main.py`: Einfaches Beispiel (CoffeeMachine) für End-to-End-Transformation
- `examples/`
  - `inputs/`: Beispiel-`*.puml`-Dateien
  - `outputs/`: generierter Python-Code (u. a. in `outputs/own/`)
- `docs/`: Skizzen, Diagramme und Notizen zur Ausarbeitung
- `literature.md`: Kurz notierte Literaturrecherche

## Installation

Voraussetzung ist eine aktuelle Python-Version (z. B. 3.11).

```bash
cd /Users/marvintank/workspace/PlantUML-StateChart-To-Python
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Verwendung (Beispiel)

Standardmäßig ist in `src/main.py` der Input `examples/inputs/coffeeMachine.puml`
und das Output-Verzeichnis `examples/outputs/own/` hinterlegt.

```bash
cd src
python main.py
```

Der generierte Code landet dann z. B. in
`examples/outputs/own/coffeemachine.py`.

## PlantUML-Subset & Details

Das Projekt deckt ein bewusst kleines PlantUML-Subset ab, welches aber auch um Funktionen erweitert wurde (siehe [plantuml_subset.md](plantuml_subset.md)). Für tiefergehende Informationen siehe das begleitende Paper „Modellgetriebene Transformation von PlantUML zu Python-Code: Entwicklung eines AST-basierten Generators für komplexe Statecharts".

Weitere Hintergründe und Literaturhinweise findest du in [literature.md](literature.md).