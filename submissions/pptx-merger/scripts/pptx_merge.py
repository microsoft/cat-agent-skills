#!/usr/bin/env python3
"""
pptx_merge.py — Merge PPTX files without PowerPoint repair/open errors.

Usage:
    python pptx_merge.py output.pptx input1.pptx input2.pptx [input3.pptx ...]

Relationship handling
---------------------
Relationship IDs (`r:id`, `r:embed`, `r:link`, ...) are *part-local*: a slide,
master or layout resolves them against its own `_rels/<part>.rels` and nothing
else in the package sees them. Appended parts therefore KEEP their original
relationship IDs verbatim, which means the copied XML stays valid without any
rewriting. Only `ppt/_rels/presentation.xml.rels` gets fresh IDs, because that
part's ID space is genuinely shared between the destination deck and everything
appended into it.

What *does* get rewritten is the `Target` of each relationship, since part
names are package-global and get renamed on copy (`image1.png` ->
`s1_image1.png`, `slideLayout2.xml` -> `slideLayout9.xml`, and so on). Targets
are remapped in every `.rels` we emit — slides, masters, layouts, themes,
charts and notes — so renamed media, themes and charts stay reachable from
appended masters and layouts.

Note that `sldMasterId/@id` and `sldLayoutId/@id` are a different thing from
`r:id`: they are globally unique unsigned integers (>= 2147483648) and ARE
renumbered from a shared counter.

Also handled here:

  * [Content_Types].xml and every .rels part are serialised in the DEFAULT
    (unprefixed) OPC namespace. A prefixed `<ns0:Types>` makes PowerPoint and
    LibreOffice refuse to open the package ("can't read" / "source could not be
    loaded"). Rebuilding with nsmap={None: NS} guarantees the required form and
    also self-heals inputs that arrive prefixed.

  * Zip entry paths are validated before extraction (Zip Slip).
"""

import os
import re
import sys
import shutil
import tempfile
import zipfile
from pathlib import Path

try:
    from lxml import etree
except ImportError:
    sys.exit("ERROR: lxml is required. Install it with: pip install lxml")

# ── Namespaces ──────────────────────────────────────────────────────────────
NS_P   = "http://schemas.openxmlformats.org/presentationml/2006/main"
NS_R   = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_REL = "http://schemas.openxmlformats.org/package/2006/relationships"
NS_CT  = "http://schemas.openxmlformats.org/package/2006/content-types"

RT_SLIDE        = f"{NS_R}/slide"
RT_SLIDE_LAYOUT = f"{NS_R}/slideLayout"
RT_SLIDE_MASTER = f"{NS_R}/slideMaster"
RT_THEME        = f"{NS_R}/theme"
RT_IMAGE        = f"{NS_R}/image"
RT_CHART        = f"{NS_R}/chart"
RT_NOTES        = f"{NS_R}/notesSlide"
RT_AUDIO        = f"{NS_R}/audio"
RT_VIDEO        = f"{NS_R}/video"
RT_MEDIA        = "http://schemas.microsoft.com/office/2007/relationships/media"

MEDIA_RELS = {RT_IMAGE, RT_AUDIO, RT_VIDEO, RT_MEDIA}

CT_SLIDE        = "application/vnd.openxmlformats-officedocument.presentationml.slide+xml"
CT_SLIDE_LAYOUT = "application/vnd.openxmlformats-officedocument.presentationml.slideLayout+xml"
CT_SLIDE_MASTER = "application/vnd.openxmlformats-officedocument.presentationml.slideMaster+xml"
CT_THEME        = "application/vnd.openxmlformats-officedocument.theme+xml"
CT_CHART        = "application/vnd.openxmlformats-officedocument.drawingml.chart+xml"
CT_NOTES_SLIDE  = "application/vnd.openxmlformats-officedocument.presentationml.notesSlide+xml"

MEDIA_CT = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg", "gif": "image/gif",
    "bmp": "image/bmp", "tiff": "image/tiff", "wmf": "image/x-wmf", "emf": "image/x-emf",
    "svg": "image/svg+xml", "mp4": "video/mp4", "avi": "video/avi", "mov": "video/quicktime",
    "mp3": "audio/mpeg", "wav": "audio/wav", "m4v": "video/mp4", "bin": None,
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


# ── XML helpers ─────────────────────────────────────────────────────────────
def _parser():
    return etree.XMLParser(
        remove_blank_text=False,
        recover=True,
        resolve_entities=False,
        load_dtd=False,
        no_network=True,
    )


def parse_xml(path: Path):
    return etree.parse(str(path), _parser()).getroot()


def write_xml(root, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    etree.ElementTree(root).write(
        str(path), xml_declaration=True, encoding="UTF-8", standalone=True
    )


def read_rels(rels_path: Path):
    if not rels_path.exists():
        return []
    root = parse_xml(rels_path)
    return [
        {"Id": r.get("Id", ""), "Type": r.get("Type", ""),
         "Target": r.get("Target", ""), "TargetMode": r.get("TargetMode", "")}
        for r in root
    ]


def build_rels_xml(rels):
    # DEFAULT namespace — no prefix.
    root = etree.Element(f"{{{NS_REL}}}Relationships", nsmap={None: NS_REL})
    for r in rels:
        el = etree.SubElement(root, f"{{{NS_REL}}}Relationship")
        el.set("Id", r["Id"])
        el.set("Type", r["Type"])
        el.set("Target", r["Target"])
        if r.get("TargetMode"):
            el.set("TargetMode", r["TargetMode"])
    return root


def next_rid(used: set) -> str:
    n = 1
    while f"rId{n}" in used:
        n += 1
    return f"rId{n}"


def abs_to_rel(target: str, part_folder: str) -> str:
    if not target.startswith("/"):
        return target
    rel = os.path.relpath(target.lstrip("/"), part_folder)
    return rel.replace("\\", "/")


# ── Merger ──────────────────────────────────────────────────────────────────
class PptxMerger:
    def __init__(self, tmp: Path):
        self.tmp = tmp
        self.out = tmp / "out"
        # Single global ID space shared by sldMasterId and sldLayoutId
        # (PowerPoint requires these to be globally unique together).
        self._gid_counter = 2147483648

    # ── target remapping ────────────────────────────────────────────────
    @staticmethod
    def remap_rel(r, part_folder, media_map=None, chart_map=None, theme_map=None,
                  overrides=None):
        """Return a copy of relationship `r` with its Target rewritten for the
        merged package.

        The relationship Id is deliberately left untouched: rel IDs are
        part-local, so preserving them keeps every r:id / r:embed / r:link
        reference in the copied XML valid with no rewriting of the part itself.

        `overrides` maps a relationship Type to a fixed replacement Target and
        wins over the name-based maps.
        """
        nr = dict(r)                                  # Id preserved verbatim
        if nr.get("TargetMode", "") == "External":
            return nr

        target = nr.get("Target", "")
        if target.startswith("/"):
            target = abs_to_rel(target, part_folder)
            nr["Target"] = target

        rtype = r.get("Type", "")
        if overrides and rtype in overrides:
            nr["Target"] = overrides[rtype]
            return nr

        name = Path(target).name
        if theme_map and rtype == RT_THEME and name in theme_map:
            nr["Target"] = f"../theme/{theme_map[name]}"
        elif chart_map and rtype == RT_CHART and name in chart_map:
            nr["Target"] = f"../charts/{chart_map[name]}"
        elif media_map and (rtype in MEDIA_RELS or "/media/" in target):
            if name in media_map:
                nr["Target"] = f"../media/{media_map[name]}"
        return nr

    def remap_rels(self, rels, part_folder, **kw):
        return [self.remap_rel(r, part_folder, **kw) for r in rels]

    # ── main ────────────────────────────────────────────────────────────
    def merge(self, inputs, output: Path):
        srcs = []
        for i, inp in enumerate(inputs):
            d = self.tmp / f"s{i}"
            d.mkdir(parents=True, exist_ok=True)
            base = d.resolve()
            with zipfile.ZipFile(inp) as z:
                for info in z.infolist():
                    dest = (d / info.filename).resolve()
                    if not str(dest).startswith(str(base) + os.sep):
                        sys.exit(f"Unsafe path in PPTX zip entry: {info.filename}")
                z.extractall(d)
            srcs.append(d)

        shutil.copytree(srcs[0], self.out, dirs_exist_ok=True)
        self._fix_base_rels()
        self._sync_id_counters(self.out)

        prs_path      = self.out / "ppt" / "presentation.xml"
        prs_rels_path = self.out / "ppt" / "_rels" / "presentation.xml.rels"
        prs_root      = parse_xml(prs_path)
        prs_rels      = read_rels(prs_rels_path)

        sld_id_lst = prs_root.find(f".//{{{NS_P}}}sldIdLst")
        if sld_id_lst is None:
            sld_id_lst = etree.SubElement(prs_root, f"{{{NS_P}}}sldIdLst")

        max_sld_id = max((int(el.get("id", 0)) for el in sld_id_lst), default=255)
        slide_num, layout_num, master_num, theme_num = self._count_parts(self.out)
        notes_num = self._count_notes(self.out)
        prs_rid_set = {r["Id"] for r in prs_rels}

        for src_idx, src in enumerate(srcs[1:], start=1):
            media_map = self._copy_media(src, src_idx)
            chart_map = self._copy_charts_and_deps(src, src_idx)
            theme_map = self._copy_themes(src, theme_num, media_map)
            theme_num += len(theme_map)

            master_map, layout_map = self._copy_masters_and_layouts(
                src, master_num, layout_num, theme_map, media_map, chart_map
            )
            master_num += len(master_map)
            layout_num += len(layout_map)

            master_id_lst = prs_root.find(f".//{{{NS_P}}}sldMasterIdLst")
            if master_id_lst is None:
                # Must precede sldIdLst per schema; insert at position 0.
                master_id_lst = etree.Element(f"{{{NS_P}}}sldMasterIdLst")
                prs_root.insert(0, master_id_lst)

            for _, new_master_fname in master_map.items():
                # presentation.xml.rels IS a shared ID space -> new Id here.
                new_rid = next_rid(prs_rid_set)
                prs_rid_set.add(new_rid)
                prs_rels.append({
                    "Id": new_rid, "Type": RT_SLIDE_MASTER,
                    "Target": f"slideMasters/{new_master_fname}", "TargetMode": "",
                })
                el = etree.SubElement(master_id_lst, f"{{{NS_P}}}sldMasterId")
                self._gid_counter += 1
                el.set("id", str(self._gid_counter))   # required, globally unique
                el.set(f"{{{NS_R}}}id", new_rid)

            old_to_new_slides = {}
            for slide_fname in self._ordered_slides(src):
                src_slide = src / "ppt" / "slides" / slide_fname
                if not src_slide.exists():
                    continue

                slide_num += 1
                new_slide_fname = f"slide{slide_num}.xml"
                old_to_new_slides[slide_fname] = new_slide_fname

                out_slide = self.out / "ppt" / "slides" / new_slide_fname
                out_slide.parent.mkdir(parents=True, exist_ok=True)
                # Copied byte-for-byte: rel IDs are preserved, so every r:id /
                # r:embed / r:link inside still resolves.
                shutil.copy2(src_slide, out_slide)

                src_rels = src / "ppt" / "slides" / "_rels" / f"{slide_fname}.rels"
                new_slide_rels = self.remap_rels(
                    read_rels(src_rels), "ppt/slides",
                    media_map=media_map, chart_map=chart_map,
                    overrides=None,
                )
                new_slide_rels = [
                    self._remap_layout_target(r, layout_map) for r in new_slide_rels
                ]

                out_rels_dir = self.out / "ppt" / "slides" / "_rels"
                out_rels_dir.mkdir(parents=True, exist_ok=True)
                write_xml(build_rels_xml(new_slide_rels),
                          out_rels_dir / f"{new_slide_fname}.rels")

                max_sld_id += 1
                new_prs_rid = next_rid(prs_rid_set)
                prs_rid_set.add(new_prs_rid)
                sld_el = etree.SubElement(sld_id_lst, f"{{{NS_P}}}sldId")
                sld_el.set("id", str(max_sld_id))
                sld_el.set(f"{{{NS_R}}}id", new_prs_rid)
                prs_rels.append({
                    "Id": new_prs_rid, "Type": RT_SLIDE,
                    "Target": f"slides/{new_slide_fname}", "TargetMode": "",
                })

            notes_num = self._copy_notes(src, old_to_new_slides, notes_num, media_map)

        write_xml(prs_root, prs_path)
        write_xml(build_rels_xml(prs_rels), prs_rels_path)
        self._rebuild_content_types()

        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as zout:
            # [Content_Types].xml first is conventional and harmless.
            ct = self.out / "[Content_Types].xml"
            if ct.exists():
                zout.write(ct, "[Content_Types].xml")
            for f in sorted(self.out.rglob("*")):
                if f.is_file() and f.name != "[Content_Types].xml":
                    zout.write(f, f.relative_to(self.out))

        print(f"OK  merged {len(inputs)} files -> {output}")

    # ── helpers ─────────────────────────────────────────────────────────
    @staticmethod
    def _remap_layout_target(r, layout_map):
        if r.get("Type") != RT_SLIDE_LAYOUT or r.get("TargetMode") == "External":
            return r
        name = Path(r.get("Target", "")).name
        if name in layout_map:
            nr = dict(r)
            nr["Target"] = f"../slideLayouts/{layout_map[name]}"
            return nr
        return r

    def _count_parts(self, base: Path):
        ppt = base / "ppt"
        n = lambda g: sum(1 for _ in ppt.glob(g))
        return (n("slides/slide[0-9]*.xml"), n("slideLayouts/slideLayout[0-9]*.xml"),
                n("slideMasters/slideMaster[0-9]*.xml"), n("theme/theme[0-9]*.xml"))

    def _count_notes(self, base: Path):
        d = base / "ppt" / "notesSlides"
        return sum(1 for _ in d.glob("notesSlide[0-9]*.xml")) if d.exists() else 0

    def _sync_id_counters(self, base: Path):
        ns = {"p": NS_P}
        prs = base / "ppt" / "presentation.xml"
        if prs.exists():
            root = parse_xml(prs)
            ml = root.find(".//p:sldMasterIdLst", ns)
            if ml is not None:
                for el in ml:
                    try:
                        self._gid_counter = max(self._gid_counter, int(el.get("id", 0)))
                    except ValueError:
                        pass
        md = base / "ppt" / "slideMasters"
        if md.exists():
            for mf in md.glob("slideMaster*.xml"):
                root = parse_xml(mf)
                ll = root.find(".//p:sldLayoutIdLst", ns)
                if ll is not None:
                    for el in ll:
                        try:
                            self._gid_counter = max(self._gid_counter, int(el.get("id", 0)))
                        except ValueError:
                            pass

    def _fix_base_rels(self):
        for rels_path in sorted(self.out.rglob("*.rels")):
            root = parse_xml(rels_path)
            changed = False
            try:
                part_folder = str(rels_path.parent.parent.relative_to(self.out)).replace("\\", "/")
            except ValueError:
                part_folder = "."
            for rel in root:
                t = rel.get("Target", "")
                if t.startswith("/") and rel.get("TargetMode", "") != "External":
                    rel.set("Target", abs_to_rel(t, part_folder))
                    changed = True
            if changed:
                write_xml(root, rels_path)

    def _ordered_slides(self, src: Path):
        prs_root = parse_xml(src / "ppt" / "presentation.xml")
        prs_rels = read_rels(src / "ppt" / "_rels" / "presentation.xml.rels")
        rid_to_slide = {r["Id"]: Path(r["Target"]).name
                        for r in prs_rels if r["Type"] == RT_SLIDE}
        lst = prs_root.find(f".//{{{NS_P}}}sldIdLst")
        if lst is None:
            return []
        return [rid_to_slide[el.get(f"{{{NS_R}}}id")] for el in lst
                if el.get(f"{{{NS_R}}}id") in rid_to_slide]

    def _copy_media(self, src: Path, src_idx: int):
        sm = src / "ppt" / "media"
        if not sm.exists():
            return {}
        om = self.out / "ppt" / "media"
        om.mkdir(parents=True, exist_ok=True)
        mp = {}
        for f in sorted(sm.iterdir()):
            if f.is_file():
                new = f"s{src_idx}_{f.name}"
                shutil.copy2(f, om / new)
                mp[f.name] = new
        return mp

    def _copy_charts_and_deps(self, src: Path, src_idx: int):
        sc = src / "ppt" / "charts"
        se = src / "ppt" / "embeddings"
        oc = self.out / "ppt" / "charts"
        oe = self.out / "ppt" / "embeddings"
        chart_map, embed_map = {}, {}
        if se.exists():
            oe.mkdir(parents=True, exist_ok=True)
            for f in sorted(se.iterdir()):
                if f.is_file():
                    new = f"s{src_idx}_{f.name}"
                    shutil.copy2(f, oe / new)
                    embed_map[f.name] = new
        if not sc.exists():
            return chart_map
        oc.mkdir(parents=True, exist_ok=True)
        for f in sorted(sc.glob("chart*.xml")):
            new = f"s{src_idx}_{f.name}"
            shutil.copy2(f, oc / new)
            chart_map[f.name] = new
            ncr = []
            for r in read_rels(sc / "_rels" / f"{f.name}.rels"):
                nr = dict(r)                       # Id preserved
                if nr.get("TargetMode", "") != "External":
                    oldn = Path(r.get("Target", "")).name
                    if oldn in embed_map:
                        nr["Target"] = f"../embeddings/{embed_map[oldn]}"
                ncr.append(nr)
            (oc / "_rels").mkdir(exist_ok=True)
            write_xml(build_rels_xml(ncr), oc / "_rels" / f"{new}.rels")
        return chart_map

    def _copy_themes(self, src: Path, theme_start: int, media_map):
        sd = src / "ppt" / "theme"
        od = self.out / "ppt" / "theme"
        od.mkdir(parents=True, exist_ok=True)
        tm = {}
        if not sd.exists():
            return tm
        n = theme_start + 1
        for f in sorted(sd.glob("theme*.xml")):
            new = f"theme{n}.xml"
            shutil.copy2(f, od / new)
            tm[f.name] = new
            sr = sd / "_rels" / f"{f.name}.rels"
            if sr.exists():
                # Themes can reference media (background fills); remap targets
                # while preserving Ids so the theme XML's r:embed still resolves.
                (od / "_rels").mkdir(exist_ok=True)
                write_xml(
                    build_rels_xml(self.remap_rels(read_rels(sr), "ppt/theme",
                                                   media_map=media_map)),
                    od / "_rels" / f"{new}.rels",
                )
            n += 1
        return tm

    def _copy_masters_and_layouts(self, src, master_start, layout_start,
                                  theme_map, media_map, chart_map=None):
        chart_map = chart_map or {}
        sm = src / "ppt" / "slideMasters"
        sl = src / "ppt" / "slideLayouts"
        om = self.out / "ppt" / "slideMasters"
        ol = self.out / "ppt" / "slideLayouts"
        om.mkdir(parents=True, exist_ok=True)
        ol.mkdir(parents=True, exist_ok=True)
        master_map, layout_map = {}, {}
        if not sm.exists():
            return master_map, layout_map

        m_num = master_start + 1
        l_num = layout_start + 1

        for smf in sorted(sm.glob("slideMaster*.xml")):
            new_master = f"slideMaster{m_num}.xml"
            master_map[smf.name] = new_master

            this_layouts, new_mrels = {}, []
            for r in read_rels(sm / "_rels" / f"{smf.name}.rels"):
                if r["Type"] == RT_SLIDE_LAYOUT and r.get("TargetMode") != "External":
                    old_l = Path(r["Target"]).name
                    new_l = layout_map.get(old_l)
                    if new_l is None:
                        new_l = f"slideLayout{l_num}.xml"
                        l_num += 1
                        layout_map[old_l] = new_l
                    this_layouts[old_l] = new_l
                    nr = dict(r)                    # Id preserved
                    nr["Target"] = f"../slideLayouts/{new_l}"
                    new_mrels.append(nr)
                else:
                    new_mrels.append(self.remap_rel(
                        r, "ppt/slideMasters",
                        media_map=media_map, chart_map=chart_map, theme_map=theme_map,
                    ))

            # Copied byte-for-byte. No string surgery on the XML is needed: rel
            # IDs are preserved so r:id/r:embed still resolve, and media paths
            # never appear in master XML (only in its .rels).
            shutil.copy2(smf, om / new_master)

            mxml = parse_xml(om / new_master)
            lst = mxml.find(f".//{{{NS_P}}}sldLayoutIdLst")
            if lst is not None:
                for el in lst:
                    # @id is the globally unique int and IS renumbered.
                    # @r:id is the part-local rel ref and is left alone.
                    self._gid_counter += 1
                    el.set("id", str(self._gid_counter))
            write_xml(mxml, om / new_master)

            (om / "_rels").mkdir(exist_ok=True)
            write_xml(build_rels_xml(new_mrels), om / "_rels" / f"{new_master}.rels")

            for old_l, new_l in this_layouts.items():
                slf = sl / old_l
                if not slf.exists():
                    continue
                shutil.copy2(slf, ol / new_l)
                nlr = self.remap_rels(
                    read_rels(sl / "_rels" / f"{old_l}.rels"), "ppt/slideLayouts",
                    media_map=media_map, chart_map=chart_map, theme_map=theme_map,
                    overrides={RT_SLIDE_MASTER: f"../slideMasters/{new_master}"},
                )
                (ol / "_rels").mkdir(exist_ok=True)
                write_xml(build_rels_xml(nlr), ol / "_rels" / f"{new_l}.rels")

            m_num += 1
        return master_map, layout_map

    def _copy_notes(self, src, old_to_new, notes_start, media_map=None):
        sn = src / "ppt" / "notesSlides"
        if not sn.exists():
            return notes_start
        on = self.out / "ppt" / "notesSlides"
        on.mkdir(parents=True, exist_ok=True)
        (on / "_rels").mkdir(exist_ok=True)
        ssr = src / "ppt" / "slides" / "_rels"
        slide_to_notes = {}
        if ssr.exists():
            for rf in ssr.glob("slide*.xml.rels"):
                for r in read_rels(rf):
                    if r["Type"] == RT_NOTES:
                        slide_to_notes[rf.stem] = Path(r["Target"]).name
                        break
        n = notes_start
        for old_slide, new_slide in old_to_new.items():
            nf = slide_to_notes.get(old_slide)
            if not nf:
                continue
            snp = sn / nf
            if not snp.exists():
                continue
            n += 1
            new_nf = f"notesSlide{n}.xml"
            shutil.copy2(snp, on / new_nf)
            nnr = self.remap_rels(
                read_rels(sn / "_rels" / f"{nf}.rels"), "ppt/notesSlides",
                media_map=media_map,
                overrides={RT_SLIDE: f"../slides/{new_slide}"},
            )
            write_xml(build_rels_xml(nnr), on / "_rels" / f"{new_nf}.rels")

            osr = self.out / "ppt" / "slides" / "_rels" / f"{new_slide}.rels"
            if osr.exists():
                srels = read_rels(osr)
                updated = False
                for r in srels:
                    if r["Type"] == RT_NOTES:
                        r["Target"] = f"../notesSlides/{new_nf}"
                        updated = True
                if not updated:
                    rs = {r["Id"] for r in srels}
                    srels.append({"Id": next_rid(rs), "Type": RT_NOTES,
                                  "Target": f"../notesSlides/{new_nf}", "TargetMode": ""})
                write_xml(build_rels_xml(srels), osr)
        return n

    def _rebuild_content_types(self):
        ct_path = self.out / "[Content_Types].xml"
        existing = parse_xml(ct_path) if ct_path.exists() else None

        # DEFAULT namespace, rebuilt fresh so no prefix can leak.
        root = etree.Element(f"{{{NS_CT}}}Types", nsmap={None: NS_CT})

        known_defaults = set()
        if existing is not None:
            for d in existing.findall(f"{{{NS_CT}}}Default"):
                ext = d.get("Extension", "").lower()
                if ext and ext not in known_defaults:
                    el = etree.SubElement(root, f"{{{NS_CT}}}Default")
                    el.set("Extension", d.get("Extension"))
                    el.set("ContentType", d.get("ContentType"))
                    known_defaults.add(ext)

        regen = {CT_SLIDE, CT_SLIDE_LAYOUT, CT_SLIDE_MASTER, CT_THEME, CT_CHART, CT_NOTES_SLIDE}
        if existing is not None:
            for ov in existing.findall(f"{{{NS_CT}}}Override"):
                if ov.get("ContentType") not in regen:
                    el = etree.SubElement(root, f"{{{NS_CT}}}Override")
                    el.set("PartName", ov.get("PartName"))
                    el.set("ContentType", ov.get("ContentType"))

        def add(glob_pat, prefix, ctype):
            base = self.out / "ppt"
            for f in sorted(base.glob(glob_pat)):
                el = etree.SubElement(root, f"{{{NS_CT}}}Override")
                el.set("PartName", f"/ppt/{prefix}/{f.name}")
                el.set("ContentType", ctype)

        add("slides/slide[0-9]*.xml", "slides", CT_SLIDE)
        add("slideLayouts/slideLayout[0-9]*.xml", "slideLayouts", CT_SLIDE_LAYOUT)
        add("slideMasters/slideMaster[0-9]*.xml", "slideMasters", CT_SLIDE_MASTER)
        add("theme/theme[0-9]*.xml", "theme", CT_THEME)
        add("notesSlides/notesSlide[0-9]*.xml", "notesSlides", CT_NOTES_SLIDE)

        cdir = self.out / "ppt" / "charts"
        if cdir.exists():
            for f in sorted(cdir.glob("*.xml")):
                if re.match(r"^(s\d+_)?chart\d+\.xml$", f.name):
                    el = etree.SubElement(root, f"{{{NS_CT}}}Override")
                    el.set("PartName", f"/ppt/charts/{f.name}")
                    el.set("ContentType", CT_CHART)

        mdir = self.out / "ppt" / "media"
        if mdir.exists():
            for f in sorted(mdir.iterdir()):
                ext = f.suffix.lower().lstrip(".")
                if ext and ext not in known_defaults and MEDIA_CT.get(ext):
                    el = etree.SubElement(root, f"{{{NS_CT}}}Default")
                    el.set("Extension", ext)
                    el.set("ContentType", MEDIA_CT[ext])
                    known_defaults.add(ext)

        write_xml(root, ct_path)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    output = Path(sys.argv[1])
    inputs = [Path(p) for p in sys.argv[2:]]
    missing = [str(p) for p in inputs if not p.exists()]
    if missing:
        sys.exit(f"Files not found: {', '.join(missing)}")
    tmp = Path(tempfile.mkdtemp(prefix="pptx_merge_"))
    try:
        PptxMerger(tmp).merge(inputs, output)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
