"""Regression tests: python -m unittest discover -s submissions/pptx-template-applier/scripts/tests."""
import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE
from pptx.enum.dml import MSO_THEME_COLOR
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.opc.constants import CONTENT_TYPE as CT, RELATIONSHIP_TYPE as RT
from pptx.opc.packuri import PackURI
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.parts.slide import SlideLayoutPart, SlideMasterPart
from pptx.util import Inches, Pt

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from apply_template import (Report, _title_runs, add_picture, build, build_slide, copy_shape,
                            rebuild_chart, rebuild_table, remap_connections,
                            text_height_pt, write_paragraphs)
from deck_model import paragraphs_of, read_slide
from deck_qa import lint, render
from inspect_decks import inspect_template
from plan_mapping import layout_table, plan, resolve_override
from make_samples import png_bytes
from pptx_common import A, P, R, picture_bounds, theme_colors, theme_fonts
from restyle import restyle

C = "{http://schemas.openxmlformats.org/drawingml/2006/chart}"
FLOORS = {"title": 24, "body": 14, "table": 10}


def roundtrip(prs):
    data = io.BytesIO()
    prs.save(data)
    data.seek(0)
    return Presentation(data)


def chart_shape(slide, kind=XL_CHART_TYPE.PIE):
    data = CategoryChartData()
    data.categories = ["North", "South"]
    data.add_series("Visits", [3, 7])
    return slide.shapes.add_chart(kind, Inches(1), Inches(1), Inches(5), Inches(4), data)


def add_second_master(prs):
    master_xml = copy.deepcopy(prs.slide_master._element)
    master_xml.find(f"{P}sldLayoutIdLst").clear()
    package = prs.part.package
    mp = SlideMasterPart.load(PackURI("/ppt/slideMasters/slideMaster2.xml"),
                              CT.PML_SLIDE_MASTER, package, etree.tostring(master_xml))
    layout_xml = copy.deepcopy(prs.slide_layouts[1]._element)
    layout_xml.find(f"{P}cSld").set("name", "Second master content")
    lp = SlideLayoutPart.load(PackURI("/ppt/slideLayouts/slideLayout12.xml"),
                              CT.PML_SLIDE_LAYOUT, package, etree.tostring(layout_xml))
    lp.relate_to(mp, RT.SLIDE_MASTER)
    rid = mp.relate_to(lp, RT.SLIDE_LAYOUT)
    etree.SubElement(mp._element.find(f"{P}sldLayoutIdLst"), f"{P}sldLayoutId",
                     {"id": "2147483649", f"{R}id": rid})
    theme = prs.slide_master.part.part_related_by(RT.THEME)
    cloned_theme = type(theme).load(PackURI("/ppt/theme/theme2.xml"), theme.content_type, package, theme.blob)
    mp.relate_to(cloned_theme, RT.THEME)
    rid = prs.part.relate_to(mp, RT.SLIDE_MASTER)
    etree.SubElement(prs._element.find(f"{P}sldMasterIdLst"), f"{P}sldMasterId",
                     {"id": "2147483649", f"{R}id": rid})
    return prs.slide_masters[1]


class TemplateRegressions(unittest.TestCase):
    def setUp(self):
        self.src = Presentation()
        self.slide = self.src.slides.add_slide(self.src.slide_layouts[1])
        self.slide.shapes.title.text = "Source title"
        self.dst = Presentation()
        self.report = Report()

    def build_slide(self, split=False, layout=1):
        model = read_slide(self.slide, 1, self.src.slide_width, self.src.slide_height)
        return build_slide(self.dst, model, {"slide": 1, "target_layout_index": layout},
                           self.slide, {}, 0.5, FLOORS, split, self.report, 1)

    def test_runs_breaks_and_field_display_text_survive_body_and_title(self):
        tf = self.slide.placeholders[1].text_frame
        tf.clear()
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = "Before"
        r.font.bold = True
        r.hyperlink.address = "https://example.com"
        p.add_line_break()
        field = parse_xml('<a:fld ' + nsdecls("a") +
                          ' id="{00000000-0000-0000-0000-000000000001}" type="slidenum">'
                          '<a:rPr i="1"/><a:t>42</a:t></a:fld>')
        p._p.append(field)
        p.add_run().text = "After"
        model = paragraphs_of(tf)
        self.assertEqual("".join(r["text"] for r in model[0]["runs"]), "Before\v42After")
        self.assertTrue(model[0]["runs"][2]["italic"])
        self.assertGreater(text_height_pt(model, 500, [18], 0.5),
                           text_height_pt([{"runs": [{"text": "Before42After"}]}], 500, [18], 0.5))
        target = self.dst.slides.add_slide(self.dst.slide_layouts[1])
        write_paragraphs(target.placeholders[1].text_frame, model)
        write_paragraphs(target.shapes.title.text_frame,
                         [{"runs": _title_runs({"title_shape": self.slide.placeholders[1]})}])
        saved = roundtrip(self.dst).slides[0]
        self.assertEqual(saved.placeholders[1].text_frame.text, "Before\v42After")
        self.assertEqual(saved.shapes.title.text, "Before\v42After")
        self.assertEqual(saved.placeholders[1].text_frame.paragraphs[0].runs[0].hyperlink.address,
                         "https://example.com")

    def test_free_shapes_use_single_unused_body_placeholder(self):
        for x in (1, 4):
            self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(2), Inches(1), Inches(1))
        result = self.build_slide()[0]
        self.assertEqual(len(result.shapes), 3)
        saved = roundtrip(self.dst).slides[0]
        body = self.dst.slide_layouts[1].placeholders[1]
        for shape in list(saved.shapes)[1:]:
            self.assertGreaterEqual(shape.left, body.left)
            self.assertLessEqual(shape.left + shape.width, body.left + body.width)

    def test_single_chart_build_uses_content_area(self):
        chart_shape(self.slide)
        result = self.build_slide()[0]
        self.assertEqual(len(result.shapes), 2)
        self.assertTrue(result.shapes[-1].has_chart)

    def test_connector_targets_rebuilt_body_placeholder(self):
        self.slide.placeholders[1].text = "Body"
        connector = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 100, 100)
        connector.begin_connect(self.slide.placeholders[1], 0)
        result = self.build_slide()[0]
        self.assertEqual(result._element.find(f".//{A}stCxn").get("id"),
                         str(result.placeholders[1].shape_id))
        self.assertFalse(any("detached" in w["detail"] for w in self.report.warnings))

    def test_extra_picture_keeps_its_position_beside_body_text(self):
        body = self.slide.placeholders[1]
        body.text = "Bullets beside a photo"
        body.left, body.top, body.width, body.height = Inches(0.5), Inches(2), Inches(4), Inches(3)
        self.slide.shapes.add_picture(io.BytesIO(png_bytes(120, 60, "Photo")),
                                     Inches(5), Inches(2), Inches(3), Inches(1.5))
        self.build_slide()
        saved = roundtrip(self.dst).slides[0]
        body, picture = saved.placeholders[1], saved.shapes[-1]
        self.assertLess(body.left + body.width, picture.left)
        area = self.dst.slide_layouts[1].placeholders[1]
        self.assertGreaterEqual(body.left, area.left)
        self.assertLessEqual(picture.left + picture.width, area.left + area.width)

    def test_extra_shape_keeps_its_position_below_body_text(self):
        body = self.slide.placeholders[1]
        body.text = "Text above a shape"
        body.left, body.top, body.width, body.height = Inches(1), Inches(2), Inches(5), Inches(1)
        self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(4), Inches(5), Inches(1))
        self.build_slide()
        saved = roundtrip(self.dst).slides[0]
        self.assertLess(saved.placeholders[1].top + saved.placeholders[1].height, saved.shapes[-1].top)

    def test_picture_rotation_flips_and_transformed_bounds_survive(self):
        source = self.slide.shapes.add_picture(io.BytesIO(png_bytes(120, 60, "Photo")), 0, 0,
                                              Inches(4), Inches(2))
        source.crop_left = 0.1
        xfrm = source._element.spPr.xfrm
        xfrm.set("flipH", "1")
        xfrm.set("flipV", "1")
        area = (Inches(1), Inches(2), Inches(3), Inches(2))
        for angle in (30, 90, 270):
            with self.subTest(angle=angle):
                source.rotation = angle
                dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
                add_picture(source, dest, area)
                pic = roundtrip(self.dst).slides[-1].shapes[0]
                self.assertEqual(pic.rotation, angle)
                self.assertEqual(pic._element.spPr.xfrm.get("flipH"), "1")
                self.assertEqual(pic._element.spPr.xfrm.get("flipV"), "1")
                self.assertAlmostEqual(pic.crop_left, 0.1)
                left, top, width, height = picture_bounds(pic)
                self.assertGreaterEqual(left, area[0] - 2)
                self.assertGreaterEqual(top, area[1] - 2)
                self.assertLessEqual(left + width, area[0] + area[2] + 2)
                self.assertLessEqual(top + height, area[1] + area[3] + 2)

    def test_picture_links_survive_placeholder_and_free_picture_paths(self):
        self.slide = self.src.slides.add_slide(self.src.slide_layouts[8])
        self.slide.shapes.title.text = "Linked photo"
        self.slide.placeholders[2].text = "Caption"
        picture = self.slide.placeholders[1].insert_picture(io.BytesIO(png_bytes(120, 60, "Photo")))
        nv = picture._element.find(f"{P}nvPicPr/{P}cNvPr")
        for tag in ("hlinkClick", "hlinkHover"):
            rid = picture.part.relate_to(f"https://example.com/{tag}", RT.HYPERLINK, is_external=True)
            etree.SubElement(nv, f"{A}{tag}", {f"{R}id": rid, "tooltip": tag})
        for layout in (1, 8):
            with self.subTest(layout=layout):
                self.dst = Presentation()
                self.build_slide(layout=layout)
                saved = roundtrip(self.dst).slides[0]
                pic = next(s for s in saved.shapes if hasattr(s, "image"))
                for tag in ("hlinkClick", "hlinkHover"):
                    link = pic._element.find(f"{P}nvPicPr/{P}cNvPr/{A}{tag}")
                    self.assertIsNotNone(link)
                    self.assertEqual(link.get("tooltip"), tag)
                    rel = saved.part.rels[link.get(f"{R}id")]
                    self.assertTrue(rel.is_external)
                    self.assertEqual(rel.target_ref, f"https://example.com/{tag}")

    def test_lint_uses_rotated_picture_bounds_at_slide_edge(self):
        source = self.slide.shapes.add_picture(io.BytesIO(png_bytes(120, 30, "Photo")), 0, 0,
                                              Inches(4), Inches(1))
        source.rotation = 90
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        add_picture(source, dest, (0, 0, Inches(1), Inches(4)))
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "rotated.pptx"
            self.dst.save(path)
            _, findings = lint(str(path), require_notes=False)
        self.assertFalse(any(f["check"] == "off_slide" for f in findings))

    def test_promoted_title_retains_hyperlinks_and_connector_target(self):
        self.slide = self.src.slides.add_slide(self.src.slide_layouts[6])
        title = self.slide.shapes.add_textbox(Inches(1), Inches(0.1), Inches(7), Inches(1))
        run = title.text_frame.paragraphs[0].add_run()
        run.text, run.font.size = "Linked title", Pt(32)
        run.hyperlink.address = "https://example.com/title"
        shape = self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(3), Inches(2), Inches(1))
        connector = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 100, 100)
        connector.begin_connect(title, 0)
        connector.end_connect(shape, 1)
        model = read_slide(self.slide, 1, self.src.slide_width, self.src.slide_height)
        self.assertEqual(model["title_shape"].shape_id, title.shape_id)
        self.build_slide()
        saved = roundtrip(self.dst).slides[0]
        self.assertEqual(saved.shapes.title.text_frame.paragraphs[0].runs[0].hyperlink.address,
                         "https://example.com/title")
        self.assertEqual(saved._element.find(f".//{A}stCxn").get("id"), str(saved.shapes.title.shape_id))
        self.assertFalse(any("detached" in w["detail"] for w in self.report.warnings))

    def test_paragraph_numbering_and_bullet_suppression_survive(self):
        tf = self.slide.placeholders[1].text_frame
        tf.text = "Step three\nNo bullet\nNested roman"
        etree.SubElement(tf.paragraphs[0]._p.get_or_add_pPr(), f"{A}buAutoNum",
                         type="arabicPeriod", startAt="3")
        etree.SubElement(tf.paragraphs[1]._p.get_or_add_pPr(), f"{A}buNone")
        tf.paragraphs[2].level = 1
        style = tf._txBody.find(f"{A}lstStyle")
        props = etree.SubElement(style, f"{A}lvl2pPr")
        etree.SubElement(props, f"{A}buAutoNum", type="romanLcParenR", startAt="4")
        self.build_slide()
        saved = roundtrip(self.dst).slides[0].placeholders[1].text_frame.paragraphs
        auto = saved[0]._p.find(f"{A}pPr/{A}buAutoNum")
        self.assertEqual(dict(auto.attrib), {"type": "arabicPeriod", "startAt": "3"})
        self.assertIsNotNone(saved[1]._p.find(f"{A}pPr/{A}buNone"))
        inherited = saved[2]._p.find(f"{A}pPr/{A}buAutoNum")
        self.assertEqual(dict(inherited.attrib), {"type": "romanLcParenR", "startAt": "4"})

    def test_bullet_suppression_inherited_from_source_layout_survives(self):
        self.slide.placeholders[1].text = "Unbulleted source layout"
        style = self.src.slide_layouts[1].placeholders[1].text_frame._txBody.find(f"{A}lstStyle")
        props = etree.SubElement(style, f"{A}lvl1pPr")
        etree.SubElement(props, f"{A}buNone")
        self.build_slide()
        saved = roundtrip(self.dst).slides[0].placeholders[1].text_frame.paragraphs[0]
        self.assertIsNotNone(saved._p.find(f"{A}pPr/{A}buNone"))

    def test_group_descendants_and_cross_shape_connectors_get_new_ids(self):
        group = self.slide.shapes.add_group_shape()
        a = group.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(1), Inches(2), Inches(1), Inches(1))
        nested = group.shapes.add_group_shape()
        b = nested.shapes.add_shape(MSO_SHAPE.OVAL, Inches(3), Inches(2), Inches(1), Inches(1))
        connector = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 100, 100)
        connector.begin_connect(a, 0)
        connector.end_connect(b, 1)
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[1])
        dest.shapes.add_textbox(0, 0, 100, 100)
        ids = {}
        # Forward references must work even when the connector precedes its targets.
        for sh in (connector, group):
            copy_shape(sh, self.slide, dest, (0, 0, 1000000, 1000000), 1, {}, self.report, 1, ids)
        remap_connections(dest, ids, self.report, 1)
        saved = roundtrip(self.dst).slides[0]
        values = saved._element.xpath(".//p:cNvPr/@id")
        self.assertEqual(len(values), len(set(values)))
        self.assertEqual(saved._element.find(f".//{A}stCxn").get("id"), ids[str(a.shape_id)])
        self.assertEqual(saved._element.find(f".//{A}endCxn").get("id"), ids[str(b.shape_id)])
        self.assertFalse(self.report.warnings)

    def test_missing_connector_target_is_detached_and_reported(self):
        a = self.slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, 100, 100)
        connector = self.slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 100, 100)
        connector.begin_connect(a, 0)
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        copy_shape(connector, self.slide, dest, (0, 0, 100, 100), 1, {}, self.report, 1, {})
        remap_connections(dest, {}, self.report, 1)
        self.assertIsNone(dest._element.find(f".//{A}stCxn"))
        self.assertTrue(self.report.warnings)

    def test_chart_labels_keep_flags_formats_and_custom_text(self):
        source = chart_shape(self.slide)
        plot = source.chart.plots[0]
        plot.has_data_labels = True
        plot.data_labels.show_value = False
        plot.data_labels.show_percentage = True
        plot.data_labels.show_category_name = True
        plot.data_labels.number_format = "0.0%"
        plot.data_labels.number_format_is_linked = False
        labels = plot._element.find(f"{C}dLbls")
        label = parse_xml('<c:dLbl ' + nsdecls("c", "a") +
                          '><c:idx val="0"/><c:tx><c:rich><a:bodyPr/><a:lstStyle/><a:p>'
                          '<a:r><a:rPr b="1"/><a:t>Custom north</a:t></a:r></a:p></c:rich></c:tx>'
                          '<c:showVal val="0"/></c:dLbl>')
        labels.insert(0, label)
        series_labels = etree.Element(f"{C}dLbls")
        etree.SubElement(series_labels, f"{C}showSerName", val="1")
        source.chart.series[0]._element._insert_dLbls(series_labels)
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_chart(source, dest, (0, 0, Inches(5), Inches(4)), self.report, 1)
        saved = roundtrip(self.dst).slides[0].shapes[0].chart
        self.assertFalse(saved.plots[0].data_labels.show_value)
        self.assertTrue(saved.plots[0].data_labels.show_percentage)
        self.assertTrue(saved.plots[0].data_labels.show_category_name)
        self.assertEqual(saved.plots[0].data_labels.number_format, "0.0%")
        self.assertEqual(etree.tostring(saved.plots[0]._element.find(f"{C}dLbls")),
                         etree.tostring(rebuilt.chart.plots[0]._element.find(f"{C}dLbls")))
        self.assertEqual(saved.plots[0]._element.find(f".//{A}t").text, "Custom north")
        self.assertIsNotNone(saved.series[0]._element.find(f"{C}dLbls/{C}showSerName"))

    def test_workbook_linked_label_uses_cache_and_reports_limit(self):
        source = chart_shape(self.slide)
        source.chart.plots[0].has_data_labels = True
        labels = source.chart.plots[0]._element.find(f"{C}dLbls")
        labels.insert(0, parse_xml('<c:dLbl ' + nsdecls("c") +
                                  '><c:idx val="0"/><c:tx><c:strRef><c:f>Sheet1!$Z$1</c:f>'
                                  '<c:strCache><c:ptCount val="1"/><c:pt idx="0"><c:v>Special label</c:v>'
                                  '</c:pt></c:strCache></c:strRef></c:tx></c:dLbl>'))
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_chart(source, dest, (0, 0, Inches(5), Inches(4)), self.report, 1)
        self.assertIsNone(rebuilt.chart._chartSpace.find(f".//{C}dLbls//{C}strRef"))
        self.assertEqual(rebuilt.chart._chartSpace.find(f".//{C}dLbls//{A}t").text, "Special label")
        self.assertIn("cached", self.report.warnings[0]["detail"])

    def test_linked_label_number_format_follows_rebuilt_series(self):
        source = chart_shape(self.slide, XL_CHART_TYPE.COLUMN_CLUSTERED)
        source.chart.series[0]._element.find(f"{C}val/{C}numRef/{C}numCache/{C}formatCode").text = "0.00%"
        source.chart.plots[0].has_data_labels = True
        source.chart.plots[0].data_labels.number_format = "0.00%"
        source.chart.plots[0].data_labels.number_format_is_linked = True
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_chart(source, dest, (0, 0, Inches(5), Inches(4)), self.report, 1)
        fmt = rebuilt.chart.series[0]._element.find(f"{C}val/{C}numRef/{C}numCache/{C}formatCode")
        self.assertEqual(fmt.text, "0.00%")
        self.assertTrue(rebuilt.chart.plots[0].data_labels.number_format_is_linked)

    def test_label_without_cached_display_text_is_reported(self):
        source = chart_shape(self.slide)
        source.chart.plots[0].has_data_labels = True
        source.chart.plots[0]._element.find(f"{C}dLbls").insert(
            0, parse_xml('<c:dLbl ' + nsdecls("c") + '><c:idx val="0"/><c:tx>'
                         '<c:strRef><c:f>Sheet1!$Z$1</c:f></c:strRef></c:tx></c:dLbl>'))
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_chart(source, dest, (0, 0, Inches(5), Inches(4)), self.report, 1)
        self.assertIsNone(rebuilt.chart._chartSpace.find(f".//{C}dLbl/{C}tx"))
        self.assertIn("without cached text", self.report.warnings[0]["detail"])

    def test_chart_axes_retain_titles_and_explicit_number_formats(self):
        for kind in (XL_CHART_TYPE.COLUMN_CLUSTERED, XL_CHART_TYPE.LINE):
            with self.subTest(kind=kind):
                source = chart_shape(self.slide, kind).chart
                for axis, title, fmt in ((source.category_axis, "Year", "0"),
                                         (source.value_axis, "$ millions", "0.0%")):
                    axis.has_title = True
                    axis.axis_title.text_frame.text = title
                    axis.tick_labels.number_format = fmt
                    axis.tick_labels.number_format_is_linked = False
                dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
                rebuild_chart(self.slide.shapes[-1], dest, (0, 0, Inches(5), Inches(4)), self.report, 1)
                saved = roundtrip(self.dst).slides[-1].shapes[0].chart
                self.assertEqual(saved.category_axis.axis_title.text_frame.text, "Year")
                self.assertEqual(saved.value_axis.axis_title.text_frame.text, "$ millions")
                self.assertEqual(saved.value_axis.tick_labels.number_format, "0.0%")
                self.assertFalse(saved.value_axis.tick_labels.number_format_is_linked)
                self.assertEqual(saved.category_axis.tick_labels.number_format, "0")

    def test_multiline_table_rows_receive_required_height(self):
        source = self.slide.shapes.add_table(2, 1, 0, 0, Inches(3), Inches(1))
        source.table.cell(0, 0).text = "First\nSecond\vThird"
        source.table.cell(1, 0).text = "Short"
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_table(source, dest, (0, 0, Inches(3), Inches(3)), 10, self.report, 1, 0.5)
        saved = roundtrip(self.dst).slides[0].shapes[0]
        self.assertGreaterEqual(saved.table.rows[0].height, int((3 * 18 * 1.2 + 10) * 12700))
        self.assertGreater(saved.table.rows[0].height, saved.table.rows[1].height)
        self.assertEqual(rebuilt.height, sum(row.height for row in rebuilt.table.rows))
        self.assertFalse(self.report.overflow)

    def test_wrapped_table_reports_overflow_at_floor(self):
        source = self.slide.shapes.add_table(1, 1, 0, 0, Inches(1), Inches(1))
        source.table.cell(0, 0).text = "A very long wrapped cell " * 25
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_table(source, dest, (0, 0, Inches(1), Inches(0.5)), 10, self.report, 1, 0.5)
        self.assertTrue(self.report.overflow)
        self.assertGreater(rebuilt.height, Inches(0.5))
        self.assertEqual(rebuilt.table.cell(0, 0).text_frame.paragraphs[0].runs[0].font.size.pt, 10)

    def test_merged_table_cell_height_covers_span(self):
        source = self.slide.shapes.add_table(2, 2, 0, 0, Inches(4), Inches(1))
        source.table.cell(0, 0).merge(source.table.cell(1, 1))
        source.table.cell(0, 0).text = "One\nTwo\nThree\nFour"
        dest = self.dst.slides.add_slide(self.dst.slide_layouts[6])
        rebuilt = rebuild_table(source, dest, (0, 0, Inches(4), Inches(3)), 10, self.report, 1, 0.5)
        self.assertTrue(rebuilt.table.cell(0, 0).is_merge_origin)
        self.assertGreaterEqual(rebuilt.height, int((4 * 18 * 1.2 + 10) * 12700))

    def test_oversized_indivisible_chunk_keeps_overflow_warning(self):
        tf = self.slide.placeholders[1].text_frame
        write_paragraphs(tf, [{"level": 0, "runs": [{"text": "Short"}]},
                              {"level": 0, "runs": [{"text": "Huge parent"}]},
                              {"level": 1, "runs": [{"text": "Nested " * 3000}]}])
        result = self.build_slide(split=True)
        self.assertEqual(len(result), 1)
        self.assertEqual(len(self.report.overflow), 1)
        self.assertIn("Nested", result[0].placeholders[1].text)

    def test_fitting_chunks_still_create_continuations(self):
        write_paragraphs(self.slide.placeholders[1].text_frame,
                         [{"level": 0, "runs": [{"text": f"Bullet {i} " + "words " * 20}]} for i in range(12)])
        result = self.build_slide(split=True)
        self.assertGreater(len(result), 1)
        self.assertFalse(self.report.overflow)

    def test_restyle_strips_fonts_from_layout_master_and_chart(self):
        self.slide.placeholders[1].text = "Inherited body"
        layout = self.src.slide_layouts[1]
        layout.placeholders[1].text_frame.paragraphs[0].font.name = "Arial"
        self.src.slide_master.placeholders[1].text_frame.paragraphs[0].font.name = "Arial"
        chart = chart_shape(self.slide).chart
        chart.has_title = True
        chart.chart_title.text_frame.text = "Chart title"
        chart.chart_title.text_frame.paragraphs[0].runs[0].font.name = "Arial"
        with tempfile.TemporaryDirectory() as td:
            source, brand, out = [Path(td) / name for name in ("source.pptx", "brand.json", "out.pptx")]
            self.src.save(source)
            brand.write_text(json.dumps({"colors": theme_colors(self.src),
                                         "fonts": {"major": "Georgia", "minor": "Verdana"}}), encoding="utf-8")
            report = restyle(str(source), str(brand), str(out))
            saved = Presentation(out)
        roots = [saved.slide_master._element, saved.slide_layouts[1]._element,
                 saved.slides[0].shapes[-1].chart._chartSpace]
        for root in roots:
            self.assertFalse(root.xpath('.//a:rPr/a:latin[@typeface="Arial"] | '
                                        './/a:defRPr/a:latin[@typeface="Arial"]'))
        self.assertEqual(report["font_overrides_removed"], 3)
        self.assertEqual(theme_fonts(saved)["minor"], "Verdana")

    def test_second_master_layout_is_inspected_mapped_and_built(self):
        template = Presentation()
        add_second_master(template)
        first_master = template.slide_master
        blank = template.slide_layouts[6].part
        for item in list(first_master._element.find(f"{P}sldLayoutIdLst")):
            rid = item.get(f"{R}id")
            if first_master.part.related_part(rid) is not blank:
                first_master.part.drop_rel(rid)
                item.getparent().remove(item)
        self.slide.placeholders[1].text = "Second master body"
        with tempfile.TemporaryDirectory() as td:
            source, tpl, out = [Path(td) / name for name in ("source.pptx", "template.pptx", "out.pptx")]
            self.src.save(source)
            template.save(tpl)
            inspected = inspect_template(str(tpl))
            self.assertTrue(inspected["usable_layouts"])
            self.assertEqual(len(inspected["layouts"]), 2)
            mapping = plan(str(tpl), str(source), {})
            self.assertEqual(mapping["mode"], "rebuild")
            self.assertEqual(mapping["slides"][0]["target_master_index"], 1)
            self.assertEqual(mapping["slides"][0]["target_layout_index"], 0)
            override = resolve_override("1:0", layout_table(template))
            self.assertEqual(override["name"], "Second master content")
            self.assertEqual(resolve_override("1", layout_table(template)), override)
            build(mapping, str(out), "", FLOORS)
            saved = Presentation(out)
        self.assertEqual(saved.slides[0].slide_layout.name, "Second master content")
        self.assertIs(saved.slides[0].slide_layout.slide_master, saved.slide_masters[1])
        self.assertEqual(saved.slides[0].placeholders[1].text, "Second master body")


class MasterThemeRegressions(unittest.TestCase):
    def setUp(self):
        self.prs = Presentation()
        self.master = add_second_master(self.prs)
        theme = self.master.part.part_related_by(RT.THEME)
        root = etree.fromstring(theme.blob)
        root.find(f".//{A}minorFont/{A}latin").set("typeface", "Verdana")
        root.find(f".//{A}clrScheme/{A}accent1/{A}srgbClr").set("val", "FFFFFF")
        theme._blob = etree.tostring(root)
        self.master._element.find(f"{P}clrMap").set("tx1", "accent1")

    def test_lint_uses_actual_master_colors_map_and_font_metrics(self):
        for layout in (self.prs.slide_layouts[6], self.master.slide_layouts[0]):
            slide = self.prs.slides.add_slide(layout)
            for shape in list(slide.placeholders):
                shape._element.getparent().remove(shape._element)
            slide.background.fill.solid()
            slide.background.fill.fore_color.rgb = RGBColor(255, 255, 255)
            tb = slide.shapes.add_textbox(Inches(1), Inches(1), Pt(114.4), Pt(57.2))
            tb.text = "A" * 21
            tb.text_frame.paragraphs[0].runs[0].font.color.theme_color = MSO_THEME_COLOR.TEXT_1
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "themes.pptx"
            self.prs.save(path)
            _, findings = lint(str(path), require_notes=False)
        self.assertFalse(any(f["check"] in ("contrast", "overflow") and f["slide"] == 1 for f in findings))
        self.assertTrue(any(f["check"] == "contrast" and f["slide"] == 2 for f in findings))
        self.assertTrue(any(f["check"] == "overflow" and f["slide"] == 2 for f in findings))

    def test_build_fits_using_selected_masters_body_font(self):
        source = Presentation()
        slide = source.slides.add_slide(source.slide_layouts[1])
        slide.shapes.title.text = "Title"
        slide.placeholders[1].text = "A" * 21
        layout = self.master.slide_layouts[0]
        body = layout.placeholders[1]
        body.left, body.top, body.width, body.height = Inches(1), Inches(2), Pt(114.4), Pt(57.2)
        style = body.text_frame._txBody.find(f"{A}lstStyle")
        for node in list(style):
            style.remove(node)
        props = etree.SubElement(style, f"{A}lvl1pPr")
        etree.SubElement(props, f"{A}defRPr", sz="1800")
        with tempfile.TemporaryDirectory() as td:
            src, tpl, out = [Path(td) / name for name in ("source.pptx", "template.pptx", "out.pptx")]
            source.save(src)
            self.prs.save(tpl)
            mapping = plan(str(tpl), str(src), {"1": "1:0"})
            build(mapping, str(out), "", FLOORS)
            saved = Presentation(out)
        size = saved.slides[0].placeholders[1].text_frame.paragraphs[0].runs[0].font.size
        self.assertIsNotNone(size)
        self.assertEqual(size.pt, 16)


class PreviewRegressions(unittest.TestCase):
    def test_failed_conversion_cannot_reuse_old_pdf_or_images(self):
        for returncode, create_pdf in ((0, False), (1, False), (1, True)):
            with self.subTest(returncode=returncode, create_pdf=create_pdf), tempfile.TemporaryDirectory() as td:
                pdf = Path(td) / "deck.pdf"
                pdf.write_bytes(b"old PDF")
                for name in ("slide-01.png", "contact-1.png"):
                    (Path(td) / name).write_bytes(b"old preview")

                def convert(argv, **kwargs):
                    self.assertFalse(pdf.exists())
                    if create_pdf:
                        pdf.write_bytes(b"incomplete conversion")
                    return subprocess.CompletedProcess(argv, returncode, stdout="", stderr="conversion failed")

                with patch("deck_qa.shutil.which", side_effect=lambda name: name), \
                        patch("deck_qa.subprocess.run", side_effect=convert) as run:
                    result, error = render("deck.pptx", td, 60, 12)
                self.assertIsNone(result)
                self.assertIn("PDF conversion failed", error)
                self.assertEqual(run.call_count, 1)
                self.assertFalse(list(Path(td).glob("*.png")))


if __name__ == "__main__":
    unittest.main()
