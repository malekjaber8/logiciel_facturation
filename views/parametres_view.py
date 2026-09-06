import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import db
from ui_helpers import BoutonArrondi

FOND = "#f5f6fa"
DEVISES = ["DT", "DA", "DH", "EUR", "USD"]
ACCENT = "#8b5e34"
ACCENT_HOVER = "#734a2a"


class ParametresFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent, bg=FOND, padx=25, pady=20)
        self.controller = controller
        params = db.get_all_params()

        tk.Label(self, text="Paramètres de l'entreprise", font=("Segoe UI", 18, "bold"),
                 bg=FOND).pack(anchor="w", pady=(0, 20))

        cadre = tk.Frame(self, bg=FOND)
        cadre.pack(anchor="w")

        tk.Label(cadre, text="Nom de l'entreprise", bg=FOND).grid(row=0, column=0, sticky="w", pady=5)
        self.nom_var = tk.StringVar(value=params.get("entreprise_nom", ""))
        ttk.Entry(cadre, textvariable=self.nom_var, width=45).grid(row=0, column=1, pady=5)

        tk.Label(cadre, text="Adresse", bg=FOND).grid(row=1, column=0, sticky="w", pady=5)
        self.adresse_var = tk.StringVar(value=params.get("entreprise_adresse", ""))
        ttk.Entry(cadre, textvariable=self.adresse_var, width=45).grid(row=1, column=1, pady=5)

        tk.Label(cadre, text="Téléphone", bg=FOND).grid(row=2, column=0, sticky="w", pady=5)
        self.tel_var = tk.StringVar(value=params.get("entreprise_tel", ""))
        ttk.Entry(cadre, textvariable=self.tel_var, width=45).grid(row=2, column=1, pady=5)

        tk.Label(cadre, text="Matricule fiscal", bg=FOND).grid(row=3, column=0, sticky="w", pady=5)
        self.matricule_var = tk.StringVar(value=params.get("entreprise_matricule", ""))
        ttk.Entry(cadre, textvariable=self.matricule_var, width=45).grid(row=3, column=1, pady=5)

        tk.Label(cadre, text="Devise", bg=FOND).grid(row=4, column=0, sticky="w", pady=5)
        self.devise_var = tk.StringVar(value=params.get("devise", "DT"))
        ttk.Combobox(cadre, textvariable=self.devise_var, values=DEVISES,
                     state="readonly", width=10).grid(row=4, column=1, sticky="w", pady=5)

        tk.Label(cadre, text="Logo (image)", bg=FOND).grid(row=5, column=0, sticky="w", pady=5)
        logo_frame = tk.Frame(cadre, bg=FOND)
        logo_frame.grid(row=5, column=1, sticky="w", pady=5)
        self.logo_var = tk.StringVar(value=params.get("entreprise_logo", ""))
        ttk.Entry(logo_frame, textvariable=self.logo_var, width=35).pack(side="left")
        ttk.Button(logo_frame, text="Parcourir...", command=self.choisir_logo).pack(
            side="left", padx=(5, 0)
        )

        BoutonArrondi(
            self, "💾  Enregistrer les paramètres", commande=self.enregistrer, bg_page=FOND,
            couleur=ACCENT, couleur_survol=ACCENT_HOVER,
            police=("Segoe UI", 11, "bold"), padx=18, pady=9,
        ).pack(anchor="w", pady=20)

        tk.Label(
            self,
            text="Ces informations apparaissent sur toutes les factures, bons de livraison "
                 "et devis.",
            bg=FOND, fg="#7f8c8d",
        ).pack(anchor="w")

    def choisir_logo(self):
        chemin = filedialog.askopenfilename(
            title="Choisir un logo",
            filetypes=[("Images", "*.png *.jpg *.jpeg")],
        )
        if chemin:
            self.logo_var.set(db.copier_logo(chemin))

    def enregistrer(self):
        db.set_param("entreprise_nom", self.nom_var.get().strip())
        db.set_param("entreprise_adresse", self.adresse_var.get().strip())
        db.set_param("entreprise_tel", self.tel_var.get().strip())
        db.set_param("entreprise_matricule", self.matricule_var.get().strip())
        db.set_param("devise", self.devise_var.get())
        db.set_param("entreprise_logo", self.logo_var.get().strip())
        messagebox.showinfo("Enregistré", "Les paramètres ont été mis à jour.")
