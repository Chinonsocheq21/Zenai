#!/usr/bin/env python3
"""Turn the source files into the openable ones.

    python3 tools/build_deliverables.py

    presentations/midterm-oct15.json  ->  presentations/ZenAI-Midterm-Oct15.pptx
    docs/build-plan.md               ->  docs/ZenAI-Build-Plan.docx
    docs/diagrams.md                 ->  docs/ZenAI-Diagrams-Source.docx

Edit the SOURCE (json / md), then re-run this. Never hand-edit the .pptx or
.docx -- they are build output and the next run overwrites them.

Needs: pip install python-pptx python-docx
"""
from __future__ import annotations

import json
import os
import re

from docx import Document
from docx.shared import Inches as DInches, Pt as DPt, RGBColor as DRGB
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

# ZenAI's palette -- same values as design/screens.html
PAPER = RGBColor(0xFB, 0xF9, 0xF6)
INK = RGBColor(0x1C, 0x26, 0x20)
MUTED = RGBColor(0x6B, 0x7A, 0x72)
GREEN = RGBColor(0x2F, 0x6F, 0x5E)
SOFT = RGBColor(0xE3, 0xEF, 0xE9)
LINE = RGBColor(0xE4, 0xE0, 0xD8)
SER = "Georgia"

TEAM = "Abraham Irabor  ·  Fnu Soh Tah Fon  ·  Joseph Williams  ·  Chinonso Egeolu"


def clean(t: str) -> str:
    """Strip markdown that has no meaning once rendered."""
    return re.sub(r"`([^`]+)`", r"\1", t or "")


def split_bold(text: str):
    """'a **b** c' -> [('a ',False),('b',True),(' c',False)]"""
    parts, buf, on = [], "", False
    i = 0
    while i < len(text):
        if text[i:i + 2] == "**":
            parts.append((buf, on)); buf = ""; on = not on; i += 2
        else:
            buf += text[i]; i += 1
    parts.append((buf, on))
    return [(c, b) for c, b in parts if c]


# --------------------------------------------------------------------- PPTX
def _tf(slide, x, y, w, h):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    return tf


def _p(tf, text, size, color=INK, bold=False, first=False, after=8,
       align=PP_ALIGN.LEFT, italic=False, font="Helvetica Neue"):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.alignment = align
    p.space_after = Pt(after)
    for chunk, b in split_bold(clean(text)):
        r = p.add_run(); r.text = chunk
        r.font.size = Pt(size); r.font.color.rgb = color
        r.font.bold = bold or b; r.font.italic = italic; r.font.name = font
    return p


def _rule(slide, x, y, w, color=GREEN, h=0.035):
    s = slide.shapes.add_shape(1, Inches(x), Inches(y), Inches(w), Inches(h))
    s.fill.solid(); s.fill.fore_color.rgb = color
    s.line.fill.background(); s.shadow.inherit = False


def build_pptx(src="presentations/midterm-oct15.json",
               out="presentations/ZenAI-Midterm-Oct15.pptx",
               diagram="docs/diagrams/01-architecture.png"):
    deck = json.load(open(src))
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    blank = prs.slide_layouts[6]

    for i, s in enumerate(deck["slides"]):
        lay = s.get("layout")
        sl = prs.slides.add_slide(blank)
        sl.background.fill.solid(); sl.background.fill.fore_color.rgb = PAPER
        note = s.get("note", "")

        if lay == "title":
            _rule(sl, 1.0, 2.35, 1.6)
            _p(_tf(sl, 1.0, 2.7, 11.3, 2.0), s["title"], 66, INK, first=True, font=SER, after=14)
            _p(_tf(sl, 1.0, 4.35, 10.5, 1.6), s.get("subtitle", ""), 17, MUTED, first=True)
            _p(_tf(sl, 1.0, 6.3, 11.3, 0.5), TEAM, 14, GREEN, first=True, bold=True)

        elif lay == "stat":
            box = sl.shapes.add_shape(1, Inches(0.9), Inches(1.5), Inches(3.5), Inches(2.6))
            box.fill.solid(); box.fill.fore_color.rgb = SOFT
            box.line.color.rgb = GREEN; box.line.width = Pt(2); box.shadow.inherit = False
            box.text_frame.word_wrap = True
            box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
            _p(box.text_frame, s.get("body", ""), 60, GREEN, first=True,
               align=PP_ALIGN.CENTER, font=SER)
            _p(_tf(sl, 5.0, 1.5, 7.5, 1.6), s.get("title", ""), 30, INK,
               first=True, font=SER, after=16)
            _p(_tf(sl, 5.0, 3.3, 7.5, 3.0), s.get("subtitle", ""), 16, MUTED, first=True)

        elif lay == "bullets" and i == 2 and os.path.exists(diagram):
            # the architecture slide carries the real rendered diagram
            _p(_tf(sl, 0.8, 0.55, 11.8, 0.7), s["title"], 30, INK, first=True, font=SER)
            _rule(sl, 0.8, 1.25, 1.3)
            sl.shapes.add_picture(diagram, Inches(2.55), Inches(1.55), height=Inches(5.15))
            _p(_tf(sl, 0.8, 6.85, 11.8, 0.5),
               "Shaded = built.  Outlined = next.  The yellow box is the contribution.",
               13, MUTED, first=True, italic=True)

        elif lay in ("bullets", "split"):
            _p(_tf(sl, 0.8, 0.55, 11.8, 0.8), s["title"], 32, INK, first=True, font=SER)
            _rule(sl, 0.8, 1.32, 1.3)
            wide = 11.8 if lay == "bullets" else 7.1
            tf = _tf(sl, 0.8, 1.85, wide, 5.0)
            for j, b in enumerate(s.get("bullets", [])):
                _p(tf, "—   " + b, 17, INK, first=(j == 0), after=15)
            if lay == "split":
                ph = sl.shapes.add_shape(1, Inches(8.3), Inches(1.85), Inches(4.2), Inches(4.4))
                ph.fill.solid(); ph.fill.fore_color.rgb = RGBColor(0xF2, 0xEF, 0xE9)
                ph.line.color.rgb = LINE; ph.shadow.inherit = False
                ph.text_frame.word_wrap = True
                ph.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
                _p(ph.text_frame,
                   "[ screenshot: docker compose up,\n4 services healthy + green CI ]",
                   13, MUTED, first=True, align=PP_ALIGN.CENTER, italic=True)

        if note:
            sl.notes_slide.notes_text_frame.text = note

    prs.save(out)
    return out


# --------------------------------------------------------------------- DOCX
DINK = DRGB(0x1C, 0x26, 0x20)
DGREEN = DRGB(0x2F, 0x6F, 0x5E)
DMUTED = DRGB(0x6B, 0x7A, 0x72)


def _dp(p, text, size=11, color=DINK, base_bold=False):
    for chunk, b in split_bold(clean(text)):
        r = p.add_run(chunk)
        r.font.size = DPt(size); r.font.color.rgb = color
        r.font.bold = b or base_bold; r.font.name = "Calibri"
    return p


def build_docx(md_path, out_path, title, subtitle):
    doc = Document()
    for s in doc.sections:
        s.left_margin = s.right_margin = DInches(0.9)
        s.top_margin = s.bottom_margin = DInches(0.8)

    r = doc.add_paragraph().add_run(title)
    r.font.size = DPt(26); r.font.bold = True; r.font.color.rgb = DINK; r.font.name = "Calibri"
    r = doc.add_paragraph().add_run(subtitle)
    r.font.size = DPt(11); r.font.color.rgb = DGREEN; r.font.name = "Calibri"
    doc.add_paragraph()

    lines = open(md_path).read().split("\n")
    i = 0
    while i < len(lines):
        st = lines[i].strip()

        if st.startswith("|") and i + 1 < len(lines) and set(lines[i + 1].strip()) <= set("|-: "):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not set("".join(cells)) <= set("-: "):
                    rows.append(cells)
                i += 1
            if rows:
                cols = max(len(x) for x in rows)
                t = doc.add_table(rows=0, cols=cols); t.style = "Light Grid Accent 1"
                for ri, row in enumerate(rows):
                    cs = t.add_row().cells
                    for ci in range(cols):
                        _dp(cs[ci].paragraphs[0], row[ci] if ci < len(row) else "",
                            size=9.5, base_bold=(ri == 0))
                doc.add_paragraph()
            continue

        if st.startswith("```"):
            i += 1; buf = []
            while i < len(lines) and not lines[i].strip().startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            r = doc.add_paragraph().add_run("\n".join(buf))
            r.font.name = "Menlo"; r.font.size = DPt(8.5); r.font.color.rgb = DMUTED
            continue

        if re.match(r"^#{1,4} ", st):
            lvl = len(st.split(" ")[0])
            p = doc.add_paragraph()
            p.paragraph_format.space_before = DPt(16 if lvl <= 2 else 10)
            p.paragraph_format.space_after = DPt(5)
            _dp(p, st[lvl + 1:], size={1: 20, 2: 16, 3: 13, 4: 11.5}[lvl],
                color=DINK if lvl <= 2 else DGREEN, base_bold=True)
        elif st.startswith("> "):
            p = doc.add_paragraph(); p.paragraph_format.left_indent = DInches(0.35)
            _dp(p, st[2:], color=DGREEN)
        elif re.match(r"^[-*] ", st):
            _dp(doc.add_paragraph(style="List Bullet"), st[2:])
        elif re.match(r"^\d+\. ", st):
            _dp(doc.add_paragraph(style="List Number"), re.sub(r"^\d+\. ", "", st))
        elif st and not st.startswith("---"):
            p = doc.add_paragraph(); p.paragraph_format.space_after = DPt(7)
            _dp(p, st)
        i += 1

    doc.save(out_path)
    return out_path


if __name__ == "__main__":
    print("→", build_pptx())
    print("→", build_docx("docs/build-plan.md", "docs/ZenAI-Build-Plan.docx",
                          "ZenAI — Build Plan",
                          "COSC 490 · Project 5 · Group 3 · Sep 30 → Dec 3, 2026"))
    print("→", build_docx("docs/diagrams.md", "docs/ZenAI-Diagrams-Source.docx",
                          "ZenAI — Diagram source (Mermaid)",
                          "Paste into Lucidchart: Insert → Diagram as code → Mermaid"))
