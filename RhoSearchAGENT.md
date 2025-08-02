## Neue ρ-Suchparameter
```python
# ALTE WERTE (fehlerhaft)
rho_lo = 0.40  # Zu optimistisch

# NEUE WERTE (funktional)
rho_lo = 0.20  # Realistisches Minimum
rho_hi = 0.35  # Stabiler Suchbereich
```

## Known Issues
Alle 7 kritischen Fehler behoben (v2.2)

## Parameters
ρ-Bereich: 0.20-0.35, MIN_SPACING: 5

## Testing
Neue Testsequenz: --rho_lo 0.20 --rho_hi 0.32
