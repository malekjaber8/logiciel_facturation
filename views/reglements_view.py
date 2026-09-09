import tkinter as tk
from tkinter import ttk, messagebox

import db
from ui_helpers import BoutonArrondi

FOND = "#f5f6fa"
CARTE_BG = "white"
VERT = "#16a34a"
VERT_HOVER = "#15803d"
BLEU = "#2563eb"
BLEU_HOVER = "#1d4ed8"
GRIS = "#6b7280"
GRIS_HOVER = "#4b5563"
ROUGE = "#c0392b"
ROUGE_HOVER = "#a93226"
VERT_CLAIR = "#dcfce7"
ROUGE_CLAIR = "#fee2e2"
ORANGE_CLAIR = "#fef3c7"

MODES = [
    ("especes", "Espèces"),
    ("cheque", "Chèque"),
    ("traite", "Traite"),
    ("tpe", "TPE"),
    ("virement", "Virement"),
]
LABELS_MODES = {label: code for code, label in MODES}
LABEL_REFERENCE = {
    "especes": "Référence (optionnel)",
    "cheque": "N° de chèque",
    "traite": "N° de traite",
    "tpe": "N° de reçu TPE",
    "virement": "Référence du virement",
}
STATUT_LABELS = {"paye": "Payé", "partiel": "Partiel", "impaye": "Impayé"}
STATUT_FOND = {"paye": VERT_CLAIR, "partiel": ORANGE_CLAIR, "impaye": ROUGE_CLAIR}


class ReglementsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND)
        self.controller = controller
        self.devise = db.get_param("devise", "DT")
        self.document_selectionne = None
        self.paiement_selectionne = None

        self._construire_scroll()

        tk.Label(
            self.contenu, text="Gestion des règlements", font=("Segoe UI", 18, "bold"), bg=FOND,
        ).pack(anchor="w", pady=(0, 4))
        tk.Label(
            self.contenu, text="Bons de livraison et factures, avec le détail de leurs règlements.",
            bg=FOND, fg="#6b7280",
        ).pack(anchor="w", pady=(0, 15))

        tk.Label(
            self.contenu, text="Bons de livraison", font=("Segoe UI", 12, "bold"), bg=FOND,
        ).pack(anchor="w", pady=(0, 6))
        self.tree_bl = self._creer_table_documents()
        self.tree_bl.pack(fill="x", pady=(0, 12))
        self.tree_bl.bind("<<TreeviewSelect>>", lambda e: self._selectionner_document("bl"))

        tk.Label(
            self.contenu, text="Factures", font=("Segoe UI", 12, "bold"), bg=FOND,
        ).pack(anchor="w", pady=(0, 6))
        self.tree_facture = self._creer_table_documents()
        self.tree_facture.pack(fill="x", pady=(0, 12))
        self.tree_facture.bind(
            "<<TreeviewSelect>>", lambda e: self._selectionner_document("facture")
        )

        self.label_detail = tk.Label(
            self.contenu, text="Détail des règlements", font=("Segoe UI", 12, "bold"), bg=FOND,
        )
        self.label_detail.pack(anchor="w", pady=(0, 6))
        self.tree_detail = self._creer_table_detail()
        self.tree_detail.pack(fill="x", pady=(0, 8))
        self.tree_detail.bind("<<TreeviewSelect>>", self._selectionner_paiement)

        actions = tk.Frame(self.contenu, bg=FOND)
        actions.pack(fill="x", pady=(4, 20))
        BoutonArrondi(
            actions, "💳  Saisir un nouveau règlement", commande=self._nouveau_reglement,
            bg_page=FOND, couleur=VERT, couleur_survol=VERT_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "✏️  Modifier le règlement", commande=self._modifier_reglement,
            bg_page=FOND, couleur=BLEU, couleur_survol=BLEU_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "🗑️  Supprimer le règlement", commande=self._supprimer_reglement,
            bg_page=FOND, couleur=ROUGE, couleur_survol=ROUGE_HOVER,
        ).pack(side="left")

        self._documents = {}
        self.rafraichir()

    def _construire_scroll(self):
        canvas = tk.Canvas(self, bg=FOND, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.contenu = tk.Frame(canvas, bg=FOND, padx=25, pady=20)
        fenetre = canvas.create_window((0, 0), window=self.contenu, anchor="nw")
        self.contenu.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(fenetre, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all(
            "<MouseWheel>", lambda e: canvas.yview_scroll(int(-e.delta / 120), "units")
        )

    # ---------- Construction des tableaux ----------

    def _creer_table_documents(self):
        style = ttk.Style(self)
        style.map(
            "Reglements.Treeview",
            background=[("selected", "#cbd5e1")],
            foreground=[("selected", "#111827")],
        )
        colonnes = ("numero", "date", "client", "montant", "paye", "solde", "statut", "mode")
        tree = ttk.Treeview(
            self.contenu, columns=colonnes, show="headings", height=5,
            style="Reglements.Treeview",
        )
        entetes = {
            "numero": "N°", "date": "Date", "client": "Client",
            "montant": "Montant", "paye": "Payé", "solde": "Solde",
            "statut": "Statut", "mode": "Règlements",
        }
        for c in colonnes:
            tree.heading(c, text=entetes[c])
            tree.column(c, width=100, anchor="center")
        tree.column("client", width=170, anchor="w")
        tree.column("mode", width=200, anchor="w")
        for cle, couleur in STATUT_FOND.items():
            tree.tag_configure(cle, background=couleur)
        return tree

    def _creer_table_detail(self):
        colonnes = ("date", "montant", "mode", "reference")
        tree = ttk.Treeview(self.contenu, columns=colonnes, show="headings", height=6)
        entetes = {
            "date": "Date", "montant": f"Montant", "mode": "Type de règlement",
            "reference": "N° chèque / reçu / référence",
        }
        for c in colonnes:
            tree.heading(c, text=entetes[c])
            tree.column(c, width=140, anchor="center")
        tree.column("reference", width=220, anchor="w")
        return tree

    # ---------- Rafraîchissement ----------

    def rafraichir(self):
        self._remplir(self.tree_bl, "bl")
        self._remplir(self.tree_facture, "facture")
        self._rafraichir_detail()

    def _remplir(self, tree, type_doc):
        selection_precedente = self.document_selectionne
        for item in tree.get_children():
            tree.delete(item)
        documents = db.list_documents(type_doc=type_doc)
        for d in documents:
            solde = d["montant_total"] - d["montant_paye"]
            mode = db.get_details_paiements(d["id"])
            tree.insert("", "end", iid=d["id"], values=(
                d["numero"], d["date"], d["client_nom"],
                db.format_montant(d['montant_total']), db.format_montant(d['montant_paye']),
                db.format_montant(solde), STATUT_LABELS.get(d["statut"], d["statut"]), mode,
            ), tags=(d["statut"],))
            self._documents[d["id"]] = d
        if selection_precedente and str(selection_precedente) in tree.get_children():
            tree.selection_set(str(selection_precedente))

    def _selectionner_document(self, type_doc):
        tree = self.tree_bl if type_doc == "bl" else self.tree_facture
        autre = self.tree_facture if type_doc == "bl" else self.tree_bl
        sel = tree.selection()
        if not sel:
            return
        autre.selection_remove(*autre.selection()) if autre.selection() else None
        self.document_selectionne = int(sel[0])
        self._rafraichir_detail()

    def _rafraichir_detail(self):
        for item in self.tree_detail.get_children():
            self.tree_detail.delete(item)
        self.paiement_selectionne = None
        if not self.document_selectionne:
            self.label_detail.config(text="Détail des règlements")
            return
        doc, _, paiements = db.get_document(self.document_selectionne)
        self.label_detail.config(
            text=f"Détail des règlements — {doc['numero']} ({doc['client_nom']})"
        )
        for p in paiements:
            libelle_mode = db.MODES_PAIEMENT.get(p["mode"], p["mode"] or "-")
            self.tree_detail.insert("", "end", iid=p["id"], values=(
                p["date"], db.format_montant(p['montant']), libelle_mode, p["reference"] or "",
            ))

    def _selectionner_paiement(self, event=None):
        sel = self.tree_detail.selection()
        self.paiement_selectionne = int(sel[0]) if sel else None

    # ---------- Actions ----------

    def _nouveau_reglement(self):
        if not self.document_selectionne:
            messagebox.showwarning(
                "Aucune sélection",
                "Sélectionnez d'abord un bon de livraison ou une facture dans les tableaux.",
            )
            return
        doc, _, _ = db.get_document(self.document_selectionne)
        solde = doc["montant_total"] - doc["montant_paye"]
        if solde <= 0.001:
            messagebox.showinfo("Déjà réglé", "Ce document est déjà entièrement réglé.")
            return
        DialogueReglement(self, doc, solde, self.devise, on_confirme=self._confirmer_ajout)

    def _confirmer_ajout(self, document_id, montant, mode, reference):
        db.add_paiement(document_id, montant, mode=mode, reference=reference)
        self.rafraichir()

    def _modifier_reglement(self):
        if not self.paiement_selectionne:
            messagebox.showwarning(
                "Aucune sélection", "Sélectionnez d'abord un règlement dans le détail.",
            )
            return
        doc, _, paiements = db.get_document(self.document_selectionne)
        paiement = next(p for p in paiements if p["id"] == self.paiement_selectionne)
        solde_disponible = doc["montant_total"] - doc["montant_paye"] + paiement["montant"]
        DialogueReglement(
            self, doc, solde_disponible, self.devise, on_confirme=self._confirmer_modification,
            paiement_existant=paiement,
        )

    def _confirmer_modification(self, document_id, montant, mode, reference):
        db.update_paiement(self.paiement_selectionne, montant, mode=mode, reference=reference)
        self.rafraichir()

    def _supprimer_reglement(self):
        if not self.paiement_selectionne:
            messagebox.showwarning(
                "Aucune sélection", "Sélectionnez d'abord un règlement dans le détail.",
            )
            return
        if messagebox.askyesno(
            "Confirmation", "Supprimer définitivement ce règlement ?\n"
            "Le solde du document sera recalculé automatiquement.",
        ):
            db.delete_paiement(self.paiement_selectionne)
            self.rafraichir()


class DialogueReglement(tk.Toplevel):
    """Fenêtre de saisie (ou de modification) d'un règlement : type de
    règlement (espèces, chèque, traite, TPE, virement), sa référence (n° de
    chèque, de reçu TPE...) et le montant. Une facture ou un BL peut être
    réglé en plusieurs fois : le montant saisi ne peut pas dépasser le solde
    disponible, et ce qui n'est pas encore payé reste affiché comme impayé."""

    def __init__(self, parent, doc, solde_disponible, devise, on_confirme, paiement_existant=None):
        super().__init__(parent)
        self.on_confirme = on_confirme
        self.document_id = doc["id"]
        self.solde_disponible = solde_disponible
        self.devise = devise
        self.paiement_existant = paiement_existant

        modification = paiement_existant is not None
        self.title(
            f"Modifier le règlement — {doc['numero']}" if modification
            else f"Nouveau règlement — {doc['numero']}"
        )
        self.configure(bg=FOND, padx=28, pady=24)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        tk.Label(
            self, text="Modifier un règlement" if modification else "Saisir un règlement",
            font=("Segoe UI", 14, "bold"), bg=FOND,
        ).pack(anchor="w", pady=(0, 14))

        cadre_infos = tk.Frame(self, bg=CARTE_BG, highlightbackground="#e5e7eb",
                                 highlightthickness=1, padx=16, pady=12)
        cadre_infos.pack(fill="x", pady=(0, 16))
        self._ligne_info(cadre_infos, "Client", doc["client_nom"])
        self._ligne_info(cadre_infos, "Document N°", doc["numero"])
        self._ligne_info(
            cadre_infos,
            "Solde disponible" if modification else "Solde restant",
            f"{db.format_montant(solde_disponible)} {devise}", couleur="#c0392b",
        )

        tk.Label(self, text="Type de règlement", font=("Segoe UI", 10), bg=FOND).pack(
            anchor="w"
        )
        mode_initial = db.MODES_PAIEMENT.get(
            paiement_existant["mode"] if modification else "especes", MODES[0][1]
        )
        self.mode_var = tk.StringVar(value=mode_initial)
        combo_mode = ttk.Combobox(
            self, textvariable=self.mode_var, values=[label for _, label in MODES],
            state="readonly", width=30, font=("Segoe UI", 10),
        )
        combo_mode.pack(anchor="w", pady=(4, 14), ipady=4)
        combo_mode.bind("<<ComboboxSelected>>", lambda e: self._maj_label_reference())

        self.label_reference = tk.Label(self, text="", font=("Segoe UI", 10), bg=FOND)
        self.label_reference.pack(anchor="w")
        self.reference_var = tk.StringVar(
            value=paiement_existant["reference"] if modification and paiement_existant["reference"] else ""
        )
        ttk.Entry(
            self, textvariable=self.reference_var, width=32, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 14), ipady=4)
        self._maj_label_reference()

        tk.Label(
            self, text=f"Montant reçu ({devise})", font=("Segoe UI", 10), bg=FOND,
        ).pack(anchor="w")
        montant_initial = paiement_existant["montant"] if modification else solde_disponible
        self.montant_var = tk.StringVar(value=f"{montant_initial:.3f}")
        ttk.Entry(
            self, textvariable=self.montant_var, width=26, font=("Segoe UI", 10),
        ).pack(anchor="w", pady=(4, 20), ipady=4)

        boutons = tk.Frame(self, bg=FOND)
        boutons.pack(fill="x")
        BoutonArrondi(
            boutons, "Enregistrer les modifications" if modification else "Valider",
            commande=self._valider, bg_page=FOND, couleur=VERT, couleur_survol=VERT_HOVER,
            police=("Segoe UI", 10, "bold"), padx=16, pady=8,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            boutons, "Annuler", commande=self.destroy, bg_page=FOND,
            couleur=GRIS, couleur_survol=GRIS_HOVER, padx=16, pady=8,
        ).pack(side="left")

    def _ligne_info(self, parent, label, valeur, couleur="#111827"):
        ligne = tk.Frame(parent, bg=CARTE_BG)
        ligne.pack(fill="x", pady=2)
        tk.Label(
            ligne, text=f"{label} :", font=("Segoe UI", 10), bg=CARTE_BG, fg="#6b7280", width=16,
            anchor="w",
        ).pack(side="left")
        tk.Label(
            ligne, text=valeur, font=("Segoe UI", 10, "bold"), bg=CARTE_BG, fg=couleur,
        ).pack(side="left")

    def _maj_label_reference(self):
        code = LABELS_MODES.get(self.mode_var.get(), "especes")
        self.label_reference.config(text=LABEL_REFERENCE.get(code, "Référence"))

    def _valider(self):
        try:
            montant = float(self.montant_var.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Montant invalide", "Entrez un montant valide.", parent=self)
            return
        if montant <= 0:
            messagebox.showwarning(
                "Montant invalide", "Le montant doit être supérieur à 0.", parent=self,
            )
            return
        if montant > self.solde_disponible + 0.001:
            messagebox.showwarning(
                "Montant trop élevé",
                f"Le montant dépasse le solde disponible "
                f"({db.format_montant(self.solde_disponible)} {self.devise}).",
                parent=self,
            )
            return
        mode_code = LABELS_MODES[self.mode_var.get()]
        reference = self.reference_var.get().strip() or None
        self.on_confirme(self.document_id, montant, mode_code, reference)
        self.destroy()
