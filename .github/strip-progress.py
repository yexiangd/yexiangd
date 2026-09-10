import re, glob, traceback, os
lines = []
lines.append("cwd=" + os.getcwd())
try:
    files = sorted(glob.glob('dist/*.svg'))
    lines.append("svg_files=" + (",".join(files) if files else "(none)"))
    total = 0
    for p in files:
        svg = open(p).read()
        before = len(re.findall('class="u', svg))
        svg, n = re.subn(r'<rect[^>]*class="u[^"]*"[^>]*>', '', svg)
        svg = re.sub(r'viewBox="[^"]*"', 'viewBox="-16 -24 880 143"', svg, count=1)
        svg = re.sub(r'height="192"', 'height="143"', svg, count=1)
        open(p, 'w').write(svg)
        after = len(re.findall('class="u', svg))
        total += n
        lines.append("%s: u_before=%d removed=%d u_after=%d" % (p, before, n, after))
    lines.append("TOTAL_REMOVED=%d" % total)
except Exception:
    lines.append("EXCEPTION:\n" + traceback.format_exc())
report = "\n".join(lines) + "\n"
try:
    os.makedirs('dist', exist_ok=True)
    open('dist/strip-report.txt', 'w').write(report)
except Exception as e:
    lines.append("REPORT_WRITE_FAILED: %r" % e)
    report = "\n".join(lines) + "\n"
print(report, flush=True)
