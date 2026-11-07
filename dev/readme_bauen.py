"""Setzt die README zusammen: Tabellen und Text der Annahmen kommen aus denselben Funktionen wie in der App (nur zum Schreiben der README, nicht Teil der Laufzeit).

    python dev/readme_bauen.py [ANZAHL_TESTS]
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import arf_algorithm as A  # noqa: E402
import arf_constants as C  # noqa: E402
import arf_evaluation as ev  # noqa: E402
from arf_scenario import beispiel  # noqa: E402


def zellen():
    return [(v, ni) for v in range(len(C.VERTEILUNGEN)) for ni in range(len(C.MESS_N))]


def tabellen():
    """(A, B, C, D): A = Größe des Graphen je Zelle (Mittel Knoten und Bögen je Stufe, Anteil), B = Ausgänge je Zelle, C = LP-Vergleiche je Zelle, D = die Beispiele (Größen, LP-Werte, Optimum)."""
    ta = ["| Verteilung | n | Knoten voll / normal / geordnet | Bögen voll / normal / geordnet | Bögen geordnet am vollen |", "|---|---|---|---|---|"]
    tb = ["| Verteilung | n | L1 | L2 | LP | FFD optimal, nur das Programm | FFD verliert | offen |", "|---|---|---|---|---|---|---|---|"]
    tc = ["| Verteilung | n | LP geordnet = Optimum | LP normal = Optimum | LP Stück 4 = Optimum | LP größer durch die Ordnung | LP geordnet unter Stück 4 |", "|---|---|---|---|---|---|---|"]
    for v, ni in zellen():
        z = ev.zeile(v, ni)
        kn, bg, a, k = z["knoten"], z["bogen"], z["ausgang"], z["lp"]
        ta.append(f"| {C.VERTEILUNG_KURZ[v]} | {z['n']} | {kn[0]:.0f} / {kn[1]:.0f} / {kn[2]:.0f} | {bg[0]:.0f} / {bg[1]:.0f} / {bg[2]:.0f} | {z['bogen_anteil']:.0f} % |")
        tb.append(f"| {C.VERTEILUNG_KURZ[v]} | {z['n']} | {a['l1']} | {a['l2']} | {a['lp']} | {a['ffd_nur_ilp']} | {a['ffd_verliert']} | {a['offen']} |")
        tc.append(f"| {C.VERTEILUNG_KURZ[v]} | {z['n']} | {k['rund_s2_opt']} von {z['entschieden']} | {k['rund_s1_opt']} | {k['rund_item_opt']} | {k['s1_kleiner_s2']} | {k['s2_kleiner_item']} |")
    td = ["| Beispiel | Pakete | Kapazität | Knoten / Bögen voll | Knoten / Bögen geordnet | LP voll / normal / geordnet | LP Stück 4 | Optimum | FFD |", "|---|---|---|---|---|---|---|---|---|"]
    for i in sorted(C.BEISPIELE):
        b = beispiel(i)
        s = list(b.sizes)
        g = A.groessen(s, b.cap)
        lp = [A.loese(s, b.cap, st, False)["wert"] for st in (0, 1, 2)]
        item = A.lp_muster(s, b.cap) if b.n <= 14 else None
        opt = A.loese(s, b.cap, 2, True)["wert"]
        td.append(f"| {C.BEISPIEL_NAMEN[i]} | {b.n} | {b.cap} | {g[0][0]} / {g[0][1]} | {g[2][0]} / {g[2][1]} | " + " / ".join(f"{x:.2f}".replace(".", ",") for x in lp)
                  + f" | {('%.2f' % item).replace('.', ',')} | {int(round(opt))} | {len(A.ffd(s, b.cap))} |")
    return "\n".join(ta), "\n".join(tb), "\n".join(tc), "\n".join(td)


if __name__ == "__main__":
    vorlage = (ROOT / "dev" / "readme_vorlage.md").read_text(encoding="utf-8")
    ta, tb, tc, td = tabellen()
    anzahl = sys.argv[1] if len(sys.argv) > 1 else "TESTZAHL"
    text = vorlage.replace("{{TABELLE_A}}", ta).replace("{{TABELLE_B}}", tb).replace("{{TABELLE_C}}", tc).replace("{{TABELLE_D}}", td).replace("{{ANNAHMEN}}", C.ASSUMPTIONS_MARKDOWN).replace("{{TESTS}}", anzahl)
    (ROOT / "README.md").write_text(text, encoding="utf-8")
    print("README.md geschrieben")
