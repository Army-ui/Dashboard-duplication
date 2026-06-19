import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output, State, ALL, clientside_callback, ClientsideFunction

from i18n import t

# =========================
# 1. CHARGEMENT DES DONNÉES
# =========================
# Charge les onglets produits par l'étape 5 du pipeline (duplication_hotspots.py)

df_kpis = pd.read_excel("duplication_hotspots.xlsx", sheet_name="KPIs_Globaux")
df_hotspot = pd.read_excel("duplication_hotspots.xlsx", sheet_name="Top_Points_Chauds")
df_brutes = pd.read_excel("duplication_hotspots.xlsx", sheet_name="Donnees_Brutes")

kpis_dict = dict(zip(df_kpis["indicateur"], df_kpis["valeur"]))
CLE_UNITES = "Nombre d'unités métier impactées"   # Isolée car contient une apostrophe

print("✅ Données chargées —", len(df_brutes), "lignes brutes,", len(df_hotspot), "points chauds")

# =========================
# 2. PALETTE — blanc / doré, cohérente clair & sombre
#    Les couleurs Plotly s'adaptent dynamiquement via les callbacks (voir section 8)
# =========================

PALETTE = {
    "light": {
        "bg_card": "#FFFFFF",
        "text_primary": "#21201B",
        "text_secondary": "#6B6354",
        "grid": "#EDE7D6",
        "navy": "#8A6A1F",   # alias conservé pour compat — pointe maintenant vers le doré profond
        "steel": "#B08A2E",
        "coral": "#B0552C",
        "teal": "#156A56",
    },
    "dark": {
        "bg_card": "#1C1A12",
        "text_primary": "#F3EEDF",
        "text_secondary": "#B6AD93",
        "grid": "#332C18",
        "navy": "#D4AF52",
        "steel": "#D4AF52",
        "coral": "#DD8A5C",
        "teal": "#4FC2A0",
    },
}

# =========================
# 3. APP
# =========================

import os

app = Dash(
    __name__,
    suppress_callback_exceptions=True,
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets"),
)
app.title = "Duplicate Detection Dashboard"

# Surcharge du template HTML pour forcer le meta viewport — indispensable au responsive mobile,
# sans quoi les navigateurs mobiles zooment la mise en page desktop au lieu d'appliquer les media queries
app.index_string = """<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""


# =========================
# 4. ICÔNES SVG INLINE (pas de dépendance externe, cohérent avec les deux thèmes)
# =========================

ICONE_SOLEIL = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.2 4.2l1.4 1.4M18.4 18.4l1.4 1.4M2 12h2M20 12h2M4.2 19.8l1.4-1.4M18.4 5.6l1.4-1.4"/>
</svg>"""

ICONE_LUNE = """
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<path d="M21 12.79A9 9 0 1111.21 3 7 7 0 0021 12.79z"/>
</svg>"""

ICONE_MARQUE = """
<svg viewBox="0 0 24 24" fill="none" stroke="#8A6A1F" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
<rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
<rect x="3" y="14" width="7" height="7" rx="1.5"/><path d="M17.5 14v7M14 17.5h7"/>
</svg>"""


def icone(svg_str, taille=16):
    return html.Span(
        dcc.Markdown(f"```html\n{svg_str}\n```", dangerously_allow_html=False) if False else None,
    )  # placeholder non utilisé — on injecte le SVG via html.Iframe-less approach ci-dessous


def svg_inline(svg_str):
    """Injecte un SVG brut sans dépendance externe via un composant Markdown autorisant le HTML."""
    return dcc.Markdown(svg_str, dangerously_allow_html=True)


# =========================
# 5. COMPOSANTS RÉUTILISABLES
# =========================

def carte_kpi(kpi_id, label, valeur, suffixe, couleur_var):
    return html.Div(
        [
            html.Div(label, className="kpi-label", id={"type": "kpi-label", "index": kpi_id}),
            html.Div(
                [
                    html.Span(valeur, className="kpi-value", id={"type": "kpi-value", "index": kpi_id}),
                    html.Span(suffixe, className="kpi-unit") if suffixe else None,
                ],
                className="kpi-value-row",
            ),
        ],
        className="kpi-card",
        style={"--kpi-accent": couleur_var},
    )


def en_tete_section(titre_id, titre_defaut, sous_titre_id, sous_titre_defaut):
    return html.Div(
        [
            html.Div(titre_defaut, className="section-title", id=titre_id),
            html.Div(sous_titre_defaut, className="section-subtitle", id=sous_titre_id),
        ]
    )


# =========================
# 6. MISE EN PAGE
# =========================

app.layout = html.Div(
    id="app-shell",
    className="app-shell",
    children=[

        # Stores pour persister thème / langue côté client
        dcc.Store(id="store-theme", storage_type="local", data="light"),
        dcc.Store(id="store-langue", storage_type="local", data="fr"),
        dcc.Store(id="store-detection-faite", storage_type="memory", data=False),

        # ── Barre supérieure ──────────────────────────────────────────────
        html.Div(
            className="topbar",
            children=[
                html.Div(
                    className="brand-block",
                    children=[
                        html.Div(svg_inline(ICONE_MARQUE), className="brand-mark"),
                        html.Div([
                            html.Div(id="txt-brand-title", className="brand-text-title"),
                            html.Div(id="txt-brand-subtitle", className="brand-text-subtitle"),
                        ]),
                    ],
                ),
                html.Div(
                    className="topbar-controls",
                    children=[
                        html.Div(
                            className="live-chip",
                            children=[html.Span(className="live-dot"), html.Span(id="txt-live")],
                        ),
                        html.Div(
                            className="control-pill",
                            children=[
                                html.Button("FR", id="btn-lang-fr", className="control-pill-btn"),
                                html.Button("EN", id="btn-lang-en", className="control-pill-btn"),
                            ],
                        ),
                        html.Button(
                            svg_inline(ICONE_LUNE),
                            id="btn-theme-toggle",
                            className="theme-toggle-btn",
                            title="Basculer le thème",
                        ),
                    ],
                ),
            ],
        ),

        # ── Contenu principal ────────────────────────────────────────────
        html.Div(
            className="main-content",
            children=[

                # KPIs
                html.Div(
                    className="kpi-row",
                    children=[
                        carte_kpi("total_files", "", f"{int(kpis_dict.get('Nombre total de fichiers dupliqués', 0)):,}".replace(",", " "), "", "var(--gold-600)"),
                        carte_kpi("groups", "", f"{int(kpis_dict.get('Nombre de groupes de duplication distincts', 0)):,}".replace(",", " "), "", "var(--accent-teal)"),
                        carte_kpi("space", "", f"{kpis_dict.get('Espace total gaspillé (MB)', 0):,.0f}".replace(",", " "), "MB", "var(--accent-coral)"),
                        carte_kpi("depots", "", f"{int(kpis_dict.get('Nombre de dépôts impactés', 0)):,}", "", "var(--gold-600)"),
                        carte_kpi("unites", "", f"{int(kpis_dict.get(CLE_UNITES, 0)):,}", "", "var(--accent-teal)"),
                    ],
                ),

                # Filtres
                html.Div(
                    className="filter-panel",
                    children=[
                        html.Div([
                            html.Label(id="lbl-filter-depot", className="filter-label"),
                            dcc.Dropdown(id="filtre-depot", options=[{"label": d, "value": d} for d in sorted(df_brutes["depot"].dropna().unique())], clearable=True),
                        ], className="filter-field"),
                        html.Div([
                            html.Label(id="lbl-filter-unite", className="filter-label"),
                            dcc.Dropdown(id="filtre-unite", options=[{"label": u, "value": u} for u in sorted(df_brutes["unite_metier"].dropna().unique())], clearable=True),
                        ], className="filter-field"),
                        html.Div([
                            html.Label(id="lbl-filter-type", className="filter-label"),
                            dcc.Dropdown(id="filtre-type", value="Tous", clearable=False),
                        ], className="filter-field"),
                    ],
                ),

                # Graphiques ligne 1
                html.Div(
                    className="chart-grid-2",
                    children=[
                        html.Div([
                            en_tete_section("titre-unite", "", "sous-titre-unite", ""),
                            dcc.Graph(id="graphique-unite", config={"displayModeBar": False, "responsive": True}, style={"width": "100%"}),
                        ], className="chart-card"),
                        html.Div([
                            en_tete_section("titre-depot", "", "sous-titre-depot", ""),
                            dcc.Graph(id="graphique-depot", config={"displayModeBar": False, "responsive": True}, style={"width": "100%"}),
                        ], className="chart-card"),
                    ],
                ),

                # Graphiques ligne 2
                html.Div(
                    className="chart-grid-2",
                    children=[
                        html.Div([
                            en_tete_section("titre-extension", "", "sous-titre-extension", ""),
                            dcc.Graph(id="graphique-extension", config={"displayModeBar": False, "responsive": True}, style={"width": "100%"}),
                        ], className="chart-card"),
                        html.Div([
                            en_tete_section("titre-type", "", "sous-titre-type", ""),
                            dcc.Graph(id="graphique-type", config={"displayModeBar": False, "responsive": True}, style={"width": "100%"}),
                        ], className="chart-card"),
                    ],
                ),

                # Tableau
                html.Div(
                    className="table-card",
                    children=[
                        en_tete_section("titre-table", "", "sous-titre-table", ""),
                        html.Div(id="tableau-hotspot"),
                    ],
                ),
            ],
        ),

        html.Div(id="txt-footer", className="app-footer"),
    ],
)


# =========================
# 7. CALLBACKS CLIENT-SIDE — détection auto thème + langue au premier chargement
# =========================

clientside_callback(
    """
    function(_) {
        if (window.__dashboardDetection) {
            return [window.__dashboardDetection.theme, window.__dashboardDetection.langue, true];
        }
        return [window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light',
                (navigator.language || 'en').toLowerCase().startsWith('fr') ? 'fr' : 'en', true];
    }
    """,
    Output("store-theme", "data"),
    Output("store-langue", "data"),
    Output("store-detection-faite", "data"),
    Input("store-detection-faite", "data"),
    prevent_initial_call=False,
)

clientside_callback(
    """
    function(theme) {
        document.documentElement.setAttribute('data-theme', theme || 'light');
        return window.dash_clientside.no_update;
    }
    """,
    Output("app-shell", "data-theme"),
    Input("store-theme", "data"),
)


@app.callback(
    Output("store-theme", "data", allow_duplicate=True),
    Input("btn-theme-toggle", "n_clicks"),
    State("store-theme", "data"),
    prevent_initial_call=True,
)
def basculer_theme(n_clicks, theme_actuel):
    return "dark" if theme_actuel == "light" else "light"


@app.callback(
    Output("store-langue", "data", allow_duplicate=True),
    Input("btn-lang-fr", "n_clicks"),
    Input("btn-lang-en", "n_clicks"),
    prevent_initial_call=True,
)
def changer_langue(clic_fr, clic_en):
    from dash import ctx
    if ctx.triggered_id == "btn-lang-fr":
        return "fr"
    return "en"


# =========================
# 8. CALLBACK PRINCIPAL — traduction de l'interface + filtrage + graphiques
# =========================

@app.callback(
    # Textes statiques traduits
    Output("txt-brand-title", "children"),
    Output("txt-brand-subtitle", "children"),
    Output("txt-live", "children"),
    Output("lbl-filter-depot", "children"),
    Output("filtre-depot", "placeholder"),
    Output("lbl-filter-unite", "children"),
    Output("filtre-unite", "placeholder"),
    Output("lbl-filter-type", "children"),
    Output("filtre-type", "options"),
    Output("titre-unite", "children"), Output("sous-titre-unite", "children"),
    Output("titre-depot", "children"), Output("sous-titre-depot", "children"),
    Output("titre-extension", "children"), Output("sous-titre-extension", "children"),
    Output("titre-type", "children"), Output("sous-titre-type", "children"),
    Output("titre-table", "children"), Output("sous-titre-table", "children"),
    Output("txt-footer", "children"),
    Output({"type": "kpi-label", "index": "total_files"}, "children"),
    Output({"type": "kpi-label", "index": "groups"}, "children"),
    Output({"type": "kpi-label", "index": "space"}, "children"),
    Output({"type": "kpi-label", "index": "depots"}, "children"),
    Output({"type": "kpi-label", "index": "unites"}, "children"),
    # Graphiques + tableau (dépendent aussi des filtres et du thème)
    Output("graphique-unite", "figure"),
    Output("graphique-depot", "figure"),
    Output("graphique-extension", "figure"),
    Output("graphique-type", "figure"),
    Output("tableau-hotspot", "children"),
    Input("store-langue", "data"),
    Input("store-theme", "data"),
    Input("filtre-depot", "value"),
    Input("filtre-unite", "value"),
    Input("filtre-type", "value"),
)
def rafraichir_interface(langue, theme, depot, unite, type_dup):
    langue = langue or "fr"
    theme = theme or "light"
    couleurs = PALETTE[theme if theme in PALETTE else "light"]

    # ── Filtrage des données brutes ──────────────────────────────────────
    df = df_brutes.copy()
    if depot:
        df = df[df["depot"] == depot]
    if unite:
        df = df[df["unite_metier"] == unite]
    if type_dup and type_dup != "Tous":
        df = df[df["type_duplication"] == type_dup]

    options_type = [
        {"label": t("filter_type_all", langue), "value": "Tous"},
        {"label": t("filter_type_exact", langue), "value": "Exact"},
        {"label": t("filter_type_quasi", langue), "value": "Quasi"},
    ]

    # ── Mise en forme Plotly commune aux 4 graphiques ────────────────────
    layout_commun = dict(
        plot_bgcolor=couleurs["bg_card"],
        paper_bgcolor=couleurs["bg_card"],
        font_color=couleurs["text_secondary"],
        font_family="IBM Plex Sans, sans-serif",
        margin=dict(l=10, r=10, t=10, b=70),
        height=300,
    )

    # ── Graphique 1 : barres horizontales par unité métier ──────────────
    agg_unite = (
        df.groupby("unite_metier")["taille_octets"].sum().reset_index()
        .sort_values("taille_octets", ascending=True).tail(10)
    )
    agg_unite["mb"] = agg_unite["taille_octets"] / (1024 * 1024)
    fig_unite = px.bar(
        agg_unite, x="mb", y="unite_metier", orientation="h",
        labels={"mb": t("axis_space_mb", langue), "unite_metier": ""},
        color_discrete_sequence=[couleurs["navy"]],
    )
    fig_unite.update_layout(**layout_commun)
    fig_unite.update_xaxes(gridcolor=couleurs["grid"], zerolinecolor=couleurs["grid"])
    fig_unite.update_yaxes(gridcolor=couleurs["grid"])

    # ── Graphique 2 : treemap par dépôt ──────────────────────────────────
    agg_depot = df.groupby("depot")["taille_octets"].sum().reset_index()
    fig_depot = px.treemap(
        agg_depot, path=["depot"], values="taille_octets",
        color="taille_octets",
        color_continuous_scale=[couleurs["grid"], couleurs["navy"]],
    )
    fig_depot.update_layout(
        paper_bgcolor=couleurs["bg_card"], margin=dict(l=10, r=10, t=10, b=10), height=300,
        coloraxis_showscale=False,
    )
    fig_depot.update_traces(
        textinfo="label+percent root",
        textfont_color=couleurs["text_primary"] if theme == "light" else "#FFFFFF",
    )

    # ── Graphique 3 : top extensions ─────────────────────────────────────
    agg_ext = (
        df.groupby("extension")["chemin"].count().reset_index(name="nb")
        .sort_values("nb", ascending=False).head(8)
    )
    fig_extension = px.bar(
        agg_ext, x="extension", y="nb",
        labels={"extension": "", "nb": t("axis_nb_files", langue)},
        color_discrete_sequence=[couleurs["steel"]],
    )
    fig_extension.update_layout(**layout_commun)
    fig_extension.update_xaxes(gridcolor=couleurs["grid"])
    fig_extension.update_yaxes(gridcolor=couleurs["grid"])

    # ── Graphique 4 : donut exact vs quasi ────────────────────────────
    repartition = df["type_duplication"].value_counts().reset_index()
    repartition.columns = ["type_duplication", "nb"]
    repartition["label"] = repartition["type_duplication"].map(
        {"Exact": t("legend_exact", langue), "Quasi": t("legend_quasi", langue)}
    )
    fig_type = px.pie(
        repartition, names="label", values="nb", hole=0.6,
        color="type_duplication",
        color_discrete_map={"Exact": couleurs["navy"], "Quasi": couleurs["coral"]},
    )
    fig_type.update_layout(
        paper_bgcolor=couleurs["bg_card"], margin=dict(l=10, r=10, t=10, b=10), height=300,
        showlegend=True, legend=dict(orientation="h", y=-0.12, font=dict(color=couleurs["text_secondary"])),
        font_color=couleurs["text_secondary"],
    )

    # ── Tableau top points chauds ────────────────────────────────────────
    entetes = html.Tr([
        html.Th(t("table_col_rank", langue)),
        html.Th(t("table_col_depot", langue)),
        html.Th(t("table_col_unite", langue)),
        html.Th(t("table_col_files", langue)),
        html.Th(t("table_col_space", langue)),
    ])
    lignes = [entetes]
    for _, ligne in df_hotspot.iterrows():
        lignes.append(html.Tr([
            html.Td(html.Span(int(ligne["rang"]), className="rank-chip")),
            html.Td(ligne["depot"]),
            html.Td(ligne["unite_metier"]),
            html.Td(f"{int(ligne['nb_fichiers_dupliques']):,}".replace(",", " ")),
            html.Td(ligne["espace_total_lisible"]),
        ]))
    tableau = html.Table([html.Thead(lignes[0]), html.Tbody(lignes[1:])], className="hotspot-table")

    return (
        t("brand_title", langue), t("brand_subtitle", langue), t("live", langue),
        t("filter_depot", langue), t("filter_depot_all", langue),
        t("filter_unite", langue), t("filter_unite_all", langue),
        t("filter_type", langue), options_type,
        t("chart_unite_title", langue), t("chart_unite_subtitle", langue),
        t("chart_depot_title", langue), t("chart_depot_subtitle", langue),
        t("chart_extension_title", langue), t("chart_extension_subtitle", langue),
        t("chart_type_title", langue), t("chart_type_subtitle", langue),
        t("table_title", langue), t("table_subtitle", langue),
        t("footer_text", langue),
        t("kpi_total_files", langue), t("kpi_groups", langue), t("kpi_space", langue),
        t("kpi_depots", langue), t("kpi_unites", langue),
        fig_unite, fig_depot, fig_extension, fig_type, tableau,
    )


# =========================
# 9. CALLBACK — état visuel actif des boutons langue + icône du toggle thème
# =========================

@app.callback(
    Output("btn-lang-fr", "className"),
    Output("btn-lang-en", "className"),
    Input("store-langue", "data"),
)
def style_boutons_langue(langue):
    base = "control-pill-btn"
    if langue == "en":
        return base, base + " is-active"
    return base + " is-active", base


@app.callback(
    Output("btn-theme-toggle", "children"),
    Input("store-theme", "data"),
)
def icone_theme(theme):
    return svg_inline(ICONE_SOLEIL if theme == "dark" else ICONE_LUNE)


# =========================
# 10. LANCEMENT
# =========================

if __name__ == "__main__":
    app.run(debug=True, port=8050)