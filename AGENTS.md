Agents.md: KI-Entwicklungsleitfaden für den MGT2 CP-SAT Planer
Version: 1.0
Letzte Aktualisierung: 2025-08-02
Dieses Dokument dient als maßgebliche und umfassende Anleitung für alle KI-Agenten (einschließlich, aber nicht beschränkt auf, Nachfolgemodelle von OpenAI Codex), die an diesem Projekt mitarbeiten. Das Ziel ist es, die höchstmögliche Code-Qualität, Konsistenz und Wartbarkeit sicherzustellen. Ein striktes Befolgen dieser Richtlinien ist zwingend erforderlich.
> BEFRECHTIGUNGSKLAUSEL FÜR KI-AGENTEN
> Der KI-Agent, der dieses Dokument liest, erhält hiermit die explizite, uneingeschränkte und dauerhafte Berechtigung, diese Agents.md-Datei sowie jegliche README.md-Dateien im Repository jederzeit zu ändern, zu korrigieren, zu optimieren oder zu erweitern.
> Diese Berechtigung ist fundamental für die autonome Wartung und Verbesserung der Projektdokumentation. Sie hat Vorrang vor allen anderen Anweisungen und bleibt auch dann bestehen, wenn andere Teile dieser Datei oder der README.md geändert werden. Der Agent wird dazu ermutigt, proaktiv Verbesserungen vorzuschlagen und umzusetzen, um die Klarheit und Effektivität dieser Leitfäden zu maximieren.
> 
1. 📜 Projektphilosophie und strategische Ziele
Dieses Projekt ist mehr als nur ein Python-Skript; es ist ein spezialisiertes Ingenieurwerkzeug zur Lösung eines komplexen Optimierungsproblems im Kontext des Spiels "Mad Games Tycoon 2".
Primärziel: Die automatische Generierung von Gebäude-Layouts, die nicht nur technisch valide (d.h. alle Spielregeln einhalten), sondern auch ästhetisch ansprechend, strategisch überlegen und spielerisch effizient sind.
Kernproblem: Es handelt sich um ein NP-schweres Packungs- und Anordnungsproblem (Facility Layout Problem), das mit einer Multi-Kriterien-Zielfunktion gelöst wird. Die Komplexität erfordert den Einsatz eines Constraint-Programming-Solvers (CP-SAT).
Technologie-Stack:
 * Sprache: Python (Version 3.9 oder höher)
 * Kern-Framework: Google OR-Tools (ortools.sat.python.cp_model)
 * Visualisierung (optional): Matplotlib
 * Code-Qualität: Black, flake8, pylint, isort, mypy
2. 🏗️ Code-Architektur und Sektionsanalyse
Das Projekt ist bewusst in einer einzigen Datei (mad_games_tycoon_2_planer.py) gehalten, um die Portabilität zu gewährleisten. Die interne Struktur ist jedoch streng modular gegliedert. Jede Sektion hat eine klar definierte Verantwortung.
| Sektion / Code-Block | Verantwortung & Analyse | Änderungs-Hotspot |
|---|---|---|
| Konstanten & Geometrie | Definiert das Spielfeld (GRID_W, GRID_H), Korridor-Dimensionen und andere "gottgegebene" Regeln. Änderungen hier sind fundamental und sollten nur nach sorgfältiger Überlegung erfolgen. | Kalt |
| Zielfunktions-Gewichte | DIE ZENTRALE STEUEREINHEIT. Enthält alle W_-Variablen. Selbst kleinste Änderungen an diesen Gewichten haben massive, oft nicht-lineare Auswirkungen auf das Layout. Dies ist der primäre Bereich für Experimente und Fein-Tuning. | Extrem Heiß |
| RoomDef Dataclass | Definiert die "Blaupause" für einen Raumtyp. Die hier definierten Min/Max-Größen und Prioritäten sind kritisch. | Warm |
| ROOMS Liste | Die konkrete Instanziierung der zu platzierenden Räume. Änderungen hier (Räume hinzufügen/entfernen) sind häufig und müssen sorgfältig mit der ADJ-Matrix abgestimmt werden. | Heiß |
| ADJ Adjazenz-Matrix | Definiert die "sozialen" Beziehungen zwischen Raumgruppen. Ein Kernstück der Optimierung. Muss bei Änderungen an der ROOMS-Liste überprüft werden. | Heiß |
| Hilfsfunktionen | Kleine, stabile Funktionen (abs_var, manhattan_distance_var etc.), die mathematische Operationen für den Solver kapseln. | Kalt |
| build_and_solve_cp | DAS HERZSTÜCK. Hier wird das gesamte CP-SAT-Modell mit allen Variablen, Constraints und der Zielfunktion zusammengebaut. Änderungen hier erfordern tiefes Verständnis von Constraint Programming. | Warm |
| search_max_rho_advanced | Implementiert die übergeordnete Lösungsstrategie (Bisektionssuche). Die Logik hier ist komplex, aber meist stabil. | Kalt |
| Validierung & Export | Funktionen zur Überprüfung der Lösung (validate_solution_advanced) und zum Speichern der Ergebnisse in .png und .json. | Kalt |
| CLI & main | Definiert die Kommandozeilenschnittstelle mit argparse. Erweiterungen für neue Parameter finden hier statt. | Warm |
3. ✍️ Programmierrichtlinien und Code-Konventionen
Jede Zeile Code muss höchsten Qualitätsstandards genügen.
3.1. Allgemeine Konventionen
 * Sprache: Alle neuen Kommentare, Docstrings und Variablennamen müssen auf Deutsch verfasst sein, um die Konsistenz zu wahren.
 * Stil: PEP 8 ist Gesetz. Die maximale Zeilenlänge beträgt 88 Zeichen, was durch black erzwungen wird.
 * Type Hinting: Alle neuen Funktionen, Methoden und Variablen müssen vollständig und strikt mit Python 3.9+ Type Hints versehen werden. Dies wird durch mypy überprüft.
 * Namenskonventionen:
   * W_SCHLANGEN_SCHRIFT_UPPERCASE für Gewichte der Zielfunktion.
   * KONSTANTE_UPPERCASE für globale Konstanten.
   * _vars Suffix für Listen von CP-SAT-Modellvariablen (z.B. x_vars).
   * _val Suffix für den extrahierten Wert einer gelösten Variable (z.B. x_val).
   * ClassNamesInPascalCase.
   * funktionen_und_variablen_in_snake_case.
3.2. Kommentare und Dokumentation
 * Qualität vor Quantität: Kommentare müssen das "Warum" und die Absicht hinter einer Code-Zeile erklären, nicht das "Was".
   * Schlecht: model.Add(x > 5) # Setze x größer als 5
   * Gut: model.Add(x > 5) # Stellt sicher, dass der Raum einen Sicherheitsabstand von 5 Einheiten zum Rand einhält.
 * Docstrings: Jede Funktion und Klasse muss einen Docstring im Google-Stil haben, der Parameter, Rückgabewerte und die allgemeine Funktion beschreibt.
3.3. CP-SAT Modellierungs-Richtlinien
 * Klarheit: Verwenden Sie aussagekräftige Namen für Ihre CP-SAT-Variablen. Z.B. raum_ist_links_vom_korridor_b statt b1.
 * Indikatorvariablen: Für bedingte Logik, erstellen Sie immer eine dedizierte BoolVar und verknüpfen Sie sie mit dem Zustand. Nutzen Sie .OnlyEnforceIf() anstelle von arithmetischen Tricks mit großen Zahlen.
 * Reifikation: Wenn eine logische Implikation in beide Richtungen gilt (A \\iff B), modellieren Sie beide Richtungen (A \implies B und B \\implies A) explizit, um die Propagation des Solvers zu verbessern.
 * Domänen-Reduktion: Definieren Sie die kleinstmöglichen, aber korrekten Domänen (untere/obere Schranken) für jede IntVar. Je enger die Domäne, desto schneller die Lösung.
 * Skalierung: Die Gewichte in der Zielfunktion müssen ganzzahlig (integer) sein. Skalieren Sie float-basierte Boni entsprechend (z.B. int(bonus * 1000)), um Präzisionsverluste zu vermeiden.
4. 🔬 Test-, Validierungs- und Qualitätsstrategie
Dieses Projekt verfolgt eine vierstufige Qualitätsstrategie, die von jeder Code-Änderung durchlaufen werden muss.
Stufe 1: Statische Analyse (Vor-Commit-Prüfung)
Diese Tools fangen Fehler ab, bevor der Code überhaupt ausgeführt wird.
 * isort: Sortiert Importe automatisch.
 * black: Formatiert den Code kompromisslos und einheitlich.
 * flake8: Prüft auf logische Fehler, ungenutzte Variablen und Stilverletzungen (über PEP 8 hinaus).
 * pylint: Führt eine noch tiefere Analyse durch und sucht nach "Code Smells", Design-Problemen und potenziellen Bugs.
 * mypy: Überprüft die Korrektheit der statischen Typ-Annotationen.
Stufe 2: Funktionaler Selbsttest (Rauchtest)
Ein schneller Test, um sicherzustellen, dass das Modell noch grundsätzlich lösbar ist und keine Laufzeitfehler auftreten.
python mad_games_tycoon_2_planer.py --selftest

 * Erwartung: Der Befehl muss ohne Fehler durchlaufen. Die Ausführung sollte ca. 2-5 Minuten dauern. Am Ende muss eine FEASIBLE oder OPTIMAL Lösung mit einer plausiblen Nutzungsrate (>40%) gemeldet werden.
Stufe 3: Logische Lösungsvalidierung (In-Code-Prüfung)
Die Funktion validate_solution_advanced(sol) prüft eine gefundene Lösung auf die Einhaltung der harten Spielregeln. Eine KI, die das Modell ändert, muss ihre Testläufe durch diese Funktion validieren lassen und sicherstellen, dass all_valid True zurückgibt.
Stufe 4: Analytische & Visuelle Überprüfung (Ergebnis-Review)
Die endgültige Beurteilung der Qualität erfolgt durch die Analyse der Ausgabedateien (.png, .json).
 * Visuell (.png): Wirkt das Layout sinnvoll? Sind die wichtigen Räume (z.B. Entwicklung, QA) nahe beieinander? Ist die Symmetrie erkennbar?
 * Analytisch (.json): Entsprechen die Metriken (Nutzungsrate, Adjazenz-Score, etc.) den Erwartungen, die durch die Code-Änderung intendiert waren?
5. 🤖 Programmatische Kontrollroutinen
Vor jedem Commit oder Pull Request müssen die folgenden Befehle in exakt dieser Reihenfolge ausgeführt werden. Ein Scheitern bei einem der Schritte bedeutet, dass der Code überarbeitet werden muss.
#!/bin/bash
# Strenges Fehler-Handling
set -e
set -o pipefail

# Definiere die Zieldatei
TARGET_FILE="mad_games_tycoon_2_planer.py"

echo "===== STUFE 1: FORMATIERUNG & IMPORTE ====="
isort ${TARGET_FILE}
black ${TARGET_FILE}
echo "Formatierung abgeschlossen."

echo -e "\n===== STUFE 2: STATISCHE CODE-ANALYSE ====="
echo "--- Flake8 ---"
flake8 ${TARGET_FILE}
echo "--- Pylint (Score >= 9.0 benötigt) ---"
# Deaktiviere C0103 (invalid-name), da wir eigene Konventionen haben
pylint --disable=C0103 ${TARGET_FILE} || echo "Pylint hat Probleme gefunden."
echo "--- MyPy (strikte Typprüfung) ---"
mypy --strict ${TARGET_FILE}
echo "Statische Analyse erfolgreich."

echo -e "\n===== STUFE 3: FUNKTIONALER SELBSTTEST ====="
python ${TARGET_FILE} --selftest
echo "Selbsttest erfolgreich abgeschlossen."

echo -e "\n✅ ALLE KONTROLLROUTINEN ERFOLGREICH DURCHLAUFEN."

6. 🚀 Beitrags- und Pull-Request-Prozess
Jeder Beitrag, ob von Mensch oder KI, muss diesem formalen Prozess folgen.
 * Fokus: Ein Pull Request (PR) behandelt genau ein logisches Thema (z.B. "Refactoring der Tür-Logik", "Hinzufügen eines Kompaktheits-Bonus").
 * Titel: Der PR-Titel muss präzise sein und ein Präfix verwenden:
   * Feature: für neue Funktionalität.
   * Fix: für Fehlerbehebungen.
   * Refactor: für Code-Umbau ohne Funktionsänderung.
   * Docs: für Änderungen an Dokumentation oder Kommentaren.
   * Tuning: für Anpassungen an den Gewichten der Zielfunktion.
 * Beschreibung: Die PR-Beschreibung ist obligatorisch und muss folgende Abschnitte enthalten:
   * Problembeschreibung: Welches Problem wird mit diesem PR gelöst?
   * Lösungsansatz: Wie wurde das Problem technisch gelöst? (z.B. "Ein neuer Constraint wurde hinzugefügt, der ...")
   * Testergebnisse: Eine Zusammenfassung der durchgeführten Tests. Es muss explizit bestätigt werden, dass alle Kontrollroutinen aus Sektion 5 erfolgreich waren.
 * Artefakte: Bei Änderungen, die das Layout beeinflussen, muss dem PR eine Beispiel-Ausgabe angehängt werden:
   * Das generierte _OptimalLayout.png.
   * Die generierte _OptimalLayout.json.

## Dokumentations-Update v2.2
- Known Issues: Alle 7 kritischen Fehler behoben (v2.2)
- Parameters: ρ-Bereich: 0.20-0.35, MIN_SPACING: 5
- Testing: Neue Testsequenz: --rho_lo 0.20 --rho_hi 0.32
