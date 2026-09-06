import tkinter as tk
from tkinter import ttk, messagebox

import db
from ui_helpers import BoutonArrondi

FOND = "#f5f6fa"
ENTETE_BG = "#2c3e50"
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


class ClientDialog(tk.Toplevel):
    """Fiche de création / modification d'un client, en fenêtre séparée.
    Rien n'est enregistré tant que l'utilisateur ne clique pas sur Enregistrer.
    Même structure (bandeau, colonne icône + colonne champs, pied) que la
    fiche article, pour garder les deux fiches à la même taille."""

    def __init__(self, parent, client=None):
        super().__init__(parent)
        self.client = client
        self.resultat = None

        self.title("Modifier le client" if client else "Nouveau client")
        self.configure(bg=FOND)
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        style = ttk.Style(self)
        style.configure("Dialogue.TEntry", font=POLICE_ENTREE, padding=6)

        # --- Bandeau d'en-tête ---
        entete = tk.Frame(self, bg=ENTETE_BG)
        entete.pack(fill="x")
        tk.Label(
            entete, text=("Modifier le client" if client else "Nouveau client"),
            bg=ENTETE_BG, fg="white", font=POLICE_ENTETE,
        ).pack(anchor="w", padx=25, pady=14)

        # --- Corps : colonne icône | colonne champs ---
        corps = tk.Frame(self, bg=FOND, padx=25, pady=20)
        corps.pack(fill="both", expand=True)

        type_initial = (client["type_client"] if client else "societe") or "societe"
        self.type_var = tk.StringVar(value=type_initial)

        col_icone = tk.Frame(corps, bg=FOND)
        col_icone.grid(row=0, column=0, sticky="n")

        tk.Label(col_icone, text="Type de client", bg=FOND,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 8))
        icone_cadre = tk.Frame(
            col_icone, bg="white", relief="solid", bd=1,
            width=APERCU_FICHE[0], height=APERCU_FICHE[1],
        )
        icone_cadre.pack()
        icone_cadre.pack_propagate(False)
        self.icone_label = tk.Label(icone_cadre, bg="white", font=("Segoe UI Emoji", 64))
        self.icone_label.pack(fill="both", expand=True)

        type_frame = tk.Frame(col_icone, bg=FOND)
        type_frame.pack(pady=(10, 0))
        tk.Radiobutton(
            type_frame, text="Société", variable=self.type_var, value="societe",
            bg=FOND, font=POLICE_LABEL, command=self._basculer_type,
        ).pack(side="left", padx=(0, 12))
        tk.Radiobutton(
            type_frame, text="Particulier", variable=self.type_var, value="particulier",
            bg=FOND, font=POLICE_LABEL, command=self._basculer_type,
        ).pack(side="left")

        col_champs = tk.Frame(corps, bg=FOND)
        col_champs.grid(row=0, column=1, sticky="n", padx=(25, 0))
        col_champs.columnconfigure(0, weight=1, uniform="champ")
        col_champs.columnconfigure(1, weight=1, uniform="champ")

        tk.Label(col_champs, text="Nom *", bg=FOND, font=POLICE_LABEL).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.nom_var = tk.StringVar(value=client["nom"] if client else "")
        ttk.Entry(
            col_champs, textvariable=self.nom_var, font=POLICE_ENTREE, style="Dialogue.TEntry",
        ).grid(row=1, column=0, columnspan=2, sticky="we", pady=(0, 12), ipady=3)

        self.identifiant_label = tk.Label(col_champs, text="Matricule fiscal", bg=FOND,
                                           font=POLICE_LABEL)
        self.identifiant_label.grid(row=2, column=0, sticky="w", pady=(0, 4))
        tk.Label(col_champs, text="Téléphone", bg=FOND, font=POLICE_LABEL).grid(
            row=2, column=1, sticky="w", pady=(0, 4), padx=(12, 0)
        )
        valeur_identifiant = ""
        if client:
            if type_initial == "particulier":
                valeur_identifiant = client["cin"] or ""
            else:
                valeur_identifiant = client["matricule_fiscal"] or ""
        self.identifiant_var = tk.StringVar(value=valeur_identifiant)
        ttk.Entry(
            col_champs, textvariable=self.identifiant_var, font=POLICE_ENTREE,
            style="Dialogue.TEntry",
        ).grid(row=3, column=0, sticky="we", pady=(0, 12), ipady=3)

        self.tel_var = tk.StringVar(value=(client["telephone"] or "") if client else "")
        ttk.Entry(
            col_champs, textvariable=self.tel_var, font=POLICE_ENTREE, style="Dialogue.TEntry",
        ).grid(row=3, column=1, sticky="we", pady=(0, 12), ipady=3, padx=(12, 0))

        tk.Label(col_champs, text="Adresse", bg=FOND, font=POLICE_LABEL).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.adresse_var = tk.StringVar(value=(client["adresse"] or "") if client else "")
        ttk.Entry(
            col_champs, textvariable=self.adresse_var, font=POLICE_ENTREE,
            style="Dialogue.TEntry",
        ).grid(row=5, column=0, columnspan=2, sticky="we", pady=(0, 12), ipady=3)

        tk.Label(col_champs, text="Email", bg=FOND, font=POLICE_LABEL).grid(
            row=6, column=0, columnspan=2, sticky="w", pady=(0, 4)
        )
        self.email_var = tk.StringVar(value=(client["email"] or "") if client else "")
        ttk.Entry(
            col_champs, textvariable=self.email_var, font=POLICE_ENTREE,
            style="Dialogue.TEntry",
        ).grid(row=7, column=0, columnspan=2, sticky="we", ipady=3)

        self._basculer_type()

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

    def _basculer_type(self):
        if self.type_var.get() == "particulier":
            self.identifiant_label.config(text="N° CIN")
            self.icone_label.config(text="👤")
        else:
            self.identifiant_label.config(text="Matricule fiscal")
            self.icone_label.config(text="🏢")

    def _centrer(self, parent):
        self.update_idletasks()
        largeur = self.winfo_reqwidth()
        hauteur = self.winfo_reqheight()
        fenetre = parent.winfo_toplevel()
        x = fenetre.winfo_rootx() + (fenetre.winfo_width() - largeur) // 2
        y = fenetre.winfo_rooty() + (fenetre.winfo_height() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{max(x, 0)}+{max(y, 0)}")

    def enregistrer(self):
        nom = self.nom_var.get().strip()
        if not nom:
            messagebox.showwarning("Champ requis", "Le nom du client est obligatoire.",
                                    parent=self)
            return
        type_client = self.type_var.get()
        identifiant = self.identifiant_var.get().strip()
        self.resultat = {
            "nom": nom,
            "adresse": self.adresse_var.get().strip(),
            "telephone": self.tel_var.get().strip(),
            "type_client": type_client,
            "matricule_fiscal": identifiant if type_client == "societe" else "",
            "cin": identifiant if type_client == "particulier" else "",
            "email": self.email_var.get().strip(),
        }
        self.destroy()


class ClientsFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND, padx=25, pady=20)
        self.controller = controller
        self.client_selectionne = None

        tk.Label(self, text="Clients", font=("Segoe UI", 18, "bold"), bg=FOND).pack(
            anchor="w", pady=(0, 15)
        )

        recherche_frame = tk.Frame(self, bg=FOND)
        recherche_frame.pack(fill="x", pady=(0, 10))
        tk.Label(recherche_frame, text="Rechercher:", bg=FOND).pack(side="left")
        self.recherche_var = tk.StringVar()
        entry = ttk.Entry(recherche_frame, textvariable=self.recherche_var)
        entry.pack(side="left", fill="x", expand=True, padx=8)
        entry.bind("<KeyRelease>", lambda e: self.rafraichir())

        colonnes = ("nom", "type", "telephone", "identifiant", "adresse")
        self.tree = ttk.Treeview(self, columns=colonnes, show="headings")
        for c, label, w in [
            ("nom", "Nom", 180), ("type", "Type", 90), ("telephone", "Téléphone", 110),
            ("identifiant", "Matricule / CIN", 140), ("adresse", "Adresse", 220),
        ]:
            self.tree.heading(c, text=label)
            self.tree.column(c, width=w, anchor="w")
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

    def rafraichir(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for c in db.list_clients(self.recherche_var.get()):
            type_label = "Particulier" if c["type_client"] == "particulier" else "Société"
            identifiant = c["cin"] if c["type_client"] == "particulier" else c["matricule_fiscal"]
            self.tree.insert(
                "", "end", iid=c["id"],
                values=(c["nom"], type_label, c["telephone"] or "",
                        identifiant or "", c["adresse"] or ""),
            )
        self.client_selectionne = None

    def selectionner(self, event=None):
        sel = self.tree.selection()
        self.client_selectionne = int(sel[0]) if sel else None

    def ajouter(self):
        dialogue = ClientDialog(self, client=None)
        self.wait_window(dialogue)
        if dialogue.resultat:
            r = dialogue.resultat
            db.add_client(
                r["nom"], r["adresse"], r["telephone"], r["type_client"],
                r["matricule_fiscal"], r["cin"], r["email"],
            )
            self.rafraichir()

    def modifier(self):
        if not self.client_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un client à modifier.")
            return
        client = db.get_client(self.client_selectionne)
        if not client:
            return
        dialogue = ClientDialog(self, client=client)
        self.wait_window(dialogue)
        if dialogue.resultat:
            r = dialogue.resultat
            db.update_client(
                self.client_selectionne, r["nom"], r["adresse"], r["telephone"],
                r["type_client"], r["matricule_fiscal"], r["cin"], r["email"],
            )
            self.rafraichir()

    def supprimer(self):
        if not self.client_selectionne:
            messagebox.showwarning("Aucune sélection", "Sélectionnez un client à supprimer.")
            return
        if messagebox.askyesno(
            "Confirmation",
            "Supprimer ce client ? Cette action est irréversible.",
        ):
            try:
                db.delete_client(self.client_selectionne)
            except Exception:
                messagebox.showerror(
                    "Impossible",
                    "Ce client a des factures, BL ou devis associés, suppression "
                    "impossible.",
                )
                return
            self.rafraichir()
