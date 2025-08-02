# ValidationAGENT

## Türpositions-Validierung
Zusätzliche Constraints sichern gültige Koordinaten:
```python
model.Add(doorx[r] >= 0)
model.Add(doory[r] >= 0)
```

## Erweiterte Layout-Prüfung
Die neue Funktion `validate_realistic_layout` ergänzt `validate_solution_advanced`
um folgende Checks:
- Auslastung zwischen 15% und 40%
- Dev-Raumgröße zwischen 36 und 80 Feldern
- Kein Raum größer als 112 Felder

## Known Issues
Alle 7 kritischen Fehler behoben (v2.2)

## Parameters
ρ-Bereich: 0.20-0.35, MIN_SPACING: 5

## Testing
Neue Testsequenz: --rho_lo 0.20 --rho_hi 0.32
