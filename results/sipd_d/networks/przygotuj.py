"""Sieci parków wg wiadomości S z 02.10 10:13 (wątek SIPD-D).

- Szczytnicki: tylko część północna (dolna część z Halą Stulecia usunięta).
- Zachodni: dwie części (zachodnia i wschodnia), małe fragmenty na wschodzie usunięte.
- Ślepe odnogi wewnątrz parku zostają (bez przycinania).
- Sieć przycięta do obrysu; wejście = miejsce, w którym ścieżka przecina obrys (zawsze na obrysie).
  Ślepy koniec najwyżej SNAP_M od obrysu jest przedłużany do obrysu i też staje się wejściem.
- Wejścia bliżej siebie niż GATE_M (po obrysie) tworzą jedną bramę (do losowania miejsca pojawienia się).
- Obejście: ścieżka wzdłuż obrysu łącząca wszystkie wejścia (osobna warstwa "bypass").
Źródło: biblioteka web/parki z SIPD (= po_poprawkach, przed przycinaniem odnóg).
Wyjście: podzial/<park>.geojson (roads + obstacles + boundary + bypass + entrances, format web/parki;
warstwy bypass i entrances pomijane przez dotychczasowe wczytywanie), parki.csv, podglad.png."""
import json, math, os, csv

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.environ.get('PARKI_SRC', '/home/claude/sipd-wt/web/parki')
SNAP_M = 8.0
GATE_M = 20.0
# park wyjściowy -> {nowa nazwa: indeks wielokąta boundary}
PARTS = {
    'park_staszica': {'park_staszica': 0},
    'park_poludniowy': {'park_poludniowy': 0},
    'park_grabiszynski': {'park_grabiszynski': 0},
    'park_zachodni': {'park_zachodni_zach': 0, 'park_zachodni_wsch': 1},
    'park_szczytnicki': {'park_szczytnicki_pn': 2},
}


class Proj:
    def __init__(self, lon0, lat0):
        self.lon0, self.lat0 = lon0, lat0
        self.kx, self.ky = 111320.0 * math.cos(math.radians(lat0)), 110540.0

    def fwd(self, p):
        return ((p[0] - self.lon0) * self.kx, (p[1] - self.lat0) * self.ky)

    def inv(self, q):
        return [round(self.lon0 + q[0] / self.kx, 8), round(self.lat0 + q[1] / self.ky, 8)]


def inside(p, ring):
    x, y = p; ins = False; j = len(ring) - 1
    for i in range(len(ring)):
        (xi, yi), (xj, yj) = ring[i], ring[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            ins = not ins
        j = i
    return ins


def seg_x(a, b, c, d):
    """Parametr t na odcinku ab przecięcia z cd (lub None)."""
    rx, ry = b[0] - a[0], b[1] - a[1]; sx, sy = d[0] - c[0], d[1] - c[1]
    den = rx * sy - ry * sx
    if abs(den) < 1e-12:
        return None
    t = ((c[0] - a[0]) * sy - (c[1] - a[1]) * sx) / den
    u = ((c[0] - a[0]) * ry - (c[1] - a[1]) * rx) / den
    return t if 0 <= t <= 1 and 0 <= u <= 1 else None


def ring_pos(p, ring):
    """(odległość, pozycja po obwodzie, punkt rzutu) najbliższego punktu obrysu."""
    best, acc = None, 0.0
    for i in range(len(ring) - 1):
        a, b = ring[i], ring[i + 1]
        dx, dy = b[0] - a[0], b[1] - a[1]; L = math.hypot(dx, dy)
        t = 0.0 if L == 0 else max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / L ** 2))
        q = (a[0] + t * dx, a[1] + t * dy); d = math.dist(p, q)
        if best is None or d < best[0]:
            best = (d, acc + t * L, q)
        acc += L
    return best


def clip(line, ring):
    """Kawałki polilinii wewnątrz obrysu; zwraca listę (punkty, [indeksy końców na obrysie])."""
    pts = [line[0]]; on = set()
    for a, b in zip(line, line[1:]):
        ts = sorted(t for i in range(len(ring) - 1) for t in [seg_x(a, b, ring[i], ring[i + 1])] if t is not None and 1e-9 < t < 1 - 1e-9)
        for t in ts:
            pts.append((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]))); on.add(len(pts) - 1)
        pts.append(b)
    pieces, cur, cur_on = [], [pts[0]], []
    for i in range(1, len(pts)):
        cur.append(pts[i])
        if i in on or i == len(pts) - 1:
            mid = ((cur[0][0] + cur[1][0]) / 2, (cur[0][1] + cur[1][1]) / 2) if len(cur) > 1 else cur[0]
            if len(cur) > 1 and inside(mid, ring):
                pieces.append((cur, [k for k, idx in ((0, i - len(cur) + 1), (len(cur) - 1, i)) if idx in on]))
            cur = [pts[i]]
    return pieces


def key(p):
    return (round(p[0], 2), round(p[1], 2))


def build(src_park, name, idx):
    d = json.load(open(os.path.join(SRC, src_park + '.geojson')))
    lon0, lat0 = d['psm_processed']['origin']
    P = Proj(lon0, lat0)
    bnds = [f for f in d['features'] if f['properties'].get('layer') == 'boundary']
    ring = [P.fwd(c) for c in bnds[idx]['geometry']['coordinates'][0]]
    if ring[0] != ring[-1]:
        ring.append(ring[0])
    roads = [[P.fwd(c) for c in f['geometry']['coordinates']] for f in d['features'] if f['properties'].get('layer') == 'roads']
    L0 = sum(sum(math.dist(a, b) for a, b in zip(l, l[1:])) for l in roads)
    pieces, ents = [], []
    for l in roads:
        for pts, onb in clip(l, ring):
            pieces.append(pts)
            for k in onb:
                ents.append(pts[k])
    # ślepe końce przy obrysie -> przedłużenie do obrysu
    deg = {}
    for pts in pieces:
        for p in (pts[0], pts[-1]):
            deg[key(p)] = deg.get(key(p), 0) + 1
    ent_keys = {key(e) for e in ents}
    snapped = 0
    for pts in pieces:
        for end in (0, -1):
            p = pts[end]
            if deg[key(p)] == 1 and key(p) not in ent_keys:
                dist, s, q = ring_pos(p, ring)
                if dist <= SNAP_M:
                    if dist > 0.01:
                        if end == 0: pts.insert(0, q)
                        else: pts.append(q)
                    ents.append(q); ent_keys.add(key(q)); snapped += 1
    # tylko największa spójna składowa
    adj = {}
    for i, pts in enumerate(pieces):
        a, b = key(pts[0]), key(pts[-1])
        adj.setdefault(a, set()).add(b); adj.setdefault(b, set()).add(a)
    comps, seen = [], set()
    for v in adj:
        if v in seen: continue
        st, c = [v], {v}; seen.add(v)
        while st:
            x = st.pop()
            for y in adj[x]:
                if y not in seen: seen.add(y); c.add(y); st.append(y)
        comps.append(c)
    big = max(comps, key=len)
    pieces = [p for p in pieces if key(p[0]) in big]
    ents = [e for e in ents if key(e) in big]
    L1 = sum(sum(math.dist(a, b) for a, b in zip(l, l[1:])) for l in pieces)
    # obejście: obrys podzielony w punktach wejść
    per = sum(math.dist(a, b) for a, b in zip(ring, ring[1:]))
    epos = sorted({round(ring_pos(e, ring)[1], 2): e for e in ents}.items())
    # bramy: wejścia bliżej niż GATE_M po obrysie
    gates = []
    for s, e in epos:
        if gates and s - gates[-1][-1][0] < GATE_M:
            gates[-1].append((s, e))
        else:
            gates.append([(s, e)])
    if len(gates) > 1 and per - gates[-1][-1][0] + gates[0][0][0] < GATE_M:
        gates[0] = gates.pop() + gates[0]
    bypass, verts, acc = [], [], 0.0
    marks = [(s, e) for s, e in epos]
    cur, mi = [], 0
    for i in range(len(ring) - 1):
        a, b = ring[i], ring[i + 1]; L = math.dist(a, b)
        if not cur: cur = [a]
        while mi < len(marks) and marks[mi][0] <= acc + L:
            cur.append(marks[mi][1]); bypass.append(cur); cur = [marks[mi][1]]; mi += 1
        cur.append(b); acc += L
    if bypass:
        bypass[0] = cur + bypass[0][1:]          # domknięcie pierścienia przez punkt startowy obrysu
    else:
        bypass = [cur]
    bypass = [[p for j, p in enumerate(b) if j == 0 or math.dist(p, b[j - 1]) > 0.01] for b in bypass]
    bypass = [b for b in bypass if len(b) > 1]
    feats = [{'type': 'Feature', 'properties': {'layer': 'roads'},
              'geometry': {'type': 'LineString', 'coordinates': [P.inv(q) for q in pts]}} for pts in pieces]
    feats += [f for f in d['features'] if f['properties'].get('layer') == 'obstacles'
              and inside(P.fwd(f['geometry']['coordinates'][0][0]), ring)]
    feats.append(bnds[idx])
    feats += [{'type': 'Feature', 'properties': {'layer': 'bypass'},
               'geometry': {'type': 'LineString', 'coordinates': [P.inv(q) for q in b]}} for b in bypass]
    feats += [{'type': 'Feature', 'properties': {'layer': 'entrances', 'gate': gi, 'perimeter_m': round(s, 1)},
               'geometry': {'type': 'Point', 'coordinates': P.inv(e)}} for gi, g in enumerate(gates) for s, e in g]
    out = {'type': 'FeatureCollection', 'psm_processed': d['psm_processed'],
           'park_split': {'source': src_park, 'boundary_index': idx, 'snap_m': SNAP_M, 'gate_m': GATE_M,
                          'interior_dead_ends_kept': True, 'length_before': round(L0), 'length_after': round(L1),
                          'perimeter_m': round(per), 'entrances': len(epos), 'gates': len(gates)},
           'features': feats}
    json.dump(out, open(os.path.join(HERE, name + '.geojson'), 'w'))
    dead = sum(1 for v in big if len(adj[v]) == 1)
    return [name, src_park, round(L1), round(per), len(epos), len(gates), snapped, dead]


if __name__ == '__main__':
    rows = [build(sp, n, i) for sp, parts in PARTS.items() for n, i in parts.items()]
    with open(os.path.join(HERE, 'parki.csv'), 'w', newline='') as fh:
        w = csv.writer(fh)
        w.writerow(['park', 'zrodlo', 'dlugosc_sciezek_m', 'obwod_obejscia_m', 'wejscia', 'bramy', 'przedluzone_konce', 'slepe_konce'])
        w.writerows(rows)
    for r in rows:
        print(*r)
