"""Pakiet do GAMA ze strony SIPD: kopia models/PD.gaml z ustawieniami strony, sieć i pliki punktów w SHP, skrypty.

Bez zależności spoza biblioteki standardowej (działa w Pyodide). Kod modelu się nie zmienia: kopia dostaje tylko
wartości zmiennych globalnych, nazwy plików sieci i wyników, zmienną run_seed i jeden eksperyment „web” zamiast
eksperymentów z repozytorium. Każda podmiana jest liczona; brak trafienia przerywa budowę.

Układ współrzędnych jak w narzędziach przeliczenia (eksport_park.py, siec/syn*.shp): metry z przesunięciem OFF;
sieć z GeoJSON: X = x + OFF, Y = OFF + H - y (GAMA odwraca oś y, więc dostaje te same x, y co port);
sieć syntetyczna: X = x + OFF, Y = y + OFF (jak siec/syn*.shp użyte w przeliczeniu)."""
import hashlib, io, json, re, struct, zipfile

PRJ = ('PROJCS["ETRS89 / Poland CS92",GEOGCS["ETRS89",DATUM["European_Terrestrial_Reference_System_1989",'
       'SPHEROID["GRS 1980",6378137,298.257222101]],PRIMEM["Greenwich",0],UNIT["degree",0.0174532925199433]],'
       'PROJECTION["Transverse_Mercator"],PARAMETER["latitude_of_origin",0],PARAMETER["central_meridian",19],'
       'PARAMETER["scale_factor",0.9993],PARAMETER["false_easting",500000],PARAMETER["false_northing",-5300000],'
       'UNIT["metre",1]]')
OFF = 360000.0
EXPERIMENT = "web"
# ustawienia geometrii: trafiają do plików SHP, nie do kodu
IN_SHP = ("network_file", "geojson_crs", "synthetic_grid", "synthetic_spacing", "entrance_file", "rest_zone_file", "dest_file")
# wymuszone w pakiecie: wynik w compat_results.csv, bez dziennika wszystkich gier (PD.csv rośnie do GB)
FORCED = {"compat_export": True, "log_games": False}


def _val(v, typ):
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, str):
        return json.dumps(v, ensure_ascii=False)
    if isinstance(v, (list, tuple)):
        return "[" + ", ".join(_val(x, typ[5:-1]) for x in v) + "]"
    if typ == "int":
        return str(int(round(v)))
    return repr(float(v)) if typ == "float" else str(v)


def gaml_copy(src, p, net_shp, files, results_suffix):
    """src: PD.gaml, p: parametry portu -> (tekst GAML, raport [(parametr, wartość, gdzie)])."""
    report, s = [], src
    for k in sorted(p):
        v = FORCED.get(k, p[k])
        if k in IN_SHP:
            report.append((k, v, "shp"))
            continue
        if v is None:
            report.append((k, v, "python"))
            continue
        m = re.search(r"^\t(int|float|bool|string|list<\w+>) " + re.escape(k) + r" <- [^;]*;", s, re.M)
        if not m:
            report.append((k, v, "python"))
            continue
        typ = m.group(1)
        s, n = re.subn(r"^(\t" + re.escape(typ) + " " + re.escape(k) + r" <- )[^;]*;",
                       lambda mm: mm.group(1) + _val(v, typ) + ";", s, count=1, flags=re.M)
        assert n == 1, k
        report.append((k, v, "forced" if k in FORCED and FORCED[k] != p[k] else "gaml"))
    # sieć i pliki punktów (ścieżki względem modelu)
    s, n = re.subn(r'^(\tstring network_file <- )"[^"]*";', lambda m: m.group(1) + '"%s";' % net_shp, s, count=1, flags=re.M)
    assert n == 1, "network_file"
    for var, fname in files.items():
        s, n = re.subn(r'^(\tstring ' + var + r' <- )"[^"]*";', lambda m: m.group(1) + '"%s";' % fname, s, count=1, flags=re.M)
        assert n == 1, var
    # seed z zewnątrz (plan headless i serwer GAMA): run_seed > 0 ustawia seed na początku init
    s, n = re.subn(r"^global \{\n", "global {\n\tfloat run_seed <- 0.0;   // pakiet ze strony: seed przebiegu\n", s, count=1, flags=re.M)
    assert n == 1, "global"
    i = s.index("\nglobal {")
    j = s.index("\n\tinit {\n", i)
    assert j < s.index("\nspecies "), "init globalny"
    s = s[:j] + "\n\tinit {\n\t\tif run_seed > 0 { seed <- run_seed; }" + s[j + len("\n\tinit {"):]
    # pliki wyników z sufiksem ustawień (kolejne pakiety w jednym folderze się nie mieszają)
    s, n = re.subn(r'"\.\./results/(\w+)\.csv"', lambda m: '"../results/%s_%s.csv"' % (m.group(1), results_suffix), s)
    assert n >= 1 and '"../results/compat_results_%s.csv"' % results_suffix in s, "compat_results.csv"
    # eksperymenty repozytorium (GUI, batch, testy) -> jeden eksperyment bez wyświetlania
    k = s.index("\nexperiment PD type: gui")
    s = s[:k] + "\n// Pakiet ze strony SIPD: eksperymenty repozytorium pominięte (są w models/PD.gaml).\n" \
        "experiment %s type: gui {\n\tparameter \"run_seed\" var: run_seed;\n}\n" % EXPERIMENT
    return s, report


# ---------- SHP bez bibliotek ----------
def _shp(shape_type, items):
    """items: dla punktów [(x, y)], dla linii i wielokątów [[część [(x, y)], ...]] -> (shp, shx)"""
    recs, offs = [], []
    pts_of = (lambda it: [it]) if shape_type == 1 else (lambda it: [q for part in it for q in part])
    allpts = [q for it in items for q in pts_of(it)]
    bbox = (min(q[0] for q in allpts), min(q[1] for q in allpts), max(q[0] for q in allpts), max(q[1] for q in allpts)) if allpts else (0, 0, 0, 0)
    pos = 100
    for i, it in enumerate(items):
        if shape_type == 1:
            body = struct.pack("<i2d", 1, it[0], it[1])
        else:
            pts = pts_of(it)
            bb = (min(q[0] for q in pts), min(q[1] for q in pts), max(q[0] for q in pts), max(q[1] for q in pts))
            body = struct.pack("<i4d2i", shape_type, *bb, len(it), len(pts))
            start = 0
            for part in it:
                body += struct.pack("<i", start)
                start += len(part)
            for q in pts:
                body += struct.pack("<2d", q[0], q[1])
        recs.append(struct.pack(">2i", i + 1, len(body) // 2) + body)
        offs.append((pos // 2, len(body) // 2))
        pos += 8 + len(body)

    def header(length_bytes):
        return (struct.pack(">7i", 9994, 0, 0, 0, 0, 0, length_bytes // 2) + struct.pack("<2i", 1000, shape_type)
                + struct.pack("<4d", *bbox) + struct.pack("<4d", 0, 0, 0, 0))
    return header(pos) + b"".join(recs), header(100 + 8 * len(offs)) + b"".join(struct.pack(">2i", o, n) for o, n in offs)


def _dbf(layers):
    """Pole tekstowe layer (GAML czyta je w pliku wejść)."""
    n = len(layers)
    head = struct.pack("<B3BIHH20x", 3, 126, 1, 1, n, 32 + 32 + 1, 1 + 16)
    field = b"layer".ljust(11, b"\0") + b"C" + b"\0" * 4 + bytes([16, 0]) + b"\0" * 14
    rows = b"".join(b" " + l.encode()[:16].ljust(16) for l in layers)
    return head + field + b"\r" + rows + b"\x1a"


def _layer(base, shape_type, items, layer):
    shp, shx = _shp(shape_type, items)
    return {base + ".shp": shp, base + ".shx": shx, base + ".dbf": _dbf([layer] * len(items)), base + ".prj": PRJ.encode()}


def _features(text):
    data = json.loads(text)
    feats = data.get("features", []) if data.get("type") == "FeatureCollection" else [data]
    out = []
    for ft in feats:
        g = ft.get("geometry") if ft.get("type") == "Feature" else ft
        if g:
            out.append(((ft.get("properties") or {}).get("layer"), g))
    return out


def _centroid(c):
    pts = []

    def walk(q):
        if isinstance(q[0], (int, float)):
            pts.append(q)
        else:
            for r in q:
                walk(r)
    walk(c)
    return sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)


def geometry(sipd, p, geo, read):
    """Sieć jak w porcie (przed wariantem sieci i obejściem, które GAML robi sam) i pliki punktów -> SHP.
    read(ścieżka) -> tekst pliku z parametru. Zwraca ({nazwa: bajty}, {zmienna GAML: plik}, info)."""
    P = sipd.Params(**p)
    if geo is not None:
        net = sipd.PathNetwork.from_geojson(geo, drop_loops=P.network_cleanup, crs=P.geojson_crs)
        H = net.height
        loc = lambda q: (q[0] + OFF, OFF + H - q[1])
    else:
        net = sipd.PathNetwork.synthetic(n=P.synthetic_grid, spacing=P.synthetic_spacing)
        loc = lambda q: (q[0] + OFF, q[1] + OFF)
    tr = lambda x, y: loc(net.to_local(x, y))
    lines = [[[loc(q) for q in pl]] for a in net.adj for b, pl in net.adj[a].items() if a < b]
    out = _layer("@NET@", 3, lines, "roads")
    files, info = {}, {"edges": len(lines), "nodes": sum(1 for v in net.adj if net.adj[v]), "source": "geojson" if geo else "synthetic"}
    if P.entrance_file and geo is not None:
        fs = _features(read(P.entrance_file))
        pts = [tr(*g["coordinates"][:2]) for lay, g in fs if g["type"] == "Point" and lay not in ("roads", "obstacles", "boundary", "bypass")]
        rings = [[[tr(*c[:2]) for c in poly[0]]] for lay, g in fs if g["type"] in ("Polygon", "MultiPolygon") and lay in ("boundary", None)
                 for poly in ([g["coordinates"]] if g["type"] == "Polygon" else g["coordinates"])]
        if pts:
            out.update(_layer("@ENT@", 1, pts, "entrances"))
        elif rings:
            out.update(_layer("@ENT@", 5, rings, "boundary"))
        if pts or rings:
            files["entrance_file"] = "@ENT@.shp"
        byp = [[[tr(*c[:2]) for c in g["coordinates"]]] for lay, g in fs if lay == "bypass" and g["type"] == "LineString"]
        if byp:
            out.update(_layer("@BYP@", 3, byp, "bypass"))
            files["bypass_file"] = "@BYP@.shp"
        info["entrances"], info["bypass"] = len(pts) or len(rings), len(byp)
    for key, tag in (("rest_zone_file", "@REST@"), ("dest_file", "@DEST@")):
        f = getattr(P, key)
        if f and geo is not None:
            pts = [tr(*_centroid(g["coordinates"])) for lay, g in _features(read(f)) if lay not in ("roads", "obstacles", "boundary")]
            if pts:
                out.update(_layer(tag, 1, pts, "points"))
                files[key] = tag + ".shp"
                info[key] = len(pts)
    return out, files, info


def build(sipd, p, geo, gaml_src, read):
    """-> (pliki {nazwa: bajty|tekst}, raport, info). Nazwy mają skrót zawartości: serwer GAMA trzyma skompilowane
    modele według ścieżki, więc nowe ustawienia = nowy plik."""
    shp, files, ginfo = geometry(sipd, p, geo, read)
    gaml, report = gaml_copy(gaml_src, p, "@NET@.shp", files, "@H@")
    h = hashlib.sha256(gaml.encode() + b"".join(k.encode() + shp[k] for k in sorted(shp))).hexdigest()[:8]
    names = {"@NET@": "siec_" + h, "@ENT@": "wejscia_" + h, "@BYP@": "obejscie_" + h, "@REST@": "strefy_" + h, "@DEST@": "cele_" + h,
             "@H@": h}
    for a, b in names.items():
        gaml = gaml.replace(a, b)
    out = {"models/model_%s.gaml" % h: gaml}
    for k, v in shp.items():
        out["includes/" + names[k[:k.index("@", 1) + 1]] + k[k.index("@", 1) + 1:]] = v
    gaml_inc = gaml
    for k in names:                                         # pliki w includes/, model w models/
        if k not in ("@H@",):
            gaml_inc = gaml_inc.replace('"%s.shp"' % names[k], '"../includes/%s.shp"' % names[k])
    out["models/model_%s.gaml" % h] = gaml_inc
    info = dict(ginfo, hash=h, model_file="models/model_%s.gaml" % h, results="results/compat_results_%s.csv" % h,
                experiment=EXPERIMENT, end=int(p["end_cycle"]))
    return out, report, info


RUN_SH = """#!/bin/bash
# Uruchamia przebiegi w GAMA 2025.6 bez okna (headless). Użycie: bash run_gama.sh /sciezka/do/gama-platform
# (albo ustaw GAMA_HOME). Wynik: @RESULTS@, jeden wiersz na seed.
G="${1:-$GAMA_HOME}"
if [ -z "$G" ]; then echo "Podaj katalog GAMA, np. bash run_gama.sh /opt/gama-platform"; exit 1; fi
D="$(cd "$(dirname "$0")" && pwd)"
H="$G/headless/gama-headless.sh"
[ -f "$H" ] || H="$G/Contents/headless/gama-headless.sh"
[ -f "$H" ] || H="$G/Contents/Eclipse/headless/gama-headless.sh"
if [ ! -f "$H" ]; then echo "Nie znaleziono gama-headless.sh w $G"; exit 1; fi
mkdir -p "$D/results" "$D/out"
{
  echo "<Experiment_plan>"
  i=1
  for s in @SEEDS@; do
    echo "  <Simulation id=\\"$i\\" sourcePath=\\"$D/@MODEL@\\" finalStep=\\"@FINAL@\\" experiment=\\"@EXP@\\" seed=\\"$s\\"><Parameters><Parameter name=\\"run_seed\\" type=\\"FLOAT\\" value=\\"$s\\"/></Parameters><Outputs/></Simulation>"
    i=$((i+1))
  done
  echo "</Experiment_plan>"
} > "$D/plan.xml"
cd "$G/headless" 2>/dev/null || true
bash "$H" "$D/plan.xml" "$D/out"
echo "Gotowe: $D/@RESULTS@"
"""

RUN_BAT = """@echo off
rem Uruchamia przebiegi w GAMA 2025.6 bez okna (headless). Uzycie: run_gama.bat C:\\sciezka\\do\\GAMA
rem (albo ustaw GAMA_HOME). Wynik: @RESULTS@
setlocal
set "G=%~1"
if "%G%"=="" set "G=%GAMA_HOME%"
if "%G%"=="" (echo Podaj katalog GAMA, np. run_gama.bat "C:\\Program Files\\Gama" & exit /b 1)
set "D=%~dp0"
if not exist "%D%results" mkdir "%D%results"
if not exist "%D%out" mkdir "%D%out"
> "%D%plan.xml" echo ^<Experiment_plan^>
set /a i=1
for %%s in (@SEEDS@) do call :sim %%s
>> "%D%plan.xml" echo ^</Experiment_plan^>
cd /d "%G%\\headless"
call "%G%\\headless\\gama-headless.bat" "%D%plan.xml" "%D%out"
echo Gotowe: %D%@RESULTS@
exit /b 0
:sim
>> "%D%plan.xml" echo   ^<Simulation id="%i%" sourcePath="%D%@MODEL@" finalStep="@FINAL@" experiment="@EXP@" seed="%1"^>^<Parameters^>^<Parameter name="run_seed" type="FLOAT" value="%1"/^>^</Parameters^>^<Outputs/^>^</Simulation^>
set /a i+=1
exit /b 0
"""

README = """Pakiet SIPD do GAMA (wygenerowany przez stronę SIPD)
====================================================

Wymaga GAMA 2025.6 (sprawdzone na 2025.6.4). Starsze GAMA (1.9) nie kompilują PD.gaml.

Zawartość
- @MODEL@   kopia models/PD.gaml z ustawieniami ze strony: zmienione są tylko wartości zmiennych
                              globalnych, pliki sieci i wyników, zmienna run_seed i eksperyment „{exp}”
- includes/*_@H@.*            sieć ścieżek i pliki punktów (SHP, metry, EPSG:2180 z przesunięciem)
- run_gama.sh / run_gama.bat  uruchomienie headless:  bash run_gama.sh /sciezka/do/gama-platform
- config_@H@.json             ustawienia, seedy, sieć i wersja modelu
- parametry_@H@.csv           które ustawienia trafiły do kodu GAML, które do SHP, a których GAML nie ma

Przebiegi: {n} (seedy {seeds}), po {end} cykli.
Wynik: @RESULTS@ (jeden wiersz na seed, te same kolumny co compat_results.csv portu).
Wczytaj go w zakładce GAMA na stronie: pokaże GAMA obok Pythona z tymi samymi ustawieniami i seedami.

Połączenie ze stroną: rozpakuj paczkę, uruchom GAMA jako serwer (headless/gama-headless.sh -socket 6868,
w Windows gama-headless.bat -socket 6868) i podaj na stronie pełną ścieżkę tego folderu.
Kolejne paczki rozpakowuj do tego samego folderu.

W oknie GAMA: skopiuj models/ i includes/ do projektu GAMA, otwórz @MODEL@, ustaw run_seed, uruchom „{exp}”.

Generator liczb losowych GAMA różni się od Pythona, więc pojedyncze przebiegi nie będą identyczne; porównuj średnie
z kilku seedów. Ten sam run_seed daje w GAMA ten sam wynik w obu trybach.

---

SIPD package for GAMA (generated by the SIPD page). Needs GAMA 2025.6.
- @MODEL@ is a copy of models/PD.gaml with the page settings (only global values, network and result files,
  a run_seed variable and the "{exp}" experiment are changed); includes/ holds the network as SHP.
- Headless: bash run_gama.sh /path/to/gama-platform (Linux, macOS) or run_gama.bat C:\\path\\to\\GAMA (Windows).
- Load @RESULTS@ in the GAMA tab of the page to see GAMA next to Python with the same settings and seeds.
- Connection mode: unzip, start GAMA as a server (gama-headless.sh -socket 6868) and give the page the folder's full path.
- GAMA and Python use different random number generators; compare means over several seeds.
"""


def package(sipd, p, geo, gaml_src, read, seeds, meta=None):
    files, report, info = build(sipd, p, geo, gaml_src, read)
    seeds = [int(s) for s in seeds]
    end = info["end"]
    sub = lambda t: (t.replace("@SEEDS@", " ".join(map(str, seeds))).replace("@FINAL@", str(end + 1)).replace("@EXP@", EXPERIMENT)
                     .replace("@MODEL@", info["model_file"]).replace("@RESULTS@", info["results"]).replace("@H@", info["hash"]))
    buf = io.BytesIO()
    root = "sipd_gama/"
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in files.items():
            z.writestr(root + name, data)
        zi = zipfile.ZipInfo(root + "run_gama.sh")
        zi.external_attr = 0o755 << 16
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, sub(RUN_SH))
        z.writestr(root + "run_gama.bat", sub(RUN_BAT).replace("\n", "\r\n"))
        z.writestr(root + "README.txt", sub(README).format(n=len(seeds), seeds=", ".join(map(str, seeds)), end=end, exp=EXPERIMENT))
        z.writestr(root + "results/.keep", "")
        cfg = dict(meta or {}, seeds=seeds, end_cycle=end, params=p, gama=info)
        z.writestr(root + "config_%s.json" % info["hash"], json.dumps(cfg, indent=2, ensure_ascii=False, default=str) + "\n")
        z.writestr(root + "parametry_%s.csv" % info["hash"], "parametr,wartosc,gdzie\n" + "".join(
            '%s,"%s",%s\n' % (k, (json.dumps(v) if not isinstance(v, str) else v).replace('"', '""'), w) for k, v, w in report))
    return buf.getvalue(), report, info


def read_compat(text, header):
    """compat_results_*.csv z GAMA -> lista słowników. Nagłówek GAMA bywa tekstem wyrażeń z przecinkami, więc kolumny
    nazywa nagłówek portu (header, te same kolumny w tej samej kolejności); liczby jako float, wiersze nagłówka pomija."""
    import csv
    rows = []
    for cells in csv.reader(io.StringIO(text.replace("\r", ""))):
        cells = [c.strip() for c in cells]
        if not cells or "share_ALLD" in cells or len(cells) != len(header):
            continue
        r = {}
        for k, v in zip(header, cells):
            try:
                r[k] = float(v)
            except ValueError:
                r[k] = {"true": True, "false": False}.get(v.lower(), v)
        rows.append(r)
    return rows
