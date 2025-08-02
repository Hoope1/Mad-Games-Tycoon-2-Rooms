## Korrigierte Raumdefinitionen (v2.2)

Die ROOMS-Liste wurde vollständig überarbeitet. Beispielauszug:

```python
ROOMS: List[RoomDef] = [
    RoomDef("Dev", "Dev", 10, 8, 6, 6, 2, 1, 10, 1.5),
    RoomDef("QA", "QA", 9, 7, 6, 6, 1, 1, 9, 1.4),
    RoomDef("Research", "Research", 8, 7, 6, 6, 1, 1, 8, 1.1),
    # ... weitere Räume siehe Code ...
]
```

## Known Issues
Alle 7 kritischen Fehler behoben (v2.2)

## Parameters
ρ-Bereich: 0.20-0.35, MIN_SPACING: 5

## Testing
Neue Testsequenz: --rho_lo 0.20 --rho_hi 0.32
