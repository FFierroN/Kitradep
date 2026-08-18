"""Generador del PDF de propuesta: Bot hibrido con LLM para KitraDep.

Uso:
    python generar_pdf.py

Salida:
    PROPUESTA_KITRADEP_LLM.pdf en esta misma carpeta.
"""
from __future__ import annotations

from pathlib import Path
from datetime import date

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    PageBreak,
    Table,
    TableStyle,
    KeepTogether,
    ListFlowable,
    ListItem,
    HRFlowable,
)

# ============================================================================
# Paleta y estilos
# ============================================================================

VERDE = colors.HexColor("#075E54")        # verde WhatsApp
VERDE_CLARO = colors.HexColor("#25D366")  # verde brillante
GRIS_TXT = colors.HexColor("#2E2E2E")
GRIS_SOFT = colors.HexColor("#6B7280")
GRIS_BG = colors.HexColor("#F3F4F6")
AZUL = colors.HexColor("#1E40AF")
NARANJA = colors.HexColor("#B45309")
ROJO = colors.HexColor("#B91C1C")

styles = getSampleStyleSheet()

H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
                    fontSize=22, textColor=VERDE, spaceBefore=6, spaceAfter=12,
                    leading=26)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
                    fontSize=15, textColor=VERDE, spaceBefore=14, spaceAfter=8,
                    leading=19)
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold",
                    fontSize=12, textColor=GRIS_TXT, spaceBefore=10, spaceAfter=4,
                    leading=15)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica",
                      fontSize=10, textColor=GRIS_TXT, leading=14,
                      alignment=TA_JUSTIFY, spaceAfter=6)
BODY_C = ParagraphStyle("BodyC", parent=BODY, alignment=TA_CENTER)
BODY_L = ParagraphStyle("BodyL", parent=BODY, alignment=TA_LEFT)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=8, textColor=GRIS_SOFT)
CODE = ParagraphStyle("Code", parent=BODY, fontName="Courier", fontSize=9,
                      textColor=GRIS_TXT, leading=12, alignment=TA_LEFT,
                      leftIndent=10, backColor=GRIS_BG, borderPadding=6,
                      borderRadius=3)
CALLOUT = ParagraphStyle("Callout", parent=BODY, fontName="Helvetica-Oblique",
                         fontSize=10, leftIndent=12, rightIndent=12,
                         backColor=colors.HexColor("#FFF7ED"), borderPadding=8,
                         borderColor=NARANJA, borderWidth=0.5, borderRadius=3,
                         textColor=GRIS_TXT)
COVER_TITLE = ParagraphStyle("CoverTitle", parent=styles["Title"],
                             fontName="Helvetica-Bold", fontSize=32,
                             textColor=VERDE, alignment=TA_CENTER, leading=38,
                             spaceAfter=6)
COVER_SUB = ParagraphStyle("CoverSub", parent=BODY_C, fontSize=16,
                           textColor=GRIS_TXT, leading=22, spaceAfter=6)
COVER_META = ParagraphStyle("CoverMeta", parent=BODY_C, fontSize=11,
                            textColor=GRIS_SOFT, leading=15)


# ============================================================================
# Helpers de layout
# ============================================================================

def p(txt: str, style=BODY) -> Paragraph:
    return Paragraph(txt, style)


def bullets(items: list[str], style=BODY) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(x, style), leftIndent=12, value="bullet") for x in items],
        bulletType="bullet", start="•", leftIndent=14, bulletFontSize=9,
        bulletColor=VERDE, spaceBefore=2, spaceAfter=8,
    )


def numbered(items: list[str], style=BODY) -> ListFlowable:
    return ListFlowable(
        [ListItem(Paragraph(x, style)) for x in items],
        bulletType="1", leftIndent=18, bulletFontSize=9,
        bulletColor=VERDE, spaceBefore=2, spaceAfter=8,
    )


def hr() -> HRFlowable:
    return HRFlowable(width="100%", thickness=0.7, color=colors.HexColor("#E5E7EB"),
                      spaceBefore=8, spaceAfter=8)


def spacer(h: float = 0.4) -> Spacer:
    return Spacer(1, h * cm)


def tabla(datos: list[list], anchos=None, header_bg=VERDE, header_fg=colors.white,
          zebra=True, font_size=9, align_first_left=True) -> Table:
    """Tabla generica con estilo consistente."""
    filas = []
    for i, fila in enumerate(datos):
        filas.append([Paragraph(str(c), ParagraphStyle(
            "cell", parent=BODY, fontSize=font_size, leading=font_size + 3,
            textColor=colors.white if i == 0 else GRIS_TXT,
            fontName="Helvetica-Bold" if i == 0 else "Helvetica",
            alignment=TA_LEFT if (align_first_left and c is not None) else TA_CENTER,
        )) for c in fila])
    t = Table(filas, colWidths=anchos, repeatRows=1)
    ts = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), header_bg),
        ("TEXTCOLOR", (0, 0), (-1, 0), header_fg),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ])
    if zebra:
        for i in range(1, len(datos)):
            if i % 2 == 0:
                ts.add("BACKGROUND", (0, i), (-1, i), GRIS_BG)
    t.setStyle(ts)
    return t


def callout(txt: str) -> Paragraph:
    return Paragraph("<b></b> " + txt, CALLOUT)


# ============================================================================
# Header / footer con numeracion
# ============================================================================

def _footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS_SOFT)
    canvas.drawString(2 * cm, 1.2 * cm,
                      "Propuesta Chatbot Hibrido con LLM - KitraDep")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pagina {doc.page}")
    canvas.setStrokeColor(colors.HexColor("#E5E7EB"))
    canvas.setLineWidth(0.4)
    canvas.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm)
    canvas.restoreState()


def _cover_page(canvas, doc):
    """Portada sin footer para que se vea limpia."""
    canvas.saveState()
    # barra decorativa arriba
    canvas.setFillColor(VERDE)
    canvas.rect(0, A4[1] - 0.7 * cm, A4[0], 0.7 * cm, fill=1, stroke=0)
    canvas.setFillColor(VERDE_CLARO)
    canvas.rect(0, A4[1] - 0.9 * cm, A4[0], 0.2 * cm, fill=1, stroke=0)
    # barra decorativa abajo
    canvas.setFillColor(VERDE_CLARO)
    canvas.rect(0, 0.7 * cm, A4[0], 0.2 * cm, fill=1, stroke=0)
    canvas.setFillColor(VERDE)
    canvas.rect(0, 0, A4[0], 0.7 * cm, fill=1, stroke=0)
    canvas.restoreState()


# ============================================================================
# Main: ensambla el documento completo
# ============================================================================

def _todas_las_secciones():
    """Importa y concatena las 4 partes en orden.

    Import diferido para evitar ciclos: contenido_parteN.py importa de aca.
    """
    from contenido_parte1 import (
        seccion_portada, seccion_indice, seccion_resumen_ejecutivo,
        seccion_contexto,
    )
    from contenido_parte2 import (
        seccion_conceptos, seccion_arquitectura, seccion_componentes,
        seccion_comparativa_llms,
    )
    from contenido_parte3 import (
        seccion_libreto, seccion_entrenamiento, seccion_guardrails_etica,
        seccion_whatsapp,
    )
    from contenido_parte4 import (
        seccion_despliegue, seccion_plan, seccion_costos, seccion_riesgos,
        seccion_checklist, seccion_anexos,
    )

    flowables = []
    flowables += seccion_portada()
    flowables += seccion_indice()
    flowables += seccion_resumen_ejecutivo()
    flowables += seccion_contexto()
    flowables += seccion_conceptos()
    flowables += seccion_arquitectura()
    flowables += seccion_componentes()
    flowables += seccion_comparativa_llms()
    flowables += seccion_libreto()
    flowables += seccion_entrenamiento()
    flowables += seccion_guardrails_etica()
    flowables += seccion_whatsapp()
    flowables += seccion_despliegue()
    flowables += seccion_plan()
    flowables += seccion_costos()
    flowables += seccion_riesgos()
    flowables += seccion_checklist()
    flowables += seccion_anexos()
    return flowables


def main():
    salida = Path(__file__).parent / "PROPUESTA_KITRADEP_LLM.pdf"
    doc = SimpleDocTemplate(
        str(salida),
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2.2 * cm,
        title="Propuesta Chatbot Hibrido LLM - KitraDep",
        author="Kira (Code Puppy) para Felipe Fierro",
        subject="Diseno, despliegue y presupuesto para bot conversacional WhatsApp",
    )
    flowables = _todas_las_secciones()
    doc.build(flowables, onFirstPage=_cover_page, onLaterPages=_footer)
    print(f"[OK] PDF generado: {salida}")
    print(f"     Peso: {salida.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
