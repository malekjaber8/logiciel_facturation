import sqlite3
import os
import sys
import shutil
from datetime import date

if getattr(sys, "frozen", False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(APP_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "facturation.db")
PDF_DIR = os.path.join(DATA_DIR, "documents_pdf")
IMAGES_DIR = os.path.join(DATA_DIR, "images_produits")

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nom TEXT NOT NULL,
    adresse TEXT,
    telephone TEXT,
    type_client TEXT NOT NULL DEFAULT 'societe',
    matricule_fiscal TEXT,
    cin TEXT,
    email TEXT
);

CREATE TABLE IF NOT EXISTS produits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    nom TEXT NOT NULL,
    description TEXT,
    prix_unitaire REAL NOT NULL DEFAULT 0,
    unite TEXT DEFAULT 'piece',
    stock REAL NOT NULL DEFAULT 0,
    image_path TEXT,
    categorie TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL CHECK(type IN ('facture','bl','devis')),
    numero TEXT NOT NULL UNIQUE,
    date TEXT NOT NULL,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    statut TEXT NOT NULL DEFAULT 'impaye' CHECK(statut IN ('paye','partiel','impaye')),
    montant_total REAL NOT NULL DEFAULT 0,
    montant_paye REAL NOT NULL DEFAULT 0,
    notes TEXT,
    pdf_path TEXT
);

CREATE TABLE IF NOT EXISTS lignes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    designation TEXT NOT NULL,
    quantite REAL NOT NULL,
    prix_unitaire REAL NOT NULL,
    total_ligne REAL NOT NULL,
    image_path TEXT
);

CREATE TABLE IF NOT EXISTS paiements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    date TEXT NOT NULL,
    montant REAL NOT NULL,
    mode TEXT,
    reference TEXT
);

CREATE TABLE IF NOT EXISTS parametres (
    cle TEXT PRIMARY KEY,
    valeur TEXT
);

CREATE TABLE IF NOT EXISTS compteurs (
    type TEXT NOT NULL,
    annee INTEGER NOT NULL,
    dernier INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (type, annee)
);
"""

DEFAULT_PARAMS = {
    "entreprise_nom": "Mon Entreprise de Meubles",
    "entreprise_adresse": "",
    "entreprise_tel": "",
    "entreprise_matricule": "",
    "entreprise_logo": "",
    "devise": "DT",
}


def get_connection():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(PDF_DIR, exist_ok=True)
    os.makedirs(IMAGES_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _migrer_schema(conn):
    colonnes = [r["name"] for r in conn.execute("PRAGMA table_info(produits)").fetchall()]
    if "image_path" not in colonnes:
        conn.execute("ALTER TABLE produits ADD COLUMN image_path TEXT")
    if "code" not in colonnes:
        conn.execute("ALTER TABLE produits ADD COLUMN code TEXT")
    if "stock" not in colonnes:
        conn.execute("ALTER TABLE produits ADD COLUMN stock REAL NOT NULL DEFAULT 0")
    if "categorie" not in colonnes:
        conn.execute("ALTER TABLE produits ADD COLUMN categorie TEXT NOT NULL DEFAULT ''")

    colonnes_clients = [r["name"] for r in conn.execute("PRAGMA table_info(clients)").fetchall()]
    if "type_client" not in colonnes_clients:
        conn.execute(
            "ALTER TABLE clients ADD COLUMN type_client TEXT NOT NULL DEFAULT 'societe'"
        )
    if "cin" not in colonnes_clients:
        conn.execute("ALTER TABLE clients ADD COLUMN cin TEXT")

    colonnes_lignes = [r["name"] for r in conn.execute("PRAGMA table_info(lignes)").fetchall()]
    if "image_path" not in colonnes_lignes:
        conn.execute("ALTER TABLE lignes ADD COLUMN image_path TEXT")

    colonnes_paiements = [r["name"] for r in conn.execute("PRAGMA table_info(paiements)").fetchall()]
    if "reference" not in colonnes_paiements:
        conn.execute("ALTER TABLE paiements ADD COLUMN reference TEXT")

    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='documents'"
    ).fetchone()
    if row and "'devis'" not in row["sql"]:
        # On ne renomme jamais la table "documents" elle-même : SQLite réécrit
        # automatiquement la référence de clé étrangère de "lignes" vers le nom
        # renommé, ce qui casse (et supprime en cascade) les lignes existantes
        # dès que l'ancienne table est supprimée. On construit donc la nouvelle
        # table sous un autre nom, puis on supprime l'ancienne "documents" et on
        # renomme la nouvelle à sa place : "lignes" n'a jamais référencé ce nom
        # intermédiaire, sa clé étrangère reste donc intacte.
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.executescript(
            """
            CREATE TABLE documents_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('facture','bl','devis')),
                numero TEXT NOT NULL UNIQUE,
                date TEXT NOT NULL,
                client_id INTEGER NOT NULL REFERENCES clients(id),
                statut TEXT NOT NULL DEFAULT 'impaye' CHECK(statut IN ('paye','partiel','impaye')),
                montant_total REAL NOT NULL DEFAULT 0,
                montant_paye REAL NOT NULL DEFAULT 0,
                notes TEXT,
                pdf_path TEXT
            );
            INSERT INTO documents_new SELECT * FROM documents;
            DROP TABLE documents;
            ALTER TABLE documents_new RENAME TO documents;
            """
        )
        conn.execute("PRAGMA foreign_keys = ON")

    _migrer_chemins_images(conn)


def _rendre_relatif_si_possible(chemin):
    """Un chemin absolu enregistré du temps où l'appli tournait depuis ce PC
    précis ne fonctionne plus si le dossier du projet est déplacé (clé USB,
    autre PC) : on le convertit en chemin relatif à DATA_DIR quand c'est
    possible, pour que les images suivent le projet où qu'il aille."""
    if not chemin or not os.path.isabs(chemin):
        return chemin
    try:
        if os.path.commonpath([chemin, DATA_DIR]) != os.path.normpath(DATA_DIR):
            return chemin
    except ValueError:
        return chemin
    return os.path.relpath(chemin, DATA_DIR)


def _migrer_chemins_images(conn):
    for table in ("produits", "lignes"):
        rows = conn.execute(
            f"SELECT id, image_path FROM {table} WHERE image_path IS NOT NULL"
        ).fetchall()
        for r in rows:
            relatif = _rendre_relatif_si_possible(r["image_path"])
            if relatif != r["image_path"]:
                conn.execute(
                    f"UPDATE {table} SET image_path=? WHERE id=?", (relatif, r["id"])
                )
    rows_pdf = conn.execute(
        "SELECT id, pdf_path FROM documents WHERE pdf_path IS NOT NULL"
    ).fetchall()
    for r in rows_pdf:
        relatif = _rendre_relatif_si_possible(r["pdf_path"])
        if relatif != r["pdf_path"]:
            conn.execute(
                "UPDATE documents SET pdf_path=? WHERE id=?", (relatif, r["id"])
            )
    cle_logo = conn.execute(
        "SELECT valeur FROM parametres WHERE cle='entreprise_logo'"
    ).fetchone()
    if cle_logo and cle_logo["valeur"]:
        relatif = _rendre_relatif_si_possible(cle_logo["valeur"])
        if relatif != cle_logo["valeur"]:
            conn.execute(
                "UPDATE parametres SET valeur=? WHERE cle='entreprise_logo'", (relatif,)
            )


def resoudre_chemin(chemin):
    """Reconstruit le chemin absolu réel d'un fichier (image ou PDF) à partir
    de ce qui est enregistré en base (relatif à DATA_DIR depuis cette mise à
    jour, ou encore absolu pour d'anciennes données pas encore migrées).
    Reste valable si le projet est déplacé sur un autre PC/dossier."""
    if not chemin:
        return None
    if os.path.isabs(chemin):
        return chemin
    return os.path.join(DATA_DIR, chemin)


resoudre_chemin_image = resoudre_chemin


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    _migrer_schema(conn)
    for cle, valeur in DEFAULT_PARAMS.items():
        conn.execute(
            "INSERT OR IGNORE INTO parametres (cle, valeur) VALUES (?, ?)",
            (cle, valeur),
        )
    conn.commit()
    conn.close()


# ---------- Paramètres ----------

def get_param(cle, default=""):
    conn = get_connection()
    row = conn.execute("SELECT valeur FROM parametres WHERE cle=?", (cle,)).fetchone()
    conn.close()
    return row["valeur"] if row else default


def get_all_params():
    conn = get_connection()
    rows = conn.execute("SELECT cle, valeur FROM parametres").fetchall()
    conn.close()
    return {r["cle"]: r["valeur"] for r in rows}


def set_param(cle, valeur):
    conn = get_connection()
    conn.execute(
        "INSERT INTO parametres (cle, valeur) VALUES (?, ?) "
        "ON CONFLICT(cle) DO UPDATE SET valeur=excluded.valeur",
        (cle, valeur),
    )
    conn.commit()
    conn.close()


# ---------- Clients ----------

def add_client(nom, adresse="", telephone="", type_client="societe",
                matricule_fiscal="", cin="", email=""):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO clients (nom, adresse, telephone, type_client, matricule_fiscal, "
        "cin, email) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (nom, adresse, telephone, type_client, matricule_fiscal, cin, email),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def update_client(client_id, nom, adresse="", telephone="", type_client="societe",
                   matricule_fiscal="", cin="", email=""):
    conn = get_connection()
    conn.execute(
        "UPDATE clients SET nom=?, adresse=?, telephone=?, type_client=?, "
        "matricule_fiscal=?, cin=?, email=? WHERE id=?",
        (nom, adresse, telephone, type_client, matricule_fiscal, cin, email, client_id),
    )
    conn.commit()
    conn.close()


def delete_client(client_id):
    conn = get_connection()
    conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
    conn.commit()
    conn.close()


def list_clients(recherche=""):
    conn = get_connection()
    if recherche:
        rows = conn.execute(
            "SELECT * FROM clients WHERE nom LIKE ? OR telephone LIKE ? "
            "ORDER BY nom",
            (f"%{recherche}%", f"%{recherche}%"),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM clients ORDER BY nom").fetchall()
    conn.close()
    return rows


def get_client(client_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone()
    conn.close()
    return row


# ---------- Produits ----------

def _copier_image_produit(produit_id, source_path):
    _supprimer_image_produit(produit_id)
    ext = os.path.splitext(source_path)[1].lower() or ".png"
    nom_fichier = f"produit_{produit_id}{ext}"
    dest = os.path.join(IMAGES_DIR, nom_fichier)
    shutil.copyfile(source_path, dest)
    # Chemin relatif à DATA_DIR : reste valable si le projet est déplacé
    # (clé USB, autre PC), contrairement à un chemin absolu figé sur ce PC.
    return os.path.join("images_produits", nom_fichier)


def _supprimer_image_produit(produit_id):
    os.makedirs(IMAGES_DIR, exist_ok=True)
    for f in os.listdir(IMAGES_DIR):
        if f.startswith(f"produit_{produit_id}."):
            try:
                os.remove(os.path.join(IMAGES_DIR, f))
            except OSError:
                pass


def copier_logo(source_path):
    """Copie le logo choisi dans le dossier de données de l'appli et renvoie
    un chemin relatif à DATA_DIR, portable si le projet est déplacé."""
    logo_dir = os.path.join(DATA_DIR, "logo")
    os.makedirs(logo_dir, exist_ok=True)
    for f in os.listdir(logo_dir):
        try:
            os.remove(os.path.join(logo_dir, f))
        except OSError:
            pass
    ext = os.path.splitext(source_path)[1].lower() or ".png"
    nom_fichier = f"entreprise{ext}"
    dest = os.path.join(logo_dir, nom_fichier)
    shutil.copyfile(source_path, dest)
    return os.path.join("logo", nom_fichier)


def code_produit_existe(code, exclure_id=None):
    if not code:
        return False
    conn = get_connection()
    if exclure_id:
        row = conn.execute(
            "SELECT id FROM produits WHERE code=? AND id!=?", (code, exclure_id)
        ).fetchone()
    else:
        row = conn.execute("SELECT id FROM produits WHERE code=?", (code,)).fetchone()
    conn.close()
    return row is not None


def add_produit(nom, code="", description="", prix_unitaire=0.0, unite="piece", stock=0.0,
                 image_source_path=None, categorie=""):
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO produits (nom, code, description, prix_unitaire, unite, stock, categorie) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (nom, code, description, prix_unitaire, unite, stock, categorie),
    )
    new_id = cur.lastrowid
    conn.commit()
    if image_source_path:
        chemin_stocke = _copier_image_produit(new_id, image_source_path)
        conn.execute("UPDATE produits SET image_path=? WHERE id=?", (chemin_stocke, new_id))
        conn.commit()
    conn.close()
    return new_id


def update_produit(produit_id, nom, code="", description="", prix_unitaire=0.0, unite="piece",
                    stock=0.0, image_source_path=None, supprimer_image=False, categorie=""):
    conn = get_connection()
    conn.execute(
        "UPDATE produits SET nom=?, code=?, description=?, prix_unitaire=?, unite=?, stock=?, "
        "categorie=? WHERE id=?",
        (nom, code, description, prix_unitaire, unite, stock, categorie, produit_id),
    )
    if image_source_path:
        chemin_stocke = _copier_image_produit(produit_id, image_source_path)
        conn.execute("UPDATE produits SET image_path=? WHERE id=?", (chemin_stocke, produit_id))
    elif supprimer_image:
        _supprimer_image_produit(produit_id)
        conn.execute("UPDATE produits SET image_path=NULL WHERE id=?", (produit_id,))
    conn.commit()
    conn.close()


def delete_produit(produit_id):
    conn = get_connection()
    conn.execute("DELETE FROM produits WHERE id=?", (produit_id,))
    conn.commit()
    conn.close()
    _supprimer_image_produit(produit_id)


def list_produits(recherche="", categorie=None):
    conn = get_connection()
    query = "SELECT * FROM produits WHERE 1=1"
    params = []
    if recherche:
        query += " AND (nom LIKE ? OR code LIKE ?)"
        params.append(f"%{recherche}%")
        params.append(f"%{recherche}%")
    if categorie:
        query += " AND categorie=?"
        params.append(categorie)
    query += " ORDER BY nom"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def list_categories():
    conn = get_connection()
    rows = conn.execute(
        "SELECT DISTINCT categorie FROM produits WHERE categorie != '' ORDER BY categorie"
    ).fetchall()
    conn.close()
    return [r["categorie"] for r in rows]


def get_produit(produit_id):
    conn = get_connection()
    row = conn.execute("SELECT * FROM produits WHERE id=?", (produit_id,)).fetchone()
    conn.close()
    return row


# ---------- Numérotation ----------

def _next_numero(conn, type_doc):
    annee = date.today().year
    row = conn.execute(
        "SELECT dernier FROM compteurs WHERE type=? AND annee=?",
        (type_doc, annee),
    ).fetchone()
    dernier = (row["dernier"] if row else 0) + 1
    conn.execute(
        "INSERT INTO compteurs (type, annee, dernier) VALUES (?, ?, ?) "
        "ON CONFLICT(type, annee) DO UPDATE SET dernier=excluded.dernier",
        (type_doc, annee, dernier),
    )
    prefixes = {"facture": "FA", "bl": "BL", "devis": "DEV"}
    prefixe = prefixes.get(type_doc, "DOC")
    return f"{prefixe}-{annee}-{dernier:04d}"


# ---------- Documents (factures / bons de livraison) ----------

def create_document(type_doc, client_id, lignes, notes="", document_date=None):
    """lignes: liste de dicts {designation, quantite, prix_unitaire}"""
    document_date = document_date or date.today().isoformat()
    conn = get_connection()
    numero = _next_numero(conn, type_doc)
    montant_total = sum(l["quantite"] * l["prix_unitaire"] for l in lignes)
    cur = conn.execute(
        "INSERT INTO documents (type, numero, date, client_id, statut, "
        "montant_total, montant_paye, notes) VALUES (?, ?, ?, ?, 'impaye', ?, 0, ?)",
        (type_doc, numero, document_date, client_id, montant_total, notes),
    )
    document_id = cur.lastrowid
    for l in lignes:
        total_ligne = l["quantite"] * l["prix_unitaire"]
        conn.execute(
            "INSERT INTO lignes (document_id, designation, quantite, prix_unitaire, "
            "total_ligne, image_path) VALUES (?, ?, ?, ?, ?, ?)",
            (document_id, l["designation"], l["quantite"], l["prix_unitaire"], total_ligne,
             l.get("image_path")),
        )
    conn.commit()
    conn.close()
    return document_id, numero


def update_document(document_id, client_id, lignes, notes="", document_date=None):
    """lignes: liste de dicts {designation, quantite, prix_unitaire, image_path}"""
    document_date = document_date or date.today().isoformat()
    conn = get_connection()
    montant_total = sum(l["quantite"] * l["prix_unitaire"] for l in lignes)
    row = conn.execute(
        "SELECT montant_paye FROM documents WHERE id=?", (document_id,)
    ).fetchone()
    montant_paye = row["montant_paye"] if row else 0
    if montant_paye >= montant_total - 0.001 and montant_total > 0:
        statut = "paye"
    elif montant_paye > 0:
        statut = "partiel"
    else:
        statut = "impaye"
    conn.execute(
        "UPDATE documents SET client_id=?, date=?, notes=?, montant_total=?, statut=? "
        "WHERE id=?",
        (client_id, document_date, notes, montant_total, statut, document_id),
    )
    conn.execute("DELETE FROM lignes WHERE document_id=?", (document_id,))
    for l in lignes:
        total_ligne = l["quantite"] * l["prix_unitaire"]
        conn.execute(
            "INSERT INTO lignes (document_id, designation, quantite, prix_unitaire, "
            "total_ligne, image_path) VALUES (?, ?, ?, ?, ?, ?)",
            (document_id, l["designation"], l["quantite"], l["prix_unitaire"], total_ligne,
             l.get("image_path")),
        )
    conn.commit()
    conn.close()


def set_document_pdf_path(document_id, pdf_path):
    conn = get_connection()
    conn.execute(
        "UPDATE documents SET pdf_path=? WHERE id=?",
        (_rendre_relatif_si_possible(pdf_path), document_id),
    )
    conn.commit()
    conn.close()


def get_document(document_id):
    conn = get_connection()
    doc = conn.execute(
        "SELECT d.*, c.nom AS client_nom, c.adresse AS client_adresse, "
        "c.telephone AS client_telephone, c.type_client AS client_type, "
        "c.matricule_fiscal AS client_matricule, c.cin AS client_cin "
        "FROM documents d JOIN clients c ON c.id = d.client_id WHERE d.id=?",
        (document_id,),
    ).fetchone()
    lignes = conn.execute(
        "SELECT * FROM lignes WHERE document_id=? ORDER BY id", (document_id,)
    ).fetchall()
    paiements = conn.execute(
        "SELECT * FROM paiements WHERE document_id=? ORDER BY date", (document_id,)
    ).fetchall()
    conn.close()
    return doc, lignes, paiements


def list_documents(type_doc=None, statut=None, client_id=None, recherche="",
                    date_debut=None, date_fin=None):
    conn = get_connection()
    query = (
        "SELECT d.*, c.nom AS client_nom FROM documents d "
        "JOIN clients c ON c.id = d.client_id WHERE 1=1"
    )
    params = []
    if type_doc:
        query += " AND d.type=?"
        params.append(type_doc)
    if statut:
        query += " AND d.statut=?"
        params.append(statut)
    if client_id:
        query += " AND d.client_id=?"
        params.append(client_id)
    if recherche:
        query += " AND (d.numero LIKE ? OR c.nom LIKE ?)"
        params.append(f"%{recherche}%")
        params.append(f"%{recherche}%")
    if date_debut:
        query += " AND d.date >= ?"
        params.append(date_debut)
    if date_fin:
        query += " AND d.date <= ?"
        params.append(date_fin)
    query += " ORDER BY d.date DESC, d.id DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return rows


def delete_document(document_id):
    conn = get_connection()
    conn.execute("DELETE FROM documents WHERE id=?", (document_id,))
    conn.commit()
    conn.close()


MODES_PAIEMENT = {
    "especes": "Espèces",
    "cheque": "Chèque",
    "traite": "Traite",
    "tpe": "TPE",
    "virement": "Virement",
}


def get_details_paiements(document_id):
    """Résumé lisible des règlements d'un document, avec leur référence
    (n° de chèque, de reçu TPE, de virement ou de traite) quand elle existe."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT mode, reference FROM paiements WHERE document_id=? ORDER BY date, id",
        (document_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return "-"
    details = []
    for r in rows:
        libelle = MODES_PAIEMENT.get(r["mode"], r["mode"] or "-")
        if r["reference"]:
            libelle += f" ({r['reference']})"
        details.append(libelle)
    return ", ".join(details)


def _recalculer_statut_document(conn, document_id):
    total_paye = conn.execute(
        "SELECT COALESCE(SUM(montant), 0) AS s FROM paiements WHERE document_id=?",
        (document_id,),
    ).fetchone()["s"]
    montant_total = conn.execute(
        "SELECT montant_total FROM documents WHERE id=?", (document_id,)
    ).fetchone()["montant_total"]
    if montant_total > 0 and total_paye >= montant_total - 0.001:
        statut = "paye"
    elif total_paye > 0:
        statut = "partiel"
    else:
        statut = "impaye"
    conn.execute(
        "UPDATE documents SET montant_paye=?, statut=? WHERE id=?",
        (total_paye, statut, document_id),
    )


def add_paiement(document_id, montant, mode="especes", reference=None, paiement_date=None):
    paiement_date = paiement_date or date.today().isoformat()
    conn = get_connection()
    conn.execute(
        "INSERT INTO paiements (document_id, date, montant, mode, reference) "
        "VALUES (?, ?, ?, ?, ?)",
        (document_id, paiement_date, montant, mode, reference),
    )
    _recalculer_statut_document(conn, document_id)
    conn.commit()
    conn.close()


def update_paiement(paiement_id, montant, mode="especes", reference=None):
    conn = get_connection()
    document_id = conn.execute(
        "SELECT document_id FROM paiements WHERE id=?", (paiement_id,)
    ).fetchone()["document_id"]
    conn.execute(
        "UPDATE paiements SET montant=?, mode=?, reference=? WHERE id=?",
        (montant, mode, reference, paiement_id),
    )
    _recalculer_statut_document(conn, document_id)
    conn.commit()
    conn.close()


def delete_paiement(paiement_id):
    conn = get_connection()
    document_id = conn.execute(
        "SELECT document_id FROM paiements WHERE id=?", (paiement_id,)
    ).fetchone()["document_id"]
    conn.execute("DELETE FROM paiements WHERE id=?", (paiement_id,))
    _recalculer_statut_document(conn, document_id)
    conn.commit()
    conn.close()


# ---------- Statistiques (tableau de bord) ----------

def get_stats():
    conn = get_connection()
    # Un BL peut désormais lui aussi être réglé ou non (comme une facture) :
    # les montants facturé/encaissé/impayé portent donc sur factures + BL.
    # Les devis sont des propositions non engageantes, exclus de ces totaux.
    total_factures = conn.execute(
        "SELECT COALESCE(SUM(montant_total),0) AS s FROM documents WHERE type IN ('facture','bl')"
    ).fetchone()["s"]
    total_encaisse = conn.execute(
        "SELECT COALESCE(SUM(montant_paye),0) AS s FROM documents WHERE type IN ('facture','bl')"
    ).fetchone()["s"]
    total_impaye = total_factures - total_encaisse
    nb_factures = conn.execute(
        "SELECT COUNT(*) AS n FROM documents WHERE type='facture'"
    ).fetchone()["n"]
    nb_bl = conn.execute(
        "SELECT COUNT(*) AS n FROM documents WHERE type='bl'"
    ).fetchone()["n"]
    nb_clients = conn.execute("SELECT COUNT(*) AS n FROM clients").fetchone()["n"]
    dernieres = conn.execute(
        "SELECT d.*, c.nom AS client_nom FROM documents d "
        "JOIN clients c ON c.id = d.client_id ORDER BY d.id DESC LIMIT 8"
    ).fetchall()
    conn.close()
    return {
        "total_factures": total_factures,
        "total_encaisse": total_encaisse,
        "total_impaye": total_impaye,
        "nb_factures": nb_factures,
        "nb_bl": nb_bl,
        "nb_clients": nb_clients,
        "dernieres": dernieres,
    }
