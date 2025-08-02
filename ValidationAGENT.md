# ValidationAGENT

## Türpositions-Validierung
Zusätzliche Constraints sichern gültige Koordinaten:
```python
model.Add(doorx[r] >= 0)
model.Add(doory[r] >= 0)
```

## Known Issues
Alle 7 kritischen Fehler behoben (v2.1)

## Parameters
ρ-Bereich: 0.25-0.40, MIN_SPACING: 6

## Testing
Neue Testsequenz: --rho_lo 0.25 --rho_hi 0.35
