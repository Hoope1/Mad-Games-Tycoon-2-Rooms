# -*- coding: utf-8 -*-

"""

Mad Games Tycoon 2 – Ultra-Precision CP-SAT Planer

==================================================


Maximale Genauigkeit durch:

- Globale CP-SAT-Optimierung (alle harten Regeln exakt modelliert)

- ρ-Bisektion (maximiert die Flächennutzungsrate direkt als harte Nebenbedingung)

- Multi-Objective-Ziel mit gestaffelten Distanz-Boni, Prioritäten, Kompaktheit, Symmetrie

- 8 Türpositionen (4 Seitenmittel + 4 Ecken) je Raum

- Präzisions-Modus (Portfolio-Search, höhere Probing-Stufen)

- Multi-Stage-Bisektion (Exploration → Feinabstimmung)

- Erweiterte Validierung und Analyse/Export

"""


from __future__ import annotations


import os

import sys

import time

import json

import argparse

import math

from dataclasses import dataclass

from typing import List, Tuple, Dict, Optional, Any


# Matplotlib für Visualisierung (optional)

try:

    import matplotlib.pyplot as plt

    from matplotlib.patches import Rectangle, FancyBboxPatch

    HAVE_MPL = True

except ImportError:

    HAVE_MPL = False

    plt = None

    Rectangle = None


# OR-Tools CP-SAT Solver

from ortools.sat.python import cp_model


# ======================= Geometrie & Konstanten =======================

GRID_W, GRID_H = 77, 50       # Spielfeldgröße (77x50 Felder)

TOTAL_AREA = GRID_W * GRID_H  # Gesamtfläche


# Vertikaler Eingangsstamm (Hauptkorridor)

ENTRANCE_X1, ENTRANCE_W = 55, 4

ENTRANCE_X2 = ENTRANCE_X1 + ENTRANCE_W

ENTRANCE_MIN_LEN = 10          # Mindestlänge des Korridors

ENTRANCE_MAX_LEN = 35          # Maximale Länge des Korridors


# Horizontale Bänder

MAX_DEEPEST = GRID_H - 4       # Maximale Y-Position für Bänder

YCAND = list(range(0, MAX_DEEPEST + 1))  # Mögliche Y-Positionen (0..46)

MIN_BANDS = 2                  # Mindestanzahl horizontaler Bänder

MAX_BANDS = 4                  # Maximale Anzahl horizontaler Bänder

MIN_SPACING = 8                # Mindestabstand zwischen Bändern


# Tür-Cluster Grenze (max. Türen pro Feld)

DOOR_CLUSTER_LIMIT = 3


# Distanz-Schwellen für Bonifikationen

K_DOOR = 250                   # Maximaler Distanz-Bonus für Türadjazenz


# ======================= Zielfunktions-Gewichte =======================

W_CORRIDOR_AREA   = 500        # Strafe für Korridorfläche

W_ENTRANCE_LEN    = 300        # Strafe für lange Eingangskorridore

W_BORDER          = 200        # Strafe für Randpositionen

W_BAND_COUNT      = 300        # Strafe für viele horizontale Bänder

W_DOOR_ADJ        = 12000      # Bonus für kurze Türdistanzen

W_CENTER_ADJ      = 2400       # Bonus für Zentrumsnähe

W_HORIZ_PREF      = 5000       # Bonus für horizontale Präferenz

W_PROD_STORE_BON  = 16000      # Bonus für Produktion-Lager-Adjazenz

W_ROOM_EFFICIENCY = 8000       # Bonus für bevorzugte Raumgrößen

W_PRIORITY_BONUS  = 4000       # Bonus für priorisierte Räume

W_SYMMETRY_BONUS  = 1500       # Bonus für symmetrische Verteilung

W_COMPACT_BONUS   = 3500       # Bonus für kompakte Gruppenbildung


# ======================= Raumdefinitionen =======================

@dataclass(frozen=True)

class RoomDef:

    """Definition eines Raumtyps mit allen Eigenschaften."""

    name: str                   # Raumname (z.B. "Dev")

    group: str                  # Gruppenzugehörigkeit (z.B. "Dev")

    pref_w: int; pref_h: int    # Bevorzugte Breite/Höhe

    min_w: int; min_h: int      # Minimale Breite/Höhe

    step_w: int = 1; step_h: int = 1  # Schrittweite für Größen

    priority: int = 5           # Priorität (1-10, 10=hoch)

    efficiency_factor: float = 1.0  # Effizienzgewicht


# Alle Raumdefinitionen

ROOMS: List[RoomDef] = [

    # Kernentwicklung – hohe Priorität

    RoomDef("Dev",       "Dev",        8,  8,  6,  7, 2, 1, 10, 1.5),

    RoomDef("Graphics",  "Studio",     8,  6,  6,  6, 2, 1,  9, 1.3),

    RoomDef("Sound",     "Studio",     8,  7,  6,  6, 2, 1,  9, 1.3),

    RoomDef("MoCap",     "Studio",    16,  8, 12,  8, 4, 1,  8, 1.2),

    RoomDef("QA",        "QA",         8,  8,  6,  6, 2, 1,  9, 1.4),

    RoomDef("Research",  "Research",   8,  6,  6,  6, 2, 1,  8, 1.1),

    

    # Management & Betrieb

    RoomDef("Head Office","Admin",     6,  6,  6,  6, 1, 1,  9, 1.3),

    RoomDef("Marketing",  "Marketing",10,  6,  6,  6, 1, 1,  7, 1.1),

    RoomDef("Support1",   "Support",  10,  8,  8,  6, 1, 1,  6, 1.0),

    RoomDef("Support2",   "Support",  10,  8,  8,  6, 1, 1,  6, 1.0),

    

    # Spezialräume

    RoomDef("Console",   "Console",   10,  8, 10,  8, 1, 1,  7, 1.1),

    RoomDef("Server",    "Server",    10, 10,  8,  8, 1, 1,  8, 1.2),

    RoomDef("Prod1",     "Production",12, 10, 11, 10, 1, 1,  8, 1.3),

    RoomDef("Prod2",     "Production",12, 10, 11, 10, 1, 1,  8, 1.3),

    RoomDef("Storeroom", "Storage",   11, 10, 11,  8, 1, 1,  9, 1.4),

    

    # Training & Allgemein

    RoomDef("Training",  "Training",  11,  8, 11,  6, 1, 1,  6, 1.1),

    RoomDef("Toilet1",   "Facilities", 6,  4,  3,  3, 1, 1,  5, 0.8),

    RoomDef("Toilet2",   "Facilities", 6,  4,  3,  3, 1, 1,  5, 0.8),

    RoomDef("Staff1",    "Facilities", 8,  8,  6,  6, 1, 1,  6, 1.0),

    RoomDef("Staff2",    "Facilities", 8,  8,  6,  6, 1, 1,  6, 1.0),

]


# Hilfsvariablen

R = len(ROOMS)  # Anzahl Räume

GROUPS = [rd.group for rd in ROOMS]  # Alle Gruppen


# Duplikat-Sets für Symmetrie-Breaking

DUP_SETS: List[List[int]] = []

for prefix in ("Support", "Prod", "Toilet", "Staff"):

    indices = [i for i, rd in enumerate(ROOMS) if rd.name.startswith(prefix)]

    if len(indices) >= 2:

        DUP_SETS.append(indices)


# ======================= Adjazenz-Matrix =======================

ADJ: Dict[str, Dict[str, int]] = {

    "Production": {"Storage": 120, "Marketing": 60, "Admin": 50, "QA": 40},

    "Storage":    {"Production": 120, "Marketing": 40},

    

    "Dev":        {"Studio": 90, "QA": 90, "Research": 70, "Admin": 40},

    "Studio":     {"Dev": 90, "QA": 70, "Research": 30},

    "QA":         {"Dev": 90, "Studio": 70, "Support": 50, "Production": 30},

    

    "Admin":      {"Marketing": 80, "Support": 80, "Production": 50, "Console": 60, "Dev": 40},

    "Marketing":  {"Admin": 80, "Production": 60, "Console": 40},

    

    "Support":    {"Admin": 80, "QA": 50, "Server": 60, "Dev": 30},

    "Server":     {"Support": 60, "Console": 40},

    

    "Research":   {"Dev": 70, "Studio": 30, "Admin": 30},

    "Console":    {"Admin": 60, "Dev": 50, "Marketing": 40, "Server": 40},

    

    "Training":   {"Dev": 50, "Admin": 50, "Studio": 40, "Support": 30},

    "Facilities": {"Dev": 60, "Production": 60, "Support": 60, "Admin": 60, "Studio": 40},

}


# ======================= Hilfsfunktionen =======================

def all_size_pairs(rd: RoomDef) -> List[Tuple[int, int]]:

    """Generiert alle zulässigen (Breite, Höhe)-Paare für einen Raumtyp."""

    pairs = []

    for w in range(rd.min_w, rd.pref_w + 1, max(1, rd.step_w)):

        for h in range(rd.min_h, rd.pref_h + 1, max(1, rd.step_h)):

            pairs.append((w, h))

    return pairs


def abs_var(model: cp_model.CpModel, a: cp_model.IntVar, b: cp_model.IntVar, 

            ub: int, name: str) -> cp_model.IntVar:

    """Erzeugt eine Variable für |a - b| mit oberer Schranke ub."""

    diff = model.NewIntVar(-ub, ub, f"{name}_diff")

    model.Add(diff == a - b)

    abs_val = model.NewIntVar(0, ub, name)

    model.AddAbsEquality(abs_val, diff)

    return abs_val


def manhattan_distance_var(model: cp_model.CpModel,

                           x1: cp_model.IntVar, y1: cp_model.IntVar,

                           x2: cp_model.IntVar, y2: cp_model.IntVar,

                           name: str) -> cp_model.IntVar:

    """Berechnet die Manhattan-Distanz zwischen zwei Punkten als Variable."""

    dx = abs_var(model, x1, x2, GRID_W, f"{name}_dx")

    dy = abs_var(model, y1, y2, GRID_H, f"{name}_dy")

    dist = model.NewIntVar(0, GRID_W + GRID_H, f"{name}_dist")

    model.Add(dist == dx + dy)

    return dist


# ======================= Lösungsergebnis =======================

@dataclass

class CPSolution:

    """Speichert alle relevanten Informationen einer gefundenen Lösung."""

    status: str                 # Lösungsstatus (OPTIMAL, FEASIBLE, etc.)

    objective: int              # Zielfunktionswert

    rho: float                  # Ziel-Nutzungsrate

    entrance_len: int           # Länge des Eingangskorridors

    horiz_y: List[int]          # Y-Positionen der horizontalen Bänder

    rooms: List[Dict]           # Raumpositionen und Eigenschaften

    room_area: int              # Gesamte Raumfläche

    corridor_area: int          # Gesamte Korridorfläche

    utilization: float          # Tatsächliche Nutzungsrate

    time_s: float               # Berechnungsdauer in Sekunden

    efficiency_score: float = 0.0  # Anteil Räume in bevorzugter Größe


# ======================= Modellaufbau & Lösung =======================

def build_and_solve_cp(

    max_time: Optional[float], 

    threads: int, 

    seed: int,

    rho_target: Optional[float], 

    precision_mode: bool = False,

    log_progress: bool = False

) -> CPSolution:

    """

    Baut und löst das CP-SAT-Modell für das Layout-Problem.

    

    Args:

        max_time: Maximale Lösungsdauer in Sekunden (None = unbegrenzt)

        threads: Anzahl der zu verwendenden CPU-Threads

        seed: Random Seed für reproduzierbare Ergebnisse

        rho_target: Ziel-Nutzungsrate (None = nicht verwenden)

        precision_mode: Aktiviert erweiterte Solver-Optionen

        log_progress: Loggt den Lösungsfortschritt

        

    Returns:

        CPSolution-Objekt mit allen Lösungsergebnissen

    """

    model = cp_model.CpModel()

    

    # ---------- Korridor-Variablen ----------

    # Vertikaler Hauptkorridor

    L = model.NewIntVar(ENTRANCE_MIN_LEN, ENTRANCE_MAX_LEN, "L")

    

    # Horizontale Bänder

    z = {y: model.NewBoolVar(f"z_{y}") for y in YCAND}  # Aktivierungsvariablen

    border = {y: model.NewBoolVar(f"border_{y}") for y in YCAND}  # Randnähe

    

    # Anzahl Bänder

    band_count = model.NewIntVar(MIN_BANDS, MAX_BANDS, "band_count")

    model.Add(band_count == sum(z.values()))

    

    # Mindestabstand zwischen Bändern

    for y1 in YCAND:

        for y2 in YCAND:

            if y2 > y1 and y2 - y1 < MIN_SPACING:

                model.Add(z[y1] + z[y2] <= 1)

    

    # Verbindung mit Hauptkorridor

    for y in YCAND:

        model.Add(L > y).OnlyEnforceIf(z[y])

    

    # Randnähe (Bonus für frühe Positionen)

    for y in YCAND:

        model.Add(border[y] <= z[y])

        if y <= 2:

            model.Add(border[y] == z[y])

        else:

            model.Add(border[y] == 0)

    

    # Korridorfläche berechnen

    corridor_area = model.NewIntVar(0, TOTAL_AREA, "corridor_area")

    model.Add(corridor_area == ENTRANCE_W * L + sum(

        z[y] * GRID_W * 4 for y in YCAND

    ))


    # ---------- Raum-Variablen ----------

    size_opts: List[List[Tuple[int, int]]] = []  # Größenoptionen pro Raum

    x_vars: List[cp_model.IntVar] = []           # X-Positionen

    y_vars: List[cp_model.IntVar] = []           # Y-Positionen

    w_vars: List[cp_model.IntVar] = []           # Breiten

    h_vars: List[cp_model.IntVar] = []           # Höhen

    size_id: List[cp_model.IntVar] = []          # Größenindex

    is_pref: List[cp_model.BoolVar] = []         # Bevorzugte Größe?

    doorx: List[cp_model.IntVar] = []            # Tür X-Positionen

    doory: List[cp_model.IntVar] = []            # Tür Y-Positionen

    cx_vars: List[cp_model.IntVar] = []          # Raumzentrum X

    cy_vars: List[cp_model.IntVar] = []          # Raumzentrum Y

    

    for r_idx, rd in enumerate(ROOMS):

        # Größenoptionen generieren

        opts = all_size_pairs(rd)

        size_opts.append(opts)

        

        # Größenindex

        sid = model.NewIntVar(0, len(opts) - 1, f"sid_{r_idx}")

        size_id.append(sid)

        

        # Raumgröße

        w = model.NewIntVar(rd.min_w, rd.pref_w, f"w_{r_idx}")

        h = model.NewIntVar(rd.min_h, rd.pref_h, f"h_{r_idx}")

        w_vars.append(w)

        h_vars.append(h)

        

        # Größe aus Index ableiten

        model.AddElement(sid, [size[0] for size in opts], w)

        model.AddElement(sid, [size[1] for size in opts], h)

        

        # Bevorzugte Größe?

        ispf = model.NewBoolVar(f"is_pref_{r_idx}")

        is_pref.append(ispf)

        model.Add(w == rd.pref_w).OnlyEnforceIf(ispf)

        model.Add(h == rd.pref_h).OnlyEnforceIf(ispf)

        

        # Raumposition

        x = model.NewIntVar(0, GRID_W - 1, f"x_{r_idx}")

        y = model.NewIntVar(0, GRID_H - 1, f"y_{r_idx}")

        x_vars.append(x)

        y_vars.append(y)

        model.Add(x + w <= GRID_W)

        model.Add(y + h <= GRID_H)

        

        # Türpositionen (8 Optionen: 4 Seiten + 4 Ecken)

        dx_table: List[int] = []

        dy_table: List[int] = []

        for (W, H) in opts:

            midW = W // 2

            midH = H // 2

            dx_table += [0, W-1, midW, midW, 0, W-1, 0, W-1]

            dy_table += [midH, midH, 0, H-1, 0, 0, H-1, H-1]

        

        # Türkombination

        comb = model.NewIntVar(0, 8 * len(opts) - 1, f"comb_{r_idx}")

        side = model.NewIntVar(0, 7, f"side_{r_idx}")

        model.Add(comb == sid * 8 + side)

        

        # Tür-Offset

        dx_off = model.NewIntVar(0, GRID_W, f"dxoff_{r_idx}")

        dy_off = model.NewIntVar(0, GRID_H, f"dyoff_{r_idx}")

        model.AddElement(comb, dx_table, dx_off)

        model.AddElement(comb, dy_table, dy_off)

        

        # Türposition

        door_x = model.NewIntVar(0, GRID_W - 1, f"doorx_{r_idx}")

        door_y = model.NewIntVar(0, GRID_H - 1, f"doory_{r_idx}")

        doorx.append(door_x)

        doory.append(door_y)

        model.Add(door_x == x + dx_off)

        model.Add(door_y == y + dy_off)

        

        # Raumzentrum

        midw = model.NewIntVar(0, GRID_W, f"midw_{r_idx}")

        midh = model.NewIntVar(0, GRID_H, f"midh_{r_idx}")

        model.AddElement(sid, [W // 2 for (W, H) in opts], midw)

        model.AddElement(sid, [H // 2 for (W, H) in opts], midh)

        

        cx_val = model.NewIntVar(0, GRID_W, f"cx_{r_idx}")

        cy_val = model.NewIntVar(0, GRID_H, f"cy_{r_idx}")

        cx_vars.append(cx_val)

        cy_vars.append(cy_val)

        model.Add(cx_val == x + midw)

        model.Add(cy_val == y + midh)


    # ---------- Raumplatzierung ----------

    # Keine Überlappung der Räume

    x_intervals = []

    y_intervals = []

    for r in range(R):

        x_end = model.NewIntVar(0, GRID_W, f"xend_{r}")

        y_end = model.NewIntVar(0, GRID_H, f"yend_{r}")

        model.Add(x_end == x_vars[r] + w_vars[r])

        model.Add(y_end == y_vars[r] + h_vars[r])

        

        x_int = model.NewIntervalVar(

            x_vars[r], w_vars[r], x_end, f"xint_{r}"

        )

        y_int = model.NewIntervalVar(

            y_vars[r], h_vars[r], y_end, f"yint_{r}"

        )

        x_intervals.append(x_int)

        y_intervals.append(y_int)

    

    model.AddNoOverlap2D(x_intervals, y_intervals)

    

    # Räume müssen links oder rechts des Hauptkorridors sein

    for r in range(R):

        left = model.NewBoolVar(f"left_{r}")

        right = model.NewBoolVar(f"right_{r}")

        model.Add(x_vars[r] + w_vars[r] <= ENTRANCE_X1).OnlyEnforceIf(left)

        model.Add(x_vars[r] >= ENTRANCE_X2).OnlyEnforceIf(right)

        model.AddBoolOr([left, right])


    # ---------- Türpositionen ----------

    # Türen müssen auf Korridoren liegen

    d_vert = [model.NewBoolVar(f"dvert_{r}") for r in range(R)]

    d_band = [[model.NewBoolVar(f"d_{r}_{yb}") for yb in YCAND] for r in range(R)]

    

    for r in range(R):

        # Hauptkorridor

        model.Add(doorx[r] >= ENTRANCE_X1).OnlyEnforceIf(d_vert[r])

        model.Add(doorx[r] <= ENTRANCE_X2 - 1).OnlyEnforceIf(d_vert[r])

        model.Add(doory[r] < L).OnlyEnforceIf(d_vert[r])

        

        # Horizontale Bänder

        for yb in YCAND:

            model.Add(doory[r] >= yb).OnlyEnforceIf(d_band[r][yb])

            model.Add(doory[r] <= yb + 3).OnlyEnforceIf(d_band[r][yb])

            model.Add(d_band[r][yb] <= z[yb])

    

    for r in range(R):

        model.Add(sum(d_band[r][yb] for yb in YCAND) + d_vert[r] == 1)

    

    # Tür-Cluster vermeiden (max. 3 Türen pro Feld)

    # Vertikaler Korridor

    for ty in range(GRID_H):

        if ty >= ENTRANCE_MAX_LEN:

            continue

            

        row_active = model.NewBoolVar(f"row_active_{ty}")

        model.Add(L > ty).OnlyEnforceIf(row_active)

        

        for tx in range(ENTRANCE_X1, ENTRANCE_X2):

            door_count = model.NewIntVar(0, R, f"door_count_{tx}_{ty}")

            indicators = []

            for r in range(R):

                same_pos = model.NewBoolVar(f"same_pos_{r}_{tx}_{ty}")

                model.Add(doorx[r] == tx).OnlyEnforceIf(same_pos)

                model.Add(doorx[r] != tx).OnlyEnforceIf(same_pos.Not())

                model.Add(doory[r] == ty).OnlyEnforceIf(same_pos)

                model.Add(doory[r] != ty).OnlyEnforceIf(same_pos.Not())

                indicators.append(same_pos)

            

            model.Add(door_count == sum(indicators))

            model.Add(door_count <= DOOR_CLUSTER_LIMIT).OnlyEnforceIf(row_active)

    

    # Horizontale Bänder

    for yb in YCAND:

        band_active = z[yb]

        for ty in range(yb, yb + 4):

            for tx in range(GRID_W):

                door_count = model.NewIntVar(0, R, f"door_count_{tx}_{ty}")

                indicators = []

                for r in range(R):

                    same_pos = model.NewBoolVar(f"same_pos_{r}_{tx}_{ty}")

                    model.Add(doorx[r] == tx).OnlyEnforceIf(same_pos)

                    model.Add(doorx[r] != tx).OnlyEnforceIf(same_pos.Not())

                    model.Add(doory[r] == ty).OnlyEnforceIf(same_pos)

                    model.Add(doory[r] != ty).OnlyEnforceIf(same_pos.Not())

                    indicators.append(same_pos)

                

                model.Add(door_count == sum(indicators))

                model.Add(door_count <= DOOR_CLUSTER_LIMIT).OnlyEnforceIf(band_active)


    # ---------- Symmetrie-Breaking ----------

    # Für Duplikat-Räume (Support, Toiletten, etc.)

    for dup_set in DUP_SETS:

        for i in range(len(dup_set) - 1):

            a, b = dup_set[i], dup_set[i + 1]

            model.Add(x_vars[a] <= x_vars[b])

            order_flag = model.NewBoolVar(f"order_flag_{a}_{b}")

            model.Add(y_vars[a] <= y_vars[b]).OnlyEnforceIf(order_flag)

            model.Add(y_vars[a] > y_vars[b]).OnlyEnforceIf(order_flag.Not())


    # ---------- Flächenberechnung ----------

    # Raumflächen

    room_area = model.NewIntVar(0, TOTAL_AREA, "room_area")

    areas = []

    for r, opts in enumerate(size_opts):

        area = model.NewIntVar(0, TOTAL_AREA, f"area_{r}")

        model.AddElement(size_id[r], [W * H for (W, H) in opts], area)

        areas.append(area)

    model.Add(room_area == sum(areas))

    

    # Nutzungsrate-Constraint

    if rho_target is not None:

        rho_int = int(round(rho_target * 10000))

        model.Add(room_area * 10000 >= rho_int * (TOTAL_AREA - corridor_area))


    # ---------- Zielfunktion ----------

    obj = cp_model.LinearExpr()

    

    # Grundlegende Strafterme

    obj -= W_CORRIDOR_AREA * corridor_area

    obj -= W_ENTRANCE_LEN * L

    obj -= W_BORDER * sum(border.values())

    obj -= W_BAND_COUNT * band_count

    

    # Adjazenz-Boni

    pair_terms: List[cp_model.LinearExpr] = []

    center_terms: List[cp_model.LinearExpr] = []

    prod_store_terms: List[cp_model.LinearExpr] = []

    

    for i in range(R):

        gi = GROUPS[i]

        for j in range(i + 1, R):

            gj = GROUPS[j]

            base = ADJ.get(gi, {}).get(gj, 0) + ADJ.get(gj, {}).get(gi, 0)

            if base <= 0:

                continue

            

            # Prioritätsmultiplikator

            priority_mult = (ROOMS[i].priority + ROOMS[j].priority) / 10.0

            wij = int(base * priority_mult)

            

            # Türdistanz-Bonus

            d = manhattan_distance_var(

                model, doorx[i], doory[i], doorx[j], doory[j], f"d_{i}_{j}"

            )

            vclose = model.NewBoolVar(f"vclose_{i}_{j}")

            model.Add(d <= 5).OnlyEnforceIf(vclose)

            model.Add(d > 5).OnlyEnforceIf(vclose.Not())

            close_bonus = model.NewIntVar(0, K_DOOR, f"close_bonus_{i}_{j}")

            model.Add(close_bonus == K_DOOR).OnlyEnforceIf(vclose)

            

            close = model.NewBoolVar(f"close_{i}_{j}")

            model.Add(d >= 6).OnlyEnforceIf(close)

            model.Add(d <= 15).OnlyEnforceIf(close)

            medium_bonus = model.NewIntVar(0, K_DOOR // 2, f"medium_bonus_{i}_{j}")

            model.Add(medium_bonus == K_DOOR // 2).OnlyEnforceIf([close, vclose.Not()])

            

            total_bonus = model.NewIntVar(0, K_DOOR, f"total_bonus_{i}_{j}")

            model.AddMaxEquality(total_bonus, [close_bonus, medium_bonus])

            pair_terms.append(wij * total_bonus)

            

            # Zentrumsdistanz-Bonus

            dcx = abs_var(model, cx_vars[i], cx_vars[j], GRID_W, f"dcx_{i}_{j}")

            dcy = abs_var(model, cy_vars[i], cy_vars[j], GRID_H, f"dcy_{i}_{j}")

            dcent = model.NewIntVar(0, GRID_W + GRID_H, f"dcent_{i}_{j}")

            model.Add(dcent == dcx + dcy)

            

            ccl = model.NewBoolVar(f"ccl_{i}_{j}")

            model.Add(dcent <= 20).OnlyEnforceIf(ccl)

            cbonus = model.NewIntVar(0, K_DOOR // 4, f"cbonus_{i}_{j}")

            model.Add(cbonus == K_DOOR // 4).OnlyEnforceIf(ccl)

            center_terms.append(wij * cbonus)

            

            # Kritische Paare (Produktion-Lager)

            is_crit = (

                (gi == "Production" and gj == "Storage") or

                (gj == "Production" and gi == "Storage")

            )

            if is_crit:

                prod_store_terms.append(total_bonus)

    

    obj += W_DOOR_ADJ * cp_model.LinearExpr.Sum(pair_terms)

    obj += W_CENTER_ADJ * cp_model.LinearExpr.Sum(center_terms)

    obj += W_PROD_STORE_BON * cp_model.LinearExpr.Sum(prod_store_terms)

    

    # Effizienz-Boni (bevorzugte Raumgrößen)

    efficiency_terms: List[cp_model.LinearExpr] = []

    for r, rd in enumerate(ROOMS):

        eff = int(round(rd.efficiency_factor * 1000))

        efficiency_terms.append(eff * is_pref[r])

    obj += W_ROOM_EFFICIENCY * cp_model.LinearExpr.Sum(efficiency_terms)

    

    # Prioritäts-Boni (wichtige Räume nahe Eingang)

    priority_terms: List[cp_model.LinearExpr] = []

    entrance_cx = ENTRANCE_X1 + ENTRANCE_W // 2

    for r, rd in enumerate(ROOMS):

        if rd.priority >= 8:

            # Distanz zum Eingang

            dist_entrance = manhattan_distance_var(

                model, cx_vars[r], cy_vars[r], 

                model.NewConstant(entrance_cx), 

                model.NewConstant(0),

                f"dist_entr_{r}"

            )

            central = model.NewBoolVar(f"central_{r}")

            model.Add(dist_entrance <= 25).OnlyEnforceIf(central)

            pb = model.NewIntVar(0, rd.priority * 100, f"pbonus_{r}")

            model.Add(pb == rd.priority * 100).OnlyEnforceIf(central)

            priority_terms.append(pb)

    obj += W_PRIORITY_BONUS * cp_model.LinearExpr.Sum(priority_terms)

    

    # Horizontale Präferenz (bestimmte Gruppen nahe Bänder)

    H_GROUPS = {"Production": 1.5, "Storage": 1.5, "Server": 1.2}

    horiz_terms: List[cp_model.LinearExpr] = []

    for i, rd in enumerate(ROOMS):

        mult = H_GROUPS.get(rd.group, 0)

        if mult == 0:

            continue

            

        min_dists = []

        for yb in YCAND:

            # Distanz zum Band

            d = abs_var(model, doory[i], model.NewConstant(yb + 2), GRID_H, f"hdist_{i}_{yb}")

            active = model.NewBoolVar(f"active_{i}_{yb}")

            model.Add(d <= 8).OnlyEnforceIf(active)

            # Große Strafe wenn Band nicht aktiv

            min_dists.append(d + 1000 * (1 - z[yb]))

        

        min_dist = model.NewIntVar(0, 1000, f"min_dist_{i}")

        model.AddMinEquality(min_dist, min_dists)

        

        bonus_val = model.NewIntVar(0, int(1500 * mult), f"hbonus_{i}")

        model.Add(bonus_val == int(1500 * mult) - min_dist * 10)

        horiz_terms.append(bonus_val)

    obj += W_HORIZ_PREF * cp_model.LinearExpr.Sum(horiz_terms)

    

    # Kompaktheits-Boni (Gruppen-Cluster)

    compact_terms: List[cp_model.LinearExpr] = []

    for group in set(GROUPS):

        indices = [i for i, g in enumerate(GROUPS) if g == group]

        if len(indices) < 2:

            continue

            

        # Gruppenmittelpunkt

        avg_x = model.NewIntVar(0, GRID_W, f"avgx_{group}")

        avg_y = model.NewIntVar(0, GRID_H, f"avgy_{group}")

        model.AddDivisionEquality(avg_x, sum(cx_vars[i] for i in indices), len(indices))

        model.AddDivisionEquality(avg_y, sum(cy_vars[i] for i in indices), len(indices))

        

        # Distanzen zum Mittelpunkt

        for i in indices:

            dist = manhattan_distance_var(

                model, cx_vars[i], cy_vars[i], avg_x, avg_y, f"compact_{group}_{i}"

            )

            compact = model.NewBoolVar(f"compact_{group}_{i}")

            model.Add(dist <= 15).OnlyEnforceIf(compact)

            cbon = model.NewIntVar(0, 500, f"cbon_{group}_{i}")

            model.Add(cbon == 500).OnlyEnforceIf(compact)

            compact_terms.append(cbon)

    obj += W_COMPACT_BONUS * cp_model.LinearExpr.Sum(compact_terms)

    

    # Symmetrie-Bonus (Links-Rechts-Verteilung)

    left_count = model.NewIntVar(0, R, "left_count")

    right_count = model.NewIntVar(0, R, "right_count")

    model.Add(left_count == sum(

        model.NewBoolVar(f"left_{r}") for r in range(R) 

        if model.Add(x_vars[r] + w_vars[r] // 2 < GRID_W // 2)

    ))

    model.Add(right_count == R - left_count)

    

    bal_diff = abs_var(model, left_count, right_count, R, "balance_diff")

    bal_bonus = model.NewIntVar(0, 1000, "balance_bonus")

    model.Add(bal_diff <= 3).OnlyEnforceIf(bal_bonus == 1000)

    obj += W_SYMMETRY_BONUS * bal_bonus


    # Maximierung der Zielfunktion

    model.Maximize(obj)

    

    # ---------- Solver-Konfiguration ----------

    solver = cp_model.CpSolver()

    if max_time and max_time > 0:

        solver.parameters.max_time_in_seconds = float(max_time)

    solver.parameters.num_search_workers = max(1, threads)

    solver.parameters.random_seed = seed

    solver.parameters.randomize_search = True

    solver.parameters.log_search_progress = log_progress

    

    if precision_mode:

        solver.parameters.cp_model_presolve = True

        solver.parameters.cp_model_probing_level = 3

        solver.parameters.linearization_level = 2

        solver.parameters.symmetry_level = 2

        solver.parameters.search_branching = cp_model.PORTFOLIO_SEARCH

        solver.parameters.cut_level = 1

        solver.parameters.max_all_diff_cut_size = 64

    else:

        solver.parameters.cp_model_presolve = True

        solver.parameters.cp_model_probing_level = 2


    # ---------- Lösung ----------

    t0 = time.time()

    status = solver.Solve(model)

    t1 = time.time()

    status_name = solver.StatusName(status)

    

    # Ergebnis extrahieren

    if status_name in ("OPTIMAL", "FEASIBLE"):

        L_val = solver.Value(L)

        y_sel = [y for y in YCAND if solver.Value(z[y])]

        r_area = solver.Value(room_area)

        c_area = solver.Value(corridor_area)

        objective = int(round(solver.ObjectiveValue()))

    else:

        L_val, y_sel, r_area, c_area, objective = ENTRANCE_MIN_LEN, [], 0, TOTAL_AREA, 0

    

    free_area = TOTAL_AREA - c_area

    util = r_area / free_area if free_area > 0 else 0.0

    

    # Raumdaten sammeln

    rooms_data = []

    pref_count = 0

    for r, rd in enumerate(ROOMS):

        if status_name in ("OPTIMAL", "FEASIBLE"):

            x_val = solver.Value(x_vars[r])

            y_val = solver.Value(y_vars[r])

            w_val = solver.Value(w_vars[r])

            h_val = solver.Value(h_vars[r])

            door_x = solver.Value(doorx[r])

            door_y = solver.Value(doory[r])

            cx_val = solver.Value(cx_vars[r])

            cy_val = solver.Value(cy_vars[r])

            pref_flag = solver.Value(is_pref[r])

        else:

            x_val, y_val, w_val, h_val, door_x, door_y, cx_val, cy_val, pref_flag = 0, 0, 0, 0, 0, 0, 0, 0, False

            

        if pref_flag:

            pref_count += 1

            

        rooms_data.append({

            "name": rd.name,

            "group": rd.group,

            "priority": rd.priority,

            "efficiency_factor": rd.efficiency_factor,

            "x": x_val,

            "y": y_val,

            "w": w_val,

            "h": h_val,

            "is_preferred_size": bool(pref_flag),

            "door": {"x": door_x, "y": door_y},

            "center": {"x": cx_val, "y": cy_val}

        })

    

    eff_score = pref_count / R if R > 0 else 0.0

    

    return CPSolution(

        status=status_name,

        objective=objective,

        rho=rho_target if rho_target is not None else util,

        entrance_len=int(L_val),

        horiz_y=sorted(y_sel),

        rooms=rooms_data,

        room_area=int(r_area),

        corridor_area=int(c_area),

        utilization=util,

        time_s=t1 - t0,

        efficiency_score=eff_score

    )


# ======================= Multi-Stage ρ-Bisektion =======================

def search_max_rho_advanced(

    time_limit: float,

    threads: int,

    seed: int,

    precision_mode: bool,

    log_progress: bool,

    rho_lo: float = 0.40,

    rho_hi: float = 0.70,

    tol: float = 5e-4

) -> Tuple[CPSolution, CPSolution]:

    """

    Ermittelt das maximal mögliche ρ mittels zweistufiger Suche:

    1. Grobe Exploration des Suchraums

    2. Präzise Bisektion im vielversprechenden Bereich

    

    Returns:

        Tuple: (Beste gefundene Lösung, Letzte infeasible Lösung)

    """

    # Zeitverteilung: 40% Exploration, 60% Bisektion

    stage1_time = min(600, time_limit * 0.4)  # Max. 10 Min für Exploration

    stage2_time = time_limit - stage1_time

    

    print(f"[ρ-Suche] Stufe 1: Exploration ({stage1_time:.1f}s)")

    test_points = [rho_lo + i * (rho_hi - rho_lo) / 3.0 for i in range(4)]

    feasible_points = []

    

    # Grobe Exploration an Testpunkten

    for rho in test_points:

        sol = build_and_solve_cp(

            stage1_time / 4, threads, seed, rho, 

            False, log_progress

        )

        if sol.status in ("OPTIMAL", "FEASIBLE"):

            feasible_points.append((rho, sol))

            print(f"  ρ={rho:.3f} ✓ util={sol.utilization:.3f} obj={sol.objective}")

        else:

            print(f"  ρ={rho:.3f} ✗")

    

    # Bestimme vielversprechenden Bereich

    if feasible_points:

        best_rho = max(rho for rho, _ in feasible_points)

        lo = best_rho

        hi = min(best_rho + 0.05, rho_hi)

        best_sol = max(feasible_points, key=lambda x: x[0])[1]

    else:

        lo = rho_lo

        hi = rho_lo + (rho_hi - rho_lo) * 0.5

        best_sol = None

    

    print(f"[ρ-Suche] Stufe 2: Bisektion [{lo:.4f}, {hi:.4f}] ({stage2_time:.1f}s)")

    last_infeas = None

    

    # Präzise Bisektion

    for k in range(12):

        if hi - lo < tol:

            break

            

        mid = (lo + hi) / 2.0

        sol = build_and_solve_cp(

            stage2_time / 6, threads, seed + k, mid,

            precision_mode, log_progress

        )

        

        if sol.status in ("OPTIMAL", "FEASIBLE"):

            best_sol = sol

            lo = mid + tol / 10.0

            print(f"  Iter {k+1:02d}: ρ={mid:.5f} ✓ obj={sol.objective}")

        else:

            last_infeas = sol

            hi = mid - tol / 10.0

            print(f"  Iter {k+1:02d}: ρ={mid:.5f} ✗")

    

    # Fallback wenn keine feasible Lösung gefunden

    if best_sol is None:

        best_sol = build_and_solve_cp(

            time_limit * 0.2, threads, seed, 

            None, precision_mode, log_progress

        )

    

    if last_infeas is None:

        last_infeas = best_sol

    

    return best_sol, last_infeas


# ======================= Validierung =======================

def validate_solution_advanced(sol: CPSolution) -> Dict[str, bool]:

    """Führt umfangreiche Validierung der Lösung durch."""

    checks: Dict[str, bool] = {}

    

    # Türen auf Korridoren

    checks["doors_on_corridors"] = all(

        (ENTRANCE_X1 <= r["door"]["x"] < ENTRANCE_X2 and 

         0 <= r["door"]["y"] < sol.entrance_len) or

        any(yb <= r["door"]["y"] < yb + 4 for yb in sol.horiz_y)

        for r in sol.rooms

    )

    

    # Keine Überlappungen

    rects = [(r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]) for r in sol.rooms]

    checks["no_room_overlap"] = True

    for i in range(len(rects)):

        a = rects[i]

        for j in range(i + 1, len(rects)):

            b = rects[j]

            if not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1]):

                checks["no_room_overlap"] = False

                break

    

    # Korridorverbindungen

    checks["band_connection"] = all(

        yb < sol.entrance_len for yb in sol.horiz_y

    )

    

    # Bandabstände

    checks["band_spacing"] = True

    if len(sol.horiz_y) >= 2:

        sorted_y = sorted(sol.horiz_y)

        checks["band_spacing"] = all(

            sorted_y[i+1] - sorted_y[i] >= MIN_SPACING

            for i in range(len(sorted_y) - 1)

        )

    

    # Tür-Cluster

    door_positions = [(r["door"]["x"], r["door"]["y"]) for r in sol.rooms]

    checks["door_clusters"] = True

    for pos in set(door_positions):

        if door_positions.count(pos) > DOOR_CLUSTER_LIMIT:

            checks["door_clusters"] = False

            break

    

    # Raumgrößen

    checks["min_room_size"] = all(

        r["w"] >= ROOMS[i].min_w and r["h"] >= ROOMS[i].min_h

        for i, r in enumerate(sol.rooms)

    )

    

    # Gesamtgültigkeit

    checks["all_valid"] = all(checks.values())

    

    return checks


# ======================= Visualisierung =======================

def save_png_advanced(sol: CPSolution, path: str) -> None:

    """Erstellt eine detaillierte Visualisierung des Layouts als PNG."""

    if not HAVE_MPL:

        print("Visualisierung deaktiviert: Matplotlib nicht verfügbar")

        return

        

    fig, ax = plt.subplots(figsize=(20, 14))

    

    # Hintergrundgitter

    ax.set_facecolor('#f0f0f0')

    ax.grid(True, linestyle=':', linewidth=0.7, color='#cccccc')

    ax.set_xlim(0, GRID_W)

    ax.set_ylim(0, GRID_H)

    ax.set_aspect('equal')

    ax.set_title(

        f"Mad Games Tycoon 2 - Ultra-Precision Layout (ρ={sol.rho:.4f}, Util={sol.utilization*100:.2f}%)",

        fontsize=16, pad=20

    )

    ax.set_xlabel("X-Position", fontsize=12)

    ax.set_ylabel("Y-Position", fontsize=12)

    

    # Korridore zeichnen

    # Hauptkorridor (vertikal)

    ax.add_patch(Rectangle(

        (ENTRANCE_X1, 0), ENTRANCE_W, sol.entrance_len,

        facecolor='#aaccff', edgecolor='#3366cc', linewidth=1.5, alpha=0.8

    ))

    ax.text(

        ENTRANCE_X1 + ENTRANCE_W / 2, sol.entrance_len / 2, 

        'HAUPTKORRIDOR', ha='center', va='center', 

        fontsize=10, fontweight='bold', color='#003366'

    )

    

    # Horizontale Bänder

    for i, y in enumerate(sol.horiz_y):

        ax.add_patch(Rectangle(

            (0, y), GRID_W, 4,

            facecolor='#ddeeff', edgecolor='#6699cc', linewidth=1.2, alpha=0.7

        ))

        ax.text(

            GRID_W / 2, y + 2, f'BAND {i+1}', 

            ha='center', va='center', fontsize=9, color='#003366'

        )

        

        # Verbindung zum Hauptkorridor

        if y < sol.entrance_len:

            ax.plot(

                [ENTRANCE_X1, 0], [y, y], 

                'g--', linewidth=1.5, alpha=0.6

            )


    # Gruppenfarben

    group_colors = {

        "Dev": "#FF6B6B", "Studio": "#4ECDC4", "QA": "#45B7D1",

        "Admin": "#96CEB4", "Marketing": "#FFEAA7", "Support": "#DDA0DD",

        "Console": "#98D8C8", "Server": "#F7DC6F", "Production": "#BB8FCE",

        "Storage": "#85C1E9", "Research": "#F8C471", "Training": "#82E0AA",

        "Facilities": "#D5DBDB"

    }

    

    # Räume zeichnen

    for r in sol.rooms:

        col = group_colors.get(r["group"], "#CCCCCC")

        alpha = 0.85 if r["is_preferred_size"] else 0.6

        

        # Raumkörper

        ax.add_patch(Rectangle(

            (r["x"], r["y"]), r["w"], r["h"],

            facecolor=col, edgecolor='#333333', linewidth=1.0, alpha=alpha

        ))

        

        # Beschriftung

        label = f"{r['name']}\n{r['w']}×{r['h']}"

        if r["priority"] >= 8:

            label += " ★"

        if r["is_preferred_size"]:

            label += " ✓"

            

        ax.text(

            r["x"] + r["w"] / 2, r["y"] + r["h"] / 2, label,

            ha='center', va='center', fontsize=8,

            fontweight='bold' if r["priority"] >= 8 else 'normal'

        )

        

        # Tür

        ax.plot(

            r["door"]["x"], r["door"]["y"], 

            marker='s', markersize=8, markeredgewidth=1,

            markerfacecolor='red', markeredgecolor='black'

        )

        

        # Zentrum (für priorisierte Räume)

        if r["priority"] >= 8:

            ax.plot(

                r["center"]["x"], r["center"]["y"],

                marker='*', markersize=10, 

                markerfacecolor='gold', markeredgecolor='black'

            )

    

    # Legende

    from matplotlib.lines import Line2D

    legend_elements = [

        Line2D([0], [0], marker='s', color='w', markerfacecolor='red', 

               markersize=10, label='Türposition'),

        Line2D([0], [0], marker='*', color='w', markerfacecolor='gold', 

               markersize=10, label='Zentrum (Priorität)'),

        Line2D([0], [0], color='green', linestyle='--', lw=2, label='Korridorverbindung'),

        Line2D([0], [0], marker='', color='w', label=f'Effizienz: {sol.efficiency_score:.2f}'),

        Line2D([0], [0], marker='', color='w', label=f'Zielfunktion: {sol.objective:,}')

    ]

    ax.legend(

        handles=legend_elements, loc='upper right', 

        framealpha=0.9, fontsize=10

    )

    

    # Statistik-Box

    stats_text = (

        f"Raumfläche: {sol.room_area} / {TOTAL_AREA} ({sol.room_area/TOTAL_AREA*100:.1f}%)\n"

        f"Korridorfläche: {sol.corridor_area} ({sol.corridor_area/TOTAL_AREA*100:.1f}%)\n"

        f"Freie Fläche: {TOTAL_AREA - sol.corridor_area}\n"

        f"Nutzwert: {sol.utilization*100:.2f}% (Ziel ρ={sol.rho*100:.2f}%)\n"

        f"Berechnungsdauer: {sol.time_s:.1f}s\n"

        f"Status: {sol.status}"

    )

    ax.text(

        0.98, 0.02, stats_text,

        transform=ax.transAxes, fontsize=10,

        verticalalignment='bottom', horizontalalignment='right',

        bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)

    )

    

    # Speichern

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    fig.savefig(path, dpi=150, bbox_inches='tight')

    plt.close(fig)

    print(f"Visualisierung gespeichert: {path}")


# ======================= Datenexport =======================

def save_json_advanced(sol: CPSolution, path: str) -> None:

    """Exportiert alle Lösungsdaten im JSON-Format."""

    # Validierungsergebnisse

    validation = validate_solution_advanced(sol)

    

    # Adjazenz-Analyse

    adjacency_score = 0.0

    adjacency_details = []

    for i, r1 in enumerate(sol.rooms):

        for j in range(i + 1, len(sol.rooms)):

            r2 = sol.rooms[j]

            g1, g2 = r1["group"], r2["group"]

            weight = ADJ.get(g1, {}).get(g2, 0) + ADJ.get(g2, {}).get(g1, 0)

            if weight <= 0:

                continue

                

            # Distanz berechnen

            dx = abs(r1["door"]["x"] - r2["door"]["x"])

            dy = abs(r1["door"]["y"] - r2["door"]["y"])

            d = dx + dy

            

            # Score berechnen

            if d <= 5:

                score = weight * 100

            elif d <= 15:

                score = weight * 50

            else:

                score = weight * max(0.0, (K_DOOR - d) / K_DOOR * 100.0)

                

            adjacency_score += score

            adjacency_details.append({

                "rooms": [r1["name"], r2["name"]],

                "groups": [g1, g2],

                "weight": weight,

                "distance": d,

                "score": round(score, 1)

            })

    

    # Gruppenanalyse

    group_analysis = {}

    for r in sol.rooms:

        g = r["group"]

        if g not in group_analysis:

            group_analysis[g] = {

                "rooms": [],

                "total_area": 0,

                "preferred_sizes": 0,

                "avg_priority": 0.0,

                "center_of_mass": [0.0, 0.0]

            }

            

        data = group_analysis[g]

        data["rooms"].append(r["name"])

        data["total_area"] += r["w"] * r["h"]

        data["avg_priority"] += r["priority"]

        if r["is_preferred_size"]:

            data["preferred_sizes"] += 1

        data["center_of_mass"][0] += r["center"]["x"]

        data["center_of_mass"][1] += r["center"]["y"]

    

    for g, data in group_analysis.items():

        n = len(data["rooms"])

        if n > 0:

            data["avg_priority"] /= n

            data["center_of_mass"][0] /= n

            data["center_of_mass"][1] /= n

            data["preferred_size_ratio"] = data["preferred_sizes"] / n

    

    # Metadaten zusammenstellen

    out = {

        "metadata": {

            "generator": "MGT2 Ultra-Precision CP-SAT Planner",

            "version": "2.1",

            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),

            "grid_size": {"width": GRID_W, "height": GRID_H, "total_area": TOTAL_AREA}

        },

        "solution": {

            "status": sol.status,

            "objective": sol.objective,

            "computation_time": round(sol.time_s, 2),

            "validation": validation,

            "valid": validation.get("all_valid", False)

        },

        "layout": {

            "entrance": {

                "x_range": [ENTRANCE_X1, ENTRANCE_X2],

                "length": sol.entrance_len,

                "max_length": ENTRANCE_MAX_LEN,

                "area": ENTRANCE_W * sol.entrance_len

            },

            "horizontal_bands": {

                "count": len(sol.horiz_y),

                "positions": sol.horiz_y,

                "area": len(sol.horiz_y) * GRID_W * 4

            },

            "rooms": sol.rooms

        },

        "metrics": {

            "space_utilization": {

                "target_rho": sol.rho,

                "actual_utilization": sol.utilization,

                "room_area": sol.room_area,

                "corridor_area": sol.corridor_area,

                "free_area": TOTAL_AREA - sol.corridor_area,

                "efficiency_score": sol.efficiency_score

            },

            "adjacency": {

                "total_score": round(adjacency_score, 1),

                "average_score": round(adjacency_score / len(adjacency_details), 1) if adjacency_details else 0.0,

                "details_top20": sorted(adjacency_details, key=lambda x: -x["score"])[:20]

            },

            "group_analysis": group_analysis

        },

        "optimization_weights": {

            "corridor_penalty": W_CORRIDOR_AREA,

            "entrance_penalty": W_ENTRANCE_LEN,

            "border_penalty": W_BORDER,

            "band_count_penalty": W_BAND_COUNT,

            "door_adjacency": W_DOOR_ADJ,

            "center_adjacency": W_CENTER_ADJ,

            "horizontal_preference": W_HORIZ_PREF,

            "production_storage_bonus": W_PROD_STORE_BON,

            "room_efficiency": W_ROOM_EFFICIENCY,

            "priority_bonus": W_PRIORITY_BONUS,

            "symmetry_bonus": W_SYMMETRY_BONUS,

            "compact_bonus": W_COMPACT_BONUS

        }

    }

    

    # Speichern

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)

    with open(path, "w", encoding="utf-8") as f:

        json.dump(out, f, ensure_ascii=False, indent=2)

    

    print(f"Datenexport abgeschlossen: {path}")


# ======================= CLI & Hauptfunktion =======================

def main(argv: List[str]) -> None:

    """Hauptfunktion für die Kommandozeilenschnittstelle."""

    parser = argparse.ArgumentParser(

        description="Mad Games Tycoon 2 – Ultra-Precision CP-SAT Planer",

        formatter_class=argparse.ArgumentDefaultsHelpFormatter

    )

    parser.add_argument("--time", type=float, default=3600.0,

                        help="Gesamtzeitlimit in Sekunden")

    parser.add_argument("--threads", type=int, default=os.cpu_count() or 8,

                        help="Anzahl der Solver-Threads")

    parser.add_argument("--seed", type=int, default=42,

                        help="Zufallsseed für reproduzierbare Ergebnisse")

    parser.add_argument("--outdir", type=str, default="output",

                        help="Ausgabeverzeichnis für Ergebnisse")

    parser.add_argument("--precision_mode", action="store_true",

                        help="Aktiviert den Präzisionsmodus für bessere Ergebnisse")

    parser.add_argument("--analysis", action="store_true",

                        help="Führt detaillierte Lösungsanalyse durch")

    parser.add_argument("--multi_run", type=int, default=1,

                        help="Anzahl unabhängiger Durchläufe")

    parser.add_argument("--log", action="store_true",

                        help="Loggt den Lösungsfortschritt des Solvers")

    parser.add_argument("--rho_lo", type=float, default=0.45,

                        help="Untere Grenze für ρ-Suche")

    parser.add_argument("--rho_hi", type=float, default=0.65,

                        help="Obere Grenze für ρ-Suche")

    parser.add_argument("--tolerance", type=float, default=1e-4,

                        help="Toleranz für ρ-Bisektion")

    parser.add_argument("--selftest", action="store_true",

                        help="Führt einen schnellen Selbsttest durch")

    

    args = parser.parse_args(argv)

    os.makedirs(args.outdir, exist_ok=True)

    

    print("\n" + "=" * 70)

    print("Mad Games Tycoon 2 – Ultra-Precision CP-SAT Planer")

    print("=" * 70)

    print(f"Threads: {args.threads}, Seed: {args.seed}")

    print(f"Zeitbudget: {args.time:.0f}s, Präzisionsmodus: {args.precision_mode}")

    print(f"ρ-Bereich: [{args.rho_lo:.3f}, {args.rho_hi:.3f}], Toleranz: {args.tolerance:.1e}")

    print(f"Ausgabeverzeichnis: {args.outdir}")

    

    # Selbsttest-Modus

    if args.selftest:

        print("\n[Selbsttest] Starte schnellen Testlauf...")

        test_time = min(120, args.time)

        sol, _ = search_max_rho_advanced(

            test_time, args.threads, args.seed, 

            False, False, 0.4, 0.6, 1e-3

        )

        print(f"\nSelbsttest abgeschlossen: Status={sol.status}, ρ={sol.rho:.4f}")

        print(f"Raumfläche: {sol.room_area}, Korridorfläche: {sol.corridor_area}")

        print(f"Nutzungsrate: {sol.utilization*100:.2f}%")

        return

    

    # Mehrfachläufe

    solutions = []

    for run in range(1, args.multi_run + 1):

        print(f"\n{'=' * 30} LAUF {run}/{args.multi_run} {'=' * 30}")

        

        sol, _ = search_max_rho_advanced(

            args.time, args.threads, args.seed + run,

            args.precision_mode, args.log,

            args.rho_lo, args.rho_hi, args.tolerance

        )

        

        solutions.append(sol)

        print(f"Ergebnis {run}:")

        print(f"  Status: {sol.status}")

        print(f"  Zielfunktion: {sol.objective:,}")

        print(f"  Ziel ρ: {sol.rho:.4f}, Tatsächliche Nutzung: {sol.utilization*100:.2f}%")

        print(f"  Raumfläche: {sol.room_area}, Korridorfläche: {sol.corridor_area}")

        print(f"  Effizienz: {sol.efficiency_score:.3f}, Dauer: {sol.time_s:.1f}s")

    

    # Beste Lösung auswählen

    valid_solutions = [s for s in solutions if s.status in ("OPTIMAL", "FEASIBLE")]

    if valid_solutions:

        best_solution = max(valid_solutions, key=lambda s: s.objective)

        print(f"\n{'=' * 30} BESTE LÖSUNG {'=' * 30}")

        print(f"Zielfunktion: {best_solution.objective:,}")

        print(f"Nutzungsrate: {best_solution.utilization*100:.2f}% (Ziel ρ={best_solution.rho*100:.2f}%)")

        print(f"Eingangslänge: {best_solution.entrance_len}")

        print(f"Horizontale Bänder: {len(best_solution.horiz_y)} @ {best_solution.horiz_y}")

        

        # Export

        base_path = os.path.join(args.outdir, "MGT2_OptimalLayout")

        save_png_advanced(best_solution, base_path + ".png")

        save_json_advanced(best_solution, base_path + ".json")

        

        # Detaillierte Analyse

        if args.analysis:

            print("\n[Analyse] Validierungsergebnisse:")

            validation = validate_solution_advanced(best_solution)

            for check, valid in validation.items():

                print(f"  {'✓' if valid else '✗'} {check}")

            

            group_counts = {}

            for r in best_solution.rooms:

                group_counts[r["group"]] = group_counts.get(r["group"], 0) + 1

            

            print("\nRaumverteilung nach Gruppen:")

            for group, count in sorted(group_counts.items()):

                area = sum(r["w"] * r["h"] for r in best_solution.rooms if r["group"] == group)

                print(f"  {group:12s}: {count:2d} Räume, {area:5d} Tiles")

    else:

        print("\nKeine gültige Lösung gefunden!")

        if solutions:

            print("Letzter Status:", solutions[-1].status)


if __name__ == "__main__":

    main(sys.argv[1:])

