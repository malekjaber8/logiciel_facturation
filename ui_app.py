import tkinter as tk
from tkinter import ttk, messagebox

from PIL import Image, ImageTk

import db

# Palette reprise du logo de l'entreprise (fond brun tres sombre, accent bois)
# au lieu du bleu generique d'origine, pour une identite visuelle coherente.
COULEUR_SIDEBAR = "#231c14"
COULEUR_HOVER = "#372c22"
COULEUR_ACTIF = "#8b5e34"
COULEUR_TEXTE = "#e2e8f0"
COULEUR_TEXTE_MUET = "#a3968a"
COULEUR_SECTION = "#8a7c6f"
COULEUR_FOND = "#f5f6fa"
COULEUR_BORDURE = "#e5e7eb"
COULEUR_TITRE = "#111827"
LOGO_LARGEUR = 160


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Facturation - Meubles en Bois")
        self.geometry("1150x700")
        self.minsize(980, 620)
        self.configure(bg=COULEUR_FOND)

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Treeview", rowheight=26, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        style.configure("TLabel", font=("Segoe UI", 10), background=COULEUR_FOND)
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("TEntry", font=("Segoe UI", 10))

        self.sidebar = tk.Frame(self, bg=COULEUR_SIDEBAR, width=235)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        self.zone_droite = tk.Frame(self, bg=COULEUR_FOND)
        self.zone_droite.pack(side="right", fill="both", expand=True)

        self._build_topbar()

        self.container = tk.Frame(self.zone_droite, bg=COULEUR_FOND)
        self.container.pack(side="top", fill="both", expand=True)

        self.sidebar_buttons = {}
        self._active_key = None
        self._build_sidebar()

        from views.dashboard import DashboardFrame
        from views.clients_view import ClientsFrame
        from views.produits_view import ProduitsFrame
        from views.stock_view import StockFrame
        from views.document_form import DocumentFormFrame
        from views.historique_view import HistoriqueFrame
        from views.reglements_view import ReglementsFrame
        from views.statistiques_view import StatistiquesFrame
        from views.parametres_view import ParametresFrame

        self.frame_classes = {
            "dashboard": DashboardFrame,
            "clients": ClientsFrame,
            "produits": ProduitsFrame,
            "stock": StockFrame,
            "facture": lambda parent, controller, **kw: DocumentFormFrame(
                parent, controller, "facture", **kw
            ),
            "bl": lambda parent, controller, **kw: DocumentFormFrame(
                parent, controller, "bl", **kw
            ),
            "devis": lambda parent, controller, **kw: DocumentFormFrame(
                parent, controller, "devis", **kw
            ),
            "historique": HistoriqueFrame,
            "reglements": ReglementsFrame,
            "statistiques": StatistiquesFrame,
            "parametres": ParametresFrame,
        }

        self.show_frame("dashboard")

    # ---------- Barre du haut (commune à toutes les pages) ----------

    def _build_topbar(self):
        barre = tk.Frame(
            self.zone_droite, bg="white", highlightbackground=COULEUR_BORDURE,
            highlightthickness=0, height=60,
        )
        barre.pack(side="top", fill="x")
        barre.pack_propagate(False)
        tk.Frame(self.zone_droite, bg=COULEUR_BORDURE, height=1).pack(side="top", fill="x")

        interieur = tk.Frame(barre, bg="white", padx=25)
        interieur.pack(fill="both", expand=True)

        recherche_cadre = tk.Frame(
            interieur, bg="#f3f4f6",
        )
        recherche_cadre.pack(side="left", fill="x", expand=True, pady=14, ipady=6, ipadx=10)
        tk.Label(recherche_cadre, text="🔍", bg="#f3f4f6", font=("Segoe UI", 10)).pack(
            side="left", padx=(4, 6)
        )
        self.recherche_var = tk.StringVar()
        entree = tk.Entry(
            recherche_cadre, textvariable=self.recherche_var, bg="#f3f4f6", bd=0,
            font=("Segoe UI", 10), fg=COULEUR_TITRE, highlightthickness=0, relief="flat",
        )
        entree.pack(side="left", fill="x", expand=True)
        entree.bind("<Return>", self._rechercher_global)
        self._placeholder_recherche = "Rechercher un document, un client, un article..."
        entree.insert(0, self._placeholder_recherche)
        entree.config(fg=COULEUR_TEXTE_MUET)
        entree.bind("<FocusIn>", lambda e: self._effacer_placeholder(entree))
        entree.bind("<FocusOut>", lambda e: self._remettre_placeholder(entree))

        droite = tk.Frame(interieur, bg="white")
        droite.pack(side="right", padx=(15, 0))

        cloche = tk.Label(droite, text="🔔", bg="white", font=("Segoe UI", 13), cursor="hand2")
        cloche.pack(side="left", padx=(0, 18))
        cloche.bind("<Button-1>", lambda e: messagebox.showinfo(
            "Notifications", "Aucune nouvelle notification.", parent=self
        ))

        ttk.Separator(droite, orient="vertical").pack(side="left", fill="y", padx=(0, 15))

        profil = tk.Frame(droite, bg="white", cursor="hand2")
        profil.pack(side="left")
        tk.Label(
            profil, text="👤", bg="#f5ead9", fg=COULEUR_ACTIF, font=("Segoe UI", 11),
            width=2, height=1,
        ).pack(side="left", padx=(0, 8))
        bloc_nom = tk.Frame(profil, bg="white")
        bloc_nom.pack(side="left")
        nom_entreprise = db.get_param("entreprise_nom", "Mon entreprise")
        tk.Label(
            bloc_nom, text=nom_entreprise, bg="white", fg=COULEUR_TITRE,
            font=("Segoe UI", 9, "bold"), anchor="w",
        ).pack(anchor="w")
        tk.Label(
            bloc_nom, text="Paramètres", bg="white", fg=COULEUR_TEXTE_MUET,
            font=("Segoe UI", 8), anchor="w",
        ).pack(anchor="w")
        for w in (profil, *profil.winfo_children(), bloc_nom, *bloc_nom.winfo_children()):
            w.bind("<Button-1>", lambda e: self.show_frame("parametres"))

    def _effacer_placeholder(self, entree):
        if entree.get() == self._placeholder_recherche:
            entree.delete(0, "end")
            entree.config(fg=COULEUR_TITRE)

    def _remettre_placeholder(self, entree):
        if not entree.get():
            entree.insert(0, self._placeholder_recherche)
            entree.config(fg=COULEUR_TEXTE_MUET)

    def _rechercher_global(self, event=None):
        texte = self.recherche_var.get().strip()
        if not texte or texte == self._placeholder_recherche:
            return
        self.show_frame("historique", recherche_initiale=texte)

    # ---------- Barre latérale ----------

    def _build_sidebar(self):
        entete = tk.Frame(self.sidebar, bg=COULEUR_SIDEBAR)
        entete.pack(fill="x", pady=(22, 18), padx=22)
        self._logo_photo = self._charger_logo_sidebar()
        if self._logo_photo:
            tk.Label(entete, image=self._logo_photo, bg=COULEUR_SIDEBAR).pack(anchor="w")
        else:
            nom_entreprise = db.get_param("entreprise_nom", "Facturation")
            tk.Label(
                entete, text=f"🪵 {nom_entreprise}", bg=COULEUR_SIDEBAR, fg="white",
                font=("Segoe UI", 14, "bold"), wraplength=190, justify="left",
            ).pack(anchor="w")
            tk.Label(
                entete, text="Meubles • Chaises • Tables", bg=COULEUR_SIDEBAR,
                fg=COULEUR_TEXTE_MUET, font=("Segoe UI", 9),
            ).pack(anchor="w", pady=(2, 0))

        self._bouton_menu("dashboard", "🏠", "Tableau de bord")

        self._section("Gestion")
        self._bouton_menu("produits", "📦", "Articles")
        self._bouton_menu("stock", "📥", "Gestion du stock")
        self._bouton_menu("clients", "👥", "Clients")

        self._section("Facturation")
        self._bouton_menu("facture", "🧾", "Facture")
        self._bouton_menu("bl", "🚚", "Bon de livraison")
        self._bouton_menu("devis", "📝", "Devis / Proforma")

        self._section("Suivi")
        self._bouton_menu("historique", "🕒", "Historique")
        self._bouton_menu("reglements", "💰", "Gestion des règlements")
        self._bouton_menu("statistiques", "📊", "Statistiques")

        tk.Frame(self.sidebar, bg=COULEUR_SIDEBAR).pack(fill="both", expand=True)

        bas = tk.Frame(self.sidebar, bg=COULEUR_SIDEBAR)
        bas.pack(fill="x", padx=22, pady=(0, 16))
        tk.Label(
            bas, text="Le bois, notre passion", bg=COULEUR_SIDEBAR, fg=COULEUR_TEXTE_MUET,
            font=("Segoe UI", 9, "italic"),
        ).pack(anchor="w")
        tk.Frame(bas, bg=COULEUR_ACTIF, height=2, width=40).pack(anchor="w", pady=(6, 0))

        tk.Frame(self.sidebar, bg=COULEUR_HOVER, height=1).pack(fill="x", padx=22, pady=(0, 4))
        self._bouton_menu("parametres", "⚙️", "Paramètres")
        tk.Frame(self.sidebar, bg=COULEUR_SIDEBAR, height=14).pack()

    def _charger_logo_sidebar(self):
        chemin = db.resoudre_chemin_image(db.get_param("entreprise_logo", ""))
        if not chemin:
            return None
        try:
            img = Image.open(chemin)
            hauteur = int(img.height * LOGO_LARGEUR / img.width)
            img = img.resize((LOGO_LARGEUR, hauteur), Image.Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception:
            return None

    def _section(self, texte):
        tk.Label(
            self.sidebar, text=texte.upper(), bg=COULEUR_SIDEBAR, fg=COULEUR_SECTION,
            font=("Segoe UI", 8, "bold"),
        ).pack(fill="x", padx=22, pady=(16, 4), anchor="w")

    def _bouton_menu(self, key, icone, label):
        cadre = tk.Frame(self.sidebar, bg=COULEUR_SIDEBAR)
        cadre.pack(fill="x", padx=10, pady=1)

        btn = tk.Label(
            cadre, text=f"  {icone}   {label}", bg=COULEUR_SIDEBAR, fg=COULEUR_TEXTE,
            font=("Segoe UI", 10), anchor="w", padx=10, pady=10, cursor="hand2",
        )
        btn.pack(fill="x")
        btn.bind("<Button-1>", lambda e, k=key: self.show_frame(k))
        btn.bind("<Enter>", lambda e, k=key: self._survol(k, True))
        btn.bind("<Leave>", lambda e, k=key: self._survol(k, False))
        self.sidebar_buttons[key] = btn

    def _survol(self, key, entree):
        if key == self._active_key:
            return
        btn = self.sidebar_buttons[key]
        btn.configure(bg=COULEUR_HOVER if entree else COULEUR_SIDEBAR)

    def show_frame(self, key, **kwargs):
        for f in self.container.winfo_children():
            f.destroy()
        frame_class = self.frame_classes[key]
        frame = frame_class(self.container, self, **kwargs)
        frame.pack(fill="both", expand=True)
        self._active_key = key
        for k, btn in self.sidebar_buttons.items():
            btn.configure(
                bg=COULEUR_ACTIF if k == key else COULEUR_SIDEBAR,
                font=("Segoe UI", 10, "bold" if k == key else "normal"),
            )
