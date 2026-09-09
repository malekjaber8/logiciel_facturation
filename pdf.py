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
    style_normal = styles["Normal"]
    style_title = ParagraphStyle(
        "TitreDoc", parent=styles["Heading1"], alignment=TA_RIGHT, fontSize=18,
    )
    style_right = ParagraphStyle("Right", parent=style_normal, alignment=TA_RIGHT)
    style_center = ParagraphStyle("Center", parent=style_normal, alignment=TA_CENTER)

    elements = []

    # En-tête : entreprise (gauche) / titre + numéro + date (droite)
    entreprise_lines = [f"<b>{params.get('entreprise_nom','')}</b>"]
    if params.get("entreprise_adresse"):
        entreprise_lines.append(params["entreprise_adresse"])
    if params.get("entreprise_tel"):
        entreprise_lines.append(f"Tél: {params['entreprise_tel']}")
    if params.get("entreprise_matricule"):
        entreprise_lines.append(f"Matricule fiscal: {params['entreprise_matricule']}")
    entreprise_para = Paragraph("<br/>".join(entreprise_lines), style_normal)

    logo_path = db.resoudre_chemin_image(params.get("entreprise_logo", ""))
    if logo_path and os.path.isfile(logo_path):
        logo = Image(logo_path, width=30 * mm, height=20 * mm)
        entreprise_cell = Table([[logo], [entreprise_para]])
        entreprise_cell.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    else:
        entreprise_cell = entreprise_para

    titre_para = Paragraph(
        f"{titre}<br/>N&deg; {doc['numero']}<br/>Date: {doc['date']}",
        style_title,
    )

    header_table = Table([[entreprise_cell, titre_para]], colWidths=[100 * mm, 80 * mm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10 * mm))

    # Bloc client
    client_lines = [f"<b>Client:</b> {doc['client_nom']}"]
    if doc["client_adresse"]:
        client_lines.append(f"Adresse: {doc['client_adresse']}")
    if doc["client_telephone"]:
        client_lines.append(f"Tél: {doc['client_telephone']}")
    if doc["client_type"] == "particulier" and doc["client_cin"]:
        client_lines.append(f"N° CIN: {doc['client_cin']}")
    elif doc["client_matricule"]:
        client_lines.append(f"Matricule fiscal: {doc['client_matricule']}")
    client_para = Paragraph("<br/>".join(client_lines), style_normal)
    client_table = Table([[client_para]], colWidths=[180 * mm])
    client_table.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.75, colors.black),
        ("INNERPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
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
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ALIGN", (0, 0), (0, -1), "CENTER"),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    elements.append(lignes_table)
    elements.append(Spacer(1, 6 * mm))

    # Totaux
    if doc["type"] == "facture":
        total_data = [
            ["Montant total", _format_montant(doc["montant_total"], devise)],
            ["Montant payé", _format_montant(doc["montant_paye"], devise)],
            ["Reste à payer", _format_montant(
                doc["montant_total"] - doc["montant_paye"], devise)],
        ]
        total_table = Table(total_data, colWidths=[145 * mm, 35 * mm])
        total_table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
            ("FONTSIZE", (0, 0), (-1, -1), 11),
        ]))
        elements.append(total_table)
    else:
        total_data = [["Total", _format_montant(doc["montant_total"], devise)]]
        total_table = Table(total_data, colWidths=[145 * mm, 35 * mm])
        total_table.setStyle(TableStyle([
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("LINEABOVE", (0, 0), (-1, 0), 0.75, colors.black),
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
        ("BOX", (0, 0), (0, -1), 0.5, colors.grey),
        ("BOX", (1, 0), (1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    elements.append(signature_table)

    document = SimpleDocTemplate(
        filepath, pagesize=A4,
        topMargin=15 * mm, bottomMargin=15 * mm,
        leftMargin=15 * mm, rightMargin=15 * mm,
    )
    document.build(elements)

    db.set_document_pdf_path(document_id, filepath)
    return filepath
