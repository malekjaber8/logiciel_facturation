# Logiciel de Facturation - Meubles en Bois

Petit logiciel de bureau (Windows) pour créer des factures et des bons de
livraison, gérer les clients et les articles, et suivre les paiements.

## Utilisation (pour le client)

1. Ouvrir le dossier `dist`.
2. Double-cliquer sur `Facturation.exe`. Aucune installation n'est nécessaire.
3. Au premier lancement, un dossier `data` est créé automatiquement à côté de
   `Facturation.exe`. **C'est là que sont stockées toutes les données**
   (clients, articles, factures, BL, PDF générés).

### Étapes de configuration initiale

1. Aller dans **Paramètres** et renseigner le nom de l'entreprise, l'adresse,
   le téléphone, le matricule fiscal, le logo (facultatif) et la devise.
2. Aller dans **Articles** et créer chaque produit vendu (table, chaise,
   piètement, etc.) avec sa désignation, son prix unitaire et, si besoin,
   une photo (bouton "Choisir une image..."). **C'est ce catalogue qui sera
   ensuite utilisé pour facturer** : lors de la création d'une facture ou
   d'un BL, seuls les articles déjà enregistrés ici peuvent être
   sélectionnés (aucune saisie libre n'est possible), ce qui évite les
   erreurs de désignation ou de prix.
3. Aller dans **Clients** et ajouter les clients habituels (nom, adresse,
   téléphone, matricule fiscal).

### Créer une facture, un bon de livraison ou un devis

1. Cliquer sur **Facture**, **Bon de livraison** ou **Devis / Proforma**.
2. Choisir le client, la date (calendrier), ajouter les articles un par un
   depuis le catalogue (photo, quantité, prix pré-remplis, modifiables).
3. Cliquer sur **Enregistrer** : le document est enregistré dans
   l'historique et s'ouvre directement dans une fenêtre d'aperçu du
   logiciel (pas dans le navigateur), avec la photo de chaque article dans
   le tableau, et un bouton **Imprimer**.

### Suivre les paiements

Dans **Historique**, sélectionner une facture puis **Enregistrer un
paiement** pour indiquer un montant reçu (paiement partiel ou total). Le
statut (payé / partiel / impayé) et le montant restant se mettent à jour
automatiquement. Le **Tableau de bord** affiche en permanence le total
facturé, le total encaissé et le total impayé.

## Sauvegarde des données (important)

Toutes les données tiennent dans le dossier `data` (à côté de
`Facturation.exe`). Pour sauvegarder :

- Copier régulièrement ce dossier `data` sur une clé USB, un disque externe
  ou un cloud (Google Drive, OneDrive...).
- Pour déplacer le logiciel sur un autre PC : copier `Facturation.exe` et le
  dossier `data` ensemble dans un même dossier.

Ne jamais supprimer le dossier `data` — c'est l'unique copie des données.

## Pour le développeur (regénérer l'exécutable)

Le code source Python se trouve à la racine du projet (`main.py`, `db.py`,
`pdf.py`, `ui_app.py`, `views/`).

```
pip install -r requirements.txt
python main.py                 # lancer en mode développement

pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name Facturation main.py
# l'exécutable est généré dans dist/Facturation.exe
```

Architecture :
- `db.py` : base de données SQLite (fichier unique `data/facturation.db`).
- `pdf.py` : génération des PDF (factures / BL / devis) avec ReportLab.
- `pdf_viewer.py` : fenêtre d'aperçu PDF intégrée (rendu via PyMuPDF).
- `ui_app.py` + `views/` : interface graphique Tkinter.
