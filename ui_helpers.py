"""Petits composants Tkinter maison pour se rapprocher d'un rendu web moderne
(coins arrondis, boutons arrondis) - Tkinter ne les propose pas nativement."""

import tkinter as tk


def _points_rectangle_arrondi(x1, y1, x2, y2, rayon):
    r = rayon
    return [
        x1 + r, y1,
        x2 - r, y1,
        x2, y1,
        x2, y1 + r,
        x2, y2 - r,
        x2, y2,
        x2 - r, y2,
        x1 + r, y2,
        x1, y2,
        x1, y2 - r,
        x1, y1 + r,
        x1, y1,
    ]


def dessiner_rectangle_arrondi(canvas, x1, y1, x2, y2, rayon=12, **kwargs):
    return canvas.create_polygon(
        _points_rectangle_arrondi(x1, y1, x2, y2, rayon), smooth=True, **kwargs
    )


class CarteArrondie(tk.Frame):
    """Carte à coins arrondis : on pack/grid les widgets enfants dans .interior
    exactement comme dans un tk.Frame classique."""

    def __init__(self, parent, bg_page, bg_carte="white", bordure="#e5e7eb",
                 rayon=14, padx=20, pady=16, **kwargs):
        super().__init__(parent, bg=bg_page, highlightthickness=0)
        self.bg_page = bg_page
        self.bg_carte = bg_carte
        self.bordure = bordure
        self.rayon = rayon

        self.canvas = tk.Canvas(self, bg=bg_page, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        self.interior = tk.Frame(self.canvas, bg=bg_carte, padx=padx, pady=pady, **kwargs)
        # Le cadre interieur est en retrait de "rayon" sur chaque bord : ca laisse
        # la courbe du fond visible dans les coins au lieu d'etre masquee par les
        # angles droits du Frame pose par-dessus.
        self._fenetre = self.canvas.create_window(
            self.rayon, self.rayon, window=self.interior, anchor="nw"
        )

        self.canvas.bind("<Configure>", self._sur_redimension_canvas)
        self.interior.bind("<Configure>", self._sur_redimension_interior)
        self._derniere_taille = (0, 0)

    def _redessiner(self):
        largeur_dispo = self.canvas.winfo_width()
        if largeur_dispo < 4:
            largeur_dispo = self.interior.winfo_reqwidth() + 2 * self.rayon
        largeur_interior = max(largeur_dispo - 2 * self.rayon, 10)
        self.canvas.itemconfig(self._fenetre, width=largeur_interior)
        self.interior.update_idletasks()

        h = self.interior.winfo_reqheight() + 2 * self.rayon
        w = largeur_dispo
        if (w, h) == self._derniere_taille:
            return
        self._derniere_taille = (w, h)
        self.canvas.delete("fond")
        dessiner_rectangle_arrondi(
            self.canvas, 1, 1, w - 1, h - 1, rayon=self.rayon,
            fill=self.bg_carte, outline=self.bordure, width=1, tags="fond",
        )
        self.canvas.tag_lower("fond")
        self.canvas.config(height=h)

    def _sur_redimension_canvas(self, event):
        self.interior.update_idletasks()
        self._redessiner()

    def _sur_redimension_interior(self, event):
        self.after_idle(self._redessiner)


class RechercheAvecSuggestions:
    """Attache à un champ (Entry ou Combobox) une petite liste flottante de
    suggestions qui s'affiche automatiquement pendant la frappe, sans jamais
    faire perdre le focus clavier au champ (contrairement au menu déroulant
    natif du Combobox, qui capte le clavier dès qu'il s'ouvre)."""

    def __init__(self, champ, variable, valeurs, on_select=None, max_resultats=8):
        self.champ = champ
        self.variable = variable
        self.valeurs = valeurs
        self.on_select = on_select
        self.max_resultats = max_resultats
        self.popup = None
        self.listbox = None
        self.index_actif = -1

        champ.bind("<KeyRelease>", self._sur_touche, add="+")
        champ.bind("<FocusOut>", lambda e: champ.after(150, self._verifier_fermeture), add="+")

    def set_valeurs(self, valeurs):
        self.valeurs = valeurs

    def _sur_touche(self, event):
        if event.keysym == "Down":
            self._deplacer(1)
            return "break"
        if event.keysym == "Up":
            self._deplacer(-1)
            return "break"
        if event.keysym == "Return":
            if self.popup is not None and self.index_actif >= 0:
                self._choisir(self.index_actif)
                return "break"
            return
        if event.keysym == "Escape":
            self._fermer()
            return
        if event.keysym in ("Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"):
            return
        texte = self.variable.get().strip().lower()
        if not texte:
            self._fermer()
            return
        correspondances = [v for v in self.valeurs if texte in v.lower()][: self.max_resultats]
        if not correspondances:
            self._fermer()
            return
        self._afficher(correspondances)

    def _afficher(self, correspondances):
        if self.popup is None:
            self.popup = tk.Toplevel(self.champ)
            self.popup.overrideredirect(True)
            self.popup.attributes("-topmost", True)
            self.listbox = tk.Listbox(
                self.popup, font=("Segoe UI", 10), activestyle="none",
                selectbackground="#2563eb", selectforeground="white",
                highlightthickness=1, highlightbackground="#cbd5e1", bd=0,
            )
            self.listbox.pack(fill="both", expand=True)
            self.listbox.bind("<Button-1>", self._sur_clic_liste)
        x = self.champ.winfo_rootx()
        y = self.champ.winfo_rooty() + self.champ.winfo_height()
        largeur = max(self.champ.winfo_width(), 200)
        self.listbox.delete(0, "end")
        for v in correspondances:
            self.listbox.insert("end", v)
        hauteur = min(len(correspondances), self.max_resultats) * 22
        self.popup.geometry(f"{largeur}x{hauteur}+{x}+{y}")
        self.index_actif = -1

    def _deplacer(self, pas):
        if self.popup is None:
            return
        n = self.listbox.size()
        if n == 0:
            return
        self.index_actif = (self.index_actif + pas) % n
        self.listbox.selection_clear(0, "end")
        self.listbox.selection_set(self.index_actif)
        self.listbox.activate(self.index_actif)
        self.listbox.see(self.index_actif)

    def _sur_clic_liste(self, event):
        index = self.listbox.nearest(event.y)
        self._choisir(index)
        return "break"

    def _choisir(self, index):
        if self.popup is None or index < 0 or index >= self.listbox.size():
            return
        valeur = self.listbox.get(index)
        self.variable.set(valeur)
        self._fermer()
        self.champ.focus_set()
        self.champ.icursor("end")
        if self.on_select:
            self.on_select(valeur)

    def _verifier_fermeture(self):
        if self.popup is None:
            return
        self._fermer()

    def _fermer(self):
        if self.popup is not None:
            self.popup.destroy()
            self.popup = None
            self.listbox = None
        self.index_actif = -1


class BoutonArrondi(tk.Canvas):
    """Bouton à coins arrondis avec effet de survol, dessiné sur un Canvas."""

    def __init__(self, parent, texte, commande=None, bg_page="#f5f6fa",
                 couleur="#8b5e34", couleur_survol="#734a2a", couleur_texte="white",
                 police=("Segoe UI", 10, "bold"), rayon=10, padx=18, pady=10):
        super().__init__(parent, bg=bg_page, highlightthickness=0, cursor="hand2")
        self.commande = commande
        self.couleur = couleur
        self.couleur_survol = couleur_survol

        mesure = tk.Label(parent, text=texte, font=police)
        mesure.update_idletasks()
        largeur_texte = mesure.winfo_reqwidth()
        hauteur_texte = mesure.winfo_reqheight()
        mesure.destroy()

        self.largeur = largeur_texte + padx * 2
        self.hauteur = hauteur_texte + pady * 2
        self.config(width=self.largeur, height=self.hauteur)

        self._forme = dessiner_rectangle_arrondi(
            self, 1, 1, self.largeur - 1, self.hauteur - 1, rayon=rayon,
            fill=couleur, outline="",
        )
        self._texte_id = self.create_text(
            self.largeur / 2, self.hauteur / 2, text=texte, fill=couleur_texte, font=police,
        )

        self.bind("<Button-1>", self._sur_clic)
        self.bind("<Enter>", lambda e: self.itemconfig(self._forme, fill=self.couleur_survol))
        self.bind("<Leave>", lambda e: self.itemconfig(self._forme, fill=self.couleur))

    def _sur_clic(self, event):
        if self.commande:
            self.commande()

    def set_texte(self, texte):
        self.itemconfig(self._texte_id, text=texte)

    def set_command(self, commande):
        self.commande = commande
