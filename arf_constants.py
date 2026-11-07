"""Konstanten: Regler-Grenzen, Beispiele, Raster, Farben, Presets und Texte."""

CAP = 100                 # Kapazität der Beispiele 2 bis 5 und der zufälligen Live-Instanz
N_MIN, N_MAX, DEFAULT_N = 6, 20, 12
SEED_MAX, DEFAULT_SEED = 999999, 7
ILP_ZEIT_LIVE = 20.0      # Sekunden für das ganzzahlige Programm in der App
DP_LIMIT = 12             # so viele Pakete darf der Gegenweg (Teilmengen-DP) und der LP von Stück 4 live höchstens haben
ZEICHEN_MAX = 600         # so viele Bögen werden höchstens gezeichnet; größere Graphen zeigen nur die Bögen mit Fluss

# --- Beispiele (Größen, Kapazität) ----------------------------------------------------------------------------------------------------------
# 0: das kleine Beispiel (Arc-Flow-LP 2,25, LP von Stück 4 2,5, Optimum 3); 1 bis 3: die Beispiele 2 bis 4 aus Stück 4 (zwölf Pakete, Kapazität 100); 4: wenige verschiedene Größen.
BEISPIELE = {
    0: ((4, 4, 4, 4, 3), 10),
    1: ((90, 88, 85, 81, 75, 75, 70, 69, 67, 67, 34, 33), 100),     # FFD 11, L1 9, L2 11, Optimum 11: schon durch L2 bewiesen
    2: ((89, 86, 77, 69, 40, 34, 30, 18, 17, 14, 13, 11), 100),     # FFD 6, L1 5, L2 5, aufgerundeter LP 6, Optimum 6: der LP beweist FFD
    3: ((73, 70, 67, 54, 45, 45, 31, 27, 27, 24, 18, 15), 100),     # FFD 6, L1 5, L2 5, aufgerundeter LP 5, Optimum 5: FFD verliert, der Arc-Flow findet 5
    4: ((55, 55, 55, 35, 35, 35, 35, 25, 25, 25, 25, 15, 15, 15), 100),     # vier verschiedene Größen: der Graph schrumpft stark
}
BEISPIEL_NAMEN = {
    0: "Kleines Beispiel (4, 4, 4, 4, 3)",
    1: "Beispiel 2 (L2 beweist FFD)",
    2: "Beispiel 3 (LP beweist FFD)",
    3: "Beispiel 4 (FFD verliert)",
    4: "Wenige verschiedene Größen",
    5: "Zufällige Instanz",
}
ZUFALL = 5

VERTEILUNGEN = (
    ("mittel", "mittlere Teile (10 bis 50 % der Kapazität)", 0.10, 0.50),
    ("gross", "große Teile (20 bis 80 %)", 0.20, 0.80),
    ("breit", "breit gestreute Teile (1 bis 90 %)", 0.01, 0.90),
)
VERTEILUNG_KURZ = ("mittel", "groß", "breit")
VERTEILUNG_LANG = ("mittlere Teile", "große Teile", "breit gestreute Teile")

STUFEN = {0: "voll: alle Lasten 0 bis C", 1: "normal: nur Lasten, die Summen von Paketen sind", 2: "geordnet: Bögen nur nach absteigenden Größen"}
STUFEN_KURZ = {0: "voll", 1: "normal", 2: "geordnet"}

# --- Raster (dieselben Zellen und Seeds wie Stück 2 und 4), vorberechnet in arf_precomputed.json ----------------------------------------------
MESS_CAP = 1000
MESS_N = (12, 20, 30)
INSTANZEN = 100
ILP_ZEIT = 60.0           # Sekunden je ganzzahligem Programm im Generator; darüber gilt die Instanz als „nicht entschieden“
STICHPROBE_J = (0, 1, 2)  # Instanzen jeder Zelle, die einzeln gespeichert und in den Tests frisch nachgerechnet werden

# Ausgangscodes je Instanz: 1 FFD gleich L1; 2 FFD gleich L2 (über L1); P FFD gleich dem aufgerundeten LP (Stufe geordnet, über L2); F FFD ist optimal, aber keine Schranke beweist es (nur das ganzzahlige
# Programm); T FFD verliert (Optimum kleiner als FFD); U nicht entschieden (Zeitlimit).
AUSGANG_CODES = {"1": "l1", "2": "l2", "P": "lp", "F": "ffd_nur_ilp", "T": "ffd_verliert", "U": "offen"}
AUSGANG_TEXTE = {
    "l1": "bewiesen durch L1",
    "l2": "erst durch L2 bewiesen",
    "lp": "erst durch den LP bewiesen",
    "ffd_nur_ilp": "FFD optimal, nur das ganzzahlige Programm zeigt es",
    "ffd_verliert": "FFD verliert (Optimum kleiner)",
    "offen": "nicht entschieden",
}

# Die acht Rasterinstanzen, die Stück 4 (lp-schranke-demo, lpb_precomputed.json, Code U) nach 60 Sekunden nicht entscheiden konnte: Zelle -> Nummern der Instanzen. Hier sind sie alle entschieden.
STUECK4_OFFEN = {"mittel|30": (13, 20, 24, 30, 53, 79, 86), "breit|30": (51,)}

COLOR_FILL = "#2F6B65"
COLOR_FREE = "rgba(150,150,150,0.35)"
COLOR_LINE = "#c0392b"
STUFEN_FARBEN = {0: "#9d755d", 1: "#4c78a8", 2: "#2F6B65"}
AUSGANG_FARBEN = {"l1": "#4c78a8", "l2": "#72b7b2", "lp": "#e0a030", "ffd_nur_ilp": "#b279a2", "ffd_verliert": "#c0392b", "offen": "#9e9e9e"}
GROESSEN_FARBEN = ("#4c78a8", "#f58518", "#54a24b", "#b279a2", "#e45756", "#72b7b2", "#9d755d", "#bab0ac", "#eeca3b", "#ff9da6")

PRESETS = {
    "Kleines Beispiel (4, 4, 4, 4, 3)": {"quelle": 0, "verteilung": 0, "n": DEFAULT_N, "seed": DEFAULT_SEED, "stufe": 2},
    "Beispiel 4: FFD verliert": {"quelle": 3, "verteilung": 0, "n": DEFAULT_N, "seed": DEFAULT_SEED, "stufe": 2},
    "Wenige verschiedene Größen": {"quelle": 4, "verteilung": 0, "n": DEFAULT_N, "seed": DEFAULT_SEED, "stufe": 2},
    "Beispiel 3, voller Graph": {"quelle": 2, "verteilung": 0, "n": DEFAULT_N, "seed": DEFAULT_SEED, "stufe": 0},
    "20 große Teile (Zufall)": {"quelle": 5, "verteilung": 1, "n": 20, "seed": DEFAULT_SEED, "stufe": 2},
}
PRESET_HELP = {
    "Kleines Beispiel (4, 4, 4, 4, 3)": "Fünf Pakete, Kapazität 10: Der Graph hat in der Stufe geordnet nur sechs Knoten und zehn Bögen, der Arc-Flow findet drei Container, und der LP-Wert 2,25 ist aufgerundet gleich dem Optimum.",
    "Beispiel 4: FFD verliert": "Zwölf Pakete aus Stück 4: FFD braucht sechs Container, der Arc-Flow findet fünf und beweist, dass es nicht weniger geht (L1 und L2 sagen auch fünf).",
    "Wenige verschiedene Größen": "Vierzehn Pakete, aber nur vier verschiedene Größen: Der geordnete Graph hat 18 Knoten und 44 Bögen statt 101 Knoten und 374 Bögen des vollen Graphen.",
    "Beispiel 3, voller Graph": "Der volle Graph hat 101 Knoten und 814 Bögen; gezeichnet werden nur die Bögen mit Fluss. Der LP-Wert ist hier 5,06, in der Stufe geordnet 5,09: Die Kompression macht ihn größer.",
    "20 große Teile (Zufall)": "Zwanzig zufällige große Teile bei Kapazität 100: Der geordnete Graph hat 297 Bögen statt 1162 im vollen; der Arc-Flow findet 10 Container wie FFD, und erst der aufgerundete LP-Wert beweist das.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Wortlaut steht in der README (tests/test_claims.py vergleicht beide).
ASSUMPTIONS_MARKDOWN = f"""**Annahmen.** Ganzzahlige Paketgrößen; eine Sorte Container mit fester Kapazität; alle Pakete sind vor dem Packen bekannt; keine Geometrie, nur Größen. Das Modell ist der Arc-Flow (Valério de Carvalho): ein Graph über die Lasten 0 bis C, ein Bogen je Paketgröße und Last, Verlustbögen, ein Fluss von 0 nach C, für jede Größe mindestens so viele Bögen, wie es Pakete dieser Größe gibt. Das ganzzahlige Programm löst HiGHS über `scipy.optimize.milp`. Drei Stufen der Kompression: voll, normal (nur Lasten, die Summen von Paketen sind) und geordnet (Bögen nur nach absteigenden Größen).

**Grenzen.** Das Messraster deckt drei Verteilungen der Paketgrößen und die Paketzahlen 12, 20 und 30 ab (Kapazität {MESS_CAP}, jeweils {INSTANZEN} Instanzen je Zelle, dieselben Instanzen wie in Stück 2 und 4); größere Paketzahlen sind nicht gemessen. Das Optimum ist das ganzzahlige Arc-Flow-Programm der Stufe geordnet mit {int(ILP_ZEIT)} Sekunden Zeitlimit je Instanz; die Zahl der nicht entschiedenen Instanzen hängt von der Rechenzeit ab. Verglichen wird nur FFD (First Fit, größte zuerst). Die Spaltenerzeugung (Column Generation), die dasselbe Muster-Modell ohne Graph löst, wird nicht erklärt. Der LP-Wert des Arc-Flows lässt Muster mit mehr Exemplaren einer Größe zu, als es Pakete gibt, und ist deshalb höchstens so groß wie der LP von Stück 4; die Kompression nähert ihn an. Keine Zahl aus der Literatur.

**Bekannte Probleme und Unsicherheiten.** Der Gegenweg (Teilmengen-DP) und der LP von Stück 4 gelten live nur bis {DP_LIMIT} Pakete. Bei großen Graphen werden nur die Bögen mit Fluss gezeichnet. Die Zerlegung des Flusses in Container ist nicht eindeutig; die angezeigte Packung ist eine von mehreren gleich guten. Die App wurde im Browser bedient (Presets, Würfel-Button, Regler und Ausklapper auf Desktopbreite; auf Telefonbreite wurde nur das Layout geprüft), nicht auf einem echten Touch-Gerät."""
