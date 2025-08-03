# DoorPlacementAGENT
> Version 2.5 Update

## Tür-Cluster-Logik
Die Constraints verwenden wieder ein Limit:
- DOOR_CLUSTER_LIMIT = 4

Zusätzlich gelten realistische Distanzschwellen:
- THRESHOLD_VERY_CLOSE_DOORS = 3
- THRESHOLD_CLOSE_DOORS = 8
- K_DOOR = 150

## Tür-zu-Gang-Regel
Türen müssen auf eine Gangfläche zeigen. Erlaubt sind der obere Eingangskorridor
und horizontale 4er-Bänder. Türen sitzen nicht in Ecken und führen niemals in
einen anderen Raum.

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
