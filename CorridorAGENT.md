# CorridorAGENT
> Version 2.5 Update

## Fixierter Eingangskorridor
Die Nebenbedingungen verwenden nun:
- ENTRANCE_MIN_LEN = 10
- ENTRANCE_MAX_LEN = 10
- Position: x = 56..59, y = 40..49
- MIN_BANDS = 2
- MAX_BANDS = 4
- MIN_SPACING = 8

## Known Issues
Alle 7 kritischen Fehler behoben (v2.2)

## Parameters
ρ-Bereich: 0.20-0.35, MIN_SPACING: 8

## Testing
Neue Testsequenz: --rho_lo 0.20 --rho_hi 0.32

## Neueste Änderungen
### 🔧 NEUE OPTIMIERUNGEN (v2.5)
| Feature                      | Beschreibung                          | Auswirkung               |
|------------------------------|---------------------------------------|--------------------------|
| Dynamische Bandverteilung    | 3 Zonen (unten/mitte/oben)            | Gleichmäßige Raumverteilung |
| Vertikal-Bonus               | 1000 * y_span                         | ↑ Vertikale Ausdehnung |
| Fixierter Eingang            | 10×4 Felder am oberen Rand           | ↑ Stabilität          |

[Raumoptimierung](#raumoptimierung)
