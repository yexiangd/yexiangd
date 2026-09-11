"""Keep only the 3D contribution graph in profile-3d-contrib SVGs.

The github-profile-3d-contrib action renders the 3D isometric graph plus
side panels (radar chart, language pie, star/fork counts). This strips
everything except the 3D bars group and crops the viewBox to it.
"""
import glob
import re
import xml.etree.ElementTree as ET

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

def bbox_of(el, tx=0.0, ty=0.0):
    minx, miny = float("inf"), float("inf")
    maxx, maxy = float("-inf"), float("-inf")
    t = el.get("transform", "")
    m = re.search(r"translate\(\s*([\d.\-]+)[,\s]+([\d.\-]+)\s*\)", t)
    if m:
        tx += float(m.group(1))
        ty += float(m.group(2))
    if el.tag == f"{{{SVG_NS}}}rect":
        x = float(el.get("x", 0)); y = float(el.get("y", 0))
        w = float(el.get("width", 0)); h = float(el.get("height", 0))
        minx, miny = min(minx, tx + x), min(miny, ty + y)
        maxx, maxy = max(maxx, tx + x + w), max(maxy, ty + y + h)
    for c in el:
        cminx, cminy, cmaxx, cmaxy = bbox_of(c, tx, ty)
        minx, miny = min(minx, cminx), min(miny, cminy)
        maxx, maxy = max(maxx, cmaxx), max(maxy, cmaxy)
    return minx, miny, maxx, maxy

for path in sorted(glob.glob("profile-3d-contrib/*.svg")):
    tree = ET.parse(path)
    root = tree.getroot()
    groups = [c for c in root if c.tag == f"{{{SVG_NS}}}g"]
    if len(groups) < 2:
        print(f"{path}: unexpected structure, skipped")
        continue
    # The 3D bars group is by far the largest; drop the side panels.
    keep = max(groups, key=lambda g: len(ET.tostring(g)))
    for g in groups:
        if g is not keep:
            root.remove(g)
    minx, miny, maxx, maxy = bbox_of(keep)
    pad = 12
    vx, vy = int(minx - pad), int(miny - pad)
    vw, vh = int((maxx - minx) + pad * 2), int((maxy - miny) + pad * 2)
    root.set("viewBox", f"{vx} {vy} {vw} {vh}")
    root.set("width", str(vw))
    root.set("height", str(vh))
    tree.write(path, encoding="unicode", xml_declaration=False)
    # restore original one-line-ish header style is unnecessary; keep ET output
    print(f"{path}: kept 3D graph, viewBox={vx} {vy} {vw} {vh}")
