# Arc-Flow: der Graph statt der Muster – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-arc-flow-demo.streamlit.app/)**

Stück 5 (gelb) der Konzepte-Reihe **„Packen: Reihenfolge und Platzierungsregel“** für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (ein Verfahren mit wachsendem Beispiel: eine Packung entsteht aus einer Reihenfolge der Teile und einer Regel, wohin das nächste kommt; der zweite Faden ist die Schranke). Stück 2 und 4 haben mit den Schranken L1, L2 und dem LP gefragt, ob FFD optimal ist. Diese Demo liefert das **Optimum selbst**: mit dem Arc-Flow-Modell, einem Fluss in einem Graphen über die Lasten 0 bis C, und fragt, wie klein die **Graphkompression** den Graphen macht und wie oft das Optimum damit bestimmbar ist.

## Warum dieses Problem

Ein Muster ist eine Teilmenge von Paketen, die in einen Container passt; es gibt sehr viele. Der Arc-Flow zählt sie nicht auf: Ein Container ist ein Weg von 0 nach C in einem Graphen, jedes Paket ein Bogen, und der kleinste Fluss ist die Zahl der Container. Der Graph wird nur dann klein genug, wenn man ihn komprimiert: Die Demo zeigt an fünf Beispielen und an 900 Rasterinstanzen, wie viel das spart (der geordnete Graph behält 2 bis 20 % der Bögen des vollen), dass das ganzzahlige Programm im Zeitlimit **alle** Instanzen entscheidet, auch die acht, die Stück 4 offen ließ, und dass die Kompression nebenbei den LP-Wert verändert.

## Modell

Ganzzahlige Paketgrößen, eine Sorte Container mit Kapazität C, alle Pakete vorab bekannt. **Graph:** Knoten sind Lasten; ein Bogen (u, u + w) steht für ein Paket der Größe w bei der Last u; Verlustbögen füllen bis C auf; ein Rückbogen von C nach 0 zählt die Container. **Fluss:** Erhaltung in jedem Knoten; für jede Größe mindestens so viele Bögen, wie es Pakete dieser Größe gibt; gesucht ist der kleinste Fluss z. Mit reellen Flüssen ist z eine Schranke (der LP-Wert), mit ganzen Flüssen das Optimum (`scipy.optimize.milp`, HiGHS). **Drei Stufen der Kompression:** *voll* (alle Lasten 0 bis C, jeder Bogen an jedem Knoten, Verlustbögen von u nach u + 1), *normal* (nur Lasten, die als Summe von Paketen vorkommen, jede Größe höchstens so oft, wie es sie gibt; Verlustbögen von jedem Knoten nach C), *geordnet* (wie normal, aber ein Bogen der Größe w beginnt nur an Lasten aus Paketen mit Größe mindestens w: jedes Muster hat einen Weg mit absteigenden Größen). **Packung:** Der ganzzahlige Fluss wird in Wege zerlegt, jeder Weg ist ein Container. **Vergleich:** FFD, L1 und L2 aus Stück 2, der LP von Stück 4 (jedes Paket einzeln überdeckt) und, bis 12 Pakete, die Teilmengen-DP als unabhängiger Weg zum Optimum. **Drei Verteilungen** der Größen wie in Stück 2 und 4: *mittel* (10 bis 50 % der Kapazität), *groß* (20 bis 80 %), *breit* (1 bis 90 %). Formeln im Expander 📐 der App.

## Methodik

- **Kern** (`arf_algorithm.py`): `gruppen`, `graph` (die drei Stufen), `groesse_voll`, `loese` (LP und ganzzahliges Programm, mit Zeitlimit), `wege` und `packung_aus_fluss` (Flusszerlegung), `loesung_pruefen` (unabhängiger Prüfer des Flusses), dazu FFD, L1, L2, `optimum_dp` und `lp_muster` (der LP von Stück 4).
- **Beispiele:** das kleine Beispiel (4, 4, 4, 4, 3) bei Kapazität 10, die Beispiele 2 bis 4 aus Stück 4 (zwölf Pakete, Kapazität 100) und eines mit nur vier verschiedenen Größen; dazu eine Zufallsinstanz mit 6 bis 20 Paketen. Die App löst live, zeichnet den Graphen mit dem Fluss (bei mehr als 600 Bögen nur die Bögen mit Fluss) und die Packung.
- **Messraster:** drei Verteilungen × Paketzahlen 12, 20 und 30 × **100 feste Instanzen** je Zelle, Kapazität 1000, **dieselben Instanzen wie in Stück 2 und 4**. Je Instanz: Knoten und Bögen je Stufe, das Optimum (ganzzahliges Programm der Stufe geordnet, 60 Sekunden Zeitlimit), der Ausgang gegen FFD und die Schranken, die LP-Werte der Stufen normal und geordnet gegen den LP von Stück 4. Die Stufe voll ist als LP im Raster nicht gerechnet: Bei Kapazität 1000 hat sie bis zu 20 000 Bögen. Die Summen stehen als ganze Zahlen in `arf_precomputed.json` (erzeugt von `generate_precomputed.py`).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an den Instanzen dieser Demo (feste Seeds), nachgerechnet in `tests/test_claims.py`, `tests/test_algorithm.py` und `tests/test_oracle_arc_flow.py`. „Ausgang“ heißt wie in Stück 4: bewiesen durch L1, durch L2, durch den aufgerundeten LP-Wert, FFD optimal, aber nur das ganzzahlige Programm zeigt es, oder FFD verliert.

| Frage | Befund |
|---|---|
| Kleines Beispiel (4, 4, 4, 4, 3), Kapazität 10 | Der Graph hat voll 11 Knoten und 25 Bögen, normal 6 und 11, geordnet 6 und 10. Der Arc-Flow-LP ist in allen Stufen **2,25**, der LP von Stück 4 **2,5**, das Optimum **3** (= FFD); L1 und L2 sagen 2, erst der aufgerundete LP-Wert beweist FFD |
| Beispiel 4 (zwölf Pakete aus Stück 4) | FFD braucht 6 Container, der Arc-Flow findet und beweist **5** (L1 und L2 sagen ebenfalls 5) |
| Wie klein wird der Graph? | Im Mittel über die 100 Instanzen einer Zelle behält die Stufe geordnet **2 bis 20 %** der Bögen und **5 bis 63 %** der Knoten des vollen Graphen (Kapazität 1000; einzelne Instanzen 0,5 bis 33 % und 1 bis 91 %); die Ordnung der Größen behält 38 bis 67 % der Bögen der Stufe normal (die Knoten sind in beiden Stufen dieselben) |
| Wovon hängt das ab? | Am stärksten bei großen Teilen mit 12 Paketen (2 % der Bögen, 5 % der Knoten), am schwächsten bei mittleren Teilen mit 30 Paketen (20 % der Bögen, 63 % der Knoten; breit gestreute Teile mit 30 Paketen ähnlich: 17 % und 63 %): Dort liegen die Summen von Paketen vermutlich dicht (nicht getrennt gemessen) |
| Wie oft ist das Optimum bestimmbar? | Das ganzzahlige Programm entscheidet **alle 900** Rasterinstanzen im Zeitlimit von 60 Sekunden (auf dem Rechner des Autors; in einem Nachlauf brauchte eine einzelne Instanz 58 Sekunden, das Limit ist also knapp). Die **acht** Instanzen, die Stück 4 offen ließ (sieben bei mittleren Teilen mit 30 Paketen, eine bei breit gestreuten), sind hier alle „FFD verliert“ |
| Wie oft verliert FFD? | In **63 von 900** Instanzen: mittlere Teile 8 / 19 / 29, große 0 / 0 / 1, breit gestreute 0 / 3 / 3 (12 / 20 / 30 Pakete). In **keiner** der übrigen 837 Instanzen braucht es das ganzzahlige Programm, um FFD als optimal zu erkennen: Immer beweisen L1, L2 oder der aufgerundete LP-Wert es schon |
| Trifft der aufgerundete LP-Wert das Optimum? | In **900 von 900** Instanzen mit der Stufe geordnet und mit dem LP von Stück 4, in 899 mit der Stufe normal (mittlere Teile, 30 Pakete: 99 von 100) |
| Verändert die Kompression den LP-Wert? | **Ja:** Die Stufe geordnet hat in **181 von 900** Instanzen einen größeren LP-Wert als die Stufe normal. Gegenüber dem LP von Stück 4 ist sie in **347 von 900** kleiner (schwächer: Sie lässt mehr Exemplare einer Größe zu, als es gibt) und in keiner größer. Auf das aufgerundete Ergebnis wirkt es in einer Instanz: Die Stufe normal verfehlt das Optimum einmal (mittlere Teile, 30 Pakete), die Stufe geordnet nie |

**Die Beispiele** (Graphgrößen, LP-Werte der Stufen und von Stück 4, Optimum und FFD):

{{TABELLE_D}}

**Größe des Graphen** (Mittel über 100 Instanzen je Zelle, Kapazität 1000):

{{TABELLE_A}}

**Ausgänge je Zelle** (Zahl der Instanzen von 100):

{{TABELLE_B}}

**LP-Vergleiche je Zelle** (Zahl der Instanzen; „LP … = Optimum“ gilt für den aufgerundeten LP-Wert und die entschiedenen Instanzen):

{{TABELLE_C}}

## Ehrliche Grenzen

- Alle Aussagen gelten für Paketgrößen aus drei Verteilungen, Paketzahlen 12 bis 30, Kapazität 1000 im Raster (100 in den Beispielen) und nur FFD als Vergleich. Größere Instanzen und andere Verteilungen sind nicht gemessen.
- Das Optimum ist das ganzzahlige Programm mit **60 Sekunden Zeitlimit** je Instanz; die Zahl der nicht entschiedenen Instanzen hängt von der Rechenzeit ab (hier null, auf einem langsameren Rechner können es mehr sein). `generate_precomputed.py --check-opt` rechnet die Optima neu nach.
- Der **LP-Wert des Arc-Flows** ist nicht der von Stück 4: Er lässt Muster mit mehr Exemplaren einer Größe zu, als es Pakete gibt (der volle Graph beliebig viele, die komprimierten nur dort, wo Lasten zufällig zusammenfallen), und ist deshalb höchstens so groß. Die Kompression nähert ihn an. Das Optimum ändert das nicht.
- „Der aufgerundete LP-Wert trifft das Optimum“ gilt **in diesen 900 Instanzen**, nicht allgemein: In der Literatur sind Instanzen bekannt, bei denen es nicht stimmt (sehr selten und schwer zu erzeugen); in den hier gemessenen Zellen kam keine vor.
- Die **Stufe voll** ist im Raster nicht als LP gerechnet (bei Kapazität 1000 und 30 Paketen rund 20 000 bis 23 000 Bögen); live bei Kapazität 100 schon.
- Die **Spaltenerzeugung** (Column Generation), die dasselbe Muster-Modell ohne Graph löst, wird nicht erklärt; sie hat ihren Platz in der Linie Exakte Suche. Es wird keine Zahl aus der Literatur übernommen (Valério de Carvalho, Brandão und Pedroso nur als Name und Gegenstand).
- Zur **Laufzeit** der Verfahren macht die Demo keine Aussage.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

{{ANNAHMEN}}

## Verifikation

- **Kern:** die drei Stufen an einer von Hand gerechneten Mini-Instanz (fünf Pakete, Kapazität 10: Knoten und Bögen jeder Stufe einzeln aufgezählt, der Arc-Flow-LP 2,25 samt Dualzertifikat, der LP von Stück 4 2,5, Optimum 3, FFD 3, L1 und L2 2); Zerlegung des Flusses, unabhängiger Prüfer des Flusses und der Packung; die Beispiele der App mit allen Kennzahlen; Randfälle (leere Eingabe, ein Paket, Paket gleich Kapazität, lauter gleiche Größen, Kapazität 1, Zeitlimit ohne Lösung, ungültige Eingaben, Grenzen der Regler).
- **Orakel** (`tests/test_oracle_arc_flow.py`): der LP der Stufe voll gegen den LP über alle Muster mit beliebig vielen Exemplaren (Aufzählung, eigener LP-Aufruf) samt Dualzertifikat (jedes Muster höchstens 1, Summe der Preise gleich dem LP-Wert); das Optimum in jeder Stufe gegen die Teilmengen-DP; die Knoten der Stufe normal gegen alle Teilmengensummen; jede zulässige Teilmenge von Paketen hat in der Stufe geordnet einen Weg mit absteigenden Größen; die Kette LP voll ≤ normal ≤ geordnet ≤ LP von Stück 4 ≤ Optimum ≤ FFD; Skalieren, Umordnen der Pakete, Formel der Bögen der Stufe voll.
- **Messraster:** jede Zelle bei 12 Paketen frisch gerechnet, bei allen Zellen die ersten drei Instanzen einzeln (Stichprobe in der Datei); alle Zellen zusammen prüft `python generate_precomputed.py --check` (parallel, mit den gespeicherten Optima), die Optima selbst `--check-opt`. Beim Bau wurden die Ausgänge einmal mit denen von Stück 4 verglichen (892 von 900 gleich, die acht Abweichungen sind dessen nicht entschiedene Instanzen); das ist kein Test dieser Demo, getestet sind die acht Positionen und ihre Ausgänge. Jede Zahl dieser README als Textsuche (`tests/test_claims.py`).
- **Abbildungen:** Bögen als Halbkreise, Verlustbögen unter der Achse, nur Bögen mit Fluss bei großen Graphen, Balken summieren sich zu 100 % (`tests/test_visualization.py`).
- **Verdikte:** alle Zweige und Schwellen an von Hand gesetzten Werten (`tests/test_verdicts.py`).
- **Presets und Layout:** vollständig, Werte innerhalb der Reglergrenzen, erstes Preset gleich Standardeinstellung, jeder Hilfetext stimmt mit der Rechnung überein; Schnellstart oben in der Seitenleiste, fester Kopf, genau das passende Preset hervorgehoben (`tests/test_layout.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jede Auswahl in jedem Wert, Zahlenfelder an den Grenzen) und Footer-Test.
- **Tests gesamt:** {{TESTS}}.

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `arf_algorithm.py` | Kern: Graph, Arc-Flow-Modell, Flusszerlegung, FFD, Schranken, Vergleichs-LP |
| `arf_constants.py` | Beispiele, Reglerwerte, Raster, Farben, Presets, Text der Annahmen |
| `arf_evaluation.py` | Analyse, Verdikte, Messzellen |
| `arf_layout.py` | Fester Kopf (Stylesheet) und Tabellen auf dem Telefon |
| `arf_precomputed.json` | vorberechnete Summen, Optima, Ausgänge und Stichprobe des Messrasters |
| `arf_presets.py` | Permalink (Begrenzen), Presets (Schnellstart, aktives Preset hervorgehoben), Würfel-Button |
| `arf_scenario.py` | Instanzen: Beispiele, Zufallsinstanzen und Rasterinstanzen (dieselben Seeds wie Stück 2 und 4) |
| `arf_visualization.py` | Plotly-Abbildungen (Graph, Packung, Balken mit gesperrten Achsen) |
| `dev/cg.py` | LP von Stück 4 per Spaltenerzeugung (nur Generator und Tests, Kopie aus `lp-schranke-demo`) |
| `dev/readme_bauen.py`, `dev/readme_vorlage.md` | setzen die README aus der Vorlage, den Tabellen der Messzellen und dem Text der Annahmen zusammen |
| `generate_precomputed.py` | erzeugt `arf_precomputed.json` (Optima mit dem Arc-Flow, Raster, Stichprobe); `--check`, `--check-opt`, `--keep-opt`, `--nur-stichprobe` |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt; `scipy` für den LP und das ganzzahlige Programm) |
| `tests/` | Mini-Instanz und Handrechnung, Orakel, Randfälle, Verdikte, Presets, Layout, Abbildungen, Messraster und Zahlen der README, AppTest-Rauchtest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Spaltenerzeugung (Column Generation):** löst dasselbe Muster-Modell ohne Graph; Linie Exakte Suche.
- **Die Stufe voll als LP im Raster:** zu groß bei Kapazität 1000; live bei Kapazität 100 zeigbar.
- **Weitere Kompressionsschritte und andere Heuristiken als FFD:** nicht Gegenstand dieses Stücks.
- **Laufzeitvergleich:** hängt an der Umsetzung, keine Aussage.
- **Zahlen und Gütegarantien aus der Literatur:** keine übernommen.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und SciPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
