"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import arf_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.3), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _bogen_linien(bogen, hoehe, punkte=14):
    """Koordinaten (x, y) aller Bögen als eine Linie mit Lücken: jeder Bogen ein Halbkreis über (Verlustbögen: unter) der Lastachse, Höhe proportional zur Länge."""
    xs, ys = [], []
    for u, v, w in bogen:
        for k in range(punkte + 1):
            t = k / punkte
            xs.append(u + (v - u) * t)
            ys.append((1 if w else -1) * hoehe * (v - u) * math.sin(math.pi * t))
        xs.append(None)
        ys.append(None)
    return xs, ys


def build_graph(knoten, bogen, fluss, cap, sizes_farben):
    """Der Arc-Flow-Graph über der Lastachse 0 bis C: Knoten als Punkte, Bögen als Halbkreise über der Achse (Farbe nach Paketgröße), Verlustbögen grau darunter. Bögen mit Fluss sind dick, die
    übrigen blass; hat der Graph mehr als C.ZEICHEN_MAX Bögen, werden nur die Bögen mit Fluss gezeichnet. `sizes_farben` ordnet jeder Größe eine Farbe zu."""
    fig = go.Figure()
    fluss = fluss if fluss is not None else [0] * len(bogen)
    alle = len(bogen) <= C.ZEICHEN_MAX
    hoehe = 0.5
    for w in sorted({b[2] for b in bogen}, reverse=True):
        mit = [b for b, f in zip(bogen, fluss) if b[2] == w and f > 0.5]
        ohne = [b for b, f in zip(bogen, fluss) if b[2] == w and f <= 0.5] if alle else []
        farbe = "#9e9e9e" if w == 0 else sizes_farben[w]
        name = "Verlust" if w == 0 else f"Größe {w}"
        if ohne:
            xs, ys = _bogen_linien(ohne, hoehe)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=farbe, width=1), opacity=0.25, hoverinfo="skip", showlegend=False))
        if mit:
            xs, ys = _bogen_linien(mit, hoehe)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=farbe, width=3), name=name, hoverinfo="skip", showlegend=True))
    fig.add_trace(go.Scatter(x=list(knoten), y=[0] * len(knoten), mode="markers", marker=dict(size=5, color="#444444"), hovertext=[f"Last {k}" for k in knoten], hoverinfo="text", showlegend=False))
    fig.update_xaxes(title_text=f"Last (0 bis Kapazität {cap})", range=[-0.02 * cap, 1.02 * cap])
    fig.update_yaxes(visible=False, showgrid=False, zeroline=False)
    return _base(fig, 340)


def build_container(sizes, bins, cap):
    """Ein Balken je Container, darin die Pakete als gestapelte Segmente (Beschriftung = Größe), oben der freie Platz in Grau; die rote Linie ist die Kapazität."""
    labels = [f"C{b + 1}" for b in range(len(bins))]
    schichten = max((len(b) for b in bins), default=0)
    fig = go.Figure()
    for k in range(schichten):
        werte = [sizes[b[k]] if k < len(b) else 0 for b in bins]
        texte = [str(sizes[b[k]]) if k < len(b) else "" for b in bins]
        fig.add_trace(go.Bar(x=labels, y=werte, text=texte, textposition="inside", insidetextanchor="middle", marker=dict(color=C.COLOR_FILL, line=dict(color="white", width=1.5)),
                             showlegend=False, hovertemplate="%{x}: Paket %{text}<extra></extra>"))
    frei = [cap - sum(sizes[i] for i in b) for b in bins]
    fig.add_trace(go.Bar(x=labels, y=frei, text=[f"frei {f}" if f > 0 else "" for f in frei], textposition="inside", insidetextanchor="middle",
                         marker=dict(color=C.COLOR_FREE), showlegend=False, hovertemplate="%{x}: %{y} frei<extra></extra>"))
    fig.add_hline(y=cap, line=dict(color=C.COLOR_LINE, width=2, dash="dash"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Füllung (Kapazität %d)" % cap, range=[0, cap * 1.05])
    return _base(fig)


def build_groessen(groessen):
    """Knoten und Bögen des Graphen je Stufe der Kompression (logarithmische Achse). `groessen` = {Stufe: (Knoten, Bögen)}."""
    fig = go.Figure()
    for i, (name, tag) in enumerate((("Knoten", 0), ("Bögen", 1))):
        fig.add_trace(go.Bar(name=name, x=[C.STUFEN_KURZ[st] for st in sorted(groessen)], y=[groessen[st][tag] for st in sorted(groessen)], marker_color=("#4c78a8", "#f58518")[i],
                             text=[str(groessen[st][tag]) for st in sorted(groessen)], textposition="outside", hovertemplate="%{x}: %{y}<extra>" + name + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(type="log", title_text="Anzahl (logarithmisch)")
    return _base(fig, 300)


def build_raster_groesse(zeilen):
    """Mittlere Bögen je Stufe für die drei Quaderzahlen einer Verteilung (logarithmische Achse). `zeilen` = Liste der Zeilen (arf_evaluation.zeile) einer Verteilung."""
    fig = go.Figure()
    namen = [f"n = {z['n']}" for z in zeilen]
    for st in (0, 1, 2):
        fig.add_trace(go.Bar(name=C.STUFEN_KURZ[st], x=namen, y=[z["bogen"][st] for z in zeilen], marker_color=C.STUFEN_FARBEN[st], hovertemplate="%{x}: %{y:.0f} Bögen<extra>" + C.STUFEN_KURZ[st] + "</extra>"))
    fig.update_layout(barmode="group")
    fig.update_yaxes(type="log", title_text="mittlere Bögen (logarithmisch)")
    return _base(fig, 320)


def build_raster_ausgang(zeilen):
    """Gestapelte Balken je Quaderzahl: Anteil der Instanzen je Ausgang (in %). `zeilen` = Liste der Zeilen einer Verteilung."""
    namen = [f"n = {z['n']}" for z in zeilen]
    fig = go.Figure()
    for schluessel in ("l1", "l2", "lp", "ffd_nur_ilp", "ffd_verliert", "offen"):
        fig.add_trace(go.Bar(name=C.AUSGANG_TEXTE[schluessel], x=namen, y=[100.0 * z["ausgang"][schluessel] / z["instanzen"] for z in zeilen], marker_color=C.AUSGANG_FARBEN[schluessel],
                             text=[str(z["ausgang"][schluessel]) if z["ausgang"][schluessel] else "" for z in zeilen], textposition="inside",
                             hovertemplate="%{x}: %{y:.0f} % (%{text} Instanzen)<extra>" + C.AUSGANG_TEXTE[schluessel] + "</extra>"))
    fig.update_layout(barmode="stack")
    fig.update_yaxes(title_text="Anteil der Instanzen (%)", range=[0, 100])
    return _base(fig, 380)
