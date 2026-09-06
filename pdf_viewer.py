import os
import tkinter as tk
from tkinter import messagebox

import pymupdf as fitz
from PIL import Image, ImageTk

FOND = "#f5f6fa"
ENTETE_BG = "#2c3e50"
ACCENT = "#8b5e34"
ACCENT_HOVER = "#734a2a"
ZOOM_MAX = 1.8


class VisionneusePDF(tk.Toplevel):
    def __init__(self, parent, filepath, titre="Document"):
        super().__init__(parent)
        self.filepath = filepath
        self._images = []

        self.title(titre)
        self.configure(bg=FOND)

        largeur, hauteur = 950, 860
        largeur = min(largeur, self.winfo_screenwidth() - 60)
        hauteur = min(hauteur, self.winfo_screenheight() - 60)
        x = (self.winfo_screenwidth() - largeur) // 2
        y = (self.winfo_screenheight() - hauteur) // 2
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.minsize(600, 400)
        self.transient(parent)

        barre = tk.Frame(self, bg=ENTETE_BG)
        barre.pack(fill="x")
        tk.Label(
            barre, text=f"📄  {titre}", bg=ENTETE_BG, fg="white",
            font=("Segoe UI", 12, "bold"),
        ).pack(side="left", padx=15, pady=10)

        tk.Button(
            barre, text="🖨️  Imprimer", command=self.imprimer,
            bg=ACCENT, fg="white", activebackground=ACCENT_HOVER, activeforeground="white",
            font=("Segoe UI", 10, "bold"), bd=0, padx=14, pady=6,
        ).pack(side="right", padx=(0, 10), pady=10)
        tk.Button(
            barre, text="📂  Ouvrir avec une autre application", command=self.ouvrir_externe,
            bg="#3f4d5e", fg="white", activebackground="#4d5d70", activeforeground="white",
            font=("Segoe UI", 10), bd=0, padx=12, pady=6,
        ).pack(side="right", padx=(0, 10), pady=10)

        conteneur = tk.Frame(self, bg="#d9dce2")
        conteneur.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(conteneur, bg="#d9dce2", highlightthickness=0)
        scrollbar = tk.Scrollbar(conteneur, orient="vertical", command=self.canvas.yview)
        self.corps = tk.Frame(self.canvas, bg="#d9dce2")
        fenetre = self.canvas.create_window((0, 0), window=self.corps, anchor="n")
        self.corps.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: self.canvas.coords(fenetre, e.width / 2, 0),
        )
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.canvas.bind_all("<MouseWheel>", self._molette)

        self._charger_pages()
        self.bind("<Escape>", lambda e: self.destroy())
        self.focus_set()

    def _molette(self, event):
        if self.winfo_exists():
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def _charger_pages(self):
        try:
            document = fitz.open(self.filepath)
        except Exception as exc:
            tk.Label(
                self.corps, text=f"Impossible d'afficher le PDF :\n{exc}",
                bg="#d9dce2", fg="#c0392b", font=("Segoe UI", 11), pady=40,
            ).pack()
            return

        self.update()
        largeur_dispo = self.canvas.winfo_width()
        if largeur_dispo <= 1:
            largeur_dispo = self.winfo_width()
        largeur_cible = max(largeur_dispo - 30, 600)

        for numero in range(len(document)):
            page = document.load_page(numero)
            zoom = min(ZOOM_MAX, largeur_cible / page.rect.width)
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            photo = ImageTk.PhotoImage(img)
            self._images.append(photo)
            tk.Label(self.corps, image=photo, bg="white", bd=0).pack(pady=12)
        document.close()

    def imprimer(self):
        try:
            os.startfile(self.filepath, "print")
        except Exception:
            messagebox.showwarning(
                "Impression impossible",
                "Aucune imprimante ou application PDF associée n'a été trouvée. "
                "Utilisez \"Ouvrir avec une autre application\" pour imprimer manuellement.",
                parent=self,
            )

    def ouvrir_externe(self):
        try:
            os.startfile(self.filepath)
        except Exception:
            messagebox.showwarning("Impossible", "Impossible d'ouvrir le fichier.", parent=self)


def afficher_pdf(parent, filepath, titre="Document"):
    VisionneusePDF(parent, filepath, titre)
