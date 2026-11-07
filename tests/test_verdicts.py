"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt Zeilen, nicht Seeds. Damit prüft der Test die Grenzen und jede genannte Zahl direkt."""

import pytest

import arf_constants as C
import arf_evaluation as ev
from arf_scenario import Instance


def _a(opt=3, ffd=3, l1=2, l2=2, lp=(2.25, 2.25, 2.25), lp_item=2.5, stufe=2, beste=None, groessen=None, n=5):
    inst = Instance((4,) * (n - 1) + (3,), 10)
    g = groessen or {0: (11, 25), 1: (6, 11), 2: (6, 10)}
    return ev.Analysis(inst, stufe, g, (), (), None, "optimal" if opt is not None else "zeit", opt, opt if beste is None else beste, (), dict(zip((0, 1, 2), lp)), lp_item, opt, ffd, l1, l2, ev.Settings(stufe=stufe))


def test_aktuell_ffd_verliert_ist_ein_erfolg_und_nennt_die_schranke():
    kind, text = ev.verdict_aktuell(_a(opt=5, ffd=6, l1=5, l2=5, lp=(4.75, 4.75, 5.0)))
    assert kind == "success"
    assert text == ("Der Arc-Flow findet **5** Container und beweist, dass es nicht weniger geht. FFD braucht 6: **FFD verliert** um 1. Schon L1 beweist das. "
                    "(L1 5, L2 5, aufgerundeter LP-Wert 5.)")


def test_aktuell_ffd_optimal_nennt_die_erste_schranke_die_es_beweist():
    kind, text = ev.verdict_aktuell(_a(opt=3, ffd=3, l1=2, l2=2, lp=(2.25, 2.25, 2.25)))
    assert kind == "info" and text == ("Der Arc-Flow findet **3** Container und beweist, dass es nicht weniger geht. FFD braucht ebenfalls 3: FFD ist optimal. "
                                       "Erst der aufgerundete LP-Wert beweist das. (L1 2, L2 2, aufgerundeter LP-Wert 3.)")
    assert "Erst L2 beweist das." in ev.verdict_aktuell(_a(opt=11, ffd=11, l1=9, l2=11, lp=(10.5, 11.0, 11.0)))[1]
    assert "Schon L1 beweist das." in ev.verdict_aktuell(_a(opt=5, ffd=5, l1=5, l2=5, lp=(4.0, 4.0, 4.5)))[1]
    kind, text = ev.verdict_aktuell(_a(opt=6, ffd=6, l1=5, l2=5, lp=(5.0, 5.0, 5.2)))              # aufgerundeter LP-Wert 6 ist nicht 5: LP beweist
    assert "Erst der aufgerundete LP-Wert beweist das." in text
    kind, text = ev.verdict_aktuell(_a(opt=6, ffd=6, l1=5, l2=5, lp=(5.0, 5.0, 5.0)))              # aufgerundet 5 unter dem Optimum 6: nur das ganzzahlige Programm
    assert kind == "info" and "Keine Schranke beweist das: Nur das ganzzahlige Programm kennt das Optimum." in text


def test_aktuell_bei_zeitlimit_ist_eine_warnung_mit_der_besten_zahl():
    kind, text = ev.verdict_aktuell(_a(opt=None, ffd=7, l1=5, l2=5, lp=(5.0, 5.0, 5.0), beste=6))
    assert kind == "warning"
    assert text == ("Das ganzzahlige Programm hat nach 20 Sekunden kein Optimum bewiesen. Die beste gefundene Packung braucht 6 Container. FFD braucht 7 (L1 5, L2 5, aufgerundeter LP-Wert 5).")
    kind, text = ev.verdict_aktuell(_a(opt=None, beste=None))
    assert "Die beste gefundene" not in text


def test_beweis_durch_reihenfolge():
    assert ev.beweis_durch(5, 5, 5, 5) == "l1" and ev.beweis_durch(5, 4, 5, 5) == "l2" and ev.beweis_durch(5, 4, 4, 5) == "lp" and ev.beweis_durch(5, 4, 4, 4) == "ilp"


def test_kompressionsverdikt_nennt_die_zahlen_und_den_anteil():
    kind, text = ev.verdict_kompression(_a(groessen={0: (101, 1000), 1: (50, 400), 2: (50, 250)}))
    assert kind == "success"
    assert text == ("Der Graph der Stufe geordnet hat 50 Knoten und 250 Bögen, der volle Graph 101 Knoten und 1000 Bögen: Die Kompression behält **25 %** der Bögen und 50 % der Knoten.")
    kind, text = ev.verdict_kompression(_a(stufe=1, groessen={0: (101, 1000), 1: (50, 400), 2: (50, 250)}))
    assert "Stufe normal hat 50 Knoten und 400 Bögen" in text and "**40 %**" in text
    kind, text = ev.verdict_kompression(_a(stufe=0, groessen={0: (101, 1000), 1: (50, 400), 2: (50, 250)}))
    assert kind == "info" and text == ("Der volle Graph hat 101 Knoten und 1000 Bögen (jede Last von 0 bis 10, jede Größe an jedem Knoten); die Stufen normal und geordnet kommen mit 50 und 50 Knoten "
                                       "und 400 und 250 Bögen aus.")


def test_lp_verdikt_drei_zweige():
    kind, text = ev.verdict_lp(_a(lp=(5.0, 5.0, 5.0), lp_item=5.0))
    assert kind == "info" and text == "LP-Wert des Arc-Flows: voll 5.00, normal 5.00, geordnet 5.00; LP von Stück 4 5.00. Alle Werte sind gleich."
    kind, text = ev.verdict_lp(_a(lp=(10.5, 11.0, 11.0), lp_item=11.0))
    assert "voll 10.50, normal 11.00, geordnet 11.00; LP von Stück 4 11.00." in text and "macht den LP-Wert hier **größer** (stärker)" in text
    kind, text = ev.verdict_lp(_a(lp=(2.25, 2.25, 2.25), lp_item=2.5))
    assert "LP von Stück 4 2.50." in text and "Die drei Stufen geben denselben Wert; der LP von Stück 4 ist größer" in text
    kind, text = ev.verdict_lp(_a(lp=(5.0, 5.0, 5.0), lp_item=None))
    assert "LP von Stück" not in text and text.endswith("Alle Werte sind gleich.")


def test_instanz_code_alle_zweige():
    assert ev.instanz_code(5, 5, 5, 5, 5) == "1" and ev.instanz_code(6, 5, 6, 6, 6) == "2" and ev.instanz_code(6, 5, 5, 6, 6) == "P"
    assert ev.instanz_code(6, 5, 5, 5, None) == "U" and ev.instanz_code(6, 5, 5, 5, -1) == "U"
    assert ev.instanz_code(6, 5, 5, 5, 6) == "F" and ev.instanz_code(6, 5, 5, 5, 5) == "T"
    assert ev.instanz_code(6, 6, 6, 6, 5) == "1"                                       # FFD gleich L1 hat Vorrang (Schranke beweist, Optimum kann nicht kleiner sein)


# --- Messraster ----------------------------------------------------------------------------------------------------------------------------


def _z(knoten=(1001.0, 300.0, 300.0), bogen=(10000.0, 2000.0, 800.0), ausgang=None, lp=None, n=20, verteilung=0, offen=0):
    a = {name: 0 for name in C.AUSGANG_CODES.values()}
    a.update(ausgang or {"l1": 40, "l2": 20, "lp": 20, "ffd_nur_ilp": 5, "ffd_verliert": 15})
    a["offen"] = offen
    k = {x: 0 for x in ev.LP_ZAEHLER}
    k.update(lp or {})
    return {"verteilung": verteilung, "name": C.VERTEILUNG_LANG[verteilung], "n": n, "instanzen": 100, "knoten": list(knoten), "bogen": list(bogen), "bogen_anteil": 100 * bogen[2] / bogen[0],
            "knoten_anteil": 100 * knoten[2] / knoten[0], "ausgang": a, "entschieden": 100 - offen, "offen": offen, "lp": k}


def test_groesse_verdikt_nennt_mittel_und_anteil():
    kind, text = ev.verdict_groesse(_z())
    assert kind == "success"
    assert text == ("Für mittlere Teile mit n = 20 hat der Graph im Mittel 1001 / 300 / 300 Knoten und 10000 / 2000 / 800 Bögen (voll / normal / geordnet, 100 Instanzen): "
                    "Die geordnete Stufe behält **8 %** der Bögen und 30 % der Knoten.")
    assert ev.verdict_groesse(_z(bogen=(1000.0, 800.0, 504.0)))[0] == "success"            # auf ganze Prozent gerundet: 50 % zählen mit
    assert ev.verdict_groesse(_z(bogen=(1000.0, 800.0, 506.0)))[0] == "info"


def test_entscheidungsverdikt_mit_und_ohne_offene_instanzen():
    kind, text = ev.verdict_entscheidung(_z())
    assert kind == "success"
    assert text == ("Für mittlere Teile mit n = 20 entscheidet das ganzzahlige Programm **100** von 100 Instanzen: bewiesen durch L1 40, durch L2 20, durch den LP 20; "
                    "FFD optimal, nur das Programm zeigt es, in 5; FFD verliert in 15. Keine Instanz bleibt offen.")
    kind, text = ev.verdict_entscheidung(_z(offen=3, ausgang={"l1": 40, "l2": 20, "lp": 20, "ffd_nur_ilp": 2, "ffd_verliert": 15}, verteilung=2, n=30))
    assert kind == "warning" and "**97** von 100" in text and "3 Instanzen bleiben nach 60 Sekunden offen." in text and text.startswith("Für breit gestreute Teile mit n = 30")


def test_lp_rasterverdikt_nennt_alle_zahlen():
    lp = {"rund_s2_opt": 100, "rund_s1_opt": 98, "rund_item_opt": 100, "s1_kleiner_s2": 12, "s2_kleiner_item": 61}
    kind, text = ev.verdict_lp_raster(_z(lp=lp))
    assert kind == "success"
    assert text == ("Für mittlere Teile mit n = 20 trifft der aufgerundete LP-Wert das Optimum in 100 von 100 entschiedenen Instanzen (Stufe geordnet), in 98 (Stufe normal) und in 100 (LP von Stück 4). "
                    "Die Ordnung der Größen macht den LP-Wert in 12 von 100 Instanzen größer (normal zu geordnet); der LP der Stufe geordnet ist in 61 Instanzen kleiner als der von Stück 4. "
                    "Der aufgerundete LP-Wert verfehlt das Optimum nie.")
    kind, text = ev.verdict_lp_raster(_z(lp={**lp, "rund_s2_opt": 99}))
    assert kind == "warning" and "verfehlt das Optimum in einigen Instanzen" in text and "in 99 von 100 entschiedenen" in text


def test_zeile_rechnet_mittel_anteile_und_zaehlungen_aus_den_summen():
    zelle = {"knoten": [100100, 30000, 30000], "bogen": [1000000, 200000, 80000], "codes": "1" * 40 + "2" * 20 + "P" * 20 + "F" * 5 + "T" * 14 + "U", "opt": [3] * 100, **{x: i for i, x in enumerate(ev.LP_ZAEHLER)}}
    daten = {"instanzen": 100, "cap": 1000, "zellen": {"mittel|12": zelle}}
    z = ev.zeile(0, 0, daten)
    assert z["knoten"] == [1001.0, 300.0, 300.0] and z["bogen"] == [10000.0, 2000.0, 800.0] and z["bogen_anteil"] == 8.0 and z["knoten_anteil"] == pytest.approx(29.97, abs=0.01)
    assert z["ausgang"] == {"l1": 40, "l2": 20, "lp": 20, "ffd_nur_ilp": 5, "ffd_verliert": 14, "offen": 1} and z["entschieden"] == 99 and z["offen"] == 1 and z["n"] == 12
    assert z["lp"]["s1_kleiner_s2"] == ev.LP_ZAEHLER.index("s1_kleiner_s2")

