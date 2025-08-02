# OptimizationAGENT

## Flächennutzungskorrektur
Die ursprüngliche ρ-Nebenbedingung wurde durch eine Version mit 5% Puffer ersetzt.

```python
model.Add(room_area * 10000 >= rho_int * (TOTAL_AREA - corridor_area) * 0.95)
```

## Known Issues
Alle 7 kritischen Fehler behoben (v2.1)

## Parameters
ρ-Bereich: 0.25-0.40, MIN_SPACING: 6

## Testing
Neue Testsequenz: --rho_lo 0.25 --rho_hi 0.35
