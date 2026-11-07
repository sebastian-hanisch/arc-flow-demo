"""End-to-end Smoke-Test via Streamlits offiziellem AppTest-Framework: lädt app.py mit den Standardeinstellungen, klickt jeden Button, stellt jede Auswahl
auf jeden ihrer Werte und die Zahlenfelder an ihre Grenzen und prüft, dass kein Python-Fehler auftritt (insbesondere `StreamlitDuplicateElementId`
bei mehreren Diagrammen ohne key= und `StreamlitAPIException` bei Auswahlen mit ungültigem Wert)."""

import os

from streamlit.testing.v1 import AppTest

import arf_constants as C

APP_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen
WUERFEL = "🎲 Neue Zufallsinstanz würfeln"


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texte(at):
    return [e.value for e in at.info] + [e.value for e in at.success] + [e.value for e in at.warning]


def test_app_loads_without_exception():
    _fresh_app()


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_selectbox_value_does_not_raise():
    keys = [s.key for s in _fresh_app().selectbox]
    assert {"quelle_select", "verteilung_select", "stufe_select", "exp_verteilung", "exp_n"} <= set(keys)
    werte = {"quelle_select": list(C.BEISPIEL_NAMEN), "verteilung_select": list(range(len(C.VERTEILUNGEN))), "stufe_select": [0, 1, 2], "exp_verteilung": list(range(len(C.VERTEILUNGEN))),
             "exp_n": list(range(len(C.MESS_N)))}
    for key in keys:
        for wert in werte[key]:
            at = _fresh_app()
            at.selectbox(key=key).set_value(wert).run(timeout=TIMEOUT)
            assert not at.exception, (key, wert, [str(e) for e in at.exception])


def test_zahlenfelder_an_ihren_grenzen_loesen_keinen_fehler_aus():
    for n in (C.N_MIN, C.N_MAX):
        for seed in (0, C.SEED_MAX):
            at = _fresh_app()
            at.selectbox(key="quelle_select").set_value(C.ZUFALL).run(timeout=TIMEOUT)
            at.number_input(key="n_input").set_value(n).run(timeout=TIMEOUT)
            at.number_input(key="seed_input").set_value(seed).run(timeout=TIMEOUT)
            assert not at.exception, (n, seed, [str(e) for e in at.exception])


def test_wuerfeln_wechselt_vom_beispiel_zur_zufallsinstanz():
    at = _fresh_app()
    assert at.selectbox(key="quelle_select").value == 0
    at.button[[b.label for b in at.button].index(WUERFEL)].click().run(timeout=TIMEOUT)
    assert at.selectbox(key="quelle_select").value == C.ZUFALL and not at.exception
    seed_vorher = at.number_input(key="seed_input").value
    at.button[[b.label for b in at.button].index(WUERFEL)].click().run(timeout=TIMEOUT)
    assert at.selectbox(key="quelle_select").value == C.ZUFALL and at.number_input(key="seed_input").value != seed_vorher


def test_standardansicht_zeigt_das_erwartete_verdikt_und_die_kennzahlen():
    at = _fresh_app()
    texte = _texte(at)
    assert any("Der Arc-Flow findet **3** Container und beweist, dass es nicht weniger geht. FFD braucht ebenfalls 3: FFD ist optimal. Erst der aufgerundete LP-Wert beweist das." in t for t in texte)
    assert any("Der Graph der Stufe geordnet hat 6 Knoten und 10 Bögen, der volle Graph 11 Knoten und 25 Bögen: Die Kompression behält **40 %** der Bögen und 55 % der Knoten." in t for t in texte)
    assert any("LP-Wert des Arc-Flows: voll 2.25, normal 2.25, geordnet 2.25; LP von Stück 4 2.50." in t for t in texte)
    assert [m.label for m in at.metric] == ["Optimum (Arc-Flow)", "FFD", "L1 / L2", "Aufgerundeter LP-Wert"] and at.metric[0].value == "3"


def test_stufe_voll_beim_beispiel_3_zeichnet_nur_die_boegen_mit_fluss():
    at = _fresh_app()
    at.selectbox(key="quelle_select").set_value(2).run(timeout=TIMEOUT)
    at.selectbox(key="stufe_select").set_value(0).run(timeout=TIMEOUT)
    assert not at.exception
    assert any("Der Graph hat 814 Bögen: Es werden nur die Bögen mit Fluss gezeichnet." in c.value for c in at.caption)
    assert any("Der volle Graph hat 101 Knoten und 814 Bögen" in t for t in _texte(at))


def test_experimente_stehen_unter_ihren_namen_und_expander_sind_da():
    at = _fresh_app()
    markdown = [m.value for m in at.markdown]
    for titel in ("### Experiment 1: Wie klein wird der Graph?", "### Experiment 2: Wie oft ist das Optimum bestimmbar?", "### Experiment 3: Trifft der aufgerundete LP-Wert das Optimum?"):
        assert any(titel in m for m in markdown), titel
    labels = [e.label for e in at.expander]
    assert "📐 Mathematische Formulierung" in labels and "⚠️ Annahmen, Grenzen und bekannte Probleme" in labels


def test_gewaehlte_zelle_steuert_die_verdikte_der_experimente():
    at = _fresh_app()
    at.selectbox(key="exp_verteilung").set_value(2).run(timeout=TIMEOUT)
    at.selectbox(key="exp_n").set_value(2).run(timeout=TIMEOUT)
    assert not at.exception and any("Für breit gestreute Teile mit n = 30" in t for t in _texte(at))
