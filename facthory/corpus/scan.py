"""Scan a directory of OOXML files: producer (docProps/app.xml), size, sha256, features.

Usage: python3 -I scan.py ROOT [PREFIX] > out.jsonl
Reads zip members without extracting; caps every member read at 40 MB.
"""
import hashlib
import json
import os
import re
import sys
import zipfile

CAP = 40 * 1024 * 1024
EXT = {
    ".docx": "docx", ".docm": "docx", ".dotx": "docx", ".dotm": "docx",
    ".xlsx": "xlsx", ".xlsm": "xlsx", ".xltx": "xlsx", ".xltm": "xlsx",
    ".pptx": "pptx", ".pptm": "pptx", ".potx": "pptx", ".ppsx": "pptx", ".ppsm": "pptx", ".potm": "pptx",
}
CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿가-힯]")
RTL_CHARS = re.compile(r"[֐-ࣿיִ-﷿ﹰ-﻿]")


def read(z, name):
    try:
        info = z.getinfo(name)
    except KeyError:
        return ""
    if info.file_size > CAP:
        return ""
    with z.open(info) as f:
        return f.read(CAP).decode("utf-8", "replace")


def tag(xml, t):
    m = re.search(r"<(?:\w+:)?%s>([^<]*)</(?:\w+:)?%s>" % (t, t), xml)
    return m.group(1).strip() if m else ""


def text_of(xml):
    return " ".join(re.findall(r"<(?:a|w):t(?: [^>]*)?>([^<]*)<", xml)) or " ".join(re.findall(r"<t(?: [^>]*)?>([^<]*)<", xml))


def features_docx(z, names):
    f = set()
    doc = read(z, "word/document.xml")
    if not doc:
        main = [n for n in names if re.match(r"word/document\d*\.xml$", n)]
        doc = read(z, main[0]) if main else ""
    allxml = doc
    if "<w:tbl>" in doc or "<w:tbl " in doc:
        f.add("tables")
    if any(n.startswith("word/media/") for n in names):
        f.add("images")
    if any(n.startswith("word/charts/") for n in names):
        f.add("charts")
    if any(n.startswith("word/diagrams/") for n in names):
        f.add("smartart")
    if re.search(r"<w:(ins|del) ", doc):
        f.add("tracked-changes")
    if re.search(r"<w:(rPrChange|pPrChange)", doc):
        f.add("tracked-formatting")
    if "word/comments.xml" in names:
        f.add("comments")
    fn = read(z, "word/footnotes.xml")
    if fn.count("<w:footnote ") > 2:
        f.add("footnotes")
    if read(z, "word/endnotes.xml").count("<w:endnote ") > 2:
        f.add("endnotes")
    if any(re.match(r"word/header\d*\.xml", n) for n in names):
        f.add("headers-footers")
    if "word/numbering.xml" in names:
        f.add("lists")
    if "<m:oMath" in doc:
        f.add("equations")
    if "<w:sdt>" in doc or "<w:sdt " in doc:
        f.add("content-controls")
    if "w:txbxContent" in doc:
        f.add("text-boxes")
    if "<wps:wsp" in doc or "<v:shape" in doc:
        f.add("shapes")
    if re.search(r"TOC \\\\", doc) or " TOC " in doc:
        f.add("toc")
    if "<w:fldChar" in doc or "<w:fldSimple" in doc:
        f.add("fields")
    if doc.count("<w:sectPr") > 1:
        f.add("multi-section")
    if "<w:cols " in doc and re.search(r'<w:cols [^>]*w:num="[2-9]', doc):
        f.add("columns")
    if "<w:bidi/>" in doc or "<w:rtl/>" in doc or "<w:bidi " in doc:
        f.add("rtl")
    t = text_of(doc)
    if CJK.search(t):
        f.add("cjk")
    if RTL_CHARS.search(t):
        f.add("rtl-script")
    if any(n.startswith("word/embeddings/") for n in names):
        f.add("ole")
    if "word/glossary/document.xml" in names:
        f.add("glossary")
    if any(n.startswith("word/fonts/") for n in names):
        f.add("embedded-fonts")
    if "vbaProject.bin" in " ".join(names):
        f.add("macros")
    styles = read(z, "word/styles.xml")
    f.add("styles:%d" % styles.count("<w:style "))
    f.add("paras:%d" % (doc.count("<w:p>") + doc.count("<w:p ")))
    return f, allxml


def features_xlsx(z, names):
    f = set()
    sheets = [n for n in names if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]
    f.add("sheets:%d" % len(sheets))
    formulas = 0
    for s in sheets[:50]:
        x = read(z, s)
        formulas += x.count("<f>") + x.count("<f ")
        if "<conditionalFormatting" in x:
            f.add("conditional-formatting")
        if "<dataValidation" in x:
            f.add("data-validation")
        if "<mergeCell " in x:
            f.add("merged-cells")
        if "sparklineGroup" in x:
            f.add("sparklines")
        if 'rightToLeft="1"' in x:
            f.add("rtl")
        if 't="array"' in x:
            f.add("array-formulas")
        if "<pane " in x:
            f.add("freeze-panes")
        if "<autoFilter" in x:
            f.add("autofilter")
        if "<outlinePr" in x or "outlineLevel=" in x:
            f.add("outline")
        if "<x14:dataBar" in x or "<dataBar" in x:
            f.add("data-bars")
        if "<iconSet" in x:
            f.add("icon-sets")
        if "<colorScale" in x:
            f.add("color-scales")
    if formulas:
        f.add("formulas:%d" % formulas)
    if any(n.startswith("xl/charts/chart") for n in names):
        f.add("charts")
    if any(n.startswith("xl/charts/chartEx") or "chartEx" in n for n in names):
        f.add("chartex")
    if any(n.startswith("xl/pivotTables/") for n in names):
        f.add("pivot-tables")
    if any(n.startswith("xl/tables/") for n in names):
        f.add("tables")
    if any(n.startswith("xl/media/") for n in names):
        f.add("images")
    if any(n.startswith("xl/comments") for n in names):
        f.add("comments")
    if any(n.startswith("xl/threadedComments/") for n in names):
        f.add("threaded-comments")
    if any(n.startswith("xl/externalLinks/") for n in names):
        f.add("external-links")
    if any(n.startswith("xl/slicers/") or n.startswith("xl/slicerCaches/") for n in names):
        f.add("slicers")
    if "xl/vbaProject.bin" in names:
        f.add("macros")
    if any(n.startswith("xl/drawings/") for n in names):
        f.add("drawings")
    if "xl/metadata.xml" in names:
        f.add("dynamic-arrays")
    if any(n.startswith("xl/chartsheets/") for n in names):
        f.add("chartsheets")
    wb = read(z, "xl/workbook.xml")
    if "<definedName " in wb:
        f.add("defined-names")
    ss = read(z, "xl/sharedStrings.xml")
    if CJK.search(ss):
        f.add("cjk")
    if RTL_CHARS.search(ss):
        f.add("rtl-script")
    st = read(z, "xl/styles.xml")
    if "<numFmt " in st:
        f.add("custom-numfmts")
    return f, wb


def features_pptx(z, names):
    f = set()
    slides = [n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)]
    f.add("slides:%d" % len(slides))
    f.add("masters:%d" % len([n for n in names if re.match(r"ppt/slideMasters/slideMaster\d+\.xml$", n)]))
    f.add("layouts:%d" % len([n for n in names if re.match(r"ppt/slideLayouts/slideLayout\d+\.xml$", n)]))
    alltext = ""
    for s in slides[:200]:
        x = read(z, s)
        alltext += text_of(x) + " "
        if "<p:timing" in x:
            f.add("animations")
        if "<p:transition" in x or "<mc:AlternateContent" in x and "transition" in x:
            f.add("transitions")
        if "<a:tbl>" in x:
            f.add("tables")
        if "<a:graphicData uri=\"http://schemas.openxmlformats.org/drawingml/2006/chart\"" in x:
            f.add("charts")
        if "<p:grpSp>" in x:
            f.add("groups")
        if 'rtl="1"' in x:
            f.add("rtl")
        if "<p:cxnSp" in x:
            f.add("connectors")
        if "<a:custGeom" in x:
            f.add("freeforms")
        if "<p:oleObj" in x:
            f.add("ole")
    if any(n.startswith("ppt/charts/") for n in names):
        f.add("charts")
    if any(n.startswith("ppt/diagrams/") for n in names):
        f.add("smartart")
    if any(n.startswith("ppt/media/") and re.search(r"\.(png|jpe?g|gif|emf|wmf|svg|tiff?|bmp)$", n, re.I) for n in names):
        f.add("images")
    if any(n.startswith("ppt/media/") and re.search(r"\.(emf|wmf)$", n, re.I) for n in names):
        f.add("emf-wmf")
    if any(n.startswith("ppt/media/") and re.search(r"\.svg$", n, re.I) for n in names):
        f.add("svg")
    if any(n.startswith("ppt/media/") and re.search(r"\.(mp4|m4v|mov|wmv|avi|mp3|wav|m4a|wma)$", n, re.I) for n in names):
        f.add("media")
    if any(n.startswith("ppt/notesSlides/") for n in names):
        f.add("notes")
    if any(n.startswith("ppt/comments/") for n in names):
        f.add("comments")
    if any(n.startswith("ppt/fonts/") for n in names):
        f.add("embedded-fonts")
    if any(n.startswith("ppt/embeddings/") for n in names):
        f.add("embeddings")
    if "ppt/vbaProject.bin" in names:
        f.add("macros")
    pres = read(z, "ppt/presentation.xml")
    if "sectionLst" in pres:
        f.add("sections")
    if CJK.search(alltext):
        f.add("cjk")
    if RTL_CHARS.search(alltext):
        f.add("rtl-script")
    return f, pres


def ms_markers(z, names, kind):
    """Traces the Office apps write and libraries rarely do (app.xml alone is copied through by libraries)."""
    if kind == "docx":
        s = read(z, "word/settings.xml")
        return "<w:rsids>" in s or "<w:rsidRoot" in s
    if kind == "xlsx":
        wb = read(z, "xl/workbook.xml")
        return bool(re.search(r'<fileVersion [^>]*appName="xl"[^>]*rupBuild="', wb))
    pres = read(z, "ppt/presentation.xml")
    slides = [n for n in names if re.match(r"ppt/slides/slide\d+\.xml$", n)][:5]
    if any("p14:creationId" in read(z, s) for s in slides):
        return True
    return "<p14:" in pres or "<p15:" in pres


def scan(path, rel):
    ext = os.path.splitext(path)[1].lower()
    kind = EXT.get(ext)
    rec = {"path": rel, "kind": kind, "size": os.path.getsize(path)}
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    rec["sha256"] = h.hexdigest()
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            app = read(z, "docProps/app.xml")
            rec["app"] = tag(app, "Application")
            rec["appver"] = tag(app, "AppVersion")
            ct = read(z, "[Content_Types].xml")
            rec["strict"] = "purl.oclc.org/ooxml" in (read(z, "word/document.xml")[:2000] + read(z, "xl/workbook.xml")[:2000] + read(z, "ppt/presentation.xml")[:2000])
            fn = {"docx": features_docx, "xlsx": features_xlsx, "pptx": features_pptx}[kind]
            feats, _ = fn(z, names)
            rec["features"] = sorted(feats)
            rec["ms_markers"] = ms_markers(z, names, kind)
            rec["encrypted"] = False
    except zipfile.BadZipFile:
        with open(path, "rb") as fh:
            head = fh.read(8)
        rec["encrypted"] = head.startswith(b"\xd0\xcf\x11\xe0")
        rec["error"] = "not-zip" + (" (CFB: encrypted or legacy)" if rec["encrypted"] else "")
    except Exception as e:  # noqa: BLE001 - report and continue
        rec["error"] = "%s: %s" % (type(e).__name__, e)
    return rec


def main():
    root = sys.argv[1]
    prefix = sys.argv[2] if len(sys.argv) > 2 else ""
    for d, _, files in os.walk(root):
        if "/.git" in d:
            continue
        for name in sorted(files):
            if os.path.splitext(name)[1].lower() in EXT:
                p = os.path.join(d, name)
                if os.path.islink(p):
                    continue
                print(json.dumps(scan(p, prefix + os.path.relpath(p, root)), ensure_ascii=False))


if __name__ == "__main__":
    main()
