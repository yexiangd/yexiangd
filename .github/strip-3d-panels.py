"""Trim profile-3d-contrib SVGs: keep 3D graph + radar chart + totals.

The github-profile-3d-contrib action renders the 3D isometric graph plus
side panels (radar chart, language pie, star/fork counts). We keep the 3D
bars, the radar chart (contribution breakdown), the total-contributions
text and the date range; the language pie and star/fork counts go.
"""
import glob
import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)
G = "{%s}g" % SVG_NS

def num(v, d=0.0):
    m = re.match(r"-?[\d.]+", str(v))
    return float(m.group(0)) if m else d

def texts_of(el):
    return "".join(el.itertext()).strip()

def bbox_of(el, tx=0.0, ty=0.0):
    minx, miny = float("inf"), float("inf")
    maxx, maxy = float("-inf"), float("-inf")
    t = el.get("transform", "")
    m = re.search(r"translate\(\s*([\d.\-]+)[,\s]+([\d.\-]+)\s*\)", t)
    if m:
        tx += float(m.group(1)); ty += float(m.group(2))
    tag = el.tag.replace("{%s}" % SVG_NS, "")
    if tag == "text":
        anchor = el.get("text-anchor", "start")
        x, y = num(el.get("x")), num(el.get("y"))
        fs = num(el.get("font-size", 12)); txt = texts_of(el)
        w = len(txt) * fs * 0.6
        x0 = x - w if anchor == "end" else (x - w / 2 if anchor == "middle" else x)
        minx, miny = min(minx, tx + x0), min(miny, ty + y - fs)
        maxx, maxy = max(maxx, tx + x0 + w), max(maxy, ty + y)
    elif tag == "rect":
        x, y, w, h = num(el.get("x")), num(el.get("y")), num(el.get("width")), num(el.get("height"))
        minx, miny = min(minx, tx + x), min(miny, ty + y)
        maxx, maxy = max(maxx, tx + x + w), max(maxy, ty + y + h)
    elif tag in ("polygon", "circle", "ellipse"):
        nums = [float(n) for n in re.findall(r"-?\d+\.?\d*", el.get("points", ""))]
        xs, ys = nums[0::2], nums[1::2]
        if tag == "circle":
            cx, cy, r = num(el.get("cx")), num(el.get("cy")), num(el.get("r"))
            xs, ys = [cx - r, cx + r], [cy - r, cy + r]
        if xs:
            minx, miny = min(minx, tx + min(xs)), min(miny, ty + min(ys))
            maxx, maxy = max(maxx, tx + max(xs)), max(maxy, ty + max(ys))
    for c in el:
        a, b, c_, d_ = bbox_of(c, tx, ty)
        minx, miny = min(minx, a), min(miny, b)
        maxx, maxy = max(maxx, c_), max(maxy, d_)
    return minx, miny, maxx, maxy

for path in sorted(glob.glob("profile-3d-contrib/*.svg")):
    tree = ET.parse(path)
    root = tree.getroot()
    groups = [c for c in root if c.tag == G]
    if len(groups) < 2:
        print(f"{path}: unexpected structure, skipped"); continue
    # 3D bars = largest group; radar = group mentioning Commit; pie = mentions C++.
    g3d = max(groups, key=lambda g: len(ET.tostring(g)))
    all_text = {g: " ".join(texts_of(t) for t in g.iter() if t.tag == "{%s}text" % SVG_NS) for g in groups}
    gradar = next((g for g in groups if "Commit" in all_text[g]), None)
    gpie = next((g for g in groups if "C++" in all_text[g]), None)
    gstats = next((g for g in groups if "contributions" in all_text[g]), None)
    keep = {g3d}
    if gradar is not None: keep.add(gradar)
    for g in groups:
        if g not in keep and g is not gstats:
            root.remove(g)
    # stats group: drop star/fork icons (paths) and their counts; keep
    # the total-contributions text and the date range.
    if gstats is not None and gstats in root:
        contrib_x = None
        for t in gstats.iter():
            if t.tag == "{%s}text" % SVG_NS and "contributions" in texts_of(t):
                contrib_x = num(t.get("x")); break
        for desc in list(gstats.iter()):
            dtag = desc.tag.replace("{%s}" % SVG_NS, "")
            if dtag in ("g", "path"):
                has_path = any(c.tag == "{%s}path" % SVG_NS for c in desc.iter())
                has_text = any(c.tag == "{%s}text" % SVG_NS for c in desc.iter())
                if has_path and not has_text and desc is not gstats:
                    # icon group (e.g. star/fork): detach from its parent
                    for parent in gstats.iter():
                        if desc in list(parent):
                            parent.remove(desc); break
        for child in list(gstats):
            tag = child.tag.replace("{%s}" % SVG_NS, "")
            if tag == "path":
                gstats.remove(child); continue
            if tag == "text":
                txt = texts_of(child)
                if "contributions" in txt or "/" in txt:
                    continue
                if contrib_x is not None and num(child.get("x")) <= contrib_x + 1:
                    continue  # the "617" count left of "contributions"
                gstats.remove(child)
        keep.add(gstats)
    # crop to remaining content
    minx = miny = float("inf"); maxx = maxy = float("-inf")
    for g in keep:
        a, b, c_, d_ = bbox_of(g)
        minx, miny = min(minx, a), min(miny, b)
        maxx, maxy = max(maxx, c_), max(maxy, d_)
    pad = 14
    vx, vy = max(0, int(minx - pad)), max(0, int(miny - pad))
    vw, vh = int(maxx - minx + pad * 2), int(maxy - miny + pad * 2)
    root.set("viewBox", f"{vx} {vy} {vw} {vh}")
    root.set("width", str(vw)); root.set("height", str(vh))
    tree.write(path, encoding="unicode", xml_declaration=False)
    print(f"{path}: kept 3D+radar+totals, viewBox={vx} {vy} {vw} {vh}")
