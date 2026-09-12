import os
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
)
from reportlab.lib.enums import TA_RIGHT, TA_CENTER

import db

# Palette reprise du logo Neo Deco (bois/brun fonce) pour que les documents
# generes ressemblent a l'identite visuelle de l'entreprise plutot qu'a un
# gabarit generique bleu/gris.
BRUN = colors.HexColor("#8b5e34")
BRUN_FONCE = colors.HexColor("#3d2b1a")
BRUN_CLAIR = colors.HexColor("#f6ede0")
BORDURE = colors.HexColor("#e3d3bb")
GRIS_TEXTE = colors.HexColor("#544840")
ROUGE = colors.HexColor("#c0392b")
VERT = colors.HexColor("#1e7e42")


def _format_montant(valeur, devise):
    return f"{db.format_montant(valeur)} {devise}"


def generate_pdf(document_id):
    doc, lignes, paiements = db.get_document(document_id)
    params = db.get_all_params()
    devise = params.get("devise", "DT")

    titres = {"facture": "FACTURE", "bl": "BON DE LIVRAISON", "devis": "DEVIS / FACTURE PROFORMA"}
    titre = titres.get(doc["type"], "DOCUMENT")
    filename = f"{doc['numero']}.pdf"
    filepath = os.path.join(db.PDF_DIR, filename)

    styles = getSampleStyleSheet()
    style_normal = ParagraphStyle(
        "NormalBrun", parent=styles["Normal"], textColor=GRIS_TEXTE, leading=13,
    )
    style_nom_entreprise = ParagraphStyle(
        "NomEntreprise", parent=style_normal, fontName="Helvetica-Bold",
        fontSize=13, textColor=BRUN_FONCE, leading=16,
    )
    style_title = ParagraphStyle(
        "TitreDoc", parent=styles["Heading1"], alignment=TA_RIGHT, fontSize=17,
        textColor=BRUN_FONCE, leading=20,
    )
    style_title_meta = ParagraphStyle(
        "TitreMeta", parent=style_normal, alignment=TA_RIGHT, fontSize=10,
    )
    style_label_client = ParagraphStyle(
        "LabelClient", parent=style_normal, fontName="Helvetica-Bold",
        fontSize=11, textColor=BRUN_FONCE,
    )

    elements = []

    # Bandeau de couleur en tete de page, aux couleurs de la marque.
    bandeau = Table([[""]], colWidths=[180 * mm], rowHeights=[3 * mm])
    bandeau.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BRUN)]))
    elements.append(bandeau)
    elements.append(Spacer(1, 8 * mm))

    # En-tête : entreprise (gauche) / titre + numéro + date (droite)
    entreprise_lines = []
    if params.get("entreprise_adresse"):
        entreprise_lines.append(params["entreprise_adresse"])
    if params.get("entreprise_tel"):
        entreprise_lines.append(f"Tél: {params['entreprise_tel']}")
    if params.get("entreprise_whatsapp"):
        entreprise_lines.append(f"WhatsApp: {params['entreprise_whatsapp']}")
    if params.get("entreprise_email"):
        entreprise_lines.append(f"Email: {params['entreprise_email']}")
    if params.get("entreprise_matricule"):
        entreprise_lines.append(f"Matricule fiscal: {params['entreprise_matricule']}")
    entreprise_nom_para = Paragraph(params.get("entreprise_nom", ""), style_nom_entreprise)
    entreprise_details_para = Paragraph("<br/>".join(entreprise_lines), style_normal)

    logo_path = db.resoudre_chemin_image(params.get("entreprise_logo", ""))
    if logo_path and os.path.isfile(logo_path):
        logo = Image(logo_path, width=26 * mm, height=22 * mm)
        entreprise_cell = Table(
            [[logo], [Spacer(1, 3 * mm)], [entreprise_nom_para], [entreprise_details_para]]
        )
    else:
        entreprise_cell = Table([[entreprise_nom_para], [entreprise_details_para]])
    entreprise_cell.setStyle(TableStyle([
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))

    titre_para_table = Table(
        [[Paragraph(titre, style_title)],
         [Paragraph(f"N° {doc['numero']}<br/>Date: {doc['date']}", style_title_meta)]],
        colWidths=[75 * mm],
    )
    titre_para_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRUN_CLAIR),
        ("BOX", (0, 0), (-1, -1), 0.75, BORDURE),
        ("TOPPADDING", (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
        ("TOPPADDING", (0, 1), (-1, 1), 2),
        ("BOTTOMPADDING", (0, 1), (-1, 1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))

    header_table = Table([[entreprise_cell, titre_para_table]], colWidths=[105 * mm, 75 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 3 * mm))
    trait = Table([[""]], colWidths=[180 * mm], rowHeights=[0.6 * mm])
    trait.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BORDURE)]))
    elements.append(trait)
    elements.append(Spacer(1, 8 * mm))

    # Bloc client, en carte avec liseré de couleur sur le bord gauche.
    client_lines = [f"<b>{doc['client_nom']}</b>"]
    if doc["client_adresse"]:
        client_lines.append(f"Adresse: {doc['client_adresse']}")
    if doc["client_telephone"]:
        client_lines.append(f"Tél: {doc['client_telephone']}")
    if doc["client_type"] == "particulier" and doc["client_cin"]:
        client_lines.append(f"N° CIN: {doc['client_cin']}")
    elif doc["client_matricule"]:
        client_lines.append(f"Matricule fiscal: {doc['client_matricule']}")
    client_titre_style = ParagraphStyle(
        "ClientTitre", parent=style_normal, fontName="Helvetica-Bold",
        fontSize=8, textColor=BRUN, spaceAfter=3,
    )
    client_contenu = [
        Paragraph("CLIENT", client_titre_style),
        Paragraph("<br/>".join(client_lines), style_label_client),
    ]
    client_table = Table([[client_contenu]], colWidths=[177 * mm])
    client_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), BRUN_CLAIR),
        ("LINEBEFORE", (0, 0), (0, -1), 3, BRUN),
        ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(client_table)
    elements.append(Spacer(1, 8 * mm))

    # Tableau des articles
    data = [["Photo", "Désignation", "Quantité", "Prix unitaire", "Total"]]
    for l in lignes:
        chemin_photo = db.resoudre_chemin_image(l["image_path"])
        if chemin_photo and os.path.isfile(chemin_photo):
            photo_cell = Image(chemin_photo, width=16 * mm, height=16 * mm)
        else:
            photo_cell = ""
        data.append([
            photo_cell,
            Paragraph(l["designation"], style_normal),
            f"{l['quantite']:g}",
            _format_montant(l["prix_unitaire"], devise),
            _format_montant(l["total_ligne"], devise),
        ])
    lignes_table = Table(data, colWidths=[20 * mm, 60 * mm, 30 * mm, 35 * mm, 35 * mm])
    lignes_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), BRUN),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, BORDURE),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, BRUN),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, BRUN_CLAIR]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(lignes_table)
    elements.append(Spacer(1, 6 * mm))

    # Totaux : le montant principal ressort sur un bandeau de couleur, le
    # reste a payer est colore selon que le document est solde ou non.
    style_total_label = ParagraphStyle(
        "TotalLabel", parent=style_normal, fontName="Helvetica-Bold",
        fontSize=12, textColor=colors.white,
    )
    style_total_valeur = ParagraphStyle(
        "TotalValeur", parent=style_total_label, alignment=TA_RIGHT,
    )
    if doc["type"] == "facture":
        reste = doc["montant_total"] - doc["montant_paye"]
        couleur_reste = VERT if reste <= 0.001 else ROUGE
        style_reste = ParagraphStyle(
            "Reste", parent=style_normal, fontName="Helvetica-Bold",
            fontSize=11, textColor=couleur_reste,
        )
        style_reste_valeur = ParagraphStyle("ResteValeur", parent=style_reste, alignment=TA_RIGHT)
        style_paye = ParagraphStyle("Paye", parent=style_normal, fontSize=10)
        style_paye_valeur = ParagraphStyle("PayeValeur", parent=style_paye, alignment=TA_RIGHT)
        total_data = [
            [Paragraph("MONTANT TOTAL", style_total_label),
             Paragraph(_format_montant(doc["montant_total"], devise), style_total_valeur)],
            [Paragraph("Montant payé", style_paye), Paragraph(
                _format_montant(doc["montant_paye"], devise), style_paye_valeur)],
            [Paragraph("Reste à payer", style_reste), Paragraph(
                _format_montant(reste, devise), style_reste_valeur)],
        ]
        total_table = Table(total_data, colWidths=[145 * mm, 35 * mm])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRUN),
            ("TOPPADDING", (0, 0), (-1, 0), 8),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
            ("TOPPADDING", (0, 1), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 4),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
            ("LINEBELOW", (0, 1), (-1, 1), 0.5, BORDURE),
        ]))
        elements.append(total_table)
    else:
        total_data = [
            [Paragraph("TOTAL", style_total_label),
             Paragraph(_format_montant(doc["montant_total"], devise), style_total_valeur)],
        ]
        total_table = Table(total_data, colWidths=[145 * mm, 35 * mm])
        total_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), BRUN),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(total_table)

    if doc["notes"]:
        elements.append(Spacer(1, 6 * mm))
        elements.append(Paragraph(f"<b>Notes:</b> {doc['notes']}", style_normal))

    elements.append(Spacer(1, 25 * mm))

    # Zone signature / cachet
    signature_table = Table(
        [["Signature du client", "Cachet et signature de l'entreprise"],
         ["", ""], ["", ""]],
        colWidths=[90 * mm, 90 * mm],
        rowHeights=[6 * mm, 18 * mm, 6 * mm],
    )
    signature_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, 0), BRUN_FONCE),
        ("BOX", (0, 0), (0, -1), 0.5, BORDURE),
        ("BOX", (1, 0), (1, -1), 0.5, BORDURE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(signature_table)

    # Pied de page : coordonnées de l'entreprise et mot de remerciement.
    pied_lignes = [params.get("entreprise_nom", "")]
    coords = [c for c in (
        params.get("entreprise_tel") and f"Tél {params['entreprise_tel']}",
        params.get("entreprise_whatsapp") and f"WhatsApp {params['entreprise_whatsapp']}",
        params.get("entreprise_email"),
    ) if c]
    if coords:
        pied_lignes.append(" · ".join(coords))
    style_pied = ParagraphStyle(
        "Pied", parent=style_normal, alignment=TA_CENTER, fontSize=8, textColor=BRUN,
    )
    elements.append(Spacer(1, 12 * mm))
    trait_pied = Table([[""]], colWidths=[180 * mm], rowHeights=[0.6 * mm])
    trait_pied.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), BORDURE)]))
    elements.append(trait_pied)
    elements.append(Spacer(1, 4 * mm))
    elements.append(Paragraph("Merci pour votre confiance", style_pied))
    elements.append(Paragraph(" · ".join(pied_lignes), style_pied))

    document = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    document.build(elements)

    db.set_document_pdf_path(document_id, filepath)
    return filepath
