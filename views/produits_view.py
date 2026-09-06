import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from PIL import Image, ImageTk

import db
from ui_helpers import BoutonArrondi

FOND = "#f5f6fa"
ENTETE_BG = "#2c3e50"
UNITES = ["piece", "m", "m2", "m3", "kg", "lot"]
CATEGORIES_DEFAUT = ["Chaises", "Tables", "Piètements", "Meubles", "Autres"]
TOUTES_CATEGORIES = "Toutes les catégories"
MINIATURE_LISTE = (54, 54)
APERCU_FICHE = (210, 210)
POLICE_LABEL = ("Segoe UI", 11)
POLICE_ENTREE = ("Segoe UI", 11)
POLICE_ENTETE = ("Segoe UI", 14, "bold")
VERT = "#16a34a"
VERT_HOVER = "#15803d"
BLEU = "#2563eb"
BLEU_HOVER = "#1d4ed8"
ROUGE = "#c0392b"
ROUGE_HOVER = "#a93226"


class ArticleDialog(tk.Toplevel):
    """Fiche de création / modification d'un article, en fenêtre séparée.
    Rien n'est enregistré tant que l'utilisateur ne clique pas sur Enregistrer."""

    def __init__(self, parent, devise, produit=None):
        super().__init__(parent)
        self.produit = produit
        self.devise = devise
        self.image_source_choisie = None
        self.supprimer_image_flag = False
        self.resultat = None
        self._photo_apercu = None

        self.title("Modifier l'article" if produit else "Nouvel article")
        self.configure(bg=FOND)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        style = ttk.Style(self)
        style.configure("Dialogue.TEntry", font=POLICE_ENTREE, padding=6)
        style.configure("Dialogue.TCombobox", font=POLICE_ENTREE, padding=6)

        # --- Bandeau d'en-tête ---
        entete = tk.Frame(self, bg=ENTETE_BG)
        entete.pack(fill="x")
        tk.Label(
            entete, text=("Modifier l'article" if produit else "Nouvel article"),
            bg=ENTETE_BG, fg="white", font=POLICE_ENTETE,
        ).pack(anchor="w", padx=25, pady=14)

        # --- Corps : colonne image | colonne champs ---
        corps = tk.Frame(self, bg=FOND, padx=25, pady=20)
        corps.pack(fill="both", expand=True)

        col_image = tk.Frame(corps, bg=FOND)
        col_image.grid(row=0, column=0, sticky="n")

        tk.Label(col_image, text="Photo de l'article", bg=FOND,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        apercu_cadre = tk.Frame(
            col_image, bg="white", relief="solid", bd=1,
            width=APERCU_FICHE[0], height=APERCU_FICHE[1],
        )
        apercu_cadre.pack()
        apercu_cadre.pack_propagate(False)
        self.apercu_label = tk.Label(apercu_cadre, bg="white", fg="#95a5a6", font=POLICE_LABEL)
        self.apercu_label.pack(fill="both", expand=True)

        chemin_initial = produit["image_path"] if produit else None
        self._afficher_apercu(chemin_initial)

        ttk.Button(col_image, text="Choisir une image...", command=self.choisir_image).pack(
            fill="x", pady=(10, 6), ipady=3
        )
        ttk.Button(col_image, text="Retirer l'image", command=self.retirer_image).pack(
            fill="x", ipady=3
        )

        col_champs = tk.Frame(corps, bg=FOND)
        col_champs.grid(row=0, column=1, sticky="n", padx=(25, 0))
        col_champs.columnconfigure(0, weight=1, uniform="champ")
        col_champs.columnconfigure(1, weight=1, uniform="champ")
        corps.columnconfigure(1, weight=1)

        # Ordre demandé : désignation, code, puis prix
        tk.Label(col_champs, text="Désignation (nom) *", bg=FOND, font=POLICE_LABEL).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.nom_var = tk.StringVar(value=produit["nom"] if produit else "")
        ttk.Entry(
            col_champs, textvariable=self.nom_var, font=POLICE_ENTREE, style="Dialogue.TEntry",
        ).grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 12), ipady=3)

        tk.Label(col_champs, text="Code article *", bg=FOND, font=POLICE_LABEL).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.code_var = tk.StringVar(value=(produit["code"] or "") if produit else "")
        ttk.Entry(
            col_champs, textvariable=self.code_var, font=POLICE_ENTREE, style="Dialogue.TEntry",
        ).grid(row=3, column=0, columnspan=2, sticky="we", pady=(0, 12), ipady=3)

        tk.Label(col_champs, text="Catégorie", bg=FOND, font=POLICE_LABEL).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        categories_existantes = sorted(set(CATEGORIES_DEFAUT) | set(db.list_categories()))
        self.categorie_var = tk.StringVar(
            value=(produit["categorie"] or "") if produit else ""
        )
        ttk.Combobox(
            col_champs, textvariable=self.categorie_var, values=categories_existantes,
            font=POLICE_ENTREE, style="Dialogue.TCombobox",
        ).grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 12), ipady=3)

        tk.Label(col_champs, text=f"Prix unitaire ({devise}) *", bg=FOND, font=POLICE_LABEL).grid(
            row=6, column=0, sticky="w", pady=(0, 4)
        )
        tk.Label(col_champs, text="Unité", bg=FOND, font=POLICE_LABEL).grid(
            row=6, column=1, sticky="w", pady=(0, 4), padx=(12, 0)
        )
        self.prix_var = tk.StringVar(
            value=str(produit["prix_unitaire"]) if produit else ""
        )
        ttk.Entry(
            col_champs, textvariable=self.prix_var, font=POLICE_ENTREE, style="Dialogue.TEntry",
        ).grid(row=7, column=0, sticky="we", pady=(0, 12), ipady=3)

        self.unite_var = tk.StringVar(value=produit["unite"] if produit else "piece")
        ttk.Combobox(
            col_champs, textvariable=self.unite_var, values=UNITES, state="readonly",
            font=POLICE_ENTREE, style="Dialogue.TCombobox",
        ).grid(row=7, column=1, sticky="we", pady=(0, 12), ipady=3, padx=(12, 0))

        tk.Label(col_champs, text="Quantité en stock", bg=FOND, font=POLICE_LABEL).grid(
            row=8, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.stock_var = tk.StringVar(
            value=str(produit["stock"]) if produit else "0"
        )
        ttk.Entry(
            col_champs, textvariable=self.stock_var, font=POLICE_ENTREE, style="Dialogue.TEntry",
        ).grid(row=9, column=0, columnspan=2, sticky="we", pady=(0, 12), ipady=3)

        tk.Label(col_champs, text="Description", bg=FOND, font=POLICE_LABEL).grid(
            row=10, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.description_var = tk.StringVar(
            value=(produit["description"] or "") if produit else ""
        )
        ttk.Entry(
            col_champs, textvariable=self.description_var, font=POLICE_ENTREE,
            style="Dialogue.TEntry",
        ).grid(row=11, column=0, columnspan=2, sticky="we", ipady=3)

        # --- Pied : séparateur + actions ---
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

        self.bind("<Escape>", lambda e: self.destroy())
        self._centrer(parent)
        self.wait_visibility()
        self.focus_set()

    def _centrer(self, parent):
        self.update_idletasks()
        largeur = self.winfo_reqwidth()
        hauteur = self.winfo_reqheight()
        fenetre = parent.winfo_toplevel()
        x = fenetre.winfo_rootx() + (fenetre.winfo_width() - largeur) // 2
        y = fenetre.winfo_rooty() + (fenetre.winfo_height() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")

    def _afficher_apercu(self, chemin):
        photo = None
        chemin = db.resoudre_chemin_image(chemin)
        if chemin:
            try:
                img = Image.open(chemin)
                img.thumbnail(APERCU_FICHE)
                photo = ImageTk.PhotoImage(img)
            except Exception:
                photo = None
        self._photo_apercu = photo
        if photo:
            self.apercu_label.config(image=photo, text="")
        else:
            self.apercu_label.config(image="", text="Aucune image")

    def choisir_image(self):
        chemin = filedialog.askopenfilename(
            title="Choisir une image d'article",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.gif")],
        )
        if chemin:
            self.image_source_choisie = chemin
            self.supprimer_image_flag = False
            self._afficher_apercu(chemin)

    def retirer_image(self):
        self.image_source_choisie = None
        self.supprimer_image_flag = True
        self._afficher_apercu(None)

    def enregistrer(self):
        nom = self.nom_var.get().strip()
        if not nom:
            messagebox.showwarning("Champ requis", "Le nom de l'article est obligatoire.",
                                    parent=self)
            return
        code = self.code_var.get().strip()
        if not code:
            messagebox.showwarning("Champ requis", "Le code de l'article est obligatoire.",
                                    parent=self)
            return
        exclure_id = self.produit["id"] if self.produit else None
        if db.code_produit_existe(code, exclure_id=exclure_id):
            messagebox.showwarning(
                "Code déjà utilisé",
                f"Le code \"{code}\" est déjà utilisé par un autre article. "
                "Choisissez un code unique.",
                parent=self,
            )
            return
        try:
            prix = float(self.prix_var.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Valeur invalide", "Le prix unitaire doit être un nombre.",
                                    parent=self)
            return
        try:
            stock = float(self.stock_var.get().replace(",", "."))
        except ValueError:
            messagebox.showwarning("Valeur invalide", "La quantité en stock doit être un nombre.",
                                    parent=self)
            return
        self.resultat = {
            "nom": nom,
            "code": code,
            "categorie": self.categorie_var.get().strip(),
            "unite": self.unite_var.get(),
            "prix_unitaire": prix,
            "stock": stock,
            "description": self.description_var.get().strip(),
            "image_source_path": self.image_source_choisie,
            "supprimer_image": self.supprimer_image_flag,
        }
        self.destroy()


class ProduitsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND, padx=25, pady=20)
        self.controller = controller
        self.produit_selectionne = None
        self.devise = db.get_param("devise", "DT")
        self._icones_liste = {}

        tk.Label(self, text="Articles", font=("Segoe UI", 18, "bold"), bg=FOND).pack(
            anchor="w", pady=(0, 5)
        )
        tk.Label(
            self,
            text="Ce catalogue est la seule source d'articles utilisable dans les "
                 "factures, bons de livraison et devis.",
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
        style.configure("Produits.Treeview", rowheight=64, font=("Segoe UI", 10))
        style.configure("Produits.Treeview.Heading", font=("Segoe UI", 10, "bold"))

        colonnes = ("nom", "code", "categorie", "unite", "prix", "stock", "description")
        self.tree = ttk.Treeview(
            self, columns=colonnes, show="tree headings", style="Produits.Treeview",
        )
        self.tree.heading("#0", text="Image")
        self.tree.column("#0", width=75, anchor="center", stretch=False)
        for c, label, w in [
            ("nom", "Désignation", 210), ("code", "Code", 90), ("categorie", "Catégorie", 130),
            ("unite", "Unité", 80),
            ("prix", f"Prix unitaire ({self.devise})", 150), ("stock", "Stock", 90),
            ("description", "Description", 260),
        ]:
            self.tree.heading(c, text=label)
            self.tree.column(c, width=w, anchor="w")
        self.tree.tag_configure("rupture", foreground="#c0392b")
        self.tree.pack(fill="both", expand=True, pady=(0, 10))
        self.tree.bind("<<TreeviewSelect>>", self.selectionner)
        self.tree.bind("<Double-1>", lambda e: self.modifier())

        actions = tk.Frame(self, bg=FOND)
        actions.pack(fill="x")
        BoutonArrondi(
            actions, "➕  Ajouter", commande=self.ajouter, bg_page=FOND,
            couleur=VERT, couleur_survol=VERT_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "✏️  Modifier", commande=self.modifier, bg_page=FOND,
            couleur=BLEU, couleur_survol=BLEU_HOVER,
        ).pack(side="left", padx=(0, 10))
        BoutonArrondi(
            actions, "🗑️  Supprimer", commande=self.supprimer, bg_page=FOND,
            couleur=ROUGE, couleur_survol=ROUGE_HOVER,
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
                        f"{p['prix_unitaire']:,.3f}", f"{p['stock']:g}",
                        p["description"] or ""),
            )
        self.produit_selectionne = None

    def selectionner(self, event=None):
        sel = self.tree.selection()
        self.produit_selectionne = int(sel[0]) if sel else None

    def ajouter(self):
        dialogue = ArticleDialog(self, self.devise, produit=None)
        self.wait_window(dialogue)
        if dialogue.resultat:
            r = dialogue.resultat
            db.add_produit(
                r["nom"], r["code"], r["description"], r["prix_unitaire"], r["unite"],
                stock=r["stock"], image_source_path=r["image_source_path"],
                categorie=r["categorie"],
            )
            self.rafraichir()

    def modifier(self):
        if not self.produit_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un article à modifier.")
            return
        produit = db.get_produit(self.produit_selectionne)
        if not produit:
            return
        dialogue = ArticleDialog(self, self.devise, produit=produit)
        self.wait_window(dialogue)
        if dialogue.resultat:
            r = dialogue.resultat
            db.update_produit(
                self.produit_selectionne, r["nom"], r["code"], r["description"],
                r["prix_unitaire"], r["unite"], stock=r["stock"],
                image_source_path=r["image_source_path"],
                supprimer_image=r["supprimer_image"],
                categorie=r["categorie"],
            )
            self.rafraichir()

    def supprimer(self):
        if not self.produit_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un article à supprimer.")
            return
        if messagebox.askyesno("Confirmation", "Supprimer cet article ?"):
            db.delete_produit(self.produit_selectionne)
            self.rafraichir()
