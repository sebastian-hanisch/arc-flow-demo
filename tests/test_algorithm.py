"""Kern an der Mini-Instanz von Hand und an den Handbeispielen der App (DEMO-PLAYBOOK §1b).

Handrechnung Mini-Instanz (Pakete 4, 4, 4, 4, 3, Kapazität 10; Gruppen: Größe 4 viermal, Größe 3 einmal):
  Stufe 0 (voll): Knoten 0 bis 10 = 11; Bögen der Größe 4 von 0 bis 6 = 7, der Größe 3 von 0 bis 7 = 8, Verlustbögen (u, u + 1) von 0 bis 9 = 10: zusammen 25.
  Stufe 1 (normal): Lasten als Summen (Größe 4 bis zu viermal, Größe 3 einmal, höchstens 10): 0, 3, 4, 7, 8 (3 + 4 = 7, 4 + 4 = 8, 3 + 4 + 4 = 11 zu groß) und der Endknoten 10: 6 Knoten.
      Bögen der Größe 4: 0 nach 4, 3 nach 7, 4 nach 8 (7 nach 11 und 8 nach 12 zu groß) = 3; der Größe 3: 0 nach 3, 4 nach 7, 7 nach 10 (3 nach 6 und 8 nach 11 fehlen) = 3; Verlustbögen
      von 0, 3, 4, 7, 8 nach 10 = 5: zusammen 11.
  Stufe 2 (geordnet): Bögen der Größe 4 nur von den Lasten aus Vieren (0, 4, 8): 0 nach 4, 4 nach 8 = 2; Bögen der Größe 3 von den Lasten aus Vieren und Dreien (0, 3, 4, 7, 8): wie in Stufe 1 = 3;
      Verlustbögen 5: zusammen 10.
  Arc-Flow-LP: Der Weg 0 - 4 - 7 - 10 hat die Größen 4, 3, und der Weg 0 - 4 - 8 - 10 die Größen 4, 4. Weil 10 ein Knoten ist, gibt es auch den Weg 0 - 4 - 7 - 10 mit den Größen 4, 3 und dem
      Bogen 7 - 10 der Größe 3 (zwei Dreien in einem Weg: ein Muster 4, 3, 3 mit nur einer vorhandenen Drei). Mit dem Muster {4, 4} (Gewicht 1,75) und {4, 3, 3} (Gewicht 0,5): Vieren 3,5 + 0,5 = 4, Dreien
      2 * 0,5 = 1: zusammen 2,25. Dual: y(4) = 0,5, y(3) = 0,25: jedes Muster hat höchstens den Wert 1 ({4,4}: 1, {4,3,3}: 1, {3,3,3}: 0,75), die Summe 4 * 0,5 + 0,25 = 2,25 beweist die Optimalität.
      Der LP von Stück 4 (jedes Paket einzeln, Muster nur Teilmengen) ist 2,5: {4,4} 1,5 und {4,3} 1.
  Optimum 3: Ein Container fasst höchstens zwei Vieren (drei wären 12). Vier Vieren brauchen also mindestens zwei Container, und mit genau zwei Containern liegen in jedem zwei Vieren (Last 8);
      die Drei passt dort nicht mehr (8 + 3 = 11): zwei Container reichen nicht, drei schon.
  FFD: 4, 4 | 4, 4 | 3: drei Container. L1 = 2, L2 = 2: nur der aufgerundete LP-Wert (3) beweist FFD optimal.
"""

import math

import pytest

import arf_algorithm as A
import arf_constants as C
from arf_scenario import beispiel


def test_gruppen_und_stufen_der_mini_instanz(mini):
    s = list(mini.sizes)
    assert A.gruppen(s) == [(4, 4), (3, 1)]
    assert A.groessen(s, 10) == {0: (11, 25), 1: (6, 11), 2: (6, 10)}
    kn0, bg0 = A.graph(s, 10, 0)
    assert (len(kn0), len(bg0)) == (11, 25) and A.groesse_voll(s, 10) == (11, 25)
    assert sum(1 for b in bg0 if b[2] == 4) == 7 and sum(1 for b in bg0 if b[2] == 3) == 8 and sum(1 for b in bg0 if b[2] == 0) == 10


def test_stufen_1_und_2_mit_allen_boegen_von_hand(mini):
    s = list(mini.sizes)
    kn1, bg1 = A.graph(s, 10, 1)
    assert kn1 == [0, 3, 4, 7, 8, 10]
    assert sorted(b for b in bg1 if b[2] == 4) == [(0, 4, 4), (3, 7, 4), (4, 8, 4)] and sorted(b for b in bg1 if b[2] == 3) == [(0, 3, 3), (4, 7, 3), (7, 10, 3)]
    assert sorted(b for b in bg1 if b[2] == 0) == [(0, 10, 0), (3, 10, 0), (4, 10, 0), (7, 10, 0), (8, 10, 0)]
    kn2, bg2 = A.graph(s, 10, 2)
    assert kn2 == kn1 and bg2 == [(0, 4, 4), (4, 8, 4), (0, 3, 3), (4, 7, 3), (7, 10, 3), (0, 10, 0), (3, 10, 0), (4, 10, 0), (7, 10, 0), (8, 10, 0)]
    assert set(bg2) < set(bg1)                                                              # die geordnete Stufe hat nur Bögen der normalen


def test_lp_und_optimum_der_mini_instanz_von_hand(mini):
    s = list(mini.sizes)
    for stufe in (0, 1, 2):
        assert A.loese(s, 10, stufe, False)["wert"] == pytest.approx(2.25)
        r = A.loese(s, 10, stufe, True)
        assert r["status"] == "optimal" and r["wert"] == 3.0
        bins = A.packung_aus_fluss(s, r["bogen"], r["fluss"], 10)
        assert A.container_pruefen(s, bins, 10) and len(bins) == 3 and A.loesung_pruefen(s, 10, r["bogen"], r["fluss"])
    assert A.lp_muster(s, 10) == pytest.approx(2.5) and A.optimum_dp(s, 10) == 3
    assert (len(A.ffd(s, 10)), A.l1(s, 10), A.l2(s, 10), A.lp_aufgerundet(2.25)) == (3, 2, 2, 3)


def test_dualzertifikat_des_lp_der_mini_instanz_von_hand():
    """y(4) = 0,5 und y(3) = 0,25 sind dual zulässig (jedes Muster mit beliebig vielen Exemplaren hat höchstens den Wert 1) und ergeben 4 * 0,5 + 0,25 = 2,25: der LP-Wert ist damit nach unten bewiesen."""
    y4, y3 = 0.5, 0.25
    for n4 in range(0, 3):
        for n3 in range(0, 4):
            if 4 * n4 + 3 * n3 <= 10:
                assert n4 * y4 + n3 * y3 <= 1 + 1e-12
    assert 4 * y4 + 1 * y3 == 2.25


def test_wege_zerlegen_den_fluss_deterministisch(mini):
    s = list(mini.sizes)
    r = A.loese(s, 10, 2, True)
    ws = A.wege(r["bogen"], r["fluss"], 10)
    assert len(ws) == 3 and all(r["bogen"][w[0]][0] == 0 and r["bogen"][w[-1]][1] == 10 for w in ws)
    assert A.wege(r["bogen"], r["fluss"], 10) == ws
    for w in ws:                                                                          # ein Weg ist durchgehend: jeder Bogen beginnt, wo der vorige endet
        assert all(r["bogen"][a][1] == r["bogen"][b][0] for a, b in zip(w, w[1:]))
    assert sum(r["bogen"][j][2] for w in ws for j in w) >= 19                            # alle Pakete sind überdeckt (19 = Summe der Größen)


def test_loesung_pruefen_erkennt_fehler(mini):
    s = list(mini.sizes)
    r = A.loese(s, 10, 2, True)
    assert A.loesung_pruefen(s, 10, r["bogen"], r["fluss"])
    zu_wenig = list(r["fluss"])
    j = next(j for j, f in enumerate(zu_wenig) if f > 0 and r["bogen"][j][2] == 3)
    zu_wenig[j] -= 1
    assert not A.loesung_pruefen(s, 10, r["bogen"], zu_wenig)                              # Erhaltung und Nachfrage verletzt
    negativ = list(r["fluss"])
    negativ[0] = -1.0
    assert not A.loesung_pruefen(s, 10, r["bogen"], negativ)
    assert not A.loesung_pruefen(s, 10, r["bogen"], [0.0] * len(r["bogen"]))              # Nachfrage nicht gedeckt


def test_vergleichswerte_ffd_l1_l2_und_dp():
    assert A.ffd([4, 4, 4, 4, 3], 10) == [[0, 1], [2, 3], [4]]
    assert A.l1([4, 4, 4, 4, 3], 10) == 2 and A.l1([], 10) == 0
    assert A.l2([6, 6, 6], 10) == 3 and A.l2([5, 5, 5, 5], 10) == 2              # drei Pakete über der halben Kapazität: drei Container
    assert A.optimum_dp([6, 6, 4, 4], 10) == 2 and A.optimum_dp([5] * 13, 10) is None
    assert A.container_pruefen([4, 4], [[0], [1]], 10) and not A.container_pruefen([4, 4], [[0, 1, 1]], 10) and not A.container_pruefen([6, 6], [[0, 1]], 10)


def test_beispiele_der_app_mit_den_angaben_der_konstanten():
    erwartet = {0: (3, 2, 2, 3, 3), 1: (11, 9, 11, 11, 11), 2: (6, 5, 5, 6, 6), 3: (6, 5, 5, 5, 5)}      # FFD, L1, L2, aufgerundeter LP (geordnet), Optimum
    for i, (ffd, a1, a2, lp, opt) in erwartet.items():
        b = beispiel(i)
        s = list(b.sizes)
        assert (len(A.ffd(s, b.cap)), A.l1(s, b.cap), A.l2(s, b.cap), A.lp_aufgerundet(A.loese(s, b.cap, 2, False)["wert"])) == (ffd, a1, a2, lp)
        assert A.loese(s, b.cap, 2, True)["wert"] == opt == A.optimum_dp(s, b.cap)
    b4 = beispiel(4)
    assert sorted(set(b4.sizes)) == [15, 25, 35, 55] and A.groessen(list(b4.sizes), 100) == {0: (101, 374), 1: (18, 63), 2: (18, 44)}


def test_lp_werte_der_beispiele_je_stufe_und_gegen_stueck_4():
    """Die Stufen verändern den LP: voll <= normal <= geordnet <= LP von Stück 4 (Beispiel 2: 10,5 / 11 / 11 / 11; Beispiel 3: 5,0588 / 5,0588 / 5,0909 / 5,1429)."""
    for i, (w, item) in {1: ((10.5, 11.0, 11.0), 11.0), 2: ((5.0588, 5.0588, 5.0909), 5.1429), 3: ((5.0, 5.0, 5.0), 5.0)}.items():
        b = beispiel(i)
        lps = [A.loese(list(b.sizes), b.cap, st, False)["wert"] for st in (0, 1, 2)]
        assert lps == pytest.approx(list(w), abs=1e-4) and A.lp_muster(list(b.sizes), b.cap) == pytest.approx(item, abs=1e-4)
        assert lps[0] <= lps[1] + 1e-9 <= lps[2] + 2e-9 <= A.lp_muster(list(b.sizes), b.cap) + 3e-9


def test_ungueltige_eingaben_werden_abgelehnt():
    for sizes, cap in (([0, 3], 10), ([11], 10), ([3.5], 10), ([3], 0)):
        with pytest.raises(ValueError):
            A.graph(sizes, cap, 2)
    with pytest.raises(ValueError):
        A.graph([3], 10, 3)
    with pytest.raises(ValueError):
        A.ffd([0], 10)
    with pytest.raises(ValueError):
        A.lp_muster([1] * 15, 10)


def test_konstanten_stimmen():
    assert C.CAP == 100 and set(C.STUFEN) == {0, 1, 2} and math.isclose(C.ILP_ZEIT, 60.0)
