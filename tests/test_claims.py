"""Jede Zahl der README und der App-Texte, nachgerechnet (DEMO-PLAYBOOK §4 und §11a).

* Das vorberechnete Raster (arf_precomputed.json): jede Zelle mit 12 Paketen frisch gerechnet (mit den gespeicherten Optima), bei allen Zellen die ersten drei Instanzen einzeln (Stichprobe in der Datei);
  alle Zellen vollständig prüft `python generate_precomputed.py --check` (parallel), die Optima selbst `--check-opt`.
* Die Optima werden an allen 900 Instanzen auf Plausibilität geprüft (L1, L2 <= Optimum <= FFD) und stichprobenweise mit der Stufe normal (zweite Formulierung) nachgerechnet.
* Die Befunde der README werden aus denselben Auswertungsfunktionen wie in der App berechnet und als Text in der README gesucht.
* Der Text des Expanders „Annahmen, Grenzen und bekannte Probleme“ steht wörtlich in der README.
Dezimalzahlen stehen in der README mit Komma, in der App mit Punkt."""

import itertools
from pathlib import Path

import pytest

import arf_algorithm as A
import arf_constants as C
import arf_evaluation as ev
from arf_scenario import beispiel, raster_instanz

ROOT = Path(__file__).resolve().parent.parent
README = (ROOT / "README.md").read_text(encoding="utf-8")
ZELLEN = list(itertools.product(range(len(C.VERTEILUNGEN)), range(len(C.MESS_N))))
KLEINE_ZELLEN = [(v, ni) for v, ni in ZELLEN if C.MESS_N[ni] == 12]


def de(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",")


def alle():
    return {(v, ni): ev.zeile(v, ni) for v, ni in ZELLEN}


def _opt(v, ni):
    return ev.vorberechnet()["zellen"][ev.zelle_schluessel(v, ni)]["opt"]


def _summe(zaehler):
    return sum(z["lp"][zaehler] for z in alle().values())


def test_raster_hat_alle_zellen_und_die_parameter():
    daten = ev.vorberechnet()
    assert daten["instanzen"] == C.INSTANZEN == 100 and daten["cap"] == C.MESS_CAP == 1000 and daten["ilp_zeit"] == C.ILP_ZEIT == 60.0 and C.MESS_N == (12, 20, 30)
    assert set(daten["zellen"]) == {ev.zelle_schluessel(v, ni) for v, ni in ZELLEN} and len(ZELLEN) == 9
    assert set(daten["stichprobe"]) == set(daten["zellen"])
    for schl, z in daten["zellen"].items():
        assert len(z["opt"]) == 100 and len(z["codes"]) == 100 and set(z["codes"]) <= set(C.AUSGANG_CODES)
        assert set(daten["stichprobe"][schl]) == {str(j) for j in C.STICHPROBE_J}


@pytest.mark.parametrize("v,ni", KLEINE_ZELLEN)
def test_jede_zelle_mit_12_paketen_stimmt_mit_frischer_rechnung(v, ni):
    gespeichert = ev.vorberechnet()["zellen"][ev.zelle_schluessel(v, ni)]
    opt = gespeichert["opt"]
    frisch = ev.messzelle(v, ni, opt)
    frisch["opt"] = opt
    assert frisch == gespeichert


@pytest.mark.parametrize("v,ni", ZELLEN)
def test_stichprobe_jeder_zelle_stimmt_mit_frischer_rechnung(v, ni):
    schl = ev.zelle_schluessel(v, ni)
    daten = ev.vorberechnet()
    zelle = daten["zellen"][schl]
    for j in C.STICHPROBE_J:
        gespeichert = daten["stichprobe"][schl][str(j)]
        assert ev.messzelle(v, ni, _opt(v, ni), [j]) == gespeichert, (schl, j)
        assert gespeichert["codes"] == zelle["codes"][j]                        # die Stichprobe ist Teil der Zelle
        for st in range(3):
            assert gespeichert["bogen"][st] <= zelle["bogen"][st] and gespeichert["knoten"][st] <= zelle["knoten"][st]


@pytest.mark.parametrize("v,ni", ZELLEN)
def test_summen_sind_in_sich_stimmig(v, ni):
    z = ev.vorberechnet()["zellen"][ev.zelle_schluessel(v, ni)]
    k = C.INSTANZEN
    assert z["knoten"][0] > z["knoten"][1] == z["knoten"][2] > 0   # normal und geordnet haben dieselben Knoten
    assert z["bogen"][0] > z["bogen"][1] > z["bogen"][2] > 0
    assert z["knoten"][0] == k * (C.MESS_CAP + 1)                                  # der volle Graph hat die Lasten 0 bis C
    for name in ev.LP_ZAEHLER:
        assert 0 <= z[name] <= k
    assert z["rund_s2_opt"] <= k - z["codes"].count("U") and z["rund_item_opt"] <= k - z["codes"].count("U")
    assert z["s2_groesser_item"] == 0 and z["lp_unter_l2"] == 0


def test_optima_liegen_zwischen_den_schranken_und_ffd():
    """Für jede Instanz des Rasters: max(L1, L2) <= Optimum <= FFD; Code F/T passt zum Optimum, 'T' heißt FFD > Optimum."""
    for v, ni in ZELLEN:
        z = ev.vorberechnet()["zellen"][ev.zelle_schluessel(v, ni)]
        for j, o in enumerate(z["opt"]):
            inst = raster_instanz(v, ni, j)
            s, cap = list(inst.sizes), inst.cap
            f, a1, a2 = len(A.ffd(s, cap)), A.l1(s, cap), A.l2(s, cap)
            assert o >= 0 and max(a1, a2) <= o <= f, (v, ni, j)
            code = z["codes"][j]
            assert (code == "T") == (o < f) and (code not in "12P" or o == f)


@pytest.mark.parametrize("v", range(len(C.VERTEILUNGEN)))
def test_stichprobe_der_optima_stimmt_mit_der_stufe_normal_ueberein(v):
    """Zweite Formulierung: das ganzzahlige Programm der Stufe normal (anderer Graph) ergibt dasselbe Optimum wie das gespeicherte der Stufe geordnet."""
    for ni in range(len(C.MESS_N)):
        for j in range(2):
            inst = raster_instanz(v, ni, j)
            r = A.loese(list(inst.sizes), inst.cap, 1, True, C.ILP_ZEIT)
            assert r["status"] == "optimal" and int(round(r["wert"])) == _opt(v, ni)[j], (v, ni, j)


# --- Beispiele ------------------------------------------------------------------------------------------------------------------------------------


def _kennzahlen(i):
    b = beispiel(i)
    s = list(b.sizes)
    return {"g": A.groessen(s, b.cap), "lp": [A.loese(s, b.cap, st, False)["wert"] for st in (0, 1, 2)], "item": A.lp_muster(s, b.cap), "opt": int(round(A.loese(s, b.cap, 2, True)["wert"])),
            "ffd": len(A.ffd(s, b.cap)), "l1": A.l1(s, b.cap), "l2": A.l2(s, b.cap)}


def test_kleines_beispiel_in_der_readme():
    k = _kennzahlen(0)
    assert k["g"][0] == (11, 25) and k["g"][1] == (6, 11) and k["g"][2] == (6, 10)
    assert [round(x, 4) for x in k["lp"]] == [2.25] * 3 and round(k["item"], 4) == 2.5 and k["opt"] == 3 == k["ffd"] and k["l1"] == k["l2"] == 2
    assert "Der Graph hat voll 11 Knoten und 25 Bögen, normal 6 und 11, geordnet 6 und 10. Der Arc-Flow-LP ist in allen Stufen **2,25**, der LP von Stück 4 **2,5**, das Optimum **3** (= FFD)" in README
    assert "L1 und L2 sagen 2, erst der aufgerundete LP-Wert beweist FFD" in README and A.lp_aufgerundet(k["lp"][2]) == 3


def test_beispiel_4_in_der_readme():
    k = _kennzahlen(3)
    assert k["ffd"] == 6 and k["opt"] == 5 and k["l1"] == k["l2"] == 5
    assert "FFD braucht 6 Container, der Arc-Flow findet und beweist **5** (L1 und L2 sagen ebenfalls 5)" in README


def test_tabelle_der_beispiele_in_der_readme():
    erwartet = {0: ("11 / 25", "6 / 10", "2,25 / 2,25 / 2,25", "2,50", 3, 3), 1: ("101 / 418", "12 / 23", "10,50 / 11,00 / 11,00", "11,00", 11, 11),
                2: ("101 / 814", "77 / 274", "5,06 / 5,06 / 5,09", "5,14", 6, 6), 3: ("101 / 686", "43 / 123", "5,00 / 5,00 / 5,00", "5,00", 5, 6),
                4: ("101 / 374", "18 / 44", "4,75 / 4,75 / 4,75", "4,75", 5, 5)}
    for i, (voll, geordnet, lp, item, opt, ffd) in erwartet.items():
        b = beispiel(i)
        zeile = f"| {C.BEISPIEL_NAMEN[i]} | {b.n} | {b.cap} | {voll} | {geordnet} | {lp} | {item} | {opt} | {ffd} |"
        assert zeile in README, zeile
        k = _kennzahlen(i)
        assert f"{k['g'][0][0]} / {k['g'][0][1]}" == voll and f"{k['g'][2][0]} / {k['g'][2][1]}" == geordnet and k["opt"] == opt and k["ffd"] == ffd
        assert " / ".join(de(x) for x in k["lp"]) == lp and de(k["item"]) == item
    assert len(set(beispiel(4).sizes)) == 4
    assert "an fünf Beispielen" in README and len(C.BEISPIELE) == 5


# --- Befunde der README --------------------------------------------------------------------------------------------------------------------


def test_alle_900_instanzen_sind_entschieden_und_die_acht_von_stueck_4_verlieren():
    z = alle()
    assert sum(x["entschieden"] for x in z.values()) == 900 and sum(x["offen"] for x in z.values()) == 0
    assert all(max(_opt(*k)) > 0 and min(_opt(*k)) > 0 for k in z)
    assert "entscheidet **alle 900** Rasterinstanzen im Zeitlimit von 60 Sekunden" in README
    assert sum(len(v) for v in C.STUECK4_OFFEN.values()) == 8 and {k: len(v) for k, v in C.STUECK4_OFFEN.items()} == {"mittel|30": 7, "breit|30": 1}
    for schl, positionen in C.STUECK4_OFFEN.items():
        zelle = ev.vorberechnet()["zellen"][schl]
        for j in positionen:
            inst = raster_instanz({"mittel": 0, "groß": 1, "breit": 2}[schl.split("|")[0]], C.MESS_N.index(int(schl.split("|")[1])), j)
            assert zelle["codes"][j] == "T" and zelle["opt"][j] < len(A.ffd(list(inst.sizes), inst.cap)), (schl, j)
    assert "Die **acht** Instanzen, die Stück 4 offen ließ (sieben bei mittleren Teilen mit 30 Paketen, eine bei breit gestreuten), sind hier alle „FFD verliert“" in README
    assert [ev.vorberechnet()["zellen"]["mittel|30"]["opt"][j] for j in C.STUECK4_OFFEN["mittel|30"]] == [9, 10, 10, 9, 9, 9, 9] and ev.vorberechnet()["zellen"]["breit|30"]["opt"][51] == 10


def test_ffd_verliert_und_ffd_optimal_ohne_schranke():
    z = alle()
    verliert = {k: x["ausgang"]["ffd_verliert"] for k, x in z.items()}
    assert sum(verliert.values()) == 63 and [verliert[(0, ni)] for ni in range(3)] == [8, 19, 29] and [verliert[(1, ni)] for ni in range(3)] == [0, 0, 1] and [verliert[(2, ni)] for ni in range(3)] == [0, 3, 3]
    assert sum(x["ausgang"]["ffd_nur_ilp"] for x in z.values()) == 0
    assert "In **63 von 900** Instanzen: mittlere Teile 8 / 19 / 29, große 0 / 0 / 1, breit gestreute 0 / 3 / 3 (12 / 20 / 30 Pakete). In **keiner** der übrigen 837 Instanzen" in README and 900 - 63 == 837
    for x in z.values():
        a = x["ausgang"]
        assert a["l1"] + a["l2"] + a["lp"] + a["ffd_nur_ilp"] + a["ffd_verliert"] + a["offen"] == 100


def test_groesse_des_graphen_in_der_readme():
    z = alle()
    anteile = [round(x["bogen_anteil"]) for x in z.values()]
    knoten = [round(x["knoten_anteil"]) for x in z.values()]
    assert (min(anteile), max(anteile)) == (2, 20) and (min(knoten), max(knoten)) == (5, 63)
    ordnung = [round(100 * x["bogen"][2] / x["bogen"][1]) for x in z.values()]
    assert (min(ordnung), max(ordnung)) == (38, 67)
    assert all(x["knoten"][1] == x["knoten"][2] for x in z.values())
    assert "Die Stufe geordnet behält **2 bis 20 %** der Bögen und **5 bis 63 %** der Knoten des vollen Graphen (Kapazität 1000); die Ordnung der Größen behält 38 bis 67 % der Bögen der Stufe normal" in README
    assert (round(z[(1, 0)]["bogen_anteil"]), round(z[(1, 0)]["knoten_anteil"])) == (2, 5) and (round(z[(0, 2)]["bogen_anteil"]), round(z[(0, 2)]["knoten_anteil"])) == (20, 63)
    assert (round(z[(2, 2)]["bogen_anteil"]), round(z[(2, 2)]["knoten_anteil"])) == (17, 63) and max(anteile) == round(z[(0, 2)]["bogen_anteil"]) and min(anteile) == round(z[(1, 0)]["bogen_anteil"])
    assert "Am stärksten bei großen Teilen mit 12 Paketen (2 % der Bögen, 5 % der Knoten), am schwächsten bei mittleren Teilen mit 30 Paketen (20 % der Bögen, 63 % der Knoten; breit gestreute Teile mit 30 Paketen ähnlich: 17 % und 63 %)" in README


def test_lp_werte_in_der_readme():
    z = alle()
    assert sum(x["lp"]["rund_s2_opt"] for x in z.values()) == 900 and sum(x["lp"]["rund_item_opt"] for x in z.values()) == 900 and sum(x["lp"]["rund_s1_opt"] for x in z.values()) == 899
    assert z[(0, 2)]["lp"]["rund_s1_opt"] == 99 and all(x["lp"]["rund_s1_opt"] == 100 for k, x in z.items() if k != (0, 2))
    assert "In **900 von 900** Instanzen mit der Stufe geordnet und mit dem LP von Stück 4, in 899 mit der Stufe normal (mittlere Teile, 30 Pakete: 99 von 100)" in README
    assert _summe("s1_kleiner_s2") == 181 and _summe("s2_kleiner_item") == 347 and _summe("s2_groesser_item") == 0
    assert "Die Stufe geordnet hat in **181 von 900** Instanzen einen größeren LP-Wert als die Stufe normal. Gegenüber dem LP von Stück 4 ist sie in **347 von 900** kleiner" in README
    assert "in keiner größer. Auf das aufgerundete Ergebnis wirkt es in einer Instanz: Die Stufe normal verfehlt das Optimum einmal (mittlere Teile, 30 Pakete), die Stufe geordnet nie" in README


def test_grenze_des_aufgerundeten_lp_steht_in_der_readme():
    assert "gilt **in diesen 900 Instanzen**, nicht allgemein" in README and _summe("rund_s2_opt") == 900 and _summe("rund_item_opt") == 900


def test_lp_ist_nie_groesser_als_der_lp_von_stueck_4_und_der_aufgerundete_wert_nie_unter_l2():
    """Der LP der Stufe geordnet liegt nie über dem LP von Stück 4 (900 von 900), der aufgerundete Wert nie unter L2."""
    assert _summe("s2_groesser_item") == 0 and _summe("lp_unter_l2") == 0 and _summe("lp_ueber_l2") == 66


def test_tabellen_der_readme_kommen_aus_den_summen():
    import importlib.util

    spec = importlib.util.spec_from_file_location("readme_bauen", ROOT / "dev" / "readme_bauen.py")
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    for tabelle in modul.tabellen():
        assert tabelle in README
    assert README.count("| mittel | 12 |") == 3 and README.count("| breit | 30 |") == 3


def test_annahmen_text_steht_woertlich_in_der_readme():
    assert C.ASSUMPTIONS_MARKDOWN in README


def test_readme_hat_testzahl_und_keine_platzhalter():
    assert "TESTZAHL" not in README and "{{" not in README
    assert "Tests gesamt:" in README
