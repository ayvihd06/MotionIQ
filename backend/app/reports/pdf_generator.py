import io
from pathlib import Path
from typing import Dict, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

class PdfReportGenerator:
    """Generates a downloadable biomechanical analysis PDF report."""

    @staticmethod
    def generate_report(analysis_data: Dict[str, Any]) -> io.BytesIO:
        buffer = io.BytesIO()

        # Letter page: 612pt wide. Margins 36pt each side → 540pt usable width.
        PAGE_W = 612
        L_MARGIN = R_MARGIN = 36
        CONTENT_W = PAGE_W - L_MARGIN - R_MARGIN  # 540pt

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=R_MARGIN,
            leftMargin=L_MARGIN,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()

        # Custom Palette
        PRIMARY_COLOR = colors.HexColor("#0f172a")  # Dark Slate
        ACCENT_CYAN   = colors.HexColor("#0891b2")  # Cyan 600
        EMERALD_COLOR = colors.HexColor("#059669")  # Emerald 600
        TEXT_MUTED    = colors.HexColor("#64748b")  # Slate 500
        BG_LIGHT      = colors.HexColor("#f8fafc")  # Slate 50
        BORDER_COLOR  = colors.HexColor("#e2e8f0")  # Slate 200

        # ── Typography Styles ────────────────────────────────────────────────
        title_style = ParagraphStyle(
            'ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=PRIMARY_COLOR
        )
        subtitle_style = ParagraphStyle(
            'ReportSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            leading=14,
            textColor=TEXT_MUTED
        )
        section_heading = ParagraphStyle(
            'SectionHeading',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=13,
            leading=16,
            textColor=PRIMARY_COLOR,
            spaceBefore=10,
            spaceAfter=6
        )
        body_style = ParagraphStyle(
            'BodyTextCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155")
        )
        bullet_style = ParagraphStyle(
            'BulletCustom',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#334155")
        )
        disclaimer_style = ParagraphStyle(
            'DisclaimerText',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=8,
            leading=11,
            textColor=TEXT_MUTED
        )

        # ── Table cell paragraph styles (used inside table cells) ────────────
        # Wraps cleanly within fixed column widths.
        cell_style = ParagraphStyle(
            'TableCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#334155"),
            wordWrap='CJK'   # ensures word-level wrapping
        )
        cell_bold = ParagraphStyle(
            'TableCellBold',
            parent=cell_style,
            fontName='Helvetica-Bold',
        )
        cell_header = ParagraphStyle(
            'TableHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=8.5,
            leading=12,
            textColor=colors.white,
            wordWrap='CJK'
        )
        desc_cell_style = ParagraphStyle(
            'DescCell',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=8,
            leading=11.5,
            textColor=colors.HexColor("#475569"),
            wordWrap='CJK'
        )

        story = []

        # ── 1. Header Banner ────────────────────────────────────────────────
        analysis_id = analysis_data.get("analysis_id", "N/A")[:8]
        created_at  = analysis_data.get("created_at", "N/A")[:10]
        running_type = analysis_data.get("running_type_context", {})
        summary      = analysis_data.get("overall_summary", {})

        header_data = [
            [
                Paragraph("<b>MOTIONIQ</b><br/><font size=9 color='#0891b2'>AI Running Biomechanics Analysis</font>", title_style),
                Paragraph(f"<b>Date:</b> {created_at}<br/><b>ID:</b> {analysis_id}<br/><b>Status:</b> Complete", subtitle_style)
            ]
        ]
        header_table = Table(header_data, colWidths=[340, 200])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        story.append(header_table)
        story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_CYAN, spaceBefore=8, spaceAfter=12))

        # ── 2. Executive Summary Box ────────────────────────────────────────
        form_class     = analysis_data.get("form_classification", "Running Form Pattern")
        form_score     = summary.get("form_consistency_score", 85.0)
        profile_summary = running_type.get("runner_profile_summary", "Road Running Session")

        summary_html = (
            f"<b>Dominant Pattern:</b> {form_class}<br/>"
            f"<b>Context:</b> {profile_summary}<br/>"
            f"<b>Consistency &amp; Symmetry Index:</b> {form_score}/100 "
            f"(Observational score, not injury risk)"
        )
        summary_p = Paragraph(summary_html, body_style)
        summary_table = Table([[summary_p]], colWidths=[CONTENT_W])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), BG_LIGHT),
            ('BOX',           (0, 0), (-1, -1), 1, BORDER_COLOR),
            ('TOPPADDING',    (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LEFTPADDING',   (0, 0), (-1, -1), 12),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 12),
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 10))

        # ── 3. Primary Telemetry Metrics Table ──────────────────────────────
        # Column widths (must sum to CONTENT_W = 540pt):
        #   Metric 105 | Value 100 | Confidence 72 | Status 65 | Description 198
        # Inner cell padding: left=6, right=6 (total 12pt per col)
        # Effective text widths: 93 | 88 | 60 | 53 | 186
        COL_METRIC = 105
        COL_VALUE  = 100
        COL_CONF   = 72
        COL_STATUS = 65
        COL_DESC   = CONTENT_W - COL_METRIC - COL_VALUE - COL_CONF - COL_STATUS  # 198

        story.append(Paragraph("Primary Biomechanical Metrics", section_heading))
        metrics = analysis_data.get("metrics_breakdown", [])

        # Header row uses Paragraph so it wraps if somehow long
        header_row = [
            Paragraph("Metric",      cell_header),
            Paragraph("Value",       cell_header),
            Paragraph("Confidence",  cell_header),
            Paragraph("Status",      cell_header),
            Paragraph("Description", cell_header),
        ]
        telemetry_rows = [header_row]

        for m in metrics[:7]:
            raw_value = str(m.get('value', ''))
            raw_unit  = str(m.get('unit', ''))
            value_str = f"{raw_value} {raw_unit}".strip()

            telemetry_rows.append([
                Paragraph(m.get("name", ""),            cell_bold),
                Paragraph(value_str,                    cell_style),
                Paragraph(m.get("confidence", "High"),  cell_style),
                Paragraph(m.get("status", "Normal"),    cell_style),
                Paragraph(m.get("description", ""),     desc_cell_style),
            ])

        telemetry_table = Table(
            telemetry_rows,
            colWidths=[COL_METRIC, COL_VALUE, COL_CONF, COL_STATUS, COL_DESC],
            repeatRows=1,        # repeat header row on page break
            splitByRow=True,     # allow splitting between rows at page boundary
        )
        telemetry_table.setStyle(TableStyle([
            # Header row styling
            ('BACKGROUND',    (0, 0), (-1,  0), PRIMARY_COLOR),
            ('TEXTCOLOR',     (0, 0), (-1,  0), colors.white),
            # Global padding — gives wrapped text vertical room
            ('TOPPADDING',    (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING',   (0, 0), (-1, -1), 6),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 6),
            # Grid lines
            ('GRID',          (0, 0), (-1, -1), 0.5, BORDER_COLOR),
            # Vertical alignment: top so multi-line rows look tidy
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            # Alternating row backgrounds (data rows only)
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
        ]))
        story.append(telemetry_table)
        story.append(Spacer(1, 12))

        # ── 4. Context-Aware Insights & "Why Flagged" ───────────────────────
        insights = analysis_data.get("context_insights", [])
        if insights:
            story.append(Paragraph("Explainable Observations &amp; Rationale", section_heading))
            for ins in insights[:4]:
                why_text = "; ".join(ins.get("why_flagged", []))
                ins_html = (
                    f"<b>{ins.get('title', '')}</b> "
                    f"({ins.get('category', '')} • Confidence: {ins.get('confidence', 'High')})<br/>"
                    f"{ins.get('description', '')}<br/>"
                    f"<b>Why this was flagged:</b> {why_text}<br/>"
                    f"<b>Practical cue:</b> {ins.get('recommended_action', '')}"
                )
                ins_table = Table([[Paragraph(ins_html, body_style)]], colWidths=[CONTENT_W])
                ins_table.setStyle(TableStyle([
                    ('BACKGROUND',    (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                    ('BOX',           (0, 0), (-1, -1), 0.5, BORDER_COLOR),
                    ('TOPPADDING',    (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('LEFTPADDING',   (0, 0), (-1, -1), 10),
                    ('RIGHTPADDING',  (0, 0), (-1, -1), 10),
                ]))
                story.append(ins_table)
                story.append(Spacer(1, 6))

        # ── 5. Educational Recommendations ─────────────────────────────────
        recs = analysis_data.get("recommendations", [])
        if recs:
            story.append(Spacer(1, 6))
            story.append(Paragraph("Evidence-Informed Educational Cues", section_heading))
            for i, r in enumerate(recs[:3]):
                story.append(Paragraph(f"• <b>{i+1}.</b> {r}", bullet_style))
                story.append(Spacer(1, 3))

        # ── 6. Scientific Limitations & Responsible AI Disclaimer ───────────
        story.append(Spacer(1, 8))
        story.append(Paragraph("System Boundaries &amp; Scientific Disclosures", section_heading))
        disclaimer_text = (
            "MotionIQ is an AI-assisted observational platform designed for educational purposes. "
            "All kinematics represent 2D sagittal projections extracted from monocular camera video; kinetic ground reaction forces "
            "(in Newtons) and internal joint torques cannot be measured without force plates. MotionIQ does NOT diagnose medical "
            "conditions, predict injury risk, or prescribe clinical treatment. If discomfort or symptoms are present, always consult "
            "a licensed sports physiotherapist or medical professional."
        )
        story.append(Paragraph(disclaimer_text, disclaimer_style))

        doc.build(story)
        buffer.seek(0)
        return buffer


pdf_report_generator = PdfReportGenerator()
