"""Presets: Vollständigkeit, gültige Werte, erstes Preset = Standardeinstellungen, jeder Hilfetext stimmt mit der Rechnung überein."""

import arf_algorithm as A
import arf_constants as C
import arf_evaluation as ev
import arf_presets as P


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_widget_bounds():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            assert spec.lo <= preset[key] <= spec.hi, (name, key)


def test_first_preset_equals_the_default_settings():
    assert ev.Settings(**next(iter(C.PRESETS.values()))) == ev.Settings()


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_defaults_of_the_widgets_equal_the_default_settings():
    s = ev.Settings()
    schluessel = ("quelle_select", "verteilung_select", "n_input", "seed_input", "stufe_select")
    assert [P.SETTING_SPECS[k].default for k in schluessel] == [s.quelle, s.verteilung, s.n, s.seed, s.stufe]


def _a(name):
    p = C.PRESETS[name]
    return ev.analyse(ev.Settings(p["quelle"], p["verteilung"], p["n"], p["seed"], p["stufe"]))


def test_presets_behaupten_nur_was_stimmt():
    eins = _a("Kleines Beispiel (4, 4, 4, 4, 3)")
    assert eins.groessen[2] == (6, 10) and eins.opt == 3 and abs(eins.lp[2] - 2.25) < 1e-9
    hilfe = C.PRESET_HELP["Kleines Beispiel (4, 4, 4, 4, 3)"]
    assert "sechs Knoten und zehn Bögen" in hilfe and "drei Container" in hilfe and "LP-Wert 2,25 ist aufgerundet gleich dem Optimum" in hilfe and A.lp_aufgerundet(eins.lp[2]) == eins.opt
    zwei = _a("Beispiel 4: FFD verliert")
    assert (zwei.ffd, zwei.opt, zwei.l1, zwei.l2) == (6, 5, 5, 5) and "FFD braucht sechs Container, der Arc-Flow findet fünf" in C.PRESET_HELP["Beispiel 4: FFD verliert"]
    drei = _a("Wenige verschiedene Größen")
    assert drei.inst.n == 14 and len(set(drei.inst.sizes)) == 4 and drei.groessen == {0: (101, 374), 1: (18, 63), 2: (18, 44)}
    assert "Vierzehn Pakete, aber nur vier verschiedene Größen" in C.PRESET_HELP["Wenige verschiedene Größen"] and "18 Knoten und 44 Bögen statt 101 Knoten und 374 Bögen" in C.PRESET_HELP["Wenige verschiedene Größen"]
    vier = _a("Beispiel 3, voller Graph")
    assert vier.stufe == 0 and vier.groessen[0] == (101, 814) and len(vier.bogen) > C.ZEICHEN_MAX and round(vier.lp[0], 2) == 5.06 and round(vier.lp[2], 2) == 5.09
    hilfe = C.PRESET_HELP["Beispiel 3, voller Graph"]
    assert "101 Knoten und 814 Bögen" in hilfe and "5,06, in der Stufe geordnet 5,09" in hilfe
    fuenf = _a("20 große Teile (Zufall)")
    assert fuenf.inst.n == 20 and fuenf.groessen[0][1] == 1162 and fuenf.groessen[2][1] == 297 and (fuenf.opt, fuenf.ffd, fuenf.l1, fuenf.l2) == (10, 10, 9, 9) and A.lp_aufgerundet(fuenf.lp[2]) == 10
    hilfe = C.PRESET_HELP["20 große Teile (Zufall)"]
    assert "297 Bögen statt 1162" in hilfe and "findet 10 Container wie FFD" in hilfe and "erst der aufgerundete LP-Wert beweist das" in hilfe
    assert ev.beweis_durch(fuenf.opt, fuenf.l1, fuenf.l2, A.lp_aufgerundet(fuenf.lp[2])) == "lp"
