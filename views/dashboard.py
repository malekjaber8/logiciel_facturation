import tkinter as tk
from tkinter import ttk
from datetime import date

import db
from ui_helpers import CarteArrondie

FOND = "#f5f6fa"
CARTE_BG = "white"
BORDURE = "#e5e7eb"
TEXTE_TITRE = "#111827"
TEXTE_MUET = "#6b7280"

ACCENT = "#8b5e34"
ACCENT_CLAIR = "#f5ead9"
VERT_CLAIR = "#dcfce7"
ROUGE_CLAIR = "#fee2e2"
ORANGE_CLAIR = "#fef3c7"

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

STATUT_FOND = {"paye": VERT_CLAIR, "partiel": ORANGE_CLAIR, "impaye": ROUGE_CLAIR}
STATUT_LABELS = {"paye": "Payé", "partiel": "Partiel", "impaye": "Impayé"}


def _date_fr(d):
    return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month - 1]} {d.year}"


class DashboardFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND)
        self.controller = controller
        self.devise = db.get_param("devise", "DT")

        contenu = tk.Frame(self, bg=FOND, padx=30, pady=22)
        contenu.pack(fill="both", expand=True)

        tk.Label(
            contenu, text="Tableau de bord", bg=FOND, fg=TEXTE_TITRE,
            font=("Segoe UI", 18, "bold"),
        ).pack(anchor="w", pady=(0, 16))

        self._construire_bienvenue(contenu)
        self._construire_documents(contenu)

    # ---------- Sections ----------

    def _construire_bienvenue(self, parent):
        carte = CarteArrondie(parent, bg_page=FOND, bg_carte=CARTE_BG, bordure=BORDURE, rayon=14)
        carte.pack(fill="x", pady=(0, 18))

        ligne = tk.Frame(carte.interior, bg=CARTE_BG)
        ligne.pack(fill="x")

        gauche = tk.Frame(ligne, bg=CARTE_BG)
        gauche.pack(side="left", fill="x", expand=True)
        tk.Label(
            gauche, text="Bienvenue sur votre espace de gestion", bg=CARTE_BG,
            fg=TEXTE_TITRE, font=("Segoe UI", 15, "bold"),
        ).pack(anchor="w")
        tk.Label(
            gauche, text="Suivez facilement vos ventes, vos clients et vos documents.",
            bg=CARTE_BG, fg=TEXTE_MUET, font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        droite = tk.Frame(
            ligne, bg=ACCENT_CLAIR, highlightbackground=BORDURE, highlightthickness=1,
            padx=14, pady=8,
        )
        droite.pack(side="right")
        tk.Label(droite, text="📅  Aujourd'hui", bg=ACCENT_CLAIR, fg=TEXTE_MUET,
                  font=("Segoe UI", 8)).pack(anchor="w")
        tk.Label(
            droite, text=_date_fr(date.today()), bg=ACCENT_CLAIR, fg=ACCENT,
            font=("Segoe UI", 10, "bold"),
        ).pack(anchor="w")

    def _construire_documents(self, parent):
        entete = tk.Frame(parent, bg=FOND)
        entete.pack(fill="x", pady=(0, 10))
        tk.Label(
            entete, text="Derniers documents", bg=FOND, fg=TEXTE_TITRE,
            font=("Segoe UI", 13, "bold"),
        ).pack(side="left")
        tk.Button(
            entete, text="Voir tout  →", command=lambda: self.controller.show_frame("historique"),
            bg=FOND, fg=ACCENT, activeforeground=ACCENT, activebackground=FOND,
            font=("Segoe UI", 9, "bold"), bd=0, cursor="hand2",
        ).pack(side="right")

        carte = CarteArrondie(
            parent, bg_page=FOND, bg_carte=CARTE_BG, bordure=BORDURE, rayon=14,
            padx=1, pady=1,
        )
        carte.pack(fill="both", expand=True)

        colonnes = ("type", "numero", "date", "client", "montant", "statut")
        style = ttk.Style(self)
        style.configure("Dashboard.Treeview", rowheight=30, font=("Segoe UI", 10),
                         background="white", fieldbackground="white", borderwidth=0)
        style.configure("Dashboard.Treeview.Heading", font=("Segoe UI", 9, "bold"),
                         background="#f3f4f6", foreground=TEXTE_MUET)

        tree = ttk.Treeview(
            carte.interior, columns=colonnes, show="headings", height=8,
            style="Dashboard.Treeview", selectmode="none",
        )
        entetes = {
            "type": "Type", "numero": "N°", "date": "Date", "client": "Client",
            "montant": "Montant", "statut": "Statut",
        }
        for c in colonnes:
            tree.heading(c, text=entetes[c])
            tree.column(c, width=140, anchor="center")
        tree.column("client", width=200, anchor="w")

        for cle, couleur in STATUT_FOND.items():
            tree.tag_configure(cle, background=couleur)

        stats = db.get_stats()
        for d in stats["dernieres"]:
            type_label = {"facture": "Facture", "bl": "Bon de livraison",
                          "devis": "Devis"}.get(d["type"], d["type"])
            tree.insert("", "end", values=(
                type_label, d["numero"], d["date"], d["client_nom"],
                f"{db.format_montant(d['montant_total'])} {self.devise}",
                STATUT_LABELS.get(d["statut"], d["statut"]),
            ), tags=(d["statut"],))
        if not stats["dernieres"]:
            tk.Label(
                carte.interior, text="Aucun document pour l'instant.", bg=CARTE_BG,
                fg=TEXTE_MUET, font=("Segoe UI", 10), pady=30,
            ).pack()
        else:
            tree.pack(fill="both", expand=True)
