# Miniatury SVG parków z biblioteki: python3 web/parki/mini/miniatury.py <katalog repozytorium>
# (web/parki/*.geojson -> web/parki/mini/*.svg, tylko do galerii na stronie)
import json, math, os, sys
root = sys.argv[1]
src = os.path.join(root, "web/parki"); out = os.path.join(src, "mini"); os.makedirs(out, exist_ok=True)
def coords(g):
    t = g["type"]; c = g["coordinates"]
    if t == "LineString": return [c]
    if t == "MultiLineString": return c
    if t == "Polygon": return c
    if t == "MultiPolygon": return [r for p in c for r in p]
    return []
def simplify(pts, eps):
    if len(pts) < 3: return pts
    a, b = pts[0], pts[-1]; dx, dy = b[0]-a[0], b[1]-a[1]; n = math.hypot(dx, dy) or 1e-12
    i, dm = 0, -1
    for k in range(1, len(pts)-1):
        d = abs(dy*pts[k][0]-dx*pts[k][1]+b[0]*a[1]-b[1]*a[0])/n
        if d > dm: i, dm = k, d
    if dm > eps: return simplify(pts[:i+1], eps)[:-1] + simplify(pts[i:], eps)
    return [a, b]
for f in sorted(os.listdir(src)):
    if not f.endswith(".geojson"): continue
    d = json.load(open(os.path.join(src, f)))
    feats = d["features"]
    allp = [p for ft in feats for ring in coords(ft["geometry"]) for p in ring]
    lat0 = sum(p[1] for p in allp)/len(allp); kx = math.cos(math.radians(lat0))
    xs = [p[0]*kx for p in allp]; ys = [p[1] for p in allp]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    S = 100.0; pad = 4; sc = (S-2*pad)/max(x1-x0, y1-y0)
    ox = pad + ((S-2*pad) - (x1-x0)*sc)/2; oy = pad + ((S-2*pad) - (y1-y0)*sc)/2
    P = lambda p: (ox + (p[0]*kx-x0)*sc, S - (oy + (p[1]-y0)*sc))
    def path(rings, close):
        segs = []
        for r in rings:
            q = simplify([P(p) for p in r], 0.35)
            segs.append("M" + " L".join("%.1f %.1f" % xy for xy in q) + (" Z" if close else ""))
        return " ".join(segs)
    lay = lambda name: [ring for ft in feats if ft["properties"].get("layer") == name for ring in coords(ft["geometry"])]
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
           '<path d="%s" fill="#7fae6a" fill-opacity=".25" stroke="#5d8a4c" stroke-width=".6"/>'
           '<path d="%s" fill="#7fae6a" stroke="none"/>'
           '<path d="%s" fill="none" stroke="#3a3a36" stroke-width=".9" stroke-linecap="round" stroke-linejoin="round"/></svg>\n'
           % (path(lay("boundary"), True), path(lay("obstacles"), True), path(lay("roads"), False)))
    open(os.path.join(out, f.replace(".geojson", ".svg")), "w").write(svg)
    print(f, len(svg))
