"""
Dictionnaire de traductions FR / EN.
Toutes les chaînes affichées dans l'interface passent par t(cle, langue).
"""

TRADUCTIONS = {
    "brand_title": {"fr": "Détection de doublons", "en": "Duplicate Detection"},
    "brand_subtitle": {"fr": "Gouvernance des données — Tableau de bord", "en": "Data Governance — Dashboard"},
    "live": {"fr": "Données à jour", "en": "Data up to date"},

    "kpi_total_files": {"fr": "Fichiers dupliqués", "en": "Duplicated files"},
    "kpi_groups": {"fr": "Groupes distincts", "en": "Distinct groups"},
    "kpi_space": {"fr": "Espace gaspillé", "en": "Wasted space"},
    "kpi_depots": {"fr": "Dépôts impactés", "en": "Impacted repositories"},
    "kpi_unites": {"fr": "Unités métier", "en": "Business units"},

    "filter_depot": {"fr": "Dépôt", "en": "Repository"},
    "filter_depot_all": {"fr": "Tous les dépôts", "en": "All repositories"},
    "filter_unite": {"fr": "Unité métier", "en": "Business unit"},
    "filter_unite_all": {"fr": "Toutes les unités", "en": "All business units"},
    "filter_type": {"fr": "Type de duplication", "en": "Duplication type"},
    "filter_type_all": {"fr": "Tous", "en": "All"},
    "filter_type_exact": {"fr": "Doublons exacts", "en": "Exact duplicates"},
    "filter_type_quasi": {"fr": "Quasi-doublons", "en": "Near-duplicates"},

    "chart_unite_title": {"fr": "Espace gaspillé par unité métier", "en": "Wasted space by business unit"},
    "chart_unite_subtitle": {"fr": "Triées par impact décroissant", "en": "Sorted by decreasing impact"},
    "chart_depot_title": {"fr": "Répartition par dépôt", "en": "Breakdown by repository"},
    "chart_depot_subtitle": {"fr": "Taille = espace gaspillé", "en": "Size = wasted space"},
    "chart_extension_title": {"fr": "Top extensions dupliquées", "en": "Top duplicated extensions"},
    "chart_extension_subtitle": {"fr": "Nombre de fichiers concernés", "en": "Number of affected files"},
    "chart_type_title": {"fr": "Exact vs quasi-doublons", "en": "Exact vs near-duplicates"},
    "chart_type_subtitle": {"fr": "Répartition globale par type", "en": "Overall breakdown by type"},

    "table_title": {"fr": "Top 20 points chauds", "en": "Top 20 hotspots"},
    "table_subtitle": {
        "fr": "Combinaison dépôt + unité métier les plus critiques",
        "en": "Most critical repository + business unit combinations",
    },
    "table_col_rank": {"fr": "Rang", "en": "Rank"},
    "table_col_depot": {"fr": "Dépôt", "en": "Repository"},
    "table_col_unite": {"fr": "Unité métier", "en": "Business unit"},
    "table_col_files": {"fr": "Fichiers dupliqués", "en": "Duplicated files"},
    "table_col_space": {"fr": "Espace gaspillé", "en": "Wasted space"},

    "axis_space_mb": {"fr": "Espace gaspillé (MB)", "en": "Wasted space (MB)"},
    "axis_nb_files": {"fr": "Nombre de fichiers", "en": "Number of files"},
    "legend_exact": {"fr": "Exact", "en": "Exact"},
    "legend_quasi": {"fr": "Quasi", "en": "Near"},

    "footer_text": {
        "fr": "Pipeline de déduplication — généré à partir de duplication_hotspots.xlsx",
        "en": "Deduplication pipeline — generated from duplication_hotspots.xlsx",
    },
}


def t(cle, langue):
    """Retourne la traduction d'une clé pour la langue donnée, avec repli sur le français."""
    entree = TRADUCTIONS.get(cle, {})
    return entree.get(langue, entree.get("fr", cle))