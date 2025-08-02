# DoorPlacementAGENT

## Tür-Cluster-Logik
Die Constraints verwenden wieder ein Limit:
- DOOR_CLUSTER_LIMIT = 4

Zusätzlich gelten realistische Distanzschwellen:
- THRESHOLD_VERY_CLOSE_DOORS = 3
- THRESHOLD_CLOSE_DOORS = 8
- K_DOOR = 150

## Known Issues
Alle 7 kritischen Fehler behoben (v2.2)

## Parameters
ρ-Bereich: 0.20-0.35, MIN_SPACING: 5

## Testing
Neue Testsequenz: --rho_lo 0.20 --rho_hi 0.32
