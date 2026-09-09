import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import date

from tkcalendar import DateEntry

import db
import pdf
import pdf_viewer
from ui_helpers import BoutonArrondi
from views.reglements_view import DialogueReglement

FOND = "#f5f6fa"
ACCENT = "#8b5e34"
ACCENT_HOVER = "#734a2a"
BLEU = "#2563eb"
BLEU_HOVER = "#1d4ed8"
VERT = "#16a34a"
VERT_HOVER = "#15803d"
GRIS = "#6b7280"
GRIS_HOVER = "#4b5563"
ROUGE = "#c0392b"
ROUGE_HOVER = "#a93226"
FONT_LABEL = ("Segoe UI", 10)
FONT_CHAMP = ("Segoe UI", 10)

TYPES = {
    "": "Tous", "facture": "Factures", "bl": "Bons de livraison",
    "devis": "Devis / Proforma",
}
STATUTS = {"": "Tous", "paye": "Payé", "partiel": "Partiel", "impaye": "Impayé"}


class HistoriqueFrame(tk.Frame):
    def __init__(self, parent, controller, recherche_initiale=""):
        super().__init__(parent, bg=FOND, padx=25, pady=20)
        self.controller = controller
        self.devise = db.get_param("devise", "DT")
        self.document_selectionne = None

        tk.Label(self, text="Historique", font=("Segoe UI", 18, "bold"), bg=FOND).pack(
            anchor="w", pady=(0, 15)
        )

        filtres = tk.Frame(self, bg=FOND)
        filtres.pack(fill="x", pady=(0, 10))

        style = ttk.Style(self)
        style.configure("Historique.TCombobox", font=FONT_CHAMP)
        style.configure("Historique.TEntry", font=FONT_CHAMP, padding=4)
        style.configure("Historique.TCheckbutton", font=FONT_LABEL, background=FOND)

        tk.Label(filtres, text="Type:", bg=FOND, font=FONT_LABEL).pack(side="left")
        self.type_var = tk.StringVar(value="")
        type_combo = ttk.Combobox(
            filtres, textvariable=self.type_var, values=list(TYPES.values()),
            state="readonly", width=20, font=FONT_CHAMP, style="Historique.TCombobox",
        )
        type_combo.current(0)
        type_combo.pack(side="left", padx=(6, 18), ipady=4)
        type_combo.bind("<<ComboboxSelected>>", lambda e: self.rafraichir())
        self.type_combo = type_combo

        tk.Label(filtres, text="Statut:", bg=FOND, font=FONT_LABEL).pack(side="left")
        self.statut_var = tk.StringVar(value="")
        statut_combo = ttk.Combobox(
            filtres, textvariable=self.statut_var, values=list(STATUTS.values()),
            state="readonly", width=16, font=FONT_CHAMP, style="Historique.TCombobox",
        )
        statut_combo.current(0)
        statut_combo.pack(side="left", padx=(6, 18), ipady=4)
        statut_combo.bind("<<ComboboxSelected>>", lambda e: self.rafraichir())
        self.statut_combo = statut_combo

        tk.Label(filtres, text="Recherche (N° ou client):", bg=FOND, font=FONT_LABEL).pack(side="left")
        self.recherche_var = tk.StringVar(value=recherche_initiale)
        entry = ttk.Entry(
            filtres, textvariable=self.recherche_var, width=28,
            font=FONT_CHAMP, style="Historique.TEntry",
        )
        entry.pack(side="left", padx=(6, 0), ipady=4)
        entry.bind("<KeyRelease>", lambda e: self.rafraichir())

        filtres_periode = tk.Frame(self, bg=FOND)
        filtres_periode.pack(fill="x", pady=(0, 10))

        self.periode_active_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            filtres_periode, text="Filtrer par période", variable=self.periode_active_var,
            command=self._basculer_periode, style="Historique.TCheckbutton",
        ).pack(side="left", padx=(0, 12))

        tk.Label(filtres_periode, text="Du:", bg=FOND, font=FONT_LABEL).pack(side="left")
        self.date_debut_var = tk.StringVar(value=date.today().isoformat())
        self.date_debut_entry = DateEntry(
            filtres_periode, textvariable=self.date_debut_var, date_pattern="yyyy-mm-dd",
            width=13, locale="fr_FR", font=FONT_CHAMP,
            background=ACCENT, foreground="white", borderwidth=1,
        )
        self.date_debut_entry.pack(side="left", padx=(6, 18), ipady=4)

        tk.Label(filtres_periode, text="Au:", bg=FOND, font=FONT_LABEL).pack(side="left")
        self.date_fin_var = tk.StringVar(value=date.today().isoformat())
        self.date_fin_entry = DateEntry(
            filtres_periode, textvariable=self.date_fin_var, date_pattern="yyyy-mm-dd",
            width=13, locale="fr_FR", font=FONT_CHAMP,
            background=ACCENT, foreground="white", borderwidth=1,
        )
        self.date_fin_entry.pack(side="left", padx=(6, 0), ipady=4)

        self.date_debut_var.trace_add("write", lambda *a: self._sur_changement_date())
        self.date_fin_var.trace_add("write", lambda *a: self._sur_changement_date())

        colonnes = ("type", "numero", "date", "client", "total", "paye", "reste", "statut", "mode")
        self.tree = ttk.Treeview(self, columns=colonnes, show="headings", height=16)
        entetes = {
            "type": "Type", "numero": "N°", "date": "Date", "client": "Client",
            "total": "Total", "paye": "Payé", "reste": "Reste", "statut": "Statut",
            "mode": "Mode de règlement",
        }
        for c in colonnes:
            self.tree.heading(c, text=entetes[c])
            self.tree.column(c, width=110, anchor="center")
        self.tree.column("client", width=180, anchor="w")
        self.tree.column("mode", width=150, anchor="w")
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.selectionner)
        self.tree.bind("<Double-1>", lambda e: self.ouvrir_pdf())

        actions = tk.Frame(self, bg=FOND)
        actions.pack(fill="x", pady=(4, 0))
        BoutonArrondi(
            actions, "📄  Ouvrir le PDF", commande=self.ouvrir_pdf, bg_page=FOND,
            couleur=ACCENT, couleur_survol=ACCENT_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "🔄  Régénérer le PDF", commande=self.regenerer_pdf, bg_page=FOND,
            couleur=GRIS, couleur_survol=GRIS_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "✏️  Modifier", commande=self.modifier, bg_page=FOND,
            couleur=BLEU, couleur_survol=BLEU_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "💳  Enregistrer un paiement", commande=self.ajouter_paiement, bg_page=FOND,
            couleur=VERT, couleur_survol=VERT_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "🗑️  Supprimer", commande=self.supprimer, bg_page=FOND,
            couleur=ROUGE, couleur_survol=ROUGE_HOVER,
        ).pack(side="left", padx=(0, 10))

        self._documents = {}
        self.rafraichir()

    def _type_reel(self):
        label = self.type_var.get()
        for k, v in TYPES.items():
            if v == label:
                return k
        return ""

    def _statut_reel(self):
        label = self.statut_var.get()
        for k, v in STATUTS.items():
            if v == label:
                return k
        return ""

    def _basculer_periode(self):
        self.rafraichir()

    def _sur_changement_date(self):
        if self.periode_active_var.get():
            self.rafraichir()

    def rafraichir(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._documents = {}
        periode_active = self.periode_active_var.get()
        rows = db.list_documents(
            type_doc=self._type_reel() or None,
            statut=self._statut_reel() or None,
            recherche=self.recherche_var.get(),
            date_debut=self.date_debut_var.get() if periode_active else None,
            date_fin=self.date_fin_var.get() if periode_active else None,
        )
        for d in rows:
            type_label = {"facture": "Facture", "bl": "Bon de livraison",
                          "devis": "Devis"}.get(d["type"], d["type"])
            reste = d["montant_total"] - d["montant_paye"]
            mode = db.get_details_paiements(d["id"])
            self.tree.insert("", "end", iid=d["id"], values=(
                type_label, d["numero"], d["date"], d["client_nom"],
                db.format_montant(d['montant_total']), db.format_montant(d['montant_paye']),
                db.format_montant(reste), d["statut"], mode,
            ))
            self._documents[d["id"]] = d

    def selectionner(self, event=None):
        sel = self.tree.selection()
        self.document_selectionne = int(sel[0]) if sel else None

    def ouvrir_pdf(self):
        if not self.document_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document.")
            return
        doc, _, _ = db.get_document(self.document_selectionne)
        chemin_pdf = db.resoudre_chemin(doc["pdf_path"])
        if chemin_pdf and os.path.isfile(chemin_pdf):
            pdf_viewer.afficher_pdf(self, chemin_pdf, titre=doc["numero"])
        else:
            messagebox.showwarning("PDF introuvable", "Régénérez le PDF pour ce document.")

    def regenerer_pdf(self):
        if not self.document_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document.")
            return
        doc, _, _ = db.get_document(self.document_selectionne)
        filepath = pdf.generate_pdf(self.document_selectionne)
        pdf_viewer.afficher_pdf(self, filepath, titre=doc["numero"])
        self.rafraichir()

    def ajouter_paiement(self):
        if not self.document_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document.")
            return
        doc, _, _ = db.get_document(self.document_selectionne)
        if doc["type"] == "devis":
            messagebox.showinfo("Non applicable", "Un devis n'est pas un document payant.")
            return
        reste = doc["montant_total"] - doc["montant_paye"]
        if reste <= 0.001:
            messagebox.showinfo("Déjà réglé", "Ce document est déjà entièrement réglé.")
            return
        DialogueReglement(self, doc, reste, self.devise, on_confirme=self._enregistrer_paiement)

    def _enregistrer_paiement(self, document_id, montant, mode, reference):
        db.add_paiement(document_id, montant, mode=mode, reference=reference)
        self.rafraichir()

    def modifier(self):
        if not self.document_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document à modifier.")
            return
        doc, _, _ = db.get_document(self.document_selectionne)
        self.controller.show_frame(doc["type"], document_id_edition=doc["id"])

    def supprimer(self):
        if not self.document_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un document.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer définitivement ce document ?"):
            db.delete_document(self.document_selectionne)
            self.document_selectionne = None
            self.rafraichir()
