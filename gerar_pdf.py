#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador Editorial Nativo (.ODT e .PDF) para o livro 'Telefone Sem Fio da Bíblia',
de Gustavo H. N. Gomes.
Lê MANUSCRITO_COMPLETO.md, constrói um arquivo OpenDocument Text (.odt) com
capa ilustrada (capa_frente.png), folha de rosto, sumário, capítulos com tipografia
editorial (Noto Serif, Noto Sans, Noto Sans Hebrew), tabelas exegéticas e
contracapa ilustrada (contracapa.png), compilando o PDF final via LibreOffice.
"""

import os
import re
import shutil
import zipfile
import subprocess
from xml.sax.saxutils import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MD_PATH = os.path.join(BASE_DIR, "documentacao", "MANUSCRITO_COMPLETO.md")
if not os.path.exists(MD_PATH):
    MD_PATH = os.path.join(BASE_DIR, "MANUSCRITO_COMPLETO.md")
FRONT_COVER_PATH = os.path.join(BASE_DIR, "capa_frente.png")
BACK_COVER_PATH = os.path.join(BASE_DIR, "contracapa.png")
ODT_PATH = os.path.join(BASE_DIR, "Telefone_Sem_Fio_da_Biblia.odt")
PDF_PATH = os.path.join(BASE_DIR, "Telefone_Sem_Fio_da_Biblia.pdf")


def format_odt_inline(text: str) -> str:
    """Converte marcações inline Markdown (***, **, *, `) em tags ODF <text:span> sem aninhamento residual."""
    tokens = []

    def save_token(xml_str: str) -> str:
        idx = len(tokens)
        tokens.append(xml_str)
        return f"@@ODTTOKEN{idx}@@"

    # 1. Código inline `...`
    def repl_code(m):
        inner = escape(m.group(1))
        return save_token(f'<text:span text:style-name="TCode">{inner}</text:span>')

    text = re.sub(r"`([^`]+)`", repl_code, text)

    # 2. Negrito + Itálico ***...***
    def repl_bi(m):
        inner = escape(m.group(1))
        return save_token(f'<text:span text:style-name="TBI">{inner}</text:span>')

    text = re.sub(r"\*\*\*([^*]+)\*\*\*", repl_bi, text)

    # 3. Negrito **...** (podendo conter *itálico* interno)
    def repl_b(m):
        raw_inner = m.group(1)
        parts = re.split(r"(\*[^*]+\*)", raw_inner)
        out_parts = []
        for p in parts:
            if p.startswith("*") and p.endswith("*") and len(p) > 2:
                out_parts.append(
                    f'<text:span text:style-name="TBI">{escape(p[1:-1])}</text:span>'
                )
            elif p:
                out_parts.append(
                    f'<text:span text:style-name="TBold">{escape(p)}</text:span>'
                )
        return save_token("".join(out_parts))

    text = re.sub(r"\*\*([^*]+(?:\*[^*]+\*[^*]*)*)\*\*", repl_b, text)

    # 4. Itálico *...*
    def repl_i(m):
        inner = escape(m.group(1))
        return save_token(f'<text:span text:style-name="TItalic">{inner}</text:span>')

    text = re.sub(r"\*([^*]+)\*", repl_i, text)

    # Escape do texto restante
    escaped = escape(text)

    # Restaurar tokens em ORDEM REVERSA para resolver tokens aninhados
    for idx, xml_str in reversed(list(enumerate(tokens))):
        escaped = escaped.replace(f"@@ODTTOKEN{idx}@@", xml_str)

    return escaped


def parse_md_to_odt_body(md_text: str) -> str:
    lines = md_text.splitlines()
    n = len(lines)
    i = 0

    # Pular cabeçalho inicial bruto do arquivo Markdown
    while i < n and (
        lines[i].startswith("# TELEFONE SEM FIO")
        or lines[i].startswith("#### Gustavo H. N. Gomes")
        or lines[i].startswith("### O Silêncio de Cristo")
        or lines[i].strip() == ""
        or lines[i].strip() == "---"
    ):
        i += 1
        if i > 7:
            break

    # Coletar Sumário (TOC)
    toc_entries = []
    for idx, line in enumerate(lines[i:], start=i):
        s = line.strip()
        if s.startswith("# "):
            label = s[2:].strip()
            sub = ""
            if idx + 1 < n and lines[idx + 1].strip().startswith("## "):
                sub = lines[idx + 1].strip()[3:].strip()
            toc_entries.append((label, sub))

    body_xml = []

    # 1. CAPA DO LIVRO (Página 1 em sangria total 210mm x 297mm usando capa_frente.png)
    body_xml.append(
        '<text:p text:style-name="CoverImagePara">'
        '<draw:frame draw:style-name="FullPageCoverFrame" draw:name="CapaFrente" '
        'text:anchor-type="paragraph" svg:x="0mm" svg:y="0mm" svg:width="210mm" svg:height="297mm" draw:z-index="0">'
        '<draw:image xlink:href="Pictures/capa_frente.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>'
        "</draw:frame>"
        "</text:p>"
    )

    # 2. FOLHA DE ROSTO (Master Page: Standard)
    body_xml.append(
        '<text:p text:style-name="TitlePageAuthor">GUSTAVO H. N. GOMES</text:p>'
    )
    body_xml.append(
        '<text:p text:style-name="TitlePageMain">TELEFONE SEM FIO DA BÍBLIA</text:p>'
    )
    body_xml.append(
        '<text:p text:style-name="TitlePageSub">'
        "O Silêncio de Cristo, o Dedo dos Tradutores e a Verdadeira História "
        "do Debate sobre Homossexualidade e Pecado"
        "</text:p>"
    )
    body_xml.append('<text:p text:style-name="TitlePageOrnament">✦</text:p>')
    body_xml.append(
        '<text:p text:style-name="MetaBoxTitle">'
        "FICHA DE REFERÊNCIA EDITORIAL, TEXTUAL E FILOLÓGICA"
        "</text:p>"
    )
    body_xml.append(
        '<text:p text:style-name="MetaBoxItem">'
        '<text:span text:style-name="TBold">Autor:</text:span> '
        "Gustavo H. N. Gomes."
        "</text:p>"
    )
    body_xml.append(
        '<text:p text:style-name="MetaBoxItem">'
        '<text:span text:style-name="TBold">Texto Hebraico Base:</text:span> '
        '<text:span text:style-name="TItalic">Biblia Hebraica Stuttgartensia</text:span> (BHS) '
        "e Manuscritos do Mar Morto (Qumran)."
        "</text:p>"
    )
    body_xml.append(
        '<text:p text:style-name="MetaBoxItem">'
        '<text:span text:style-name="TBold">Texto Grego Base:</text:span> '
        '<text:span text:style-name="TItalic">Septuaginta</text:span> (LXX) e '
        '<text:span text:style-name="TItalic">Novum Testamentum Graece</text:span> (Nestle-Aland 28ª ed. / UBS5).'
        "</text:p>"
    )
    body_xml.append(
        '<text:p text:style-name="MetaBoxItem">'
        '<text:span text:style-name="TBold">Léxicos e Dicionários:</text:span> '
        "BDB e HALOT (Hebraico); LSJ, BDAG, TDNT (Kittel) e Concordância de Strong (Grego)."
        "</text:p>"
    )
    body_xml.append(
        '<text:p text:style-name="MetaBoxItem">'
        '<text:span text:style-name="TBold">Traduções Comparadas:</text:span> '
        "ARA, ACF, ARC, NAA, NVI, NTLH, NBV, KJF, Bíblia de Jerusalém, TEB e RSV (1946)."
        "</text:p>"
    )

    # 3. PÁGINA DE SUMÁRIO (calibrada para caber inteira numa única página)
    body_xml.append('<text:p text:style-name="TOCHeading">SUMÁRIO DA OBRA</text:p>')
    for label, sub in toc_entries:
        if sub:
            body_xml.append(
                f'<text:p text:style-name="TOCEntryLabel">{escape(label)}</text:p>'
            )
            body_xml.append(
                f'<text:p text:style-name="TOCEntrySub">{escape(sub)}</text:p>'
            )
        else:
            body_xml.append(
                f'<text:p text:style-name="TOCEntryLabel">{escape(label)}</text:p>'
            )

    # 4. CORPO DOS CAPÍTULOS
    blockquote_lines = []
    table_lines = []
    table_count = 0

    def flush_blockquote():
        nonlocal blockquote_lines
        if not blockquote_lines:
            return
        for idx_b, b_line in enumerate(blockquote_lines):
            if b_line == "":
                continue
            style = "QuoteFirst" if idx_b == 0 else "QuoteBody"
            body_xml.append(
                f'<text:p text:style-name="{style}">{format_odt_inline(b_line)}</text:p>'
            )
        blockquote_lines = []

    def flush_table():
        nonlocal table_lines, table_count
        if not table_lines:
            return
        rows = []
        for idx_t, tline in enumerate(table_lines):
            stripped_t = tline.strip().strip("|")
            cells = [c.strip() for c in stripped_t.split("|")]
            if idx_t == 1 and all(re.match(r"^:?-{2,}:?$", c) for c in cells):
                continue
            rows.append((idx_t == 0, cells))
        table_lines = []
        if not rows:
            return

        table_count += 1
        num_cols = len(rows[0][1])
        cell_text_style = "TableCellWideText" if num_cols >= 4 else "TableCellText"
        header_text_style = "TableHeaderWideText" if num_cols >= 4 else "TableHeaderText"

        body_xml.append(
            f'<table:table table:name="TabelaExegese{table_count}" table:style-name="ExegeticalTable">'
        )
        body_xml.append(
            f'<table:table-column table:style-name="Col{num_cols}" table:number-columns-repeated="{num_cols}"/>'
        )

        for r_idx, (is_header, cells) in enumerate(rows):
            while len(cells) < num_cols:
                cells.append("")
            cells = cells[:num_cols]

            if is_header:
                body_xml.append("<table:table-header-rows>")
                body_xml.append("<table:table-row>")
                for c in cells:
                    body_xml.append(
                        '<table:table-cell table:style-name="TableHeaderCell" office:value-type="string">'
                        f'<text:p text:style-name="{header_text_style}">{format_odt_inline(c)}</text:p>'
                        "</table:table-cell>"
                    )
                body_xml.append("</table:table-row>")
                body_xml.append("</table:table-header-rows>")
            else:
                cell_style = "TableBodyCellEven" if r_idx % 2 == 0 else "TableBodyCellOdd"
                body_xml.append("<table:table-row>")
                for c in cells:
                    body_xml.append(
                        f'<table:table-cell table:style-name="{cell_style}" office:value-type="string">'
                        f'<text:p text:style-name="{cell_text_style}">{format_odt_inline(c)}</text:p>'
                        "</table:table-cell>"
                    )
                body_xml.append("</table:table-row>")

        body_xml.append("</table:table>")
        body_xml.append('<text:p text:style-name="AfterTableSpace"/>')

    while i < n:
        line = lines[i]
        stripped = line.strip()

        if stripped.startswith("|") and stripped.endswith("|"):
            flush_blockquote()
            table_lines.append(stripped)
            i += 1
            continue
        else:
            flush_table()

        if stripped.startswith(">"):
            b_text = stripped[1:].strip()
            blockquote_lines.append(b_text)
            i += 1
            continue
        else:
            flush_blockquote()

        if stripped == "":
            i += 1
            continue

        if stripped == "---":
            j = i + 1
            while j < n and lines[j].strip() == "":
                j += 1
            if j < n and not lines[j].strip().startswith("# "):
                body_xml.append('<text:p text:style-name="SectionDivider">✦</text:p>')
            i += 1
            continue

        if stripped.startswith("# "):
            h1_text = stripped[2:].strip()
            sub_text = ""
            if i + 1 < n and lines[i + 1].strip().startswith("## "):
                sub_text = lines[i + 1].strip()[3:].strip()
                i += 1
            body_xml.append(
                f'<text:p text:style-name="ChapterLabel">{format_odt_inline(h1_text)}</text:p>'
            )
            if sub_text:
                body_xml.append(
                    f'<text:h text:style-name="ChapterTitle" text:outline-level="1">'
                    f"{format_odt_inline(sub_text)}</text:h>"
                )
            else:
                body_xml.append(
                    f'<text:h text:style-name="ChapterTitle" text:outline-level="1">'
                    f"{format_odt_inline(h1_text)}</text:h>"
                )
            body_xml.append('<text:p text:style-name="ChapterOrnament">✦</text:p>')
            i += 1
            continue

        if stripped.startswith("## "):
            h2_text = stripped[3:].strip()
            body_xml.append(
                f'<text:h text:style-name="Heading2" text:outline-level="2">'
                f"{format_odt_inline(h2_text)}</text:h>"
            )
            i += 1
            continue

        if stripped.startswith("### "):
            h3_text = stripped[4:].strip()
            body_xml.append(
                f'<text:h text:style-name="Heading3" text:outline-level="3">'
                f"{format_odt_inline(h3_text)}</text:h>"
            )
            i += 1
            continue

        if stripped.startswith("#### "):
            h4_text = stripped[5:].strip()
            body_xml.append(
                f'<text:h text:style-name="Heading4" text:outline-level="4">'
                f"{format_odt_inline(h4_text)}</text:h>"
            )
            i += 1
            continue

        if stripped.startswith("- "):
            item_text = stripped[2:].strip()
            while i + 1 < n and lines[i + 1].startswith("   ") and lines[i + 1].strip() != "":
                i += 1
                item_text += " " + lines[i].strip()
            body_xml.append(
                f'<text:p text:style-name="BulletItem">{format_odt_inline(item_text)}</text:p>'
            )
            i += 1
            continue

        m_ol = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if m_ol:
            num_str = m_ol.group(1)
            item_text = m_ol.group(2).strip()
            while i + 1 < n and lines[i + 1].startswith("   ") and lines[i + 1].strip() != "":
                i += 1
                item_text += " " + lines[i].strip()
            body_xml.append(
                f'<text:p text:style-name="NumberedItem">'
                f'<text:span text:style-name="TBold">{num_str}.</text:span>  '
                f"{format_odt_inline(item_text)}</text:p>"
            )
            i += 1
            continue

        body_xml.append(
            f'<text:p text:style-name="BodyParagraph">{format_odt_inline(stripped)}</text:p>'
        )
        i += 1

    flush_blockquote()
    flush_table()

    # 5. CONTRACAPA DO LIVRO (Última página em sangria total 210mm x 297mm usando contracapa.png)
    body_xml.append(
        '<text:p text:style-name="BackCoverImagePara">'
        '<draw:frame draw:style-name="FullPageCoverFrame" draw:name="Contracapa" '
        'text:anchor-type="paragraph" svg:x="0mm" svg:y="0mm" svg:width="210mm" svg:height="297mm" draw:z-index="0">'
        '<draw:image xlink:href="Pictures/contracapa.png" xlink:type="simple" xlink:show="embed" xlink:actuate="onLoad"/>'
        "</draw:frame>"
        "</text:p>"
    )

    return "\n".join(body_xml)


def create_odt(body_xml: str, odt_path: str):
    manifest_xml = """<?xml version="1.0" encoding="UTF-8"?>
<manifest:manifest xmlns:manifest="urn:oasis:names:tc:opendocument:xmlns:manifest:1.0" manifest:version="1.2">
 <manifest:file-entry manifest:full-path="/" manifest:version="1.2" manifest:media-type="application/vnd.oasis.opendocument.text"/>
 <manifest:file-entry manifest:full-path="content.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="styles.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="meta.xml" manifest:media-type="text/xml"/>
 <manifest:file-entry manifest:full-path="Pictures/capa_frente.png" manifest:media-type="image/png"/>
 <manifest:file-entry manifest:full-path="Pictures/contracapa.png" manifest:media-type="image/png"/>
</manifest:manifest>"""

    meta_xml = """<?xml version="1.0" encoding="UTF-8"?>
<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:dc="http://purl.org/dc/elements/1.1/"
 xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2">
 <office:meta>
  <dc:title>Telefone Sem Fio da Bíblia</dc:title>
  <dc:creator>Gustavo H. N. Gomes</dc:creator>
  <meta:initial-creator>Gustavo H. N. Gomes</meta:initial-creator>
  <dc:subject>O Silêncio de Cristo, o Dedo dos Tradutores e a Verdadeira História do Debate sobre Homossexualidade e Pecado</dc:subject>
  <dc:language>pt-BR</dc:language>
 </office:meta>
</office:document-meta>"""

    font_decls = """
  <style:font-face style:name="Noto Serif" svg:font-family="'Noto Serif'" style:font-family-generic="roman" style:font-pitch="variable"/>
  <style:font-face style:name="Noto Serif Display" svg:font-family="'Noto Serif Display'" style:font-family-generic="roman" style:font-pitch="variable"/>
  <style:font-face style:name="Noto Sans" svg:font-family="'Noto Sans'" style:font-family-generic="swiss" style:font-pitch="variable"/>
  <style:font-face style:name="Noto Sans Hebrew" svg:font-family="'Noto Sans Hebrew'" style:font-family-generic="system" style:font-pitch="variable"/>
  <style:font-face style:name="Liberation Mono" svg:font-family="'Liberation Mono'" style:font-family-generic="modern" style:font-pitch="fixed"/>
"""

    styles_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-styles
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 office:version="1.2">
 <office:font-face-decls>
  {font_decls}
 </office:font-face-decls>
 <office:styles>
  <style:default-style style:family="paragraph">
   <style:paragraph-properties fo:hyphenation-ladder-count="no-limit" style:line-break="strict"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="11pt" fo:language="pt" fo:country="BR"
    style:font-name-asian="Noto Sans" style:font-size-asian="11pt"
    style:font-name-complex="Noto Sans Hebrew" style:font-size-complex="11.5pt"/>
  </style:default-style>

  <style:style style:name="HeaderParagraph" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-bottom="4mm"
    fo:border-bottom="0.5pt solid #cbd5e1" fo:padding-bottom="1.5mm"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="8pt" fo:color="#64748b" fo:letter-spacing="1.5pt"/>
  </style:style>

  <style:style style:name="FooterParagraph" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-top="4mm"
    fo:border-top="0.5pt solid #cbd5e1" fo:padding-top="1.5mm"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="9pt" fo:color="#475569" fo:font-weight="bold"/>
  </style:style>
 </office:styles>

 <office:automatic-styles>
  <style:page-layout style:name="pmCover">
   <style:page-layout-properties fo:page-width="210mm" fo:page-height="297mm"
    style:print-orientation="portrait"
    fo:margin-top="0mm" fo:margin-bottom="0mm" fo:margin-left="0mm" fo:margin-right="0mm"
    fo:background-color="#070a10"/>
  </style:page-layout>

  <style:page-layout style:name="pmStandard">
   <style:page-layout-properties fo:page-width="210mm" fo:page-height="297mm"
    style:print-orientation="portrait"
    fo:margin-top="20mm" fo:margin-bottom="20mm" fo:margin-left="24mm" fo:margin-right="24mm"
    fo:background-color="#ffffff"/>
   <style:header-style>
    <style:header-footer-properties fo:min-height="8mm" fo:margin-bottom="4mm"/>
   </style:header-style>
   <style:footer-style>
    <style:header-footer-properties fo:min-height="8mm" fo:margin-top="4mm"/>
   </style:footer-style>
  </style:page-layout>

  <style:page-layout style:name="pmBackCover">
   <style:page-layout-properties fo:page-width="210mm" fo:page-height="297mm"
    style:print-orientation="portrait"
    fo:margin-top="0mm" fo:margin-bottom="0mm" fo:margin-left="0mm" fo:margin-right="0mm"
    fo:background-color="#070a10"/>
  </style:page-layout>
 </office:automatic-styles>

 <office:master-styles>
  <style:master-page style:name="CoverPage" style:page-layout-name="pmCover" style:next-style-name="Standard"/>
  <style:master-page style:name="Standard" style:page-layout-name="pmStandard">
   <style:header>
    <text:p text:style-name="HeaderParagraph">TELEFONE SEM FIO DA BÍBLIA</text:p>
   </style:header>
   <style:footer>
    <text:p text:style-name="FooterParagraph"><text:page-number text:select-page="current"/></text:p>
   </style:footer>
  </style:master-page>
  <style:master-page style:name="BackCoverPage" style:page-layout-name="pmBackCover"/>
 </office:master-styles>
</office:document-styles>"""

    content_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<office:document-content
 xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0"
 xmlns:style="urn:oasis:names:tc:opendocument:xmlns:style:1.0"
 xmlns:text="urn:oasis:names:tc:opendocument:xmlns:text:1.0"
 xmlns:table="urn:oasis:names:tc:opendocument:xmlns:table:1.0"
 xmlns:draw="urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
 xmlns:fo="urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:svg="urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0"
 office:version="1.2">
 <office:font-face-decls>
  {font_decls}
 </office:font-face-decls>

 <office:automatic-styles>
  <style:style style:name="TBold" style:family="text">
   <style:text-properties fo:font-weight="bold" style:font-weight-asian="bold" style:font-weight-complex="bold"/>
  </style:style>
  <style:style style:name="TItalic" style:family="text">
   <style:text-properties fo:font-style="italic" style:font-style-asian="italic" style:font-style-complex="italic"/>
  </style:style>
  <style:style style:name="TBI" style:family="text">
   <style:text-properties fo:font-weight="bold" fo:font-style="italic"
    style:font-weight-complex="bold" style:font-style-complex="italic"/>
  </style:style>
  <style:style style:name="TCode" style:family="text">
   <style:text-properties style:font-name="Liberation Mono" fo:font-size="9pt" fo:color="#0f172a" fo:background-color="#f1f5f9"/>
  </style:style>

  <!-- Quadro de Imagem em Sangria Total para Capa e Contracapa -->
  <style:style style:name="FullPageCoverFrame" style:family="graphic">
   <style:graphic-properties style:run-through="background" style:wrap="run-through"
    style:number-wrapped-paragraphs="no-limit"
    style:horizontal-pos="from-left" style:horizontal-rel="page"
    style:vertical-pos="from-top" style:vertical-rel="page"
    fo:margin="0mm" fo:padding="0mm" fo:border="none"/>
  </style:style>

  <style:style style:name="CoverImagePara" style:family="paragraph" style:master-page-name="CoverPage">
   <style:paragraph-properties fo:margin="0mm" fo:padding="0mm" fo:line-height="2pt"/>
   <style:text-properties fo:font-size="2pt"/>
  </style:style>

  <style:style style:name="BackCoverImagePara" style:family="paragraph" style:master-page-name="BackCoverPage">
   <style:paragraph-properties fo:break-before="page" fo:margin="0mm" fo:padding="0mm" fo:line-height="2pt"/>
   <style:text-properties fo:font-size="2pt"/>
  </style:style>

  <!-- Folha de Rosto -->
  <style:style style:name="TitlePageAuthor" style:family="paragraph" style:master-page-name="Standard">
   <style:paragraph-properties fo:break-before="page" fo:text-align="center" fo:margin-top="22mm" fo:margin-bottom="6mm"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="11pt" fo:font-weight="bold" fo:color="#9a6f18" fo:letter-spacing="2.5pt"/>
  </style:style>
  <style:style style:name="TitlePageMain" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-bottom="5mm"/>
   <style:text-properties style:font-name="Noto Serif Display" fo:font-size="24pt" fo:font-weight="bold" fo:color="#0f172a"/>
  </style:style>
  <style:style style:name="TitlePageSub" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-left="12mm" fo:margin-right="12mm" fo:margin-bottom="8mm" fo:line-height="140%"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="12pt" fo:font-style="italic" fo:color="#334155"/>
  </style:style>
  <style:style style:name="TitlePageOrnament" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-bottom="38mm"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="14pt" fo:color="#b48a28"/>
  </style:style>
  <style:style style:name="MetaBoxTitle" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:margin-bottom="3mm" fo:padding-top="4mm"
    fo:border-top="1pt solid #0f172a"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="9pt" fo:font-weight="bold" fo:color="#0f172a" fo:letter-spacing="1pt"/>
  </style:style>
  <style:style style:name="MetaBoxItem" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:margin-bottom="2mm" fo:line-height="135%"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="9pt" fo:color="#334155"/>
  </style:style>

  <!-- Sumário (calibrado para 1 página) -->
  <style:style style:name="TOCHeading" style:family="paragraph">
   <style:paragraph-properties fo:break-before="page" fo:text-align="center" fo:margin-top="2mm" fo:margin-bottom="5mm"
    fo:border-bottom="1.5pt solid #0f172a" fo:padding-bottom="2.5mm"/>
   <style:text-properties style:font-name="Noto Serif Display" fo:font-size="17pt" fo:font-weight="bold" fo:color="#0f172a" fo:letter-spacing="1.5pt"/>
  </style:style>
  <style:style style:name="TOCEntryLabel" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:margin-top="2mm" fo:margin-bottom="0.4mm" fo:keep-with-next="always"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="8.5pt" fo:font-weight="bold" fo:color="#9a6f18" fo:letter-spacing="1pt"/>
  </style:style>
  <style:style style:name="TOCEntrySub" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:margin-bottom="1.5mm"
    fo:border-bottom="0.5pt dotted #cbd5e1" fo:padding-bottom="1.4mm"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="10.2pt" fo:font-weight="bold" fo:color="#0f172a"/>
  </style:style>

  <!-- Capítulos -->
  <style:style style:name="ChapterLabel" style:family="paragraph">
   <style:paragraph-properties fo:break-before="page" fo:text-align="center" fo:margin-top="2mm" fo:margin-bottom="2mm" fo:keep-with-next="always"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="9.5pt" fo:font-weight="bold" fo:color="#9a6f18" fo:letter-spacing="2.2pt"/>
  </style:style>
  <style:style style:name="ChapterTitle" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-bottom="2.5mm" fo:line-height="122%" fo:keep-with-next="always"/>
   <style:text-properties style:font-name="Noto Serif Display" fo:font-size="18.5pt" fo:font-weight="bold" fo:color="#0f172a"/>
  </style:style>
  <style:style style:name="ChapterOrnament" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-bottom="4mm"
    fo:border-bottom="0.75pt solid #d4af37" fo:padding-bottom="2.5mm" fo:keep-with-next="always"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="11pt" fo:color="#b48a28"/>
  </style:style>

  <style:style style:name="AuthorSignature" style:family="paragraph">
   <style:paragraph-properties fo:text-align="right" fo:margin-top="2mm" fo:margin-bottom="1mm"/>
   <style:text-properties style:font-name="Noto Serif Display" fo:font-size="11.5pt" fo:font-weight="bold" fo:font-style="italic" fo:color="#0f172a"/>
  </style:style>

  <style:style style:name="Heading2" style:family="paragraph">
   <style:paragraph-properties fo:margin-top="6.5mm" fo:margin-bottom="3mm" fo:keep-with-next="always"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="13.5pt" fo:font-weight="bold" fo:color="#0f172a"/>
  </style:style>
  <style:style style:name="Heading3" style:family="paragraph">
   <style:paragraph-properties fo:margin-top="6mm" fo:margin-bottom="2.5mm" fo:keep-with-next="always"
    fo:border-left="2.5pt solid #b48a28" fo:padding-left="3mm"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="11.2pt" fo:font-weight="bold" fo:color="#162234"/>
  </style:style>
  <style:style style:name="Heading4" style:family="paragraph">
   <style:paragraph-properties fo:margin-top="4.5mm" fo:margin-bottom="2mm" fo:keep-with-next="always"/>
   <style:text-properties style:font-name="Noto Sans" fo:font-size="10.2pt" fo:font-weight="bold" fo:color="#1e293b"/>
  </style:style>

  <!-- Corpo e Citações -->
  <style:style style:name="BodyParagraph" style:family="paragraph">
   <style:paragraph-properties fo:text-align="justify" fo:margin-bottom="3.2mm" fo:line-height="148%"
    fo:orphans="2" fo:widows="2"/>
   <style:text-properties style:font-name="Noto Serif" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="10.8pt" style:font-size-complex="11.5pt" fo:color="#1e242b"/>
  </style:style>

  <style:style style:name="QuoteFirst" style:family="paragraph">
   <style:paragraph-properties fo:text-align="justify" fo:margin-left="5mm" fo:margin-right="3mm"
    fo:margin-top="3.5mm" fo:margin-bottom="1.5mm" fo:line-height="140%"
    fo:background-color="#f8fafc" fo:border-left="2.5pt solid #162234" fo:padding="2.5mm"/>
   <style:text-properties style:font-name="Noto Serif" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="10pt" style:font-size-complex="11pt" fo:color="#1e293b"/>
  </style:style>
  <style:style style:name="QuoteBody" style:family="paragraph">
   <style:paragraph-properties fo:text-align="justify" fo:margin-left="5mm" fo:margin-right="3mm"
    fo:margin-top="0mm" fo:margin-bottom="2mm" fo:line-height="140%"
    fo:background-color="#f8fafc" fo:border-left="2.5pt solid #162234" fo:padding="2.5mm"/>
   <style:text-properties style:font-name="Noto Serif" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="10pt" style:font-size-complex="11pt" fo:color="#1e293b"/>
  </style:style>

  <style:style style:name="BulletItem" style:family="paragraph">
   <style:paragraph-properties fo:text-align="justify" fo:margin-left="4mm" fo:margin-bottom="2.2mm" fo:line-height="144%"
    fo:border-left="1.2pt solid #cbd5e1" fo:padding-left="2.5mm"/>
   <style:text-properties style:font-name="Noto Serif" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="10.6pt" style:font-size-complex="11.2pt" fo:color="#1e242b"/>
  </style:style>
  <style:style style:name="NumberedItem" style:family="paragraph">
   <style:paragraph-properties fo:text-align="justify" fo:margin-left="5mm" fo:margin-bottom="2.4mm" fo:line-height="144%"/>
   <style:text-properties style:font-name="Noto Serif" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="10.6pt" style:font-size-complex="11.2pt" fo:color="#1e242b"/>
  </style:style>

  <style:style style:name="SectionDivider" style:family="paragraph">
   <style:paragraph-properties fo:text-align="center" fo:margin-top="4mm" fo:margin-bottom="4mm"/>
   <style:text-properties style:font-name="Noto Serif" fo:font-size="10pt" fo:color="#b48a28"/>
  </style:style>

  <!-- Tabelas Exegéticas e Larguras de Coluna -->
  <style:style style:name="ExegeticalTable" style:family="table">
   <style:table-properties style:width="162mm" fo:margin-top="4mm" fo:margin-bottom="4mm" table:align="center"/>
  </style:style>
  <style:style style:name="Col2" style:family="table-column"><style:table-column-properties style:column-width="81mm"/></style:style>
  <style:style style:name="Col3" style:family="table-column"><style:table-column-properties style:column-width="54mm"/></style:style>
  <style:style style:name="Col4" style:family="table-column"><style:table-column-properties style:column-width="40.5mm"/></style:style>
  <style:style style:name="Col5" style:family="table-column"><style:table-column-properties style:column-width="32.4mm"/></style:style>
  <style:style style:name="Col6" style:family="table-column"><style:table-column-properties style:column-width="27mm"/></style:style>

  <style:style style:name="TableHeaderCell" style:family="table-cell">
   <style:table-cell-properties fo:background-color="#162234" fo:padding="2mm" fo:border="0.5pt solid #162234"/>
  </style:style>
  <style:style style:name="TableBodyCellOdd" style:family="table-cell">
   <style:table-cell-properties fo:background-color="#ffffff" fo:padding="1.8mm" fo:border="0.5pt solid #cbd5e1"/>
  </style:style>
  <style:style style:name="TableBodyCellEven" style:family="table-cell">
   <style:table-cell-properties fo:background-color="#f8fafc" fo:padding="1.8mm" fo:border="0.5pt solid #cbd5e1"/>
  </style:style>
  <style:style style:name="TableHeaderText" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:line-height="122%"/>
   <style:text-properties style:font-name="Noto Sans" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="8.6pt" fo:font-weight="bold" fo:color="#ffffff"/>
  </style:style>
  <style:style style:name="TableHeaderWideText" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:line-height="118%"/>
   <style:text-properties style:font-name="Noto Sans" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="7.6pt" fo:font-weight="bold" fo:color="#ffffff"/>
  </style:style>
  <style:style style:name="TableCellText" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:line-height="128%"/>
   <style:text-properties style:font-name="Noto Sans" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="8.5pt" style:font-size-complex="9.2pt" fo:color="#1e293b"/>
  </style:style>
  <style:style style:name="TableCellWideText" style:family="paragraph">
   <style:paragraph-properties fo:text-align="left" fo:line-height="122%"/>
   <style:text-properties style:font-name="Noto Sans" style:font-name-complex="Noto Sans Hebrew"
    fo:font-size="7.5pt" style:font-size-complex="8.4pt" fo:color="#1e293b"/>
  </style:style>
  <style:style style:name="AfterTableSpace" style:family="paragraph">
   <style:paragraph-properties fo:margin-bottom="3mm"/>
  </style:style>
 </office:automatic-styles>

 <office:body>
  <office:text>
   {body_xml}
  </office:text>
 </office:body>
</office:document-content>"""

    with zipfile.ZipFile(odt_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", "application/vnd.oasis.opendocument.text", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/manifest.xml", manifest_xml)
        zf.writestr("meta.xml", meta_xml)
        zf.writestr("styles.xml", styles_xml)
        zf.writestr("content.xml", content_xml)
        zf.write(FRONT_COVER_PATH, "Pictures/capa_frente.png")
        zf.write(BACK_COVER_PATH, "Pictures/contracapa.png")


def main():
    with open(MD_PATH, "r", encoding="utf-8") as f:
        md_text = f.read()

    body_xml = parse_md_to_odt_body(md_text)
    create_odt(body_xml, ODT_PATH)
    print(f"Arquivo ODT criado com sucesso: {ODT_PATH}")

    tmp_odt = "/tmp/book_export.odt"
    tmp_pdf = "/tmp/book_export.pdf"
    tmp_prof = "/tmp/lo_p_export"

    shutil.copyfile(ODT_PATH, tmp_odt)
    shutil.rmtree(tmp_prof, ignore_errors=True)
    if os.path.exists(tmp_pdf):
        os.remove(tmp_pdf)

    cmd = [
        "/usr/sbin/soffice",
        f"-env:UserInstallation=file://{tmp_prof}",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        "/tmp",
        tmp_odt,
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, cwd="/tmp")
    if res.returncode != 0 or not os.path.exists(tmp_pdf):
        print("Erro no LibreOffice:", res.stdout, res.stderr)
        raise SystemExit(1)

    shutil.copyfile(tmp_pdf, PDF_PATH)
    print(f"PDF exportado com sucesso: {PDF_PATH} ({os.path.getsize(PDF_PATH)} bytes)")


if __name__ == "__main__":
    main()
