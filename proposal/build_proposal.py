"""Build the ELEC5305 proposal PDF from proposal.md with a polished A4 layout."""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).with_name("proposal.md")
OUTPUT = Path(__file__).with_name("ELEC5305_Audio_Noise_Reduction_Proposal.pdf")

NAVY = colors.HexColor("#17324D")
TEAL = colors.HexColor("#168C8C")
LIGHT_TEAL = colors.HexColor("#E8F5F4")
PALE_BLUE = colors.HexColor("#EEF4F8")
MID_GREY = colors.HexColor("#607080")
LIGHT_GREY = colors.HexColor("#D8E0E6")
INK = colors.HexColor("#17212B")


def inline_markup(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    escaped = re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r"<i>\1</i>", escaped)
    escaped = re.sub(r"`([^`]+?)`", r'<font name="Courier">\1</font>', escaped)
    escaped = re.sub(
        r"(https://[^\s<]+)",
        r'<link href="\1" color="#168C8C">\1</link>',
        escaped,
    )
    return escaped


def parse_markdown() -> tuple[str, dict[str, list[str]]]:
    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    title = lines[0].removeprefix("# ").strip()
    sections: dict[str, list[str]] = {}
    current = ""
    buffer: list[str] = []
    for line in lines[1:]:
        if line.startswith("## "):
            if current:
                sections[current] = buffer
            current = line[3:].strip()
            buffer = []
        else:
            buffer.append(line)
    if current:
        sections[current] = buffer
    return title, sections


def paragraphs(lines: list[str]) -> list[str]:
    result: list[str] = []
    buffer: list[str] = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if buffer:
                result.append(" ".join(buffer))
                buffer = []
            continue
        if stripped.startswith(("- ", "|", "1. ", "2. ", "3. ", "4. ")):
            if buffer:
                result.append(" ".join(buffer))
                buffer = []
            result.append(stripped)
        else:
            buffer.append(stripped)
    if buffer:
        result.append(" ".join(buffer))
    return result


def body_word_count(sections: dict[str, list[str]]) -> int:
    selected = []
    for name in (
        "1. Project Overview",
        "2. Background and Motivation",
        "3. Proposed Methodology",
        "4. Expected Outcomes",
    ):
        selected.extend(sections[name])
    text = " ".join(selected).replace("`", "")
    return len(re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)*", text))


class SignalFlow(Flowable):
    def __init__(self, width: float, height: float = 27 * mm):
        super().__init__()
        self.width = width
        self.height = height

    def draw(self) -> None:
        labels = ["Noisy\nWAV", "STFT", "Noise\nPSD", "Subtract\n+ floor", "iSTFT", "Enhanced\nWAV"]
        count = len(labels)
        gap = 4 * mm
        box_w = (self.width - gap * (count - 1)) / count
        box_h = 14 * mm
        y = 6 * mm
        for i, label in enumerate(labels):
            x = i * (box_w + gap)
            self.canv.setFillColor(LIGHT_TEAL if i in (2, 3) else PALE_BLUE)
            self.canv.setStrokeColor(TEAL if i in (2, 3) else LIGHT_GREY)
            self.canv.roundRect(x, y, box_w, box_h, 2 * mm, fill=1, stroke=1)
            self.canv.setFillColor(NAVY)
            self.canv.setFont("Helvetica-Bold", 7.5)
            label_lines = label.split("\n")
            start_y = y + box_h / 2 + (len(label_lines) - 1) * 3
            for j, part in enumerate(label_lines):
                self.canv.drawCentredString(x + box_w / 2, start_y - j * 8, part)
            if i < count - 1:
                x1 = x + box_w + 0.7 * mm
                x2 = x + box_w + gap - 0.7 * mm
                cy = y + box_h / 2
                self.canv.setStrokeColor(MID_GREY)
                self.canv.line(x1, cy, x2, cy)
                self.canv.line(x2 - 1.6 * mm, cy + 1.2 * mm, x2, cy)
                self.canv.line(x2 - 1.6 * mm, cy - 1.2 * mm, x2, cy)


def header_footer(canvas, doc) -> None:
    canvas.saveState()
    width, height = A4
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 7 * mm, width, 7 * mm, fill=1, stroke=0)
    canvas.setFont("Helvetica-Bold", 7.5)
    canvas.setFillColor(colors.white)
    canvas.drawString(19 * mm, height - 4.7 * mm, "ELEC5305 PROJECT PROPOSAL")
    canvas.setFillColor(MID_GREY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(19 * mm, 10 * mm, "Audio Noise Reduction Using Spectral Subtraction")
    canvas.drawRightString(width - 19 * mm, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(LIGHT_GREY)
    canvas.line(19 * mm, 13 * mm, width - 19 * mm, 13 * mm)
    canvas.restoreState()


def build() -> None:
    title, sections = parse_markdown()
    word_count = body_word_count(sections)
    if not 700 <= word_count <= 1000:
        raise ValueError(f"Main-body word count {word_count} is outside 700-1000")

    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="TitleCustom",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=24,
            leading=28,
            textColor=NAVY,
            alignment=TA_LEFT,
            spaceAfter=5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Deck",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=11.5,
            leading=16,
            textColor=MID_GREY,
            spaceAfter=6 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SectionCustom",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=15,
            leading=18,
            textColor=NAVY,
            spaceBefore=4.5 * mm,
            spaceAfter=2.2 * mm,
            keepWithNext=True,
        )
    )
    styles.add(
        ParagraphStyle(
            name="BodyCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.35,
            leading=13.1,
            textColor=INK,
            alignment=TA_LEFT,
            spaceAfter=2.4 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SmallCustom",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=7.8,
            leading=10.4,
            textColor=INK,
            spaceAfter=1.5 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="TableHeader",
            parent=styles["SmallCustom"],
            fontName="Helvetica-Bold",
            textColor=colors.white,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Equation",
            parent=styles["BodyText"],
            fontName="Courier-Bold",
            fontSize=8.4,
            leading=12,
            textColor=NAVY,
            alignment=TA_CENTER,
            backColor=PALE_BLUE,
            borderColor=LIGHT_GREY,
            borderWidth=0.5,
            borderPadding=7,
            spaceBefore=1.5 * mm,
            spaceAfter=3 * mm,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Caption",
            parent=styles["BodyText"],
            fontName="Helvetica-Oblique",
            fontSize=7.2,
            leading=9.5,
            textColor=MID_GREY,
            alignment=TA_CENTER,
            spaceAfter=2 * mm,
        )
    )

    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        rightMargin=19 * mm,
        leftMargin=19 * mm,
        topMargin=16 * mm,
        bottomMargin=18 * mm,
        title=title,
        author="Chenyue Wang",
        subject="ELEC5305 Project Proposal",
    )
    story: list[Flowable] = []

    story.append(Spacer(1, 7 * mm))
    story.append(Paragraph("ELEC5305 / PROJECT PROPOSAL", styles["Deck"]))
    story.append(Paragraph(inline_markup(title), styles["TitleCustom"]))
    story.append(
        Paragraph(
            "An interpretable, reproducible single-channel speech-enhancement study using STFT analysis, noise-power estimation, over-subtraction, spectral flooring, and overlap-add synthesis.",
            styles["Deck"],
        )
    )

    student_lines = [line[2:] for line in sections["Student Information"] if line.startswith("- ")]
    student_rows = []
    for line in student_lines:
        label, value = line.split(":", 1)
        student_rows.append(
            [
                Paragraph(inline_markup(label), styles["SmallCustom"]),
                Paragraph(inline_markup(value.strip()), styles["SmallCustom"]),
            ]
        )
    student_rows.append(
        [
            Paragraph("Main-body word count", styles["SmallCustom"]),
            Paragraph(str(word_count), styles["SmallCustom"]),
        ]
    )
    card = Table(student_rows, colWidths=[39 * mm, 117 * mm], hAlign="LEFT")
    card.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.7, LIGHT_GREY),
                ("INNERGRID", (0, 0), (-1, -1), 0.35, LIGHT_GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 7),
                ("RIGHTPADDING", (0, 0), (-1, -1), 7),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
            ]
        )
    )
    story.append(card)

    for section_name in ("1. Project Overview", "2. Background and Motivation"):
        story.append(Paragraph(section_name, styles["SectionCustom"]))
        for text in paragraphs(sections[section_name]):
            story.append(Paragraph(inline_markup(text), styles["BodyCustom"]))

    story.append(PageBreak())
    story.append(Paragraph("3. Proposed Methodology", styles["SectionCustom"]))
    method_parts = paragraphs(sections["3. Proposed Methodology"])
    for text in method_parts:
        if text.startswith("`") and text.endswith("`"):
            story.append(Paragraph(inline_markup(text.strip("`")), styles["Equation"]))
        else:
            story.append(Paragraph(inline_markup(text), styles["BodyCustom"]))
        if text.startswith("For each time-frequency bin"):
            story.append(Spacer(1, 0.5 * mm))

    story.append(Paragraph("Signal-processing pipeline", styles["SectionCustom"]))
    story.append(SignalFlow(doc.width))
    story.append(
        Paragraph(
            "Figure 1. Proposed analysis-modification-synthesis path. Only magnitude/power is modified; the noisy phase is retained for reconstruction.",
            styles["Caption"],
        )
    )

    story.append(Paragraph("4. Expected Outcomes", styles["SectionCustom"]))
    for text in paragraphs(sections["4. Expected Outcomes"]):
        story.append(Paragraph(inline_markup(text), styles["BodyCustom"]))

    story.append(PageBreak())
    story.append(Paragraph("5. Timeline (Weeks 1-13)", styles["SectionCustom"]))
    timeline_lines = [line for line in sections["5. Timeline (Weeks 1-13)"] if line.startswith("|")]
    timeline_data = []
    for index, line in enumerate(timeline_lines):
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if index == 1:
            continue
        cell_style = styles["TableHeader"] if index == 0 else styles["SmallCustom"]
        timeline_data.append([Paragraph(inline_markup(cell), cell_style) for cell in cells])
    timeline = Table(timeline_data, colWidths=[24 * mm, 132 * mm], repeatRows=1)
    timeline.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE_BLUE]),
                ("GRID", (0, 0), (-1, -1), 0.45, LIGHT_GREY),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(timeline)

    story.append(Paragraph("6. References", styles["SectionCustom"]))
    for text in paragraphs(sections["6. References"]):
        story.append(Paragraph(inline_markup(text), styles["SmallCustom"]))

    metrics_path = ROOT / "results" / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    story.append(Paragraph("Appendix: Preliminary Proof of Concept", styles["SectionCustom"]))
    metric_data = [
        ["Synthetic input", "Input SNR", "Output SNR", "Improvement"],
        [
            "Coloured stationary noise",
            f"{metrics['input_snr_db']:.2f} dB",
            f"{metrics['output_snr_db']:.2f} dB",
            f"+{metrics['snr_improvement_db']:.2f} dB",
        ],
    ]
    metric_table = Table(metric_data, colWidths=[66 * mm, 30 * mm, 30 * mm, 30 * mm])
    metric_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.45, LIGHT_GREY),
                ("BACKGROUND", (0, 1), (-1, -1), LIGHT_TEAL),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(metric_table)
    story.append(
        Paragraph(
            "This deterministic synthetic result verifies that the implementation and evaluation pipeline run end-to-end; it is not presented as evidence of real-speech performance. Final claims will be based on licensed speech/noise data across multiple SNRs.",
            styles["Caption"],
        )
    )
    spectrogram_path = ROOT / "results" / "spectrograms.png"
    if spectrogram_path.exists():
        image = Image(str(spectrogram_path), width=122 * mm, height=85.4 * mm)
        image.hAlign = "CENTER"
        story.append(KeepTogether([image, Paragraph("Figure 2. Synthetic clean, noisy, and enhanced spectrograms used for pipeline verification.", styles["Caption"])]))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"Built {OUTPUT}")
    print(f"Main-body word count: {word_count}")


if __name__ == "__main__":
    build()
