### README.md
# MGT2 Ultra-Präzisions Layout-Optimierer

## Installation
```bash
pip install ortools matplotlib
git clone https://github.com/Hoope1/Mad-Games-Tycoon-2-Rooms
cd Mad-Games-Tycoon-2-Rooms
```

## Verwendung
```bash
# Basisoptimierung (5 Min)
python planner.py --time 300 --outdir ergebnis

# Präzisionsmodus (ρ-Zielbereich)
python planner.py --precision_mode --rho_lo 0.58 --rho_hi 0.63
```

## Kernparameter
| Parameter | Wirkung | Standard |
|-----------|---------|----------|
| `--threads` | CPU-Kerne | Systemmaximum |
| `--seed` | Reproduzierbarkeit | 42 |
| `--rho_lo` | Minimale Flächennutzung | 0.45 |
| `--multi_run` | Lösungsiterationen | 1 |

## Optimierungsziele
1. **Raumauslastung**: Maximiere ρ (Raumfläche/Freifläche)
2. **Nachbarschafts-Boni**: 
   ```python
   ADJ["Produktion"]["Lager"] = 120  # Höchster Bonus
   ```
3. **Gruppenkompaktheit**: Cluster für Dev/QA/Studio-Räume

## Ausgabe
`ergebnis/MGT2_OptimalLayout.png`:  
![Legende](https://agentsmd.net/static/media/legend.3f7a8a94.png)  
`ergebnis/MGT2_OptimalLayout.json`:
```json
{
  "Metriken": {
    "Flächennutzung": 0.6142,
    "Nachbarschafts-Score": 24781
  }
}
```

## Validierungsstandards
- ✓ Keine Raumüberlappungen
- ✓ Türen auf Korridoren
- ✓ Bandabstand ≥8 Felder
- ✓ Tür-Cluster ≤3 pro Feld
