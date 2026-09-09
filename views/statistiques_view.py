import tkinter as tk

import db
from ui_helpers import CarteArrondie

FOND = "#f5f6fa"
CARTE_BG = "white"
BORDURE = "#e5e7eb"
TEXTE_TITRE = "#111827"
TEXTE_MUET = "#6b7280"

BLEU = "#2563eb"
BLEU_CLAIR = "#dbeafe"
VERT = "#16a34a"
VERT_CLAIR = "#dcfce7"
ROUGE = "#dc2626"
ROUGE_CLAIR = "#fee2e2"
VIOLET = "#9333ea"
VIOLET_CLAIR = "#f3e8ff"


class StatistiquesFrame(tk.Frame):
    """Chiffre d'affaires, encaissements et impayés - séparés du tableau de
    bord pour ne pas exposer ces montants à quiconque ouvre le logiciel."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND, padx=30, pady=22)
        self.controller = controller
        self.devise = db.get_param("devise", "DT")

        tk.Label(
            self, text="Statistiques", bg=FOND, fg=TEXTE_TITRE,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            self, text="Chiffre d'affaires, encaissements et impayés.", bg=FOND,
            fg=TEXTE_MUET, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(0, 18))

        self._construire_cartes(self)

    def _construire_cartes(self, parent):
        stats = db.get_stats()
        devise = self.devise

        cartes_frame = tk.Frame(parent, bg=FOND)
        cartes_frame.pack(fill="x")
        for i in range(4):
            cartes_frame.grid_columnconfigure(i, weight=1, uniform="cartes")

        self._carte_stat(
            cartes_frame, 0, "💰", BLEU, BLEU_CLAIR, "Total facturé",
            f"{db.format_montant(stats['total_factures'])} {devise}",
            f"{stats['nb_factures']} facture(s) + {stats['nb_bl']} BL",
        )
        self._carte_stat(
            cartes_frame, 1, "💳", VERT, VERT_CLAIR, "Total encaissé",
            f"{db.format_montant(stats['total_encaisse'])} {devise}",
            "Paiements reçus",
        )
        self._carte_stat(
            cartes_frame, 2, "⚠️", ROUGE, ROUGE_CLAIR, "Total impayé",
            f"{db.format_montant(stats['total_impaye'])} {devise}",
            "Reste à percevoir",
        )
        self._carte_stat(
            cartes_frame, 3, "👥", VIOLET, VIOLET_CLAIR, "Clients enregistrés",
            str(stats["nb_clients"]),
            "Total dans la base",
        )

    def _carte_stat(self, parent, colonne, icone, couleur, couleur_claire, titre, valeur, note):
        carte = CarteArrondie(
            parent, bg_page=FOND, bg_carte=CARTE_BG, bordure=BORDURE, rayon=14,
            padx=16, pady=14,
        )
        carte.grid(row=0, column=colonne, sticky="nsew", padx=(0 if colonne == 0 else 8, 0))

        tk.Label(
            carte.interior, text=icone, bg=couleur_claire, fg=couleur,
            font=("Segoe UI Emoji", 13), width=3, height=1,
        ).pack(anchor="w", pady=(0, 12))
        tk.Label(
            carte.interior, text=titre, bg=CARTE_BG, fg=TEXTE_MUET, font=("Segoe UI", 9),
        ).pack(anchor="w")
        tk.Label(
            carte.interior, text=valeur, bg=CARTE_BG, fg=TEXTE_TITRE,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w", pady=(4, 4))
        tk.Label(
            carte.interior, text=note, bg=CARTE_BG, fg=TEXTE_MUET, font=("Segoe UI", 8),
        ).pack(anchor="w")
