"""Abbildungen: Der Graph zeichnet alle Bögen, bei großen Graphen nur die mit Fluss; die Bögen sind Halbkreise über (Verlust: unter) der Lastachse; die Balken zeigen die Zahlen, die sie zeigen sollen."""

import pytest

import arf_algorithm as A
import arf_constants as C
import arf_evaluation as ev
import arf_visualization as V


def farben(sizes):
    return {w: C.GROESSEN_FARBEN[k % len(C.GROESSEN_FARBEN)] for k, (w, _b) in enumerate(A.gruppen(sizes))}


def test_bogenlinien_sind_halbkreise_mit_luecken(mini):
    xs, ys = V._bogen_linien([(0, 4, 4)], 0.5, 4)
    assert xs[:5] == [0.0, 1.0, 2.0, 3.0, 4.0] and xs[5] is None and ys[5] is None
    assert ys[0] == pytest.approx(0.0, abs=1e-12) and ys[2] == pytest.approx(0.5 * 4 * 1.0) and ys[4] == pytest.approx(0.0, abs=1e-9)           # Höhe 0,5 mal Länge in der Mitte
    xs, ys = V._bogen_linien([(7, 10, 0)], 0.5, 2)
    assert ys[1] == pytest.approx(-0.5 * 3 * 1.0)                                          # Verlustbögen liegen unter der Achse


def test_graph_zeichnet_alle_boegen_bei_kleinem_graphen(mini):
    r = A.loese(list(mini.sizes), 10, 2, True)
    fig = V.build_graph(r["knoten"], r["bogen"], r["fluss"], 10, farben(list(mini.sizes)))
    linien = [t for t in fig.data if t.mode == "lines"]
    dick = [t for t in linien if t.line.width == 3]
    blass = [t for t in linien if t.line.width == 1]
    assert dick and blass                                                                  # Bögen mit und ohne Fluss
    punkte = [t for t in fig.data if t.mode == "markers"]
    assert len(punkte) == 1 and list(punkte[0].x) == r["knoten"]
    gezeichnet = sum(1 for t in linien for x in t.x if x is None)
    assert gezeichnet == len(r["bogen"])                                                  # jeder Bogen genau eine Linie (eine Lücke je Bogen)
    namen = {t.name for t in dick}
    assert namen <= {"Verlust", "Größe 4", "Größe 3"}


def test_graph_zeichnet_bei_grossen_graphen_nur_boegen_mit_fluss():
    a = ev.analyse(ev.Settings(2, 0, 12, 7, 0))                                           # Beispiel 3, voller Graph: 814 Bögen
    assert len(a.bogen) > C.ZEICHEN_MAX
    fig = V.build_graph(a.knoten, a.bogen, a.fluss, a.inst.cap, farben(list(a.inst.sizes)))
    linien = [t for t in fig.data if t.mode == "lines"]
    assert all(t.line.width == 3 for t in linien)
    gezeichnet = sum(1 for t in linien for x in t.x if x is None)
    assert gezeichnet == sum(1 for f in a.fluss if f > 0.5) and 0 < gezeichnet < len(a.bogen)


def test_graph_ohne_fluss_und_leerer_graph_werfen_nicht():
    kn, bg = A.graph([4, 3], 10, 2)
    fig = V.build_graph(kn, bg, None, 10, farben([4, 3]))
    assert all(t.line.width == 1 for t in fig.data if t.mode == "lines")
    fig = V.build_graph([0, 10], [], None, 10, {})
    assert len(fig.data) == 1


def test_container_abbildung_stapelt_die_pakete(mini):
    r = A.loese(list(mini.sizes), 10, 2, True)
    bins = A.packung_aus_fluss(list(mini.sizes), r["bogen"], r["fluss"], 10)
    fig = V.build_container(list(mini.sizes), bins, 10)
    balken = [t for t in fig.data if t.type == "bar"]
    assert len(balken) == max(len(b) for b in bins) + 1                                  # eine Schicht je Paketposition und der freie Platz
    assert sum(sum(t.y) for t in balken) == 10 * len(bins)                               # Pakete und freier Platz füllen jeden Container genau bis zur Kapazität


def test_groessen_balken_zeigen_knoten_und_boegen_je_stufe(mini):
    fig = V.build_groessen(A.groessen(list(mini.sizes), 10))
    assert [t.name for t in fig.data] == ["Knoten", "Bögen"] and list(fig.data[0].y) == [11, 6, 6] and list(fig.data[1].y) == [25, 11, 10]
    assert list(fig.data[0].x) == ["voll", "normal", "geordnet"] and fig.layout.yaxis.type == "log" and fig.layout.xaxis.fixedrange and fig.layout.yaxis.fixedrange


def test_raster_balken_haben_je_zelle_einen_balken():
    zeilen = [ev.zeile(0, k) for k in range(3)]
    fig = V.build_raster_groesse(zeilen)
    assert len(fig.data) == 3 and all(len(t.x) == 3 for t in fig.data) and list(fig.data[2].x) == ["n = 12", "n = 20", "n = 30"]
    fig = V.build_raster_ausgang(zeilen)
    assert len(fig.data) == 6 and fig.layout.barmode == "stack"
    for k in range(3):
        assert sum(t.y[k] for t in fig.data) == pytest.approx(100.0)                      # alle Ausgänge zusammen 100 %
