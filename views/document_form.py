import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from PIL import Image, ImageTk
from tkcalendar import DateEntry

import db
import pdf
import pdf_viewer
from ui_helpers import CarteArrondie, BoutonArrondi, RechercheAvecSuggestions

FOND = "#f5f6fa"
CARTE_BG = "white"
CARTE_BORDURE = "#e3e6ec"
ENTETE_TEINTE = "#fdf6ec"
ACCENT = "#8b5e34"
ACCENT_HOVER = "#734a2a"
ACCENT_CLAIR = "#f5ead9"
TEXTE_MUET = "#8b95a5"
MODIFIER_BG = "#e8f0fe"
MODIFIER_FG = "#1a56c4"
SUPPRIMER_BG = "#fdeaea"
SUPPRIMER_FG = "#c0392b"
BLEU = "#2563eb"
BLEU_HOVER = "#1d4ed8"
ROUGE = "#c0392b"
ROUGE_HOVER = "#a93226"
MINIATURE_LIGNE = (40, 40)
APERCU_TAILLE = (60, 60)
STATUT_LABELS_HISTORIQUE = {"paye": "Payé", "partiel": "Partiel", "impaye": "Impayé"}
STATUT_FOND_HISTORIQUE = {"paye": "#dcfce7", "partiel": "#fef3c7", "impaye": "#fee2e2"}

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = [
    "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

ICONES = {"facture": "🧾", "bl": "🚚", "devis": "📝"}
TITRES = {
    "facture": "Nouvelle facture",
    "bl": "Nouveau bon de livraison",
    "devis": "Nouveau devis / facture proforma",
}
SOUS_TITRES = {
    "facture": "Créez une facture et enregistrez-la automatiquement",
    "bl": "Enregistrez et gérez vos livraisons facilement",
    "devis": "Proposez un devis ou une facture proforma à votre client",
}
TITRES_HISTORIQUE = {
    "facture": "Historique des factures",
    "bl": "Historique des bons de livraison",
    "devis": "Historique des devis / factures proforma",
}


def formater_date_fr(d):
    return f"{JOURS_FR[d.weekday()]} {d.day} {MOIS_FR[d.month - 1]} {d.year}"


class DocumentFormFrame(tk.Frame):
    def __init__(self, parent, controller, type_doc, document_id_edition=None):
        super().__init__(parent, bg=FOND)
        self.controller = controller
        self.type_doc = type_doc
        self.devise = db.get_param("devise", "DT")
        self.lignes = []
        self._photo_apercu = None
        self._miniatures_lignes = []
        self._index_edition = None
        self.document_id_edition = None

        self._construire_scroll()

        self._construire_entete()
        self._construire_infos_generales()
        self._construire_ajout_article()
        self._construire_liste_lignes()
        self._construire_pied()
        self._construire_historique()

        self._mettre_a_jour_total()
        self._rafraichir_historique()

        if document_id_edition:
            self.document_historique_selectionne = document_id_edition
            self.modifier_document()

    # ---------- Construction de l'interface ----------

    def _construire_scroll(self):
        canvas = tk.Canvas(self, bg=FOND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.contenu = tk.Frame(canvas, bg=FOND, padx=25, pady=20)
        fenetre = canvas.create_window((0, 0), window=self.contenu, anchor="nw")
        self.contenu.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>",
            lambda e: canvas.itemconfig(fenetre, width=e.width),
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all(
            "<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units")
        )

    def _carte(self, expand=False):
        if expand:
            conteneur = tk.Frame(self.contenu, bg=CARTE_BG, highlightbackground=CARTE_BORDURE,
                                  highlightthickness=1, padx=20, pady=16)
            conteneur.pack(fill="both", expand=True, pady=(0, 15))
            return conteneur
        carte = CarteArrondie(
            self.contenu, bg_page=FOND, bg_carte=CARTE_BG, bordure=CARTE_BORDURE, rayon=14,
        )
        carte.pack(fill="x", pady=(0, 15))
        return carte.interior

    def _titre_section(self, parent, icone, texte, couleur_badge=ACCENT_CLAIR):
        cadre = tk.Frame(parent, bg=CARTE_BG)
        cadre.pack(fill="x", anchor="w", pady=(0, 14))
        tk.Label(
            cadre, text=icone, bg=couleur_badge, font=("Segoe UI Emoji", 13),
            width=3, height=1,
        ).pack(side="left", padx=(0, 10))
        tk.Label(
            cadre, text=texte, bg=CARTE_BG, font=("Segoe UI", 12, "bold"),
        ).pack(side="left")

    def _construire_entete(self):
        carte = CarteArrondie(
            self.contenu, bg_page=FOND, bg_carte=ENTETE_TEINTE, bordure=CARTE_BORDURE,
            rayon=14,
        )
        carte.pack(fill="x", pady=(0, 18))
        entete = carte.interior

        gauche = tk.Frame(entete, bg=ENTETE_TEINTE)
        gauche.pack(side="left")
        tk.Label(
            gauche, text=ICONES.get(self.type_doc, "📄"), bg=ACCENT_CLAIR,
            font=("Segoe UI Emoji", 20), width=3, height=1,
        ).pack(side="left", padx=(0, 12))
        textes = tk.Frame(gauche, bg=ENTETE_TEINTE)
        textes.pack(side="left")
        tk.Label(
            textes, text=TITRES.get(self.type_doc, "Nouveau document"), bg=ENTETE_TEINTE,
            font=("Segoe UI", 16, "bold"),
        ).pack(anchor="w")
        tk.Label(
            textes, text=SOUS_TITRES.get(self.type_doc, ""), bg=ENTETE_TEINTE,
            fg=TEXTE_MUET, font=("Segoe UI", 9),
        ).pack(anchor="w")

        droite = tk.Frame(
            entete, bg=CARTE_BG, highlightbackground=CARTE_BORDURE, highlightthickness=1,
            padx=14, pady=8,
        )
        droite.pack(side="right")
        tk.Label(droite, text="📅  Date du document", bg=CARTE_BG, fg=TEXTE_MUET,
                  font=("Segoe UI", 8)).pack(anchor="w")
        self.date_badge_label = tk.Label(
            droite, text="", bg=CARTE_BG, font=("Segoe UI", 10, "bold"),
        )
        self.date_badge_label.pack(anchor="w")

    def _construire_infos_generales(self):
        carte = self._carte()
        self._titre_section(carte, "📄", "Informations générales")

        ligne = tk.Frame(carte, bg=CARTE_BG)
        ligne.pack(fill="x")

        bloc_client = tk.Frame(ligne, bg=CARTE_BG)
        bloc_client.pack(side="left", padx=(0, 25))
        tk.Label(bloc_client, text="Client * (tapez pour rechercher)", bg=CARTE_BG,
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.clients = db.list_clients()
        self.noms_clients = [c["nom"] for c in self.clients]
        self.client_var = tk.StringVar()
        self.client_combo = ttk.Combobox(
            bloc_client, textvariable=self.client_var,
            values=self.noms_clients, width=42,
        )
        self.client_combo.pack(ipady=3)
        self.client_combo.bind("<<ComboboxSelected>>",
                                lambda e: self.client_combo.configure(values=self.noms_clients))
        self.recherche_client = RechercheAvecSuggestions(
            self.client_combo, self.client_var, self.noms_clients,
        )

        bloc_date = tk.Frame(ligne, bg=CARTE_BG)
        bloc_date.pack(side="left", padx=(0, 25))
        tk.Label(bloc_date, text="Date *", bg=CARTE_BG,
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.date_entry = DateEntry(
            bloc_date, textvariable=self.date_var, date_pattern="yyyy-mm-dd",
            width=13, background=ACCENT, foreground="white", borderwidth=1,
            locale="fr_FR",
        )
        self.date_entry.pack(ipady=2)
        self.date_var.trace_add("write", self._maj_badge_date)

        bloc_notes = tk.Frame(ligne, bg=CARTE_BG)
        bloc_notes.pack(side="left")
        tk.Label(bloc_notes, text="Notes", bg=CARTE_BG,
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.notes_var = tk.StringVar()
        ttk.Entry(bloc_notes, textvariable=self.notes_var, width=20).pack(ipady=3)

        self._maj_badge_date()

    def _maj_badge_date(self, *args):
        try:
            d = date.fromisoformat(self.date_var.get())
            self.date_badge_label.config(text=formater_date_fr(d))
        except ValueError:
            self.date_badge_label.config(text=self.date_var.get())

    def _construire_ajout_article(self):
        self.carte_ajout = self._carte()
        self._titre_section(self.carte_ajout, "➕", "Ajouter un article", ACCENT_CLAIR)

        produits = db.list_produits()

        def _affichage(p):
            return f"{p['nom']} ({p['code']})" if p["code"] else p["nom"]

        self.produits_par_affichage = {_affichage(p): p for p in produits}
        self.produits_par_nom = {p["nom"]: p for p in produits}

        if not produits:
            tk.Label(
                self.carte_ajout,
                text="Aucun article enregistré. Allez dans \"Articles\" pour en créer "
                     "avant de pouvoir facturer.",
                bg=CARTE_BG, fg=SUPPRIMER_FG,
            ).pack(anchor="w", pady=(0, 10))

        ligne = tk.Frame(self.carte_ajout, bg=CARTE_BG)
        ligne.pack(fill="x")

        bloc_article = tk.Frame(ligne, bg=CARTE_BG)
        bloc_article.pack(side="left", padx=(0, 15))
        tk.Label(bloc_article, text="Article * (tapez pour rechercher)", bg=CARTE_BG,
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.article_var = tk.StringVar()
        self.noms_articles = list(self.produits_par_affichage.keys())
        self.article_combo = ttk.Combobox(
            bloc_article, textvariable=self.article_var,
            values=self.noms_articles, width=40,
        )
        self.article_combo.pack(ipady=3)
        self.article_combo.bind("<<ComboboxSelected>>", self.remplir_depuis_produit)
        self.recherche_article = RechercheAvecSuggestions(
            self.article_combo, self.article_var, self.noms_articles,
            on_select=lambda v: self.remplir_depuis_produit(),
        )

        bloc_quantite = tk.Frame(ligne, bg=CARTE_BG)
        bloc_quantite.pack(side="left", padx=(0, 15))
        tk.Label(bloc_quantite, text="Quantité *", bg=CARTE_BG,
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.quantite_var = tk.StringVar(value="1")
        ttk.Spinbox(
            bloc_quantite, from_=0.001, to=100000, increment=1,
            textvariable=self.quantite_var, width=8,
        ).pack(ipady=3)

        bloc_prix = tk.Frame(ligne, bg=CARTE_BG)
        bloc_prix.pack(side="left", padx=(0, 15))
        tk.Label(bloc_prix, text=f"Prix unitaire ({self.devise}) *", bg=CARTE_BG,
                  font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 4))
        self.prix_var = tk.StringVar()
        ttk.Entry(bloc_prix, textvariable=self.prix_var, width=12).pack(ipady=3)

        bloc_apercu = tk.Frame(ligne, bg=CARTE_BG)
        bloc_apercu.pack(side="left", padx=(0, 15))
        self.apercu_frame = tk.Frame(
            bloc_apercu, bg="white", relief="solid", bd=1,
            width=APERCU_TAILLE[0], height=APERCU_TAILLE[1],
        )
        self.apercu_frame.pack_propagate(False)
        self.apercu_frame.pack(pady=(18, 0))
        self.apercu_label = tk.Label(self.apercu_frame, bg="white")
        self.apercu_label.pack(fill="both", expand=True)

        bloc_bouton = tk.Frame(ligne, bg=CARTE_BG)
        bloc_bouton.pack(side="left", fill="x", expand=True)
        self.bouton_ajouter_ligne = BoutonArrondi(
            bloc_bouton, "➕  Ajouter la ligne", commande=self.ajouter_ligne,
            bg_page=CARTE_BG, couleur=ACCENT, couleur_survol=ACCENT_HOVER,
        )
        self.bouton_ajouter_ligne.pack(side="bottom", anchor="e", pady=(18, 0))

    def _construire_liste_lignes(self):
        carte = self._carte(expand=True)
        entetes = tk.Frame(carte, bg="#eef1f8")
        entetes.pack(fill="x")
        colonnes = [
            ("Désignation", 4), ("Quantité", 1), ("Prix unitaire", 1),
            ("Total", 1), ("Actions", 1),
        ]
        for texte, poids in colonnes:
            tk.Label(entetes, text=texte, bg="#eef1f8", font=("Segoe UI", 9, "bold"),
                      anchor="w", padx=8, pady=6).pack(side="left", fill="x", expand=(poids > 1 or texte == "Désignation"))

        canvas_conteneur = tk.Frame(carte, bg=CARTE_BG)
        canvas_conteneur.pack(fill="both", expand=True)
        self.canvas_lignes = tk.Canvas(canvas_conteneur, bg=CARTE_BG, highlightthickness=0,
                                        height=230)
        scrollbar = ttk.Scrollbar(canvas_conteneur, orient="vertical",
                                   command=self.canvas_lignes.yview)
        self.corps_lignes = tk.Frame(self.canvas_lignes, bg=CARTE_BG)
        self._fenetre_lignes = self.canvas_lignes.create_window(
            (0, 0), window=self.corps_lignes, anchor="nw"
        )
        self.corps_lignes.bind(
            "<Configure>",
            lambda e: self.canvas_lignes.configure(scrollregion=self.canvas_lignes.bbox("all")),
        )
        self.canvas_lignes.bind(
            "<Configure>",
            lambda e: self.canvas_lignes.itemconfig(self._fenetre_lignes, width=e.width),
        )
        self.canvas_lignes.configure(yscrollcommand=scrollbar.set)
        self.canvas_lignes.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.label_vide = tk.Label(
            self.corps_lignes, text="Aucun article ajouté pour l'instant.",
            bg=CARTE_BG, fg=TEXTE_MUET, font=("Segoe UI", 10), pady=30,
        )
        self.label_vide.pack()

    def _construire_pied(self):
        bas = tk.Frame(self.contenu, bg=FOND)
        bas.pack(fill="x", pady=(5, 20))
        self.total_label = tk.Label(
            bas, text=f"🧮  Total : 0,000 {self.devise}", bg=FOND,
            font=("Segoe UI", 13, "bold"),
        )
        self.total_label.pack(side="left")

        self.bouton_enregistrer = BoutonArrondi(
            bas, "💾  Enregistrer", commande=self.enregistrer,
            bg_page=FOND, couleur=ACCENT, couleur_survol=ACCENT_HOVER,
            police=("Segoe UI", 11, "bold"), padx=18, pady=9,
        )
        self.bouton_enregistrer.pack(side="right")
        BoutonArrondi(
            bas, "↺  Réinitialiser", commande=self.reinitialiser,
            bg_page=FOND, couleur="#e9ebf0", couleur_survol="#dadde3",
            couleur_texte="#2c3e50", padx=14, pady=9,
        ).pack(side="right", padx=(0, 10))

    def _construire_historique(self):
        carte = self._carte(expand=False)
        self._titre_section(carte, "🕑", TITRES_HISTORIQUE.get(self.type_doc, "Historique"))

        filtres = tk.Frame(carte, bg=CARTE_BG)
        filtres.pack(fill="x", pady=(0, 6))

        tk.Label(filtres, text="Recherche (N° ou client):", bg=CARTE_BG).pack(side="left")
        self.hist_recherche_var = tk.StringVar()
        entree_recherche = ttk.Entry(filtres, textvariable=self.hist_recherche_var, width=22)
        entree_recherche.pack(side="left", padx=(5, 15))
        entree_recherche.bind("<KeyRelease>", lambda e: self._rafraichir_historique())

        self.hist_periode_active_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filtres, text="Filtrer par période", variable=self.hist_periode_active_var,
            command=self._rafraichir_historique,
        ).pack(side="left", padx=(0, 10))

        tk.Label(filtres, text="Du:", bg=CARTE_BG).pack(side="left")
        self.hist_date_debut_var = tk.StringVar(value=date.today().isoformat())
        DateEntry(
            filtres, textvariable=self.hist_date_debut_var, date_pattern="yyyy-mm-dd",
            width=11, locale="fr_FR",
        ).pack(side="left", padx=(5, 12))
        self.hist_date_debut_var.trace_add("write", lambda *a: self._sur_changement_periode())

        tk.Label(filtres, text="Au:", bg=CARTE_BG).pack(side="left")
        self.hist_date_fin_var = tk.StringVar(value=date.today().isoformat())
        DateEntry(
            filtres, textvariable=self.hist_date_fin_var, date_pattern="yyyy-mm-dd",
            width=11, locale="fr_FR",
        ).pack(side="left", padx=(5, 0))
        self.hist_date_fin_var.trace_add("write", lambda *a: self._sur_changement_periode())

        if self.type_doc in ("facture", "bl"):
            colonnes = ("numero", "date", "client", "total", "statut")
        else:
            colonnes = ("numero", "date", "client", "total")
        entetes = {
            "numero": "N°", "date": "Date", "client": "Client",
            "total": f"Total ({self.devise})", "statut": "Statut",
        }
        style = ttk.Style(self)
        style.map(
            "Historique.Treeview",
            background=[("selected", "#cbd5e1")],
            foreground=[("selected", "#111827")],
        )
        self.tree_historique = ttk.Treeview(
            carte, columns=colonnes, show="headings", height=6, style="Historique.Treeview",
        )
        for c in colonnes:
            self.tree_historique.heading(c, text=entetes[c])
            self.tree_historique.column(c, width=120, anchor="center")
        self.tree_historique.column("client", width=220, anchor="w")
        for cle, couleur in STATUT_FOND_HISTORIQUE.items():
            self.tree_historique.tag_configure(cle, background=couleur)
        self.tree_historique.pack(fill="x", pady=(0, 10))
        self.tree_historique.bind("<<TreeviewSelect>>", self._selectionner_historique)
        self.tree_historique.bind("<Double-1>", lambda e: self.modifier_document())

        actions = tk.Frame(carte, bg=CARTE_BG)
        actions.pack(fill="x")
        BoutonArrondi(
            actions, "📄  Ouvrir le PDF", commande=self.ouvrir_pdf_historique, bg_page=CARTE_BG,
            couleur=ACCENT, couleur_survol=ACCENT_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "✏️  Modifier", commande=self.modifier_document, bg_page=CARTE_BG,
            couleur=BLEU, couleur_survol=BLEU_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "🗑️  Supprimer", commande=self.supprimer_document, bg_page=CARTE_BG,
            couleur=ROUGE, couleur_survol=ROUGE_HOVER,
        ).pack(side="left", padx=(0, 10))

        self._documents_historique = {}
        self.document_historique_selectionne = None

    # ---------- Logique ----------

    def remplir_depuis_produit(self, event=None):
        self.article_combo.configure(values=self.noms_articles)
        p = self.produits_par_affichage.get(self.article_var.get())
        if not p:
            return
        self.prix_var.set(str(p["prix_unitaire"]))
        photo = self._charger_miniature(p["image_path"], APERCU_TAILLE)
        self._photo_apercu = photo
        if photo:
            self.apercu_label.config(image=photo, text="")
        else:
            self.apercu_label.config(image="", text="Pas\nd'image", fg="#95a5a6")

    def _charger_miniature(self, chemin, taille):
        chemin = db.resoudre_chemin_image(chemin)
        if not chemin:
            return None
        try:
            img = Image.open(chemin)
            img.thumbnail(taille)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def ajouter_ligne(self):
        article_affichage = self.article_var.get()
        produit = self.produits_par_affichage.get(article_affichage)
        if not produit:
            messagebox.showwarning(
                "Article requis",
                "Choisissez un article du catalogue (aucune saisie libre n'est autorisée).",
            )
            return
        try:
            quantite = float(self.quantite_var.get().replace(",", "."))
            prix = float(self.prix_var.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning(
                "Valeur invalide", "Quantité et prix unitaire doivent être des nombres."
            )
            return

        ligne = {
            "designation": produit["nom"], "code": produit["code"] or "",
            "quantite": quantite, "prix_unitaire": prix,
            "image_path": produit["image_path"], "affichage": article_affichage,
        }
        if self._index_edition is not None:
            self.lignes[self._index_edition] = ligne
            self._index_edition = None
            self.bouton_ajouter_ligne.set_texte("➕  Ajouter la ligne")
        else:
            self.lignes.append(ligne)

        self.article_combo.set("")
        self.quantite_var.set("1")
        self.prix_var.set("")
        self.apercu_label.config(image="", text="")
        self._redessiner_lignes()
        self._mettre_a_jour_total()

    def _modifier_ligne(self, index):
        ligne = self.lignes[index]
        self.article_var.set(ligne["affichage"])
        self.quantite_var.set(f"{ligne['quantite']:g}")
        self.prix_var.set(str(ligne["prix_unitaire"]))
        photo = self._charger_miniature(ligne["image_path"], APERCU_TAILLE)
        self._photo_apercu = photo
        if photo:
            self.apercu_label.config(image=photo, text="")
        self._index_edition = index
        self.bouton_ajouter_ligne.set_texte("✓  Modifier la ligne")

    def _supprimer_ligne(self, index):
        del self.lignes[index]
        if self._index_edition == index:
            self._index_edition = None
            self.bouton_ajouter_ligne.set_texte("➕  Ajouter la ligne")
        self._redessiner_lignes()
        self._mettre_a_jour_total()

    def _redessiner_lignes(self):
        for w in self.corps_lignes.winfo_children():
            w.destroy()
        self._miniatures_lignes = []

        if not self.lignes:
            self.label_vide = tk.Label(
                self.corps_lignes, text="Aucun article ajouté pour l'instant.",
                bg=CARTE_BG, fg=TEXTE_MUET, font=("Segoe UI", 10), pady=30,
            )
            self.label_vide.pack()
            return

        for i, ligne in enumerate(self.lignes):
            total_ligne = ligne["quantite"] * ligne["prix_unitaire"]
            rangee_bg = CARTE_BG if i % 2 == 0 else "#fafbfd"
            rangee = tk.Frame(self.corps_lignes, bg=rangee_bg)
            rangee.pack(fill="x")

            bloc_designation = tk.Frame(rangee, bg=rangee_bg)
            bloc_designation.pack(side="left", fill="x", expand=True, padx=8, pady=6)
            icone = self._charger_miniature(ligne.get("image_path"), MINIATURE_LIGNE)
            if icone:
                self._miniatures_lignes.append(icone)
                tk.Label(bloc_designation, image=icone, bg=rangee_bg).pack(side="left",
                                                                            padx=(0, 8))
            else:
                tk.Label(bloc_designation, text="🪵", bg=rangee_bg,
                          font=("Segoe UI Emoji", 16)).pack(side="left", padx=(0, 8))
            textes = tk.Frame(bloc_designation, bg=rangee_bg)
            textes.pack(side="left")
            tk.Label(textes, text=ligne["designation"], bg=rangee_bg,
                      font=("Segoe UI", 10, "bold"), anchor="w").pack(anchor="w")
            if ligne.get("code"):
                tk.Label(textes, text=ligne["code"], bg=rangee_bg, fg=TEXTE_MUET,
                          font=("Segoe UI", 8), anchor="w").pack(anchor="w")

            tk.Label(rangee, text=f"{ligne['quantite']:g}", bg=rangee_bg,
                      font=("Segoe UI", 10), width=10).pack(side="left")
            tk.Label(rangee, text=db.format_montant(ligne['prix_unitaire']), bg=rangee_bg,
                      font=("Segoe UI", 10), width=14).pack(side="left")
            tk.Label(rangee, text=db.format_montant(total_ligne), bg=rangee_bg,
                      font=("Segoe UI", 10, "bold"), width=14).pack(side="left")

            actions = tk.Frame(rangee, bg=rangee_bg)
            actions.pack(side="left", padx=8)
            tk.Button(
                actions, text="✏️", bg=MODIFIER_BG, fg=MODIFIER_FG, bd=0,
                font=("Segoe UI", 9), padx=6, pady=2,
                command=lambda idx=i: self._modifier_ligne(idx),
            ).pack(side="left", padx=(0, 4))
            tk.Button(
                actions, text="🗑️", bg=SUPPRIMER_BG, fg=SUPPRIMER_FG, bd=0,
                font=("Segoe UI", 9), padx=6, pady=2,
                command=lambda idx=i: self._supprimer_ligne(idx),
            ).pack(side="left")

            tk.Frame(self.corps_lignes, bg=CARTE_BORDURE, height=1).pack(fill="x")

    def _mettre_a_jour_total(self):
        total = sum(l["quantite"] * l["prix_unitaire"] for l in self.lignes)
        self.total_label.config(text=f"🧮  Total : {db.format_montant(total)} {self.devise}")

    def _vider_formulaire(self):
        self.lignes = []
        self._index_edition = None
        self.document_id_edition = None
        self.client_combo.set("")
        self.client_combo.configure(values=self.noms_clients)
        self.date_var.set(date.today().isoformat())
        self.notes_var.set("")
        self.article_combo.set("")
        self.article_combo.configure(values=self.noms_articles)
        self.quantite_var.set("1")
        self.prix_var.set("")
        self.apercu_label.config(image="", text="")
        self.bouton_ajouter_ligne.set_texte("➕  Ajouter la ligne")
        self.bouton_enregistrer.set_texte("💾  Enregistrer")
        self._redessiner_lignes()
        self._mettre_a_jour_total()

    def reinitialiser(self):
        if self.lignes and not messagebox.askyesno(
            "Réinitialiser", "Vider le formulaire et recommencer ?"
        ):
            return
        self._vider_formulaire()

    def enregistrer(self):
        if not self.client_var.get():
            messagebox.showwarning("Champ requis", "Sélectionnez un client.")
            return
        if not self.lignes:
            messagebox.showwarning("Aucun article", "Ajoutez au moins un article.")
            return
        client = next((c for c in self.clients if c["nom"] == self.client_var.get()), None)
        if not client:
            messagebox.showwarning(
                "Client invalide",
                "Sélectionnez un client existant dans la liste (utilisez la recherche).",
            )
            return
        if self.document_id_edition:
            db.update_document(
                self.document_id_edition, client["id"], self.lignes,
                self.notes_var.get().strip(), self.date_var.get().strip(),
            )
            document_id = self.document_id_edition
            numero = db.get_document(document_id)[0]["numero"]
        else:
            document_id, numero = db.create_document(
                self.type_doc, client["id"], self.lignes,
                self.notes_var.get().strip(), self.date_var.get().strip(),
            )
        filepath = pdf.generate_pdf(document_id)
        pdf_viewer.afficher_pdf(self, filepath, titre=numero)
        self._vider_formulaire()
        self._rafraichir_historique()

    # ---------- Historique intégré ----------

    def _sur_changement_periode(self):
        if self.hist_periode_active_var.get():
            self._rafraichir_historique()

    def _rafraichir_historique(self):
        for item in self.tree_historique.get_children():
            self.tree_historique.delete(item)
        self._documents_historique = {}
        periode_active = self.hist_periode_active_var.get()
        documents = db.list_documents(
            type_doc=self.type_doc,
            recherche=self.hist_recherche_var.get(),
            date_debut=self.hist_date_debut_var.get() if periode_active else None,
            date_fin=self.hist_date_fin_var.get() if periode_active else None,
        )
        for d in documents:
            if self.type_doc in ("facture", "bl"):
                valeurs = (d["numero"], d["date"], d["client_nom"],
                           db.format_montant(d['montant_total']),
                           STATUT_LABELS_HISTORIQUE.get(d["statut"], d["statut"]))
                self.tree_historique.insert(
                    "", "end", iid=d["id"], values=valeurs, tags=(d["statut"],),
                )
            else:
                valeurs = (d["numero"], d["date"], d["client_nom"],
                           db.format_montant(d['montant_total']))
                self.tree_historique.insert("", "end", iid=d["id"], values=valeurs)
            self._documents_historique[d["id"]] = d
        self.document_historique_selectionne = None

    def _selectionner_historique(self, event=None):
        sel = self.tree_historique.selection()
        self.document_historique_selectionne = int(sel[0]) if sel else None

    def ouvrir_pdf_historique(self):
        if not self.document_historique_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document.")
            return
        doc, _, _ = db.get_document(self.document_historique_selectionne)
        chemin_pdf = db.resoudre_chemin(doc["pdf_path"])
        if chemin_pdf and os.path.isfile(chemin_pdf):
            pdf_viewer.afficher_pdf(self, chemin_pdf, titre=doc["numero"])
        else:
            messagebox.showwarning(
                "PDF introuvable", "Régénérez ce document (modifiez-le puis enregistrez)."
            )

    def modifier_document(self):
        if not self.document_historique_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document à modifier.")
            return
        doc, lignes_db, _ = db.get_document(self.document_historique_selectionne)
        self.document_id_edition = doc["id"]
        self._index_edition = None
        self.bouton_ajouter_ligne.set_texte("➕  Ajouter la ligne")
        self.client_combo.set(doc["client_nom"])
        self.date_var.set(doc["date"])
        self.notes_var.set(doc["notes"] or "")
        self.lignes = []
        for l in lignes_db:
            produit = self.produits_par_nom.get(l["designation"])
            code = produit["code"] if produit and produit["code"] else ""
            affichage = f"{l['designation']} ({code})" if code else l["designation"]
            self.lignes.append({
                "designation": l["designation"], "code": code,
                "quantite": l["quantite"], "prix_unitaire": l["prix_unitaire"],
                "image_path": l["image_path"], "affichage": affichage,
            })
        self._redessiner_lignes()
        self._mettre_a_jour_total()
        self.bouton_enregistrer.set_texte(f"💾  Mettre à jour {doc['numero']}")
        messagebox.showinfo(
            "Modification",
            f"Le document {doc['numero']} est chargé dans le formulaire ci-dessus.\n"
            "Modifiez les informations ou les articles puis cliquez sur "
            "\"Mettre à jour\" pour enregistrer, ou \"Réinitialiser\" pour annuler.",
        )

    def supprimer_document(self):
        if not self.document_historique_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document à supprimer.")
            return
        doc = self._documents_historique.get(self.document_historique_selectionne)
        numero = doc["numero"] if doc else ""
        if messagebox.askyesno(
            "Confirmation", f"Supprimer définitivement le document {numero} ?"
        ):
            if self.document_id_edition == self.document_historique_selectionne:
                self._vider_formulaire()
            db.delete_document(self.document_historique_selectionne)
            self._rafraichir_historique()
