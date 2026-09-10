import re, glob
for p in sorted(glob.glob('dist/*.svg')):
    svg = open(p).read()
    svg, n = re.subn(r'<rect[^>]*class="u[^"]*"[^>]*>', '', svg)
    svg = re.sub(r'viewBox="[^"]*"', 'viewBox="-16 -24 880 143"', svg, count=1)
    svg = re.sub(r'height="192"', 'height="143"', svg, count=1)
    open(p, 'w').write(svg)
    print(p, 'removed u-rects:', n)
