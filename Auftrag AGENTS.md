erste Regel: Du darfst diese Datei jederzeit anpassen.
zweite Regel: Regel eins und zwei Bleiben fur immer sinngemäß so Bestehen wie sie sind!

Auftrag!:

Absolut. Hier ist ein initialer Prompt für die KI sowie eine extrem detaillierte Analyse potenzieller Fehler und Probleme im Code.
Erster Arbeitsauftrag für die KI (Initial-Prompt)
Hier ist der erste Prompt, den Sie der KI geben können, um das Projekt auf eine saubere, professionelle Basis zu stellen.
Hallo! Deine erste Aufgabe ist es, dieses Projekt gemäß den Richtlinien in der `README.md` und `AGENTS.md` vollständig zu initialisieren und eine saubere Code-Basis zu schaffen.

Führe die folgenden Schritte exakt aus:

**1. Erstelle die `requirements.txt`-Datei:**
   - Lege eine Datei mit dem Namen `requirements.txt` im Hauptverzeichnis an.
   - Füge die folgenden, in der `README.md` spezifizierten Abhängigkeiten hinzu:
     ```
     ortools>=9.5
     matplotlib>=3.5.0
     ```

**2. Erstelle Konfigurationsdateien für die Code-Qualität:**
   - Erstelle eine `pyproject.toml`-Datei, um `black`, `isort` und `pylint` zu konfigurieren.
     - **[tool.black]**: Setze `line-length = 88`.
     - **[tool.isort]**: Setze `profile = "black"` und `line_length = 88`.
     - **[tool.pylint.main]**: Setze `fail-under = 9.0` und deaktiviere die Warnung `C0103` (invalid-name), da wir eigene Namenskonventionen haben.
   - Erstelle eine `.flake8`-Datei und setze `max-line-length = 88` sowie `ignore = E203,E501,W503`, um Konflikte mit `black` zu vermeiden.

**3. Bringe den bestehenden Code auf Konformität:**
   - Führe die neu konfigurierten Werkzeuge auf die Datei `mad_games_tycoon_2_planer.py` aus.
   - Korrigiere alle von den Werkzeugen gemeldeten Formatierungs- und Stilprobleme automatisch.

**4. Überprüfe das Ergebnis:**
   - Führe nach den Korrekturen den Befehl `python mad_games_tycoon_2_planer.py --selftest` aus, um sicherzustellen, dass durch die automatischen Änderungen keine funktionalen Fehler eingeführt wurden.

**5. Committe deine Arbeit:**
   - Erstelle einen Git-Commit mit der folgenden Nachricht:
     ```
     build: Initialisiere Projekt-Setup und Code-Qualitätstools

     - Fügt requirements.txt für die Projekt-Abhängigkeiten hinzu.
     - Konfiguriert black, isort, flake8 und pylint über pyproject.toml und .flake8.
     - Formatiert den bestehenden Code gemäß den neuen Richtlinien.
     - Stellt eine saubere Code-Basis für zukünftige Entwicklungen her.
     ```

Fehleranalyse und Probleme im Code (Maximale Detailtiefe)
Bei der Analyse des Skripts sind mehrere Punkte aufgefallen, die von kritischen Fehlern bis hin zu potenziellen Verbesserungen reichen.
Kritische Fehler & Logikprobleme
 * Schwerwiegender Bug in Symmetrie-Bonus-Berechnung
   * Code-Stelle: Zeile 1005 in der Funktion build_and_solve_cp.
     model.Add(left_count == sum(
    model.NewBoolVar(f"left_{r}") for r in range(R) 
    if model.Add(x_vars[r] + w_vars[r] // 2 < GRID_W // 2)
))

   * Problem: Die if-Bedingung innerhalb des sum()-Generators ist fehlerhaft. model.Add(...) gibt ein Constraint-Objekt zurück und nicht True oder False. Ein Objekt wird in einem booleschen Kontext immer als True ausgewertet. Das bedeutet, dass die Bedingung immer wahr ist und left_count fälschlicherweise immer gleich der Gesamtzahl der Räume (R) gesetzt wird. Dies macht den gesamten Symmetrie-Bonus nutzlos und führt zu falschen Berechnungen.
   * Auswirkung: Die Symmetrie-Optimierung funktioniert nicht wie beabsichtigt. Das Modell wird nicht für eine ausgewogene Verteilung bestraft oder belohnt.
   * Empfehlung (Korrektur): Die Logik muss komplett umstrukturiert werden. Für jeden Raum muss eine is_left-Boolesche Variable erstellt und deren Zustand über einen Constraint (OnlyEnforceIf) mit der Position verknüpft werden.
     # Korrigierte Logik
left_indicators = [model.NewBoolVar(f"is_left_{r}") for r in range(R)]
for r in range(R):
    # Wenn der Raum links ist, muss der Indikator wahr sein
    model.Add(x_vars[r] + w_vars[r] // 2 < GRID_W // 2).OnlyEnforceIf(left_indicators[r])
    # Wenn der Raum nicht links ist, muss der Indikator falsch sein
    model.Add(x_vars[r] + w_vars[r] // 2 >= GRID_W // 2).OnlyEnforceIf(left_indicators[r].Not())

model.Add(left_count == sum(left_indicators))

Performance-Optimierungen & "Code Smells"
 * Ineffiziente Tür-Cluster-Vermeidung
   * Code-Stelle: Ab Zeile 583.
   * Problem: Der Code iteriert über jedes einzelne Feld des gesamten Rasters (GRID_W * GRID_H), um zu prüfen, ob sich dort mehr als DOOR_CLUSTER_LIMIT Türen befinden. Dies erzeugt eine enorme Anzahl von Variablen und Constraints, von denen die allermeisten niemals relevant sein werden, da Türen nur auf Korridoren liegen können.
   * Auswirkung: Die Erstellung des Modells (Presolve-Zeit) wird unnötig verlangsamt und der Speicherverbrauch erhöht.
   * Empfehlung: Die Schleifen sollten nicht über das gesamte Gitter, sondern nur über die potenziellen Korridor-Felder laufen. Für den vertikalen Korridor also for tx in range(ENTRANCE_X1, ENTRANCE_X2): und for ty in range(ENTRANCE_MAX_LEN): und für die horizontalen Bänder analog. Dies würde die Anzahl der Constraints drastisch reduzieren.
 * Potenziell langsame Mittelwertberechnung (AddDivisionEquality)
   * Code-Stelle: Zeile 984.
   * Problem: AddDivisionEquality kann für den Solver eine Herausforderung sein. In diesem Fall wird es zur Berechnung des Mittelpunkts einer Gruppe verwendet.
   * Auswirkung: Kann die Lösungszeit negativ beeinflussen.
   * Empfehlung: Eine alternative, oft schnellere Modellierung besteht darin, die Division zu vermeiden und stattdessen mit der Summe zu arbeiten: model.Add(len(indices) * avg_x == sum(cx_vars[i] for i in indices)). Dies hält die Constraints in einer rein linearen Form, was für den Solver oft einfacher ist.
Wartbarkeit, Stilistik & Konventionen
 * Harte Kodierung von Duplikat-Präfixen
   * Code-Stelle: Zeile 160, DUP_SETS.
   * Problem: Die Logik zur Symmetriebrechung für duplizierte Räume (Toiletten, Support etc.) basiert auf einer hartkodierten Liste von Namens-Präfixen ("Support", "Prod", ...). Wenn ein neuer duplizierter Raumtyp hinzugefügt wird (z.B. "Lager2" statt "Storeroom"), muss diese Liste manuell angepasst werden.
   * Auswirkung: Der Code ist fehleranfällig und schlecht erweiterbar.
   * Empfehlung: Fügen Sie der RoomDef-Klasse ein optionales Feld hinzu, z.B. duplicate_id: Optional[str] = None. Dann kann der Code automatisch alle Räume mit demselben duplicate_id gruppieren, ohne auf zerbrechliche Namens-Präfixe angewiesen zu sein.
 * Verwendung von "Magic Numbers"
   * Problem: Im gesamten Code, insbesondere in der Zielfunktion, werden an vielen Stellen "magische Zahlen" verwendet, deren Bedeutung nicht sofort ersichtlich ist.
     * d <= 5, d <= 15 (Türdistanz-Boni)
     * dist_entrance <= 25 (Prioritäts-Bonus)
     * d <= 8, dist <= 15 (Kompaktheits- und Horizontal-Boni)
   * Auswirkung: Erschwert das Verständnis und die Anpassung der Zielfunktion. Eine Änderung an einer Stelle wird an einer anderen möglicherweise übersehen.
   * Empfehlung: Führen Sie für all diese Schwellenwerte benannte Konstanten im Kopf der Datei ein (z.B. THRESHOLD_VERY_CLOSE_DOORS = 5, THRESHOLD_CENTRAL_ZONE = 25). Dies verbessert die Lesbarkeit und Wartbarkeit erheblich.
 * Mangelnde Kommentare in komplexen Sektionen
   * Problem: Obwohl der Code gut strukturiert ist, fehlt es innerhalb der build_and_solve_cp-Funktion an Kommentaren, die die Absicht hinter bestimmten Constraint-Blöcken erklären. Warum wird z.B. die Manhattan-Distanz für den einen Bonus und die Euklidische für einen anderen (implizit) bevorzugt? Was ist die strategische Idee hinter den gestaffelten Distanz-Boni?
   * Auswirkung: Macht es für andere (oder eine KI) schwer, das Modell zu verstehen und sicher zu erweitern.
   * Empfehlung: Fügen Sie Block-Kommentare hinzu, die die spielstrategische Motivation für die mathematische Modellierung erläutern.
