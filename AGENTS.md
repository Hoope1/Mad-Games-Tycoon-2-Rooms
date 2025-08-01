
[Vollständige AGENTS.md Spezifikation](AGENTS.md)
```

### AGENTS.md
```markdown
# AGENTS.md - Leitfaden für KI-Agenten

## Projektstruktur
- `/`: Hauptverzeichnis
  - `planner.py`: Hauptoptimierungs-Skript (CP-SAT Implementierung)
  - `validation.py`: Lösungsvalidierung
  - `visualization.py`: Layout-Visualisierung
- `/config`: Parameterdefinitionen
  - `raum_defs.py`: Raumgrößen und Prioritäten
  - `nachbarschafts_regeln.py`: Bewertungsmatrix
- `/tests`: Testsuite
  - `test_validation.py`: Integritätstests
  - `benchmark.py`: Leistungsmessung

## Codierungskonventionen
1. **Typannotationen**: Pflicht für alle Funktionen
```python
def baue_loese_cp(max_zeit: float, threads: int) -> CPSolution:
```

2. **OR-Tools Muster**:
- `NewIntVar()` für Entscheidungsvariablen
- `AddNoOverlap2D()` gegen Überlappungen
- `AddElement()` für Größenoptionen

3. **Qualitätssicherung**:
- Pylint mit .pylintrc Konfiguration
- Flake8 für PEP8-Konformität
- Black für automatische Formatierung

## Testprotokoll
```bash
# Vollständiger Testlauf
pytest --cov=planner.py

# Leistungsbenchmark
python -m tests.benchmark --szenario voll
```

## Pull-Request Richtlinien
1. ρ-Wert im Titel: `[ρ=0.61] Feature-Beschreibung`
2. Vorher/Nachher Layouts anhängen
3. Metrikänderungen im JSON-Diff zeigen
4. 100% Validierungserfolg erforderlich

## Automatisierte Prüfungen
```bash
# Statische Analyse
pylint --rcfile=.pylintrc planner.py
flake8 --config=.flake8

# Typüberprüfung
mypy --strict --disallow-untyped-calls planner.py

# Lösungsvalidierung
python -c "import validation; validation.führe_schnelltest()"
```

## Agenten-Direktiven
1. **Optimierungs-Prioritäten**:
```python
WICHTIGE_GEWICHTE = [
    W_PROD_STORE_BON,  # Produktion-Lager-Bonus
    W_DOOR_ADJ         # Tür-Adjazenz
]
```

2. **Präzisionsmodus**:
- Automatisch aktivieren bei ρ > 0.6
- Probing-Level auf 3 erhöhen
- Portfolio-Search verwenden

3. **Raumplatzierung**:
- Mindestabstand 8 Felder zwischen Bändern
- Symmetrie-Breaking für Duplikat-Räume
- Priorisierte Räume nahe Eingang (x≈55, y=0)

## Leistungskennzahlen
| Metrik | Zielwert | 
|--------|----------|
| ρ-Toleranz | ≤ 0.0001 |
| Laufzeit | < 600s |
| Tür-Cluster | ≤ 3/Feld |
