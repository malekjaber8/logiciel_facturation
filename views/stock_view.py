import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

import db
from ui_helpers import BoutonArrondi
from views.produits_view import CATEGORIES_DEFAUT, TOUTES_CATEGORIES

FOND = "#f5f6fa"
ENTETE_BG = "#2c3e50"
MINIATURE_LISTE = (54, 54)
APERCU_FICHE = (110, 110)
POLICE_LABEL = ("Segoe UI", 11)
POLICE_ENTREE = ("Segoe UI", 11)
POLICE_ENTETE = ("Segoe UI", 14, "bold")
BLEU = "#2563eb"
BLEU_HOVER = "#1d4ed8"


class AjusterStockDialog(tk.Toplevel):
    """Fenêtre dédiée à la correction du stock d'un article - la seule
    façon de modifier cette quantité, séparée de la fiche article."""

    def __init__(self, parent, produit):
        super().__init__(parent)
        self.produit = produit
        self.resultat = None

        self.title("Ajuster le stock")
        self.configure(bg=FOND)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        style = ttk.Style(self)
        style.configure("Dialogue.TEntry", font=POLICE_ENTREE, padding=6)

        entete = tk.Frame(self, bg=ENTETE_BG)
        entete.pack(fill="x")
        tk.Label(
            entete, text="Ajuster le stock", bg=ENTETE_BG, fg="white", font=POLICE_ENTETE,
        ).pack(anchor="w", padx=25, pady=14)

        corps = tk.Frame(self, bg=FOND, padx=25, pady=20)
        corps.pack(fill="both", expand=True)

        col_image = tk.Frame(corps, bg=FOND)
        col_image.grid(row=0, column=0, sticky="n")
        apercu_cadre = tk.Frame(
            col_image, bg="white", relief="solid", bd=1,
            width=APERCU_FICHE[0], height=APERCU_FICHE[1],
        )
        apercu_cadre.pack()
        apercu_cadre.pack_propagate(False)
        apercu_label = tk.Label(apercu_cadre, bg="white", fg="#95a5a6", font=POLICE_LABEL)
        apercu_label.pack(fill="both", expand=True)
        self._photo_apercu = self._charger_image(produit["image_path"])
        if self._photo_apercu:
            apercu_label.config(image=self._photo_apercu)
        else:
            apercu_label.config(text="Aucune image")

        col_champs = tk.Frame(corps, bg=FOND)
        col_champs.grid(row=0, column=1, sticky="n", padx=(25, 0))

        titre = produit["nom"]
        if produit["code"]:
            titre += f" ({produit['code']})"
        tk.Label(
            col_champs, text=titre, bg=FOND, font=("Segoe UI", 13, "bold"),
        ).pack(anchor="w", pady=(0, 4))
        if produit["categorie"]:
            tk.Label(
                col_champs, text=produit["categorie"], bg=FOND, fg="#7f8c8d",
                font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(0, 14))

        tk.Label(
            col_champs, text=f"Stock actuel : {produit['stock']:g} {produit['unite']}",
            bg=FOND, font=("Segoe UI", 10), fg="#7f8c8d",
        ).pack(anchor="w", pady=(0, 4))

        tk.Label(col_champs, text="Nouvelle quantité en stock *", bg=FOND,
                 font=POLICE_LABEL).pack(anchor="w", pady=(0, 4))
        self.stock_var = tk.StringVar(value=f"{produit['stock']:g}")
        entree = ttk.Entry(
            col_champs, textvariable=self.stock_var, font=POLICE_ENTREE,
            style="Dialogue.TEntry", width=20,
        )
        entree.pack(anchor="w", ipady=3)
        entree.focus_set()
        entree.select_range(0, "end")

        ttk.Separator(self, orient="horizontal").pack(fill="x")
        pied = tk.Frame(self, bg=FOND)
        pied.pack(fill="x", padx=25, pady=15)

        tk.Button(
            pied, text="Enregistrer", command=self.enregistrer,
            bg=ENTETE_BG, fg="white", activebackground="#34495e", activeforeground="white",
            font=("Segoe UI", 11, "bold"), bd=0, padx=18, pady=8,
        ).pack(side="right")
        tk.Button(
            pied, text="Annuler", command=self.destroy,
            bg="#dcdde1", fg="#2c3e50", activebackground="#c8cbd1",
            font=("Segoe UI", 11), bd=0, padx=18, pady=8,
        ).pack(side="right", padx=(0, 10))

        self.bind("<Return>", lambda e: self.enregistrer())
        self.bind("<Escape>", lambda e: self.destroy())
        self._centrer(parent)
        self.wait_visibility()
        self.focus_set()

    def _charger_image(self, chemin):
        chemin = db.resoudre_chemin_image(chemin)
        if not chemin:
            return None
        try:
            img = Image.open(chemin)
            img.thumbnail(APERCU_FICHE)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _centrer(self, parent):
        self.update_idletasks()
        largeur = self.winfo_reqwidth()
        hauteur = self.winfo_reqheight()
        fenetre = parent.winfo_toplevel()
        x = fenetre.winfo_rootx() + (fenetre.winfo_width() - largeur) // 2
        y = fenetre.winfo_rooty() + (fenetre.winfo_height() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")

    def enregistrer(self):
        try:
            stock = float(self.stock_var.get().strip().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Valeur invalide", "La quantité en stock doit être un nombre.",
                                    parent=self)
            return
        if stock < 0:
            messagebox.showwarning("Valeur invalide", "Le stock ne peut pas être négatif.",
                                    parent=self)
            return
        self.resultat = stock
        self.destroy()


class StockFrame(tk.Frame):
    """Consultation et correction des quantités en stock, séparée de la
    gestion du catalogue (Articles) pour que les deux responsabilités ne
    soient pas mélangées dans le même écran."""

    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND, padx=25, pady=20)
        self.controller = controller
        self.produit_selectionne = None
        self._icones_liste = {}

        tk.Label(self, text="Gestion du stock", font=("Segoe UI", 18, "bold"), bg=FOND).pack(
            anchor="w", pady=(0, 5)
        )
        tk.Label(
            self,
            text="Consultez et corrigez les quantités en stock de chaque article.",
            bg=FOND, fg="#7f8c8d",
        ).pack(anchor="w", pady=(0, 15))

        recherche_frame = tk.Frame(self, bg=FOND)
        recherche_frame.pack(fill="x", pady=(0, 10))
        tk.Label(recherche_frame, text="Rechercher (nom ou code):", bg=FOND).pack(side="left")
        self.recherche_var = tk.StringVar()
        entry = ttk.Entry(recherche_frame, textvariable=self.recherche_var)
        entry.pack(side="left", fill="x", expand=True, padx=8)
        entry.bind("<KeyRelease>", lambda e: self.rafraichir())

        tk.Label(recherche_frame, text="Catégorie:", bg=FOND).pack(side="left", padx=(15, 0))
        self.categorie_filtre_var = tk.StringVar(value=TOUTES_CATEGORIES)
        self.categorie_filtre_combo = ttk.Combobox(
            recherche_frame, textvariable=self.categorie_filtre_var, state="readonly", width=22,
        )
        self.categorie_filtre_combo.pack(side="left", padx=(8, 0))
        self.categorie_filtre_combo.bind("<<ComboboxSelected>>", lambda e: self.rafraichir())

        style = ttk.Style(self)
        style.configure("Stock.Treeview", rowheight=64, font=("Segoe UI", 10))
        style.configure("Stock.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        colonnes = ("nom", "code", "categorie", "unite", "stock")
        self.tree = ttk.Treeview(
            self, columns=colonnes, show="tree headings", style="Stock.Treeview",
            height=6,
        )
        self.tree.heading("#0", text="Image")
        self.tree.column("#0", width=75, anchor="center", stretch=False)
        for c, label, w in [
            ("nom", "Désignation", 260), ("code", "Code", 110), ("categorie", "Catégorie", 150),
            ("unite", "Unité", 100), ("stock", "Stock actuel", 150),
        ]:
            self.tree.heading(c, text=label)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("rupture", foreground="#c0392b")
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.selectionner)
        self.tree.bind("<Double-1>", lambda e: self.ajuster_stock())

        actions = tk.Frame(self, bg=FOND)
        actions.pack(fill="x")
        BoutonArrondi(
            actions, "📥  Ajuster le stock", commande=self.ajuster_stock, bg_page=FOND,
            couleur=BLEU, couleur_survol=BLEU_HOVER,
        ).pack(side="left", padx=(0, 10))

        self.rafraichir()

    def _charger_miniature(self, chemin):
        chemin = db.resoudre_chemin_image(chemin)
        if not chemin:
            return None
        try:
            img = Image.open(chemin)
            img.thumbnail(MINIATURE_LISTE)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _rafraichir_filtre_categories(self):
        categories = [TOUTES_CATEGORIES] + sorted(
            set(CATEGORIES_DEFAUT) | set(db.list_categories())
        )
        self.categorie_filtre_combo.config(values=categories)
        if self.categorie_filtre_var.get() not in categories:
            self.categorie_filtre_var.set(TOUTES_CATEGORIES)

    def rafraichir(self):
        self._rafraichir_filtre_categories()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._icones_liste = {}
        categorie_filtre = self.categorie_filtre_var.get()
        if categorie_filtre == TOUTES_CATEGORIES:
            categorie_filtre = None
        for p in db.list_produits(self.recherche_var.get(), categorie=categorie_filtre):
            icone = self._charger_miniature(p["image_path"])
            if icone:
                self._icones_liste[p["id"]] = icone
            tags = ("rupture",) if p["stock"] <= 0 else ()
            self.tree.insert(
                "", "end", iid=p["id"], image=icone if icone else "", tags=tags,
                values=(p["nom"], p["code"] or "", p["categorie"] or "", p["unite"],
                        f"{p['stock']:g}"),
            )
        self.produit_selectionne = None

    def selectionner(self, event=None):
        sel = self.tree.selection()
        self.produit_selectionne = int(sel[0]) if sel else None

    def ajuster_stock(self):
        if not self.produit_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un article.")
            return
        produit = db.get_produit(self.produit_selectionne)
        if not produit:
            return
        dialogue = AjusterStockDialog(self, produit)
        self.wait_window(dialogue)
        if dialogue.resultat is not None:
            db.update_stock(self.produit_selectionne, dialogue.resultat)
            self.rafraichir()
