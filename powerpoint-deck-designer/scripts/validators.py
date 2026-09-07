"""Spec and rendered-deck validation."""

from __future__ import annotations


VALID_LAYOUTS = {"title", "section", "content", "two-column",
                 "cards", "agenda", "quote", "closing", "chart"}
VALID_CHART_TYPES = {"bar", "column", "line", "pie", "donut"}


def validate_spec(spec, theme):
    errors = []
    warnings = []

    slides = spec.get("slides")
    if not slides or not isinstance(slides, list):
        errors.append("spec.slides must be a non-empty list.")
        return {"errors": errors, "warnings": warnings}

    if not any(s.get("layout") == "title" for s in slides):
        warnings.append("No 'title' slide found. Consider adding one at the start.")

    for i, s in enumerate(slides, start=1):
        layout = s.get("layout", "content")
        if layout not in VALID_LAYOUTS:
            errors.append(f"Slide {i}: unknown layout '{layout}'. "
                          f"Valid: {sorted(VALID_LAYOUTS)}")
        if layout == "content":
            bullets = s.get("bullets", [])
            if len(bullets) > 6:
                warnings.append(f"Slide {i}: {len(bullets)} bullets exceeds "
                                "the recommended maximum of 6.")
            for j, b in enumerate(bullets, start=1):
                if len(b.split()) > 14:
                    warnings.append(f"Slide {i} bullet {j}: >14 words. "
                                    "Consider shortening.")
        if layout == "cards" and len(s.get("cards", [])) > 6:
            warnings.append(f"Slide {i}: {len(s['cards'])} cards exceeds "
                            "the recommended maximum of 6.")
        if layout == "two-column" and len(s.get("columns", [])) != 2:
            errors.append(f"Slide {i}: 'two-column' layout requires exactly 2 columns.")
        if layout == "agenda" and not s.get("items"):
            errors.append(f"Slide {i}: 'agenda' layout requires 'items'.")
        if layout == "quote" and not s.get("quote"):
            errors.append(f"Slide {i}: 'quote' layout requires a 'quote'.")

        if layout == "chart":
            chart = s.get("chart")
            if not isinstance(chart, dict):
                errors.append(f"Slide {i}: 'chart' layout requires a 'chart' object.")
                continue
            ctype = (chart.get("type") or "").lower()
            if ctype not in VALID_CHART_TYPES:
                errors.append(f"Slide {i}: chart.type must be one of "
                              f"{sorted(VALID_CHART_TYPES)}.")
            categories = chart.get("categories") or []
            series_list = chart.get("series") or []
            if not categories:
                errors.append(f"Slide {i}: chart.categories must be non-empty.")
            if not series_list:
                errors.append(f"Slide {i}: chart.series must be non-empty.")
            max_cats = 12 if ctype == "line" else 8
            if len(categories) > max_cats:
                warnings.append(f"Slide {i}: {len(categories)} categories may be "
                                f"too many for a {ctype} chart (recommended <= {max_cats}).")
            if ctype in {"pie", "donut"} and len(series_list) > 1:
                warnings.append(f"Slide {i}: {ctype} charts only display one "
                                "series; extras will be ignored.")
            stacked = chart.get("stacked", False)
            if stacked not in (False, True) and str(stacked).lower() not in {"100", "percent", "100%"}:
                errors.append(f"Slide {i}: chart.stacked must be false, true, "
                              "or '100'/'percent'.")
            if stacked and ctype in {"pie", "donut", "line"}:
                warnings.append(f"Slide {i}: 'stacked' is ignored for {ctype} charts.")
            for k, ser in enumerate(series_list, start=1):
                if not isinstance(ser, dict):
                    errors.append(f"Slide {i} series {k}: must be an object.")
                    continue
                if "name" not in ser:
                    warnings.append(f"Slide {i} series {k}: missing 'name'.")
                values = ser.get("values")
                if not isinstance(values, list) or not values:
                    errors.append(f"Slide {i} series {k}: 'values' must be a "
                                  "non-empty list of numbers.")
                    continue
                if categories and len(values) != len(categories):
                    warnings.append(f"Slide {i} series {k}: {len(values)} values "
                                    f"vs {len(categories)} categories; will be "
                                    "padded or truncated.")
                for v in values:
                    if not isinstance(v, (int, float)):
                        errors.append(f"Slide {i} series {k}: values must be numbers.")
                        break

    return {"errors": errors, "warnings": warnings}


def validate_rendered(prs, theme):
    warnings = []
    for i, slide in enumerate(prs.slides, start=1):
        text_shapes = [sh for sh in slide.shapes if sh.has_text_frame]
        if not text_shapes:
            warnings.append(f"Slide {i}: no text frames rendered.")
    return {"warnings": warnings}
