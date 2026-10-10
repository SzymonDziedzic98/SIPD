// Wspólne drobiazgi interfejsu (ten sam plik w psm-web i SIPD, web/ux.js):
// przyciski wyboru pliku w języku strony, podpowiedzi na wyszarzonych przyciskach, napisy w pustych panelach, opisy parametrów,
// zrozumiały komunikat, gdy Pyodide się nie wczyta, zapamiętywanie ustawień i link z ustawieniami, parametry podstawowe
// i zaawansowane, suwaki, porównanie dwóch przebiegów, skróty klawiszowe, karty „Co wypróbować”, wersja modelu i config.json,
// skala kolorów, zapis PNG, wykres pudełkowy, powtórzenia, samouczek, widok na telefon, galeria parków,
// obliczenia w tle (bg.js), mapa ciepła, linki do eksperymentów, pamięć podręczna (sw.js) i dostępność.
// Wymaga i18n.js (L, I18N). Nie dotyka modelu: czyta i ustawia tylko pola formularza.
"use strict";
const UX = (() => {
  const style = document.createElement("style");
  style.textContent = `
.file-pick { display: flex; align-items: center; gap: 8px; min-width: 0; }
.file-pick .btn { padding: 3px 10px; font-size: 12.5px; flex: none; }
.file-pick .file-name { font-size: 12px; color: var(--muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; min-width: 0; }
.file-pick .file-name.chosen { color: var(--ink); font-family: var(--font-mono); }
.empty-host { position: relative; }
.empty-note {
  position: absolute; inset: 0; display: grid; place-items: center; padding: 16px; text-align: center;
  color: var(--muted); font-size: 13px; pointer-events: none;
}
.load-error { display: grid; gap: 8px; }
.label-help { display: flex; align-items: center; gap: 5px; min-width: 0; }
.label-help label[title] { cursor: help; }
.help-btn {
  flex: none; width: 16px; height: 16px; padding: 0; border-radius: 50%; border: 1px solid var(--line);
  background: transparent; color: var(--muted); font: 600 10px/1 var(--font-body); cursor: pointer;
}
.help-btn[aria-expanded="true"] { background: var(--ink); color: var(--ground); border-color: var(--ink); }
.param-help { grid-column: 1 / -1; margin: -2px 0 4px; }
.load-error .btn { justify-self: start; }
.btn.small { padding: 3px 10px; font-size: 12.5px; }
.cat.basic > summary { color: var(--ink); }
.adv-toggle { justify-self: start; }
.field .slider { grid-column: 1 / -1; display: grid; grid-template-columns: auto minmax(0, 1fr) auto; gap: 6px; align-items: center;
  font: 11px var(--font-mono); color: var(--muted); margin: -2px 0 2px; }
.field .slider input[type="range"] { width: 100%; margin: 0; accent-color: var(--park); }
.try-list { display: grid; gap: 10px; }
.try-card { border: 1px solid var(--line); border-radius: 8px; padding: 10px 12px; display: grid; gap: 6px; background: var(--ground); }
.try-card h3 { text-transform: none; letter-spacing: 0; font-size: 14px; color: var(--ink); }
.try-card p { margin: 0; }
.try-card .lead { font-weight: 600; }
.try-banner { border: 1px solid var(--focus); border-radius: 8px; padding: 8px 12px; background: var(--panel); display: grid; gap: 4px; }
.try-banner p { margin: 0; }
.try-banner .controls { margin-top: 2px; }
.cmp-table td, .cmp-table th { white-space: normal; }
.cite { font-family: var(--font-mono); font-size: 12px; background: var(--ground); border: 1px solid var(--line); border-radius: 6px;
  padding: 8px 10px; white-space: pre-wrap; overflow-wrap: anywhere; margin: 0; }
kbd { font-family: var(--font-mono); font-size: 11.5px; border: 1px solid var(--line); border-bottom-width: 2px; border-radius: 4px; padding: 0 4px; background: var(--panel); }
.scale-bar { display: grid; grid-template-columns: auto minmax(60px, 220px) auto; gap: 6px; align-items: center; font-size: 11.5px; color: var(--muted); margin-top: 4px; }
.scale-bar .bar { height: 10px; border-radius: 3px; border: 1px solid var(--line); }
.scale-bar .ttl { grid-column: 1 / -1; }
.png-btn { padding: 1px 8px; font-size: 11.5px; }
.box-plot { display: grid; gap: 6px; }
.box-plot canvas { width: 100%; height: 260px; display: block; }
.box-plot canvas.heat { height: auto; }
.rep-wrap { display: grid; gap: 6px; }
.tour-mask { position: fixed; inset: 0; z-index: 20; pointer-events: none; }
.tour-hole { position: fixed; border-radius: 8px; box-shadow: 0 0 0 9999px rgba(0, 0, 0, .45); outline: 2px solid var(--focus); transition: all .2s; z-index: 21; pointer-events: none; }
.tour-tip { position: fixed; z-index: 22; max-width: min(340px, calc(100vw - 32px)); background: var(--panel); color: var(--ink); border: 1px solid var(--line);
  border-radius: 8px; padding: 10px 12px; display: grid; gap: 8px; box-shadow: 0 6px 24px rgba(0, 0, 0, .25); }
.tour-tip p { margin: 0; }
.mobile-tabs { display: none; gap: 4px; }
.mobile-tabs button { flex: 1; border: 1px solid var(--line); background: transparent; padding: 6px 10px; border-radius: 6px; font-family: var(--font-label); font-weight: 500; cursor: pointer; }
.mobile-tabs button[aria-pressed="true"] { background: var(--ink); color: var(--ground); border-color: var(--ink); }
@media (max-width: 860px) {
  .mobile-tabs { display: flex; }
  [data-mview="results"] > aside.params, [data-mview="params"] > .results { display: none !important; }
}
.run-bar { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 12px; }
.run-bar > .controls { margin: 0; }
.run-status { display: none; flex: 1 1 0; min-width: 0; font-family: var(--font-mono, monospace); font-size: 12px; color: var(--muted); overflow: hidden; }
@media (max-width: 860px) {
  .run-bar { position: sticky; top: 0; z-index: 10; background: var(--ground); border-bottom: 1px solid var(--line); margin-inline: -16px; padding: 6px 16px; }
  /* do dwóch linii zamiast ucinania podpisu */
  .run-status { display: -webkit-box; -webkit-box-orient: vertical; -webkit-line-clamp: 2; flex-basis: 100%; order: 1; font-size: 11px; line-height: 1.35; overflow-wrap: anywhere; }
  .run-bar > .mobile-tabs { order: 2; }
  .run-bar > .mobile-tabs { flex-basis: 100%; }
}
.scope-note { border-left: 3px solid var(--accent); padding: 6px 10px; margin: 0 0 10px; font-size: 12.5px; color: var(--ink); }
.scope-note p { margin: 0; }
.cmp-table th.sortable { cursor: pointer; user-select: none; }
.cmp-table th.sortable button { all: unset; cursor: pointer; }
.cmp-table th.sortable button:focus-visible { outline: 2px solid var(--focus); }
.cmp-table th[aria-sort="ascending"] button::after { content: " ▲"; font-size: 9px; }
.cmp-table th[aria-sort="descending"] button::after { content: " ▼"; font-size: 9px; }
.btn.keep-cta { outline: 2px solid var(--focus); outline-offset: 1px; }
.print-only { display: none; }
.print-only table { border-collapse: collapse; font-size: 10px; margin-top: 6px; }
.print-only td { border: 1px solid #999; padding: 2px 6px; vertical-align: top; }
@media print {
  body { background: #fff !important; color: #000 !important; }
  nav, nav.tabs, aside.params, .run-bar, .mobile-tabs, .controls, .btn, .tour-hole, .tour-tip, .try-banner, .png-btn,
  section[data-panel]:not([data-panel="sim"]), header .lang, .scope-note { display: none !important; }
  section[data-panel="sim"] { display: block !important; }
  section[data-panel="sim"] > .results { display: block !important; }
  .print-only { display: block !important; margin-bottom: 12px; }
  .panel, figure.display { break-inside: avoid; }
}
.gallery { display: grid; grid-template-columns: repeat(auto-fill, minmax(84px, 1fr)); gap: 6px; }
.gallery button { border: 1px solid var(--line); background: var(--ground); border-radius: 6px; padding: 4px; cursor: pointer; display: grid; gap: 2px; text-align: left; font-size: 11px; color: var(--muted); }
.gallery button[aria-pressed="true"] { border-color: var(--focus); outline: 1px solid var(--focus); }
.gallery img { width: 100%; aspect-ratio: 1 / 1; object-fit: contain; background: var(--map-bg, transparent); border-radius: 4px; }
.gallery b { color: var(--ink); font-weight: 600; font-size: 11.5px; }
select { background-color: var(--ground); border: 1px solid var(--line); border-radius: 4px; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; border: 0; }
.skip-link { position: absolute; left: 8px; top: -60px; z-index: 30; background: var(--ink); color: var(--ground); padding: 6px 12px; border-radius: 6px; text-decoration: none; }
.skip-link:focus { top: 8px; }
canvas.map:focus-visible { outline: 2px solid var(--focus); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; scroll-behavior: auto !important; } }
.load-error .detail { font-family: var(--font-mono); font-size: 11.5px; color: var(--muted); overflow-wrap: anywhere; }
`;
  document.head.append(style);
  const relabels = [];
  I18N.onChange(() => relabels.forEach((f) => f()));

  // ---------- A: wybór pliku ----------
  // Natywne „Choose File / No file chosen” mówi językiem przeglądarki; zamiast niego przycisk i nazwa pliku w języku strony.
  function fileInputs(root = document) {
    root.querySelectorAll('input[type="file"]:not([data-ux])').forEach((inp) => {
      inp.dataset.ux = "1";
      const wrap = document.createElement("span"); wrap.className = "file-pick";
      const btn = document.createElement("button"); btn.type = "button"; btn.className = "btn";
      const name = document.createElement("span"); name.className = "file-name";
      inp.before(wrap);
      wrap.append(btn, name, inp);
      inp.hidden = true;
      btn.addEventListener("click", () => inp.click());
      const lab = inp.id && document.querySelector(`label[for="${inp.id}"]`);
      if (lab) { btn.setAttribute("aria-describedby", inp.id + "_name"); name.id = inp.id + "_name"; }
      const render = () => {
        const f = inp.files && inp.files[0], k = inp.files ? inp.files.length : 0;
        btn.textContent = inp.multiple ? L("Wybierz pliki…", "Choose files…") : L("Wybierz plik…", "Choose file…");
        if (lab) btn.setAttribute("aria-label", lab.textContent + ": " + btn.textContent);
        name.textContent = k > 1 ? L(`${k} plików`, `${k} files`) : f ? f.name : L("nie wybrano pliku", "no file chosen");
        name.classList.toggle("chosen", !!f);
        name.title = k ? [...inp.files].map((x) => x.name).join(", ") : "";
      };
      inp.addEventListener("change", render);
      relabels.push(render);
      render();
    });
  }

  // ---------- B: podpowiedzi na wyszarzonych przyciskach ----------
  // Wyszarzony przycisk dostaje title z powodem; po odblokowaniu title znika.
  const hints = [];
  const obs = new MutationObserver((recs) => recs.forEach((r) => hints.filter((h) => h.el === r.target).forEach(upd)));
  function upd(h) {
    const t = L(h.pl, h.en);
    if (h.el.disabled) { h.el.title = t; h.shown = t; }
    else if (h.shown && h.el.title === h.shown) { h.el.removeAttribute("title"); h.shown = ""; }
  }
  function disabledHint(els, pl, en) {
    for (const x of [].concat(els)) {
      const el = typeof x === "string" ? document.getElementById(x) : x;
      if (!el) continue;
      const h = { el, pl, en, shown: "" };
      hints.push(h);
      obs.observe(el, { attributes: true, attributeFilter: ["disabled"] });
      upd(h);
    }
  }
  relabels.push(() => hints.forEach((h) => { if (h.el.disabled) upd(h); }));

  // ---------- C: napisy w pustych panelach ----------
  const empties = [];
  function emptyNote(el, pl, en) {
    if (!el) return;
    let host = el;
    if (el.tagName === "CANVAS") {
      host = document.createElement("div"); host.className = "empty-host";
      el.before(host); host.append(el);
    } else host.classList.add("empty-host");
    const n = document.createElement("div"); n.className = "empty-note";
    host.append(n);
    const e = { n, pl, en };
    empties.push(e);
    n.textContent = L(pl, en);
  }
  relabels.push(() => empties.forEach((e) => { e.n.textContent = L(e.pl, e.en); }));
  function ready(on = true) { empties.forEach((e) => { e.n.hidden = on; }); }

  // ---------- opisy parametrów ----------
  // Etykieta dostaje title (najechanie), a obok przycisk „?”, który rozwija opis pod polem (dotyk, czytniki ekranu).
  // Etykieta trafia do <span class="label-help">, więc strona może dalej zmieniać jej textContent.
  const helps = [];
  function renderHelp(h) {
    const t = h.getText();
    h.lab.title = t; h.btn.title = t; h.p.textContent = t;
    h.btn.setAttribute("aria-label", L("Opis: ", "Description: ") + h.lab.textContent);
  }
  function paramHelp(lab, getText) {
    const wrap = document.createElement("span"); wrap.className = "label-help";
    lab.before(wrap); wrap.append(lab);
    const btn = document.createElement("button"); btn.type = "button"; btn.className = "help-btn"; btn.textContent = "?";
    btn.setAttribute("aria-expanded", "false");
    wrap.append(btn);
    const p = document.createElement("p"); p.className = "hint param-help"; p.hidden = true;
    p.id = (lab.htmlFor || "f" + helps.length) + "_help";
    btn.setAttribute("aria-controls", p.id);
    wrap.parentElement.append(p);
    btn.addEventListener("click", () => { p.hidden = !p.hidden; btn.setAttribute("aria-expanded", String(!p.hidden)); });
    const h = { lab, btn, p, getText };
    helps.push(h);
    renderHelp(h);
  }
  relabels.push(() => helps.forEach(renderHelp));
  // wartość do opisu: liczby z przecinkiem po polsku, puste i logiczne słownie
  function fmtValue(v) {
    if (v === null || v === undefined || v === "") return L("puste", "empty");
    if (typeof v === "boolean") return v ? L("włączone", "on") : L("wyłączone", "off");
    if (Array.isArray(v)) return v.join(", ");
    if (typeof v === "number" && I18N.lang === "pl") return String(v).replace(".", ",");
    return String(v);
  }

  // ---------- D: Pyodide się nie wczytał ----------
  function loadFailed(err) {
    const h = document.querySelector("#loading h2");
    if (h) h.textContent = L("Nie udało się wczytać Pythona", "Could not load Python");
    const bar = document.getElementById("loadBar");
    if (bar) bar.hidden = true;
    const box = document.getElementById("loadMsg");
    const wrap = document.createElement("div"); wrap.className = "load-error";
    const p = document.createElement("p"); p.className = "hint";
    p.textContent = L(
      "Nie udało się pobrać Pythona dla przeglądarki (Pyodide z cdn.jsdelivr.net). Sprawdź połączenie z internetem. " +
      "Sieć uczelniana lub firmowa albo rozszerzenie blokujące reklamy może blokować ten adres; spróbuj wtedy w innej sieci lub przeglądarce.",
      "Could not download Python for the browser (Pyodide from cdn.jsdelivr.net). Check your internet connection. " +
      "A university or company network, or an ad-blocking extension, may block this address; then try another network or browser.");
    const again = document.createElement("button"); again.type = "button"; again.className = "btn primary";
    again.textContent = L("Spróbuj ponownie", "Try again");
    again.addEventListener("click", () => location.reload());
    const d = document.createElement("p"); d.className = "detail";
    d.textContent = L("Szczegóły: ", "Details: ") + ((err && err.message) || err);
    wrap.append(p, again, d);
    box.replaceChildren(wrap);
    box.removeAttribute("class");
  }

  // ---------- F: zapamiętywanie ustawień i link ----------
  // Pola #paramForm [data-key] i podane id. Zapisywane są tylko zmiany względem stanu startowego strony.
  // Kolejność: link (?s=…) > ostatnie ustawienia z tej przeglądarki > stan startowy. linkOnly: pola tylko w linku (np. seed).
  function settings(storeKey, ids, linkOnly = []) {
    // pola ze ścieżką do pliku (np. rest_zone_file) wskazują pliki z bieżącej sesji, więc ich nie zapamiętuję
    const els = () => [...document.querySelectorAll("#paramForm [data-key]"), ...ids.map((id) => document.getElementById(id)).filter(Boolean)]
      .filter((el) => !/_file$/.test(el.dataset.key || ""));
    const keyOf = (el) => el.dataset.key || "#" + el.id;
    const get = (el) => (el.type === "checkbox" ? el.checked : el.value);
    const set = (el, v) => { if (el.type === "checkbox") el.checked = !!v; else el.value = v; };
    const base = new Map(els().map((el) => [keyOf(el), get(el)]));
    const diff = (withLinkOnly) => {
      const o = {};
      els().forEach((el) => {
        const k = keyOf(el), v = get(el);
        if (!withLinkOnly && linkOnly.includes(k)) return;
        if (v !== base.get(k)) o[k] = v;
      });
      return o;
    };
    const apply = (o) => { els().forEach((el) => { const k = keyOf(el); if (Object.prototype.hasOwnProperty.call(o, k)) set(el, o[k]); }); };
    const enc = (o) => btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
    const dec = (s) => JSON.parse(decodeURIComponent(escape(atob(s.replace(/-/g, "+").replace(/_/g, "/")))));
    function save() {
      try {
        const o = diff(false);
        if (Object.keys(o).length) localStorage.setItem(storeKey, JSON.stringify(o));
        else localStorage.removeItem(storeKey);
      } catch (e) { /* tryb prywatny – bez zapamiętywania */ }
    }
    let restored = null, count = 0;
    try {
      const s = new URLSearchParams(location.search).get("s");
      if (s) {
        const o = dec(s);
        if (o && typeof o === "object") { apply(o); restored = "link"; count = Object.keys(o).length; }
        // bez ?s= w pasku adresu, żeby odświeżenie nie cofało późniejszych zmian
        const u = new URL(location.href); u.searchParams.delete("s"); history.replaceState(null, "", u);
      }
    } catch (e) { restored = "badlink"; }
    if (!restored || restored === "badlink") {
      try {
        const o = JSON.parse(localStorage.getItem(storeKey) || "null");
        if (o && typeof o === "object" && Object.keys(o).length) { apply(o); restored = restored || "local"; count = Object.keys(o).length; }
      } catch (e) { /* uszkodzony zapis – pomijam */ }
    }
    document.addEventListener("change", (ev) => { if (els().includes(ev.target)) save(); });
    return {
      restored, count, save,
      reset() { apply(Object.fromEntries(base)); save(); },
      link() {
        const u = new URL(location.href);
        u.searchParams.delete("s"); u.searchParams.delete("lang");
        const o = diff(true);
        if (Object.keys(o).length) u.searchParams.set("s", enc(o));
        return u.toString();
      },
    };
  }

  async function copy(text) {
    try { await navigator.clipboard.writeText(text); return true; }
    catch (e) { window.prompt(L("Skopiuj link:", "Copy the link:"), text); return false; }
  }


  // ---------- parametry podstawowe i zaawansowane ----------
  // Najważniejsze parametry trafiają do pierwszej, otwartej kategorii; reszta jest zwinięta pod przyciskiem.
  // Przycisk podaje, ile ukrytych parametrów różni się od stanu startowego (np. po linku albo gotowym scenariuszu).
  let adv = null;
  function basicAdvanced(form, keys) {
    const rowOf = (k) => { const el = document.getElementById("p_" + k); return el && el.closest(".field"); };
    const det = document.createElement("details"); det.className = "cat basic"; det.open = true;
    const sum = document.createElement("summary"); sum.dataset.pl = "Najważniejsze parametry";
    const fields = document.createElement("div"); fields.className = "fields";
    det.append(sum, fields);
    keys.forEach((k) => { const r = rowOf(k); if (r) fields.append(r); });
    const rest = [...form.children];
    rest.forEach((d) => { if (d.matches("details") && !d.querySelector(".field")) d.hidden = true; });
    const box = document.createElement("div"); box.className = "adv"; box.style.display = "grid"; box.style.gap = "8px";
    box.append(...rest);
    const btn = document.createElement("button"); btn.type = "button"; btn.className = "btn small adv-toggle";
    form.append(det, btn, box);
    const val = (el) => (el.type === "checkbox" ? el.checked : el.value);
    const hidden = () => [...box.querySelectorAll("[data-key]")].filter((el) => el.matches("input, select"));
    const base = new Map(hidden().map((el) => [el, val(el)]));
    let open = false;
    try { open = localStorage.getItem("ux:advanced") === "1"; } catch (e) { /* bez zapamiętywania */ }
    const render = () => {
      box.hidden = !open;
      const n = hidden().filter((el) => val(el) !== base.get(el)).length;
      btn.textContent = open ? L("Ukryj pozostałe parametry", "Hide the other parameters")
        : L("Pokaż wszystkie parametry", "Show all parameters") + (n ? L(` (zmienione: ${n})`, ` (changed: ${n})`) : "");
      btn.setAttribute("aria-expanded", String(open));
      sum.textContent = L("Najważniejsze parametry", "Key parameters");
    };
    btn.addEventListener("click", () => {
      open = !open;
      try { localStorage.setItem("ux:advanced", open ? "1" : "0"); } catch (e) { /* bez zapamiętywania */ }
      render();
    });
    form.addEventListener("change", render);
    relabels.push(render);
    adv = { render, show() { open = true; render(); } };
    render();
    return adv;
  }

  // ---------- suwaki ----------
  // Suwak pod polem liczbowym; pole zostaje i pokazuje dokładną wartość. Zmiana suwaka wysyła „change” z pola,
  // więc strona reaguje tak samo jak na wpisanie liczby.
  const sliders = [];
  function slidersFor(specs) {
    for (const [key, [min, max, step]] of Object.entries(specs)) {
      const num = document.getElementById("p_" + key);
      if (!num) continue;
      const wrap = document.createElement("div"); wrap.className = "slider";
      const lo = document.createElement("span"); lo.textContent = min;
      const hi = document.createElement("span"); hi.textContent = max;
      const r = document.createElement("input"); r.type = "range"; r.min = min; r.max = max; r.step = step;
      wrap.append(lo, r, hi);
      num.closest(".field").append(wrap);
      const s = { num, r, key };
      r.addEventListener("input", () => { num.value = r.value; });
      r.addEventListener("change", () => { num.value = r.value; num.dispatchEvent(new Event("change", { bubbles: true })); });
      num.addEventListener("input", () => syncSlider(s));
      num.addEventListener("change", () => syncSlider(s));
      sliders.push(s);
      syncSlider(s);
    }
    relabels.push(() => sliders.forEach((s) => {
      const lab = document.querySelector(`label[for="${s.num.id}"]`);
      s.r.setAttribute("aria-label", (lab ? lab.textContent : s.key) + L(" (suwak)", " (slider)"));
    }));
    relabels[relabels.length - 1]();
  }
  function syncSlider(s) { if (s.num.value !== "") s.r.value = s.num.value; }
  // po zmianie pól z kodu (link, reset, scenariusz): suwaki i licznik ukrytych zmian
  function refresh() { sliders.forEach(syncSlider); if (adv) adv.render(); }

  // ---------- porównanie dwóch przebiegów ----------
  // Bieżący przebieg i zapamiętany (np. wariant bazowy) na jednym wykresie, wybrana miara, tabela końcowych wartości
  // i różnice ustawień. Strona woła start() po inicjalizacji i record() przy odświeżaniu.
  function compare(host, metrics) {
    host.innerHTML = "";
    const h = document.createElement("h2");
    const hint = document.createElement("p"); hint.className = "hint";
    const ctr = document.createElement("div"); ctr.className = "controls";
    const sel = document.createElement("select"); sel.dataset.nosort = "";
    const keep = document.createElement("button"); keep.type = "button"; keep.className = "btn";
    const clear = document.createElement("button"); clear.type = "button"; clear.className = "btn";
    ctr.append(sel, keep, clear);
    const boxc = document.createElement("div"); boxc.className = "chart-box";
    const cv = document.createElement("canvas"); boxc.append(cv);
    const diff = document.createElement("p"); diff.className = "hint";
    const tw = document.createElement("div"); tw.className = "table-wrap";
    host.append(h, hint, ctr, boxc, diff, tw);
    let cur = null, base = null, chart = null, pending = false;
    const metric = () => metrics.find((m) => m.key === sel.value) || metrics[0];
    const fmt = (v) => (v === undefined || v === null ? "–" : typeof v === "number" ? (Number.isInteger(v) ? String(v) : v.toFixed(2)) : String(v));
    function labels() {
      h.textContent = L("Porównanie dwóch przebiegów", "Compare two runs");
      hint.textContent = L("Wartości same w sobie nie mówią, czy wynik jest dobry: ma sens porównanie wariantów. Zapamiętaj przebieg (np. wariant bazowy), zmień ustawienia, kliknij Inicjalizuj i uruchom. Zapamiętany przebieg jest linią przerywaną, a kolumna „zmiana” podaje różnicę względem niego.",
        "The values alone do not say whether a result is good: what makes sense is comparing variants. Keep a run (e.g. the baseline), change the settings, click Initialise and run. The kept run is the dashed line, and the “change” column gives the difference from it.");
      keep.textContent = L("Zapamiętaj ten przebieg", "Keep this run");
      clear.textContent = L("Wyczyść", "Clear");
      sel.setAttribute("aria-label", L("Miara na wykresie", "Measure on the chart"));
      const v = sel.value;
      sel.replaceChildren(...metrics.map((m) => new Option(L(m.pl, m.en), m.key)));
      sel.value = v || metrics[0].key;
      keep.disabled = !(cur && cur.pts.length);
      clear.disabled = !base;
      ctaKeep();
      draw(); table();
    }
    function draw() {
      if (typeof Chart === "undefined") return;
      const cs = getComputedStyle(document.documentElement);
      const c = (n) => cs.getPropertyValue(n).trim();
      const k = metric().key;
      const ds = [];
      if (base) ds.push({ label: base.label, data: base.pts.map((p) => ({ x: p.x, y: p.v[k] })), borderColor: c("--accent"), borderDash: [6, 4] });
      if (cur) ds.push({ label: cur.label, data: cur.pts.map((p) => ({ x: p.x, y: p.v[k] })), borderColor: c("--focus") });
      if (!chart) {
        chart = new Chart(cv, { type: "line", data: { datasets: ds }, options: {
          animation: false, maintainAspectRatio: false, parsing: false, normalized: true,
          plugins: { legend: { labels: { color: c("--muted"), boxWidth: 18, font: { size: 11 } } } },
          scales: { x: { type: "linear", ticks: { color: c("--muted") }, grid: { color: c("--line") }, title: { display: true, color: c("--muted") } },
                    y: { ticks: { color: c("--muted") }, grid: { color: c("--line") }, title: { display: true, color: c("--muted") } } },
          elements: { point: { radius: 0 }, line: { borderWidth: 1.6 } } } });
      } else chart.data.datasets = ds;
      chart.options.scales.x.title.text = L("cykl", "cycle");
      chart.options.scales.y.title.text = L(metric().pl, metric().en);
      chart.update("none");
    }
    // przycisk „Zapamiętaj” wyróżniony, dopóki nie ma przebiegu odniesienia
    function ctaKeep() {
      const on = !base && !keep.disabled;
      keep.classList.toggle("primary", on); keep.classList.toggle("keep-cta", on);
    }
    const change = (b, c) => (typeof b === "number" && typeof c === "number" && b !== 0
      ? (c >= b ? "+" : "−") + Math.abs((c - b) / Math.abs(b) * 100).toFixed(Math.abs((c - b) / b) < 0.1 ? 1 : 0) + "%" : "–");
    function table() {
      const last = (r) => (r && r.pts.length ? r.pts[r.pts.length - 1] : null);
      const lb = last(base), lc = last(cur);
      const t = document.createElement("table"); t.className = "cmp-table";
      const head = [L("miara", "measure"), base ? base.label : L("zapamiętany", "kept"), cur ? cur.label : L("bieżący", "current")];
      if (lb && lc) head.push(L("zmiana", "change"));
      t.innerHTML = "<tr>" + head.map((x, i) => `<th${i ? ' class="num"' : ""}></th>`).join("") + "</tr>";
      [...t.rows[0].cells].forEach((c, i) => { c.textContent = head[i]; });
      metrics.forEach((m) => {
        const tr = t.insertRow();
        const row = [L(m.pl, m.en), lb ? fmt(lb.v[m.key]) : "–", lc ? fmt(lc.v[m.key]) : "–"];
        if (lb && lc) row.push(change(lb.v[m.key], lc.v[m.key]));
        row.forEach((v, i) => {
          const td = tr.insertCell(); td.textContent = v; if (i) td.className = "num mono";
        });
      });
      const cyc = [L("cykl", "cycle"), lb ? lb.x : "–", lc ? lc.x : "–"];
      if (lb && lc) cyc.push("");
      const tr = t.insertRow(); cyc.forEach((v, i) => { const td = tr.insertCell(); td.textContent = v; if (i) td.className = "num mono"; });
      tw.replaceChildren(t);
      if (base && cur) {
        const keys = [...new Set([...Object.keys(base.params), ...Object.keys(cur.params)])];
        const d = keys.filter((k) => JSON.stringify(base.params[k]) !== JSON.stringify(cur.params[k]))
          .map((k) => `${k}: ${fmtValue(base.params[k])} → ${fmtValue(cur.params[k])}`);
        diff.textContent = d.length ? L("Różnice ustawień: ", "Differences in settings: ") + d.join("; ") + "."
          : L("Ustawienia obu przebiegów są takie same (różnić się może tylko seed).", "Both runs have the same settings (only the seed may differ).");
      } else diff.textContent = "";
    }
    sel.addEventListener("change", draw);
    keep.addEventListener("click", () => api.keep());
    clear.addEventListener("click", () => { base = null; labels(); });
    relabels.push(labels);
    const api = {
      // label: [pl, en] albo tekst; params: ustawienia przebiegu (do listy różnic)
      start(label, params) { cur = { label: typeof label === "string" ? label : L(label[0], label[1]), params: params || {}, pts: [] }; labels(); },
      record(x, values) {
        if (!cur) return;
        const p = cur.pts;
        if (p.length && p[p.length - 1].x === x) p[p.length - 1].v = values; else p.push({ x, v: values });
        keep.disabled = false; ctaKeep();
        if (!pending) { pending = true; setTimeout(() => { pending = false; draw(); table(); }, 300); }
      },
      keep() { if (cur && cur.pts.length) { base = { ...cur, label: cur.label + L(" (zapamiętany)", " (kept)") }; labels(); } },
      clear() { base = null; labels(); },
      get hasBase() { return !!base; },
      redraw() { if (chart) { chart.destroy(); chart = null; } draw(); },
    };
    labels();
    return api;
  }

  // ---------- skróty klawiszowe ----------
  // Spacja i → działają, gdy fokus nie stoi w polu formularza ani na przycisku (tam spacja ma swoje znaczenie).
  function shortcuts(map, active) {
    document.addEventListener("keydown", (ev) => {
      if (ev.ctrlKey || ev.metaKey || ev.altKey || ev.defaultPrevented) return;
      const t = ev.target;
      if (t && (t.isContentEditable || /^(INPUT|SELECT|TEXTAREA|BUTTON|SUMMARY|A)$/.test(t.tagName))) return;
      const f = map[ev.key === " " ? "Space" : ev.key];
      if (!f || (active && !active())) return;
      ev.preventDefault();
      f();
    });
  }

  // ---------- „Co wypróbować” ----------
  // Karty z eksperymentami: co sprawdzić, na co patrzeć, czego się spodziewać; przyciski wariantów uruchamia strona.
  let tryItems = [];
  function tryCards(host, items, run, reps) {
    tryItems = items;
    const render = () => {
      host.replaceChildren(...items.map((it) => {
        const c = document.createElement("article"); c.className = "try-card";
        const h = document.createElement("h3"); h.textContent = L(it.title[0], it.title[1]);
        const p1 = document.createElement("p"); p1.textContent = L(it.what[0], it.what[1]);
        const p2 = document.createElement("p"); p2.className = "hint"; p2.textContent = L("Na co patrzeć: ", "What to watch: ") + L(it.look[0], it.look[1]);
        const p3 = document.createElement("p"); p3.className = "hint"; p3.textContent = L("Czego się spodziewać: ", "What to expect: ") + L(it.expect[0], it.expect[1]);
        const ctr = document.createElement("div"); ctr.className = "controls";
        it.variants.forEach((v, i) => {
          const b = document.createElement("button"); b.type = "button"; b.className = "btn" + (i ? "" : " primary");
          b.textContent = (it.variants.length > 1 ? `${i + 1}. ` : "") + L(v.label[0], v.label[1]);
          b.addEventListener("click", () => run(it, i));
          ctr.append(b);
        });
        if (reps) {
          const r = document.createElement("button"); r.type = "button"; r.className = "btn";
          r.textContent = L("Oba warianty × 5 seedów", "Both variants × 5 seeds");
          r.title = L("Liczy każdy wariant z seedami 1–5 bez animacji i pokazuje średnią, odchylenie i liczbę wygranych par.",
            "Runs each variant with seeds 1–5 without animation and shows the mean, SD and number of winning pairs.");
          r.addEventListener("click", () => reps(it));
          ctr.append(r);
        }
        c.append(h, p1, p2, p3, ctr);
        return c;
      }));
    };
    relabels.push(render);
    render();
  }
  // pasek nad wynikami: który eksperyment i wariant trwa, na co patrzeć, przycisk następnego wariantu
  let bannerState = null;
  function tryBanner(el, it, i, onNext) {
    bannerState = it ? { el, it, i, onNext } : null;
    renderBanner(el);
  }
  function renderBanner(el) {
    const st = bannerState;
    if (!el) return;
    if (!st) { el.hidden = true; el.replaceChildren(); return; }
    const { it, i, onNext } = st, v = it.variants[i];
    el.hidden = false;
    const p1 = document.createElement("p");
    const b = document.createElement("b"); b.textContent = L(it.title[0], it.title[1]);
    p1.append(b, document.createTextNode(" · " + L("wariant", "variant") + ` ${i + 1}/${it.variants.length}: ` + L(v.label[0], v.label[1])));
    const p2 = document.createElement("p"); p2.className = "hint"; p2.textContent = L("Na co patrzeć: ", "What to watch: ") + L(it.look[0], it.look[1]);
    const extra = [];
    const ctr = document.createElement("div"); ctr.className = "controls";
    if (i + 1 < it.variants.length) {
      const n = document.createElement("button"); n.type = "button"; n.className = "btn primary small";
      n.textContent = L("Uruchom wariant ", "Run variant ") + (i + 2) + ": " + L(it.variants[i + 1].label[0], it.variants[i + 1].label[1]);
      n.addEventListener("click", () => onNext(it, i + 1));
      ctr.append(n);
    } else {
      const p3 = document.createElement("p"); p3.className = "hint";
      p3.textContent = L("Czego się spodziewać: ", "What to expect: ") + L(it.expect[0], it.expect[1]);
      extra.push(p3);
    }
    const x = document.createElement("button"); x.type = "button"; x.className = "btn small";
    x.textContent = L("Zamknij", "Close");
    x.addEventListener("click", () => tryBanner(el, null));
    if (tryItems.includes(it)) ctr.append(linkButton(() => tryLink(tryItems.indexOf(it), i)));
    ctr.append(x);
    el.replaceChildren(p1, p2, ...extra, ctr);
  }
  relabels.push(() => { if (bannerState) renderBanner(bannerState.el); });

  // ---------- wersja modelu i config.json ----------
  // skrót SHA-256 pliku modelu wczytanego przez stronę (pierwsze 12 znaków); bez crypto.subtle: FNV-1a
  async function hashText(text) {
    try {
      const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
      return "sha256:" + [...new Uint8Array(b)].map((x) => x.toString(16).padStart(2, "0")).join("").slice(0, 12);
    } catch (e) {
      let h = 0x811c9dc5;
      for (let i = 0; i < text.length; i++) { h ^= text.charCodeAt(i); h = Math.imul(h, 0x01000193) >>> 0; }
      return "fnv1a:" + h.toString(16).padStart(8, "0");
    }
  }
  function downloadJSON(name, obj) {
    const url = URL.createObjectURL(new Blob([JSON.stringify(obj, null, 2) + "\n"], { type: "application/json;charset=utf-8" }));
    const a = document.createElement("a"); a.href = url; a.download = name;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }


  // ---------- J: legenda skali kolorów ----------
  // el: pojemnik pod mapą; spec: { title: [pl, en], stops: [kolory CSS], min, max } albo null (ukryj)
  function scaleBar(el, spec) {
    if (!el) return;
    el.__spec = spec;
    if (!el.__ux) { el.__ux = true; relabels.push(() => scaleBar(el, el.__spec)); }
    if (!spec) { el.hidden = true; return; }
    el.hidden = false; el.className = "scale-bar";
    const f = (v) => (typeof v === "number" ? (Math.abs(v) >= 100 ? v.toFixed(0) : +v.toFixed(2)).toString() : String(v));
    const fmt = (v) => (I18N.lang === "pl" ? f(v).replace(".", ",") : f(v));
    el.innerHTML = '<span class="ttl"></span><span class="lo"></span><span class="bar"></span><span class="hi"></span>';
    el.querySelector(".ttl").textContent = L(spec.title[0], spec.title[1]);
    el.querySelector(".lo").textContent = fmt(spec.min);
    el.querySelector(".hi").textContent = fmt(spec.max) + (spec.plus ? "+" : "");
    el.querySelector(".bar").style.background = `linear-gradient(to right, ${spec.stops.join(", ")})`;
  }

  // ---------- I: zapis PNG ----------
  // canvas z tłem panelu (wykresy Chart.js mają przezroczyste tło)
  function savePNG(canvas, name) {
    const c = document.createElement("canvas"); c.width = canvas.width; c.height = canvas.height;
    const ctx = c.getContext("2d");
    ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--panel").trim() || "#fff";
    ctx.fillRect(0, 0, c.width, c.height);
    ctx.drawImage(canvas, 0, 0);
    c.toBlob((b) => {
      const url = URL.createObjectURL(b);
      const a = document.createElement("a"); a.href = url; a.download = name;
      document.body.append(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, "image/png");
  }
  const slug = (t) => (t || "obraz").toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/ł/g, "l")
    .replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "").slice(0, 40) || "obraz";
  // przycisk „PNG” przy nagłówku każdego panelu z obrazem (figcaption albo h2)
  function pngButtons(hosts) {
    hosts.forEach((host) => {
      if (!host || host.querySelector(".png-btn")) return;
      const cap = host.querySelector("figcaption") || host.querySelector("h2");
      if (!cap) return;
      const b = document.createElement("button"); b.type = "button"; b.className = "btn png-btn"; b.textContent = "PNG";
      const name = () => slug((host.querySelector("h3, h2") || {}).textContent) + ".png";
      const upd = () => { b.title = L("Zapisz obraz jako PNG", "Save the image as PNG"); b.setAttribute("aria-label", b.title + ": " + name()); };
      upd(); relabels.push(upd);
      b.addEventListener("click", () => { const cv = host.querySelector("canvas"); if (cv) savePNG(cv, name()); });
      if (cap.tagName === "H2") { const w = document.createElement("div"); w.className = "controls"; w.style.justifyContent = "space-between"; cap.before(w); w.append(cap, b); }
      else cap.append(b);
    });
  }

  // ---------- O: wykres pudełkowy ----------
  // groups: [{ label, values: [liczby] }]; rysowany na canvas (mediana, kwartyle, wąsy do min/max, punkty)
  function quant(a, q) { const s = [...a].sort((x, y) => x - y); const i = (s.length - 1) * q, lo = Math.floor(i); return s[lo] + (s[Math.min(lo + 1, s.length - 1)] - s[lo]) * (i - lo); }
  function boxPlot(canvas, groups, ylabel) {
    const cs = getComputedStyle(document.documentElement), c = (n) => cs.getPropertyValue(n).trim();
    const dpr = window.devicePixelRatio || 1, W = canvas.clientWidth || 600, H = canvas.clientHeight || 260;
    canvas.width = W * dpr; canvas.height = H * dpr;
    const ctx = canvas.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = c("--panel"); ctx.fillRect(0, 0, W, H);
    const g = groups.filter((x) => x.values.length);
    if (!g.length) return;
    const all = g.flatMap((x) => x.values);
    let lo = Math.min(...all), hi = Math.max(...all);
    if (hi - lo < 1e-12) { lo -= 1; hi += 1; }
    const pad = (hi - lo) * 0.06; lo -= pad; hi += pad;
    const L0 = 64, R0 = 12, T0 = 10, B0 = 46;
    const Y = (v) => T0 + (H - T0 - B0) * (1 - (v - lo) / (hi - lo));
    ctx.font = "11px " + (c("--font-mono") || "monospace"); ctx.fillStyle = c("--muted"); ctx.strokeStyle = c("--line"); ctx.lineWidth = 1;
    for (let k = 0; k <= 4; k++) {
      const v = lo + (hi - lo) * k / 4, y = Y(v);
      ctx.beginPath(); ctx.moveTo(L0, y); ctx.lineTo(W - R0, y); ctx.stroke();
      ctx.textAlign = "right"; ctx.textBaseline = "middle"; ctx.fillText(Math.abs(v) >= 100 ? v.toFixed(0) : v.toPrecision(3), L0 - 6, y);
    }
    ctx.save(); ctx.translate(12, T0 + (H - T0 - B0) / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = "center"; ctx.fillText(ylabel || "", 0, 0); ctx.restore();
    const bw = (W - L0 - R0) / g.length, accent = c("--focus");
    g.forEach((grp, i) => {
      const x = L0 + bw * (i + 0.5), w = Math.min(46, bw * 0.5), v = grp.values;
      const q1 = quant(v, 0.25), q2 = quant(v, 0.5), q3 = quant(v, 0.75), mn = Math.min(...v), mx = Math.max(...v);
      ctx.strokeStyle = c("--ink"); ctx.lineWidth = 1.2;
      ctx.beginPath(); ctx.moveTo(x, Y(mn)); ctx.lineTo(x, Y(q1)); ctx.moveTo(x, Y(q3)); ctx.lineTo(x, Y(mx));
      ctx.moveTo(x - w / 4, Y(mn)); ctx.lineTo(x + w / 4, Y(mn)); ctx.moveTo(x - w / 4, Y(mx)); ctx.lineTo(x + w / 4, Y(mx)); ctx.stroke();
      ctx.fillStyle = accent; ctx.globalAlpha = 0.22; ctx.fillRect(x - w / 2, Y(q3), w, Y(q1) - Y(q3)); ctx.globalAlpha = 1;
      ctx.strokeStyle = accent; ctx.strokeRect(x - w / 2, Y(q3), w, Y(q1) - Y(q3));
      ctx.lineWidth = 2.4; ctx.beginPath(); ctx.moveTo(x - w / 2, Y(q2)); ctx.lineTo(x + w / 2, Y(q2)); ctx.stroke();
      ctx.fillStyle = c("--ink");
      v.forEach((val, j) => { ctx.beginPath(); ctx.arc(x + w / 2 + 6 + (j % 3) * 3, Y(val), 1.8, 0, 2 * Math.PI); ctx.fill(); });
      ctx.fillStyle = c("--muted"); ctx.textAlign = "center"; ctx.textBaseline = "top";
      const lab = grp.label.length > 26 ? grp.label.slice(0, 25) + "…" : grp.label;
      ctx.fillText(lab, x, H - B0 + 8); ctx.fillText("n=" + v.length, x, H - B0 + 22);
    });
  }

  // ---------- K: powtórzenia (średnia ± odchylenie) ----------
  const mean = (a) => a.reduce((s, x) => s + x, 0) / a.length;
  const sd = (a) => (a.length > 1 ? Math.sqrt(a.reduce((s, x) => s + (x - mean(a)) ** 2, 0) / (a.length - 1)) : 0);
  // res: [[{metryki} na seed] na wariant]; metrics: [{key, pl, en}]; labels: [[pl, en]] wariantów
  function repTable(el, labels, metrics, res, seeds) {
    const t = document.createElement("table"); t.className = "cmp-table";
    const head = [L("miara", "measure"), ...labels.map((l) => L(l[0], l[1]) + " (" + L("średnia ± SD", "mean ± SD") + ")")];
    if (labels.length === 2) head.push(L("wariant 2 > wariant 1", "variant 2 > variant 1"));
    const tr0 = t.insertRow(); head.forEach((h, i) => { const th = document.createElement("th"); th.textContent = h; if (i) th.className = "num"; tr0.append(th); });
    const n = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(2));
    metrics.forEach((m) => {
      const tr = t.insertRow();
      const cells = [L(m.pl, m.en)];
      const cols = res.map((r) => r.map((x) => x[m.key]));
      cols.forEach((a) => cells.push(a.length ? n(mean(a)) + " ± " + n(sd(a)) : "–"));
      if (cols.length === 2) {
        const k = Math.min(cols[0].length, cols[1].length);
        let w = 0; for (let i = 0; i < k; i++) if (cols[1][i] > cols[0][i]) w++;
        cells.push(k ? `${w}/${k}` : "–");
      }
      cells.forEach((v, i) => { const td = tr.insertCell(); td.textContent = v; if (i) td.className = "num mono"; });
    });
    const p = document.createElement("p"); p.className = "hint";
    p.textContent = L(`Powtórzenia z seedami ${seeds.join(", ")}; w kolumnie „wariant 2 > wariant 1” liczba par z tym samym seedem, w których drugi wariant dał większą wartość.`,
      `Replicates with seeds ${seeds.join(", ")}; the “variant 2 > variant 1” column counts the same-seed pairs in which the second variant gave a larger value.`);
    el.replaceChildren(t, p);
  }

  // ---------- V: zestawienie grup (np. parków) ----------
  // groups: [{ label, recs: [{miary}] }]; wiersz = grupa, kolumny = n, dodatkowe kolumny i średnia ± SD miar
  // opts.ref: { key, pl, en } – kolumna z różnicą względem grupy o najniższej średniej tej miary i p testu Welcha
  function groupTable(el, groups, metrics, extra = [], opts = {}) {
    const t = document.createElement("table"); t.className = "cmp-table";
    const n = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : v.toFixed(2));
    const vals = (g, k) => g.recs.map((r) => r[k]).filter((v) => typeof v === "number");
    const ref = opts.ref;
    let best = null;
    if (ref) groups.forEach((g) => { const a = vals(g, ref.key); if (a.length && (!best || mean(a) < best.m)) best = { g, m: mean(a), a }; });
    const head = ["", "n", ...extra.map((x) => L(x.pl, x.en)), ...metrics.map((m) => L(m.pl, m.en))];
    if (ref) head.push(L("vs najniższa: ", "vs lowest: ") + L(ref.pl, ref.en));
    const tr0 = t.insertRow();
    head.forEach((h, i) => {
      const th = document.createElement("th"); th.className = "sortable" + (i ? " num" : "");
      const b = document.createElement("button"); b.type = "button"; b.textContent = h; th.append(b);
      b.addEventListener("click", () => { const s = el._sort; el._sort = { i, dir: s && s.i === i && s.dir === "ascending" ? "descending" : "ascending" }; sortRows(); });
      tr0.append(th);
    });
    // nagłówek kolumny grup tylko dla czytników ekranu
    const c0 = document.createElement("span"); c0.className = "sr-only"; c0.textContent = L("Grupa", "Group"); tr0.cells[0].firstChild.append(c0);
    groups.forEach((g) => {
      const tr = t.insertRow();
      const cells = [g.label, String(g.recs.length), ...extra.map((x) => x.get(g)),
        ...metrics.map((m) => { const a = vals(g, m.key); return a.length ? n(mean(a)) + (a.length > 1 ? " ± " + n(sd(a)) : "") : "–"; })];
      if (ref) {
        const a = vals(g, ref.key);
        if (!best || !a.length) cells.push("–");
        else if (g === best.g) cells.push(L("najniższa", "lowest"));
        else {
          const p = welchP(a, best.a);
          const pct = best.m ? "+" + ((mean(a) - best.m) / Math.abs(best.m) * 100).toFixed(0) + "%" : "+" + n(mean(a) - best.m);
          cells.push(pct + (p === null ? "" : " · p " + (p < 0.001 ? "< 0.001" : "= " + p.toFixed(3)) + (p < 0.05 ? " *" : "")));
        }
      }
      cells.forEach((v, i) => { const td = tr.insertCell(); td.textContent = v; if (i) td.className = "num mono"; });
    });
    el.replaceChildren(t);
    if (ref) {
      const note = document.createElement("p"); note.className = "hint";
      note.textContent = L("* różnica istotna przy p < 0,05 (test t Welcha względem grupy o najniższej średniej, bez poprawki na wiele porównań; wymaga co najmniej 2 seedów w grupie). Kliknij nagłówek kolumny, żeby posortować.",
        "* difference significant at p < 0.05 (Welch t test against the group with the lowest mean, no correction for multiple comparisons; needs at least 2 seeds per group). Click a column header to sort.");
      el.append(note);
    }
    sortRows();
    function sortRows() {
      const s = el._sort; if (!s || s.i >= t.rows[0].cells.length) return;
      [...t.rows[0].cells].forEach((c, i) => { if (i === s.i) c.setAttribute("aria-sort", s.dir); else c.removeAttribute("aria-sort"); });
      const num = (r) => { const x = parseFloat(r.cells[s.i].textContent.replace("−", "-")); return isNaN(x) ? (s.dir === "ascending" ? Infinity : -Infinity) : x; };
      const rows = [...t.rows].slice(1);
      rows.sort((a, b) => (s.i === 0 ? a.cells[0].textContent.localeCompare(b.cells[0].textContent, "pl") : num(a) - num(b)) * (s.dir === "ascending" ? 1 : -1));
      rows.forEach((r) => r.parentNode.append(r));
    }
  }

  // test t Welcha (dwustronny); null, gdy w którejś grupie jest mniej niż 2 wartości
  function welchP(a, b) {
    if (a.length < 2 || b.length < 2) return null;
    const va = sd(a) ** 2 / a.length, vb = sd(b) ** 2 / b.length, d = mean(a) - mean(b);
    if (va + vb === 0) return d === 0 ? 1 : 0;
    const tt = d / Math.sqrt(va + vb);
    const df = (va + vb) ** 2 / (va ** 2 / (a.length - 1) + vb ** 2 / (b.length - 1));
    return ibeta(df / (df + tt * tt), df / 2, 0.5);
  }
  function lgamma(z) {
    const c = [76.18009172947146, -86.50532032941677, 24.01409824083091, -1.231739572450155, 0.1208650973866179e-2, -0.5395239384953e-5];
    let x = z, y = z, tmp = x + 5.5; tmp -= (x + 0.5) * Math.log(tmp);
    let ser = 1.000000000190015; for (const k of c) ser += k / ++y;
    return -tmp + Math.log(2.5066282746310005 * ser / x);
  }
  function betacf(a, b, x) {
    const TINY = 1e-300; let c = 1, d = 1 - (a + b) * x / (a + 1); if (Math.abs(d) < TINY) d = TINY; d = 1 / d; let h = d;
    for (let m = 1; m <= 300; m++) {
      const m2 = 2 * m;
      let aa = m * (b - m) * x / ((a - 1 + m2) * (a + m2));
      d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY; c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY; d = 1 / d; h *= d * c;
      aa = -(a + m) * (a + b + m) * x / ((a + m2) * (a + 1 + m2));
      d = 1 + aa * d; if (Math.abs(d) < TINY) d = TINY; c = 1 + aa / c; if (Math.abs(c) < TINY) c = TINY; d = 1 / d;
      const del = d * c; h *= del; if (Math.abs(del - 1) < 3e-12) break;
    }
    return h;
  }
  function ibeta(x, a, b) {
    if (x <= 0) return 0; if (x >= 1) return 1;
    const bt = Math.exp(lgamma(a + b) - lgamma(a) - lgamma(b) + a * Math.log(x) + b * Math.log(1 - x));
    return x < (a + 1) / (a + b + 2) ? bt * betacf(a, b, x) / a : 1 - bt * betacf(b, a, 1 - x) / b;
  }

  // ---------- błędy plików: komunikat po ludzku zamiast wyjątku Pythona ----------
  function fileError(e, name) {
    const m = String((e && e.message) || e);
    console.warn(m);
    const f = name ? "„" + name + "”" : "", fe = name ? "“" + name + "”" : "";
    if (/nie ma ścieżek|nie zawiera linii|sieć ścieżek jest pusta/.test(m))
      return L(`W pliku ${f} nie ma ścieżek. Ścieżki muszą być liniami (LineString lub MultiLineString), a plik zawiera tylko inne geometrie (np. poligony). Sprawdź, czy to plik ze ścieżkami.`,
        `The file ${fe} has no paths. Paths must be lines (LineString or MultiLineString), but the file holds only other geometries (e.g. polygons). Check that this is the paths file.`);
    if (/za krótki|zły nagłówek|\.shp/.test(m))
      return L(`Plik ${f} nie jest poprawnym plikiem .shp. Wskaż główny plik warstwy z rozszerzeniem .shp (nie .shx ani .dbf) albo zapisz warstwę jako GeoJSON.`,
        `The file ${fe} is not a valid .shp file. Choose the main layer file with the .shp extension (not .shx or .dbf) or save the layer as GeoJSON.`);
    if (/JSONDecodeError|Expecting|Unterminated|Extra data|Invalid control|UnicodeDecodeError|not valid JSON|Unexpected token|JSON\.parse/.test(m))
      return L(`Plik ${f} nie jest poprawnym plikiem GeoJSON. Zapisz warstwę w QGIS jako GeoJSON (Eksportuj → Zapisz obiekty jako…) i wczytaj ponownie; wzór jest w przykładowym pliku pod polem wyboru.`,
        `The file ${fe} is not a valid GeoJSON file. Save the layer in QGIS as GeoJSON (Export → Save Features As…) and load it again; the sample file below the file field shows the format.`);
    if (/AttributeError|KeyError|TypeError|IndexError|object has no attribute|brak geometrii/.test(m))
      return L(`Plik ${f} nie ma oczekiwanej struktury GeoJSON (FeatureCollection z obiektami Feature i geometrią). Porównaj go z przykładowym plikiem pod polem wyboru.`,
        `The file ${fe} does not have the expected GeoJSON structure (a FeatureCollection of Features with geometry). Compare it with the sample file below the file field.`);
    return L(`Nie udało się odczytać pliku ${f}. Sprawdź format (opis i przykładowy plik pod polem wyboru).`,
      `Could not read the file ${fe}. Check the format (description and sample file below the file field).`);
  }

  // ---------- wydruk / PDF podsumowania przebiegu ----------
  // summary(): { title, note, rows: [[nazwa, wartość], ...] }; tylko na czas drukowania: tytuł i zastrzeżenie na górze wyników,
  // tabela ustawień na końcu
  function printButton(btn, host, summary) {
    const top = document.createElement("div"), end = document.createElement("div");
    top.className = end.className = "print-only";
    const fill = () => {
      const s = summary();
      const h = document.createElement("h2"); h.textContent = s.title;
      const meta = document.createElement("p"); meta.textContent = new Date().toLocaleString(I18N.lang === "en" ? "en-GB" : "pl-PL") + " · " + location.origin + location.pathname;
      const note = document.createElement("p"); note.textContent = s.note;
      top.replaceChildren(h, meta, note);
      const h3 = document.createElement("h3"); h3.textContent = L("Ustawienia przebiegu", "Run settings");
      const t = document.createElement("table");
      s.rows.forEach(([k, v]) => { const tr = t.insertRow(); tr.insertCell().textContent = k; tr.insertCell().textContent = v; });
      end.replaceChildren(h3, t);
      host.prepend(top); host.append(end);
    };
    window.addEventListener("beforeprint", fill);
    window.addEventListener("afterprint", () => { top.remove(); end.remove(); });
    btn.addEventListener("click", () => { fill(); window.print(); });
  }

  // ---------- H: samouczek ----------
  // steps: [{ el: () => element, text: [pl, en] }]; pokazywany raz (klucz w localStorage), potem z przycisku
  function tour(key, steps, force) {
    try { if (!force && localStorage.getItem(key)) return; } catch (e) { if (!force) return; }
    // na telefonie bez samoczynnego startu (nakładka zasłaniałaby wypełniane pole); jest przycisk „Samouczek”
    if (!force && window.matchMedia("(max-width: 860px)").matches) return;
    const hole = document.createElement("div"); hole.className = "tour-hole";
    const tip = document.createElement("div"); tip.className = "tour-tip"; tip.setAttribute("role", "dialog");
    tip.setAttribute("aria-label", L("Samouczek", "Tutorial"));
    document.body.append(hole, tip);
    let i = 0;
    const end = () => { hole.remove(); tip.remove(); document.removeEventListener("keydown", onKey, true); window.removeEventListener("resize", show);
      try { localStorage.setItem(key, "1"); } catch (e) { /* bez zapamiętywania */ } };
    const onKey = (ev) => { if (ev.key === "Escape") { ev.preventDefault(); end(); } };
    document.addEventListener("keydown", onKey, true);
    function show() {
      const st = steps[i], el = st.el();
      if (!el || !el.getClientRects().length) { if (i + 1 < steps.length) { i++; show(); } else end(); return; }
      el.scrollIntoView({ block: el.getBoundingClientRect().height > window.innerHeight * 0.6 ? "start" : "nearest" });
      const r = el.getBoundingClientRect();
      Object.assign(hole.style, { left: r.left - 4 + "px", top: r.top - 4 + "px", width: r.width + 8 + "px", height: r.height + 8 + "px" });
      tip.replaceChildren();
      const p = document.createElement("p"); p.textContent = L(st.text[0], st.text[1]);
      const ctr = document.createElement("div"); ctr.className = "controls";
      const skip = document.createElement("button"); skip.type = "button"; skip.className = "btn small"; skip.textContent = L("Zamknij", "Close");
      const next = document.createElement("button"); next.type = "button"; next.className = "btn primary small";
      next.textContent = i + 1 < steps.length ? L("Dalej", "Next") + ` (${i + 1}/${steps.length})` : L("Gotowe", "Done");
      skip.onclick = end; next.onclick = () => { if (i + 1 < steps.length) { i++; show(); } else end(); };
      ctr.append(next, skip); tip.append(p, ctr);
      const tw = Math.min(340, window.innerWidth - 32);
      let left = Math.min(Math.max(16, r.left), window.innerWidth - tw - 16);
      Object.assign(tip.style, { left: left + "px", top: "0px" });
      const th = tip.offsetHeight || 140;
      let top = r.bottom + 12;
      if (top + th > window.innerHeight - 8) top = r.top - th - 12;
      if (top < 8) top = Math.max(8, window.innerHeight - th - 8);
      tip.style.top = top + "px";
      next.focus({ preventScroll: true });
    }
    window.addEventListener("resize", show);
    show();
  }

  // ---------- L: telefon – przełącznik Parametry / Wyniki ----------
  function mobileTabs(section) {
    const nav = document.createElement("div"); nav.className = "mobile-tabs"; nav.setAttribute("role", "group");
    const bp = document.createElement("button"); bp.type = "button";
    const br = document.createElement("button"); br.type = "button";
    nav.append(bp, br);
    section.before(nav);
    const set = (v) => { section.dataset.mview = v; bp.setAttribute("aria-pressed", String(v === "params")); br.setAttribute("aria-pressed", String(v === "results")); };
    bp.onclick = () => set("params"); br.onclick = () => { set("results"); window.dispatchEvent(new Event("resize")); };
    const lab = () => { bp.textContent = L("Parametry", "Parameters"); br.textContent = L("Wyniki", "Results"); nav.setAttribute("aria-label", L("Widok na telefonie", "Phone view")); };
    relabels.push(lab); lab(); set("params");
    // nawigacja zakładek ukrywa przełącznik razem z sekcją
    new MutationObserver(() => { nav.hidden = section.hidden; }).observe(section, { attributes: true, attributeFilter: ["hidden"] });
    return { show: set };
  }

  // ---------- pasek przebiegu: Inicjalizuj, Start, Krok i licznik cykli nad panelami ----------
  // Przyciski nie siedzą w panelu parametrów, więc są pod ręką także w widoku wyników; na telefonie pasek
  // (razem z przełącznikiem Parametry / Wyniki) zostaje u góry ekranu przy przewijaniu.
  function runBar(section, controls, status) {
    const bar = document.createElement("div"); bar.className = "run-bar";
    const prev = section.previousElementSibling;
    const tabs = prev && prev.classList.contains("mobile-tabs") ? prev : null;
    section.before(bar);
    bar.append(controls);
    if (status) {
      const mirror = document.createElement("div"); mirror.className = "run-status"; mirror.setAttribute("aria-hidden", "true");
      const copy = () => { mirror.textContent = status.textContent.replace(/\s+/g, " ").trim(); };
      new MutationObserver(copy).observe(status, { subtree: true, childList: true, characterData: true });
      copy(); bar.append(mirror);
    }
    if (tabs) bar.append(tabs);
    const sync = () => { bar.hidden = section.hidden; };
    new MutationObserver(sync).observe(section, { attributes: true, attributeFilter: ["hidden"] });
    sync();
    return bar;
  }

  // ---------- N: galeria parków ----------
  // items: [{ name, file, length_m, junctions }]; miniatury SVG z katalogu dir
  function gallery(host, items, dir, onPick) {
    const render = () => {
      host.className = "gallery";
      host.replaceChildren(...items.map((it) => {
        const b = document.createElement("button"); b.type = "button"; b.dataset.name = it.name;
        const img = document.createElement("img"); img.alt = ""; img.loading = "lazy"; img.src = dir + it.file.replace(/\.geojson$/, ".svg");
        const n = document.createElement("b"); n.textContent = it.name.replace(/^Park /, "");
        const d = document.createElement("span");
        const km = (it.length_m / 1000).toFixed(1);
        d.textContent = L(`${km.replace(".", ",")} km · ${it.junctions} skrzyż.`, `${km} km · ${it.junctions} junct.`);
        b.title = it.name + " – " + d.textContent;
        b.append(img, n, d);
        b.addEventListener("click", () => onPick(it.name));
        return b;
      }));
    };
    relabels.push(render); render();
    return { mark(name) { host.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.name === name))); } };
  }


  // ---------- T: obliczenia w tle ----------
  // cfg: { pyodide: adres katalogu Pyodide, files: async () => ({ ścieżka: tekst }), setup: kod Pythona, mainPy: () => py strony }
  // run(code, vars, onEvent, files): code to wyrażenie Pythona zwracające generator tekstów JSON; wynik { stopped }.
  // Bez workera (np. strona z dysku) ten sam kod idzie w Pyodide strony, z przerwą po każdym elemencie generatora.
  function background(cfg) {
    let w = null, ready = null, job = null, seq = 0, mainStop = false;
    let mode = typeof Worker === "function" && location.protocol !== "file:" ? "worker" : "main";
    const kill = () => { if (w) w.terminate(); w = null; ready = null; };
    function spawn() {
      ready = (async () => {
        const files = await cfg.files();
        await new Promise((res, rej) => {
          w = new Worker(cfg.worker || "bg.js");
          w.onmessage = (ev) => {
            const m = ev.data;
            if (m.type === "ready") { res(); return; }
            if (m.type === "init-error") { rej(new Error(m.message)); return; }
            if (!job || m.id !== job.id) return;
            const j = job;
            if (m.type === "event") j.onEvent(JSON.parse(m.data));
            else { job = null; if (m.type === "done") j.res({ stopped: false }); else j.rej(new Error(m.message)); }
          };
          w.onerror = (ev) => {
            ev.preventDefault();
            const err = new Error(ev.message || "worker");
            rej(err);
            if (job) { const j = job; job = null; j.rej(err); }
          };
          w.postMessage({ type: "init", pyodide: cfg.pyodide, files, setup: cfg.setup });
        });
      })();
      return ready;
    }
    let busy = false;
    async function run(code, vars, onEvent, files) {
      if (busy) throw new Error(L("trwa inne liczenie w tle; zatrzymaj je albo poczekaj na koniec", "another background computation is running; stop it or wait for it to finish"));
      busy = true;
      try { return await run1(code, vars, onEvent, files); } finally { busy = false; }
    }
    async function run1(code, vars, onEvent, files) {
      if (mode === "worker") {
        try { await (ready || spawn()); }
        catch (e) { kill(); mode = "main"; console.warn("obliczenia w tle niedostępne, liczę na stronie:", e); }
      }
      if (mode === "worker") {
        return new Promise((res, rej) => {
          job = { id: ++seq, res, rej, onEvent };
          w.postMessage({ type: "job", id: job.id, code, vars, files });
        });
      }
      const py = cfg.mainPy();
      mainStop = false;
      Object.entries(files || {}).forEach(([p, d]) => py.FS.writeFile(p, d));
      Object.entries(vars || {}).forEach(([k, v]) => py.globals.set(k, v));
      const gen = py.runPython(code);
      try {
        for (;;) {
          if (mainStop) return { stopped: true };
          const r = gen.next();
          if (r.done) break;
          onEvent(JSON.parse(r.value));
          await new Promise((res) => setTimeout(res, 0));
        }
      } finally { if (gen.destroy) gen.destroy(); }
      return { stopped: false };
    }
    function stop() {
      mainStop = true;
      if (job) { const j = job; job = null; kill(); j.res({ stopped: true }); }
    }
    return { run, stop, get mode() { return mode; }, get starting() { return mode === "worker" && !!ready && !job; } };
  }

  // ---------- S: mapa ciepła dla przeglądu dwóch parametrów ----------
  // xs, ys: wartości parametrów; cell(x, y) -> [liczby]; w komórce średnia i n; skala sekwencyjna (viridis)
  const VIRIDIS = ["#440154", "#3b528b", "#21908c", "#5dc963", "#fde725"];
  function viridis(t) {
    t = Math.min(1, Math.max(0, t)) * (VIRIDIS.length - 1);
    const i = Math.min(VIRIDIS.length - 2, Math.floor(t)), f = t - i;
    const a = VIRIDIS[i], b = VIRIDIS[i + 1], h = (c, k) => parseInt(c.slice(1 + 2 * k, 3 + 2 * k), 16);
    return "rgb(" + [0, 1, 2].map((k) => Math.round(h(a, k) + (h(b, k) - h(a, k)) * f)).join(",") + ")";
  }
  function heatmap(canvas, spec) {
    const { xs, ys, cell, xlabel, ylabel, title } = spec;
    const cs = getComputedStyle(document.documentElement), c = (n) => cs.getPropertyValue(n).trim();
    const dpr = window.devicePixelRatio || 1, W = canvas.clientWidth || 600;
    const H = Math.max(200, Math.min(420, 70 + ys.length * 44));
    canvas.style.height = H + "px";
    canvas.width = W * dpr; canvas.height = H * dpr;
    const ctx = canvas.getContext("2d"); ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.fillStyle = c("--panel"); ctx.fillRect(0, 0, W, H);
    const vals = xs.map((x) => ys.map((y) => { const v = cell(x, y); return { m: v.length ? mean(v) : null, n: v.length }; }));
    const all = vals.flat().filter((v) => v.m !== null).map((v) => v.m);
    if (!all.length) return;
    const lo = Math.min(...all), hi = Math.max(...all);
    ctx.font = "11px " + (c("--font-mono") || "monospace");
    const L0 = Math.max(56, 30 + Math.max(...ys.map((y) => ctx.measureText(String(y)).width))), R0 = 56, T0 = 22, B0 = 44;
    const cw = (W - L0 - R0) / xs.length, ch = (H - T0 - B0) / ys.length;
    const f = (v) => (Math.abs(v) >= 100 ? v.toFixed(0) : Math.abs(v) >= 1 ? v.toFixed(2) : v.toPrecision(2));
    ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillStyle = c("--ink"); ctx.fillText(title || "", L0, 4);
    vals.forEach((col, i) => col.forEach((v, j) => {
      const x = L0 + i * cw, y = T0 + (ys.length - 1 - j) * ch;
      if (v.m === null) { ctx.strokeStyle = c("--line"); ctx.strokeRect(x + 1, y + 1, cw - 2, ch - 2); return; }
      const t = hi > lo ? (v.m - lo) / (hi - lo) : 0.5;
      ctx.fillStyle = viridis(t); ctx.fillRect(x + 1, y + 1, cw - 2, ch - 2);
      ctx.fillStyle = t > 0.6 ? "#111" : "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
      if (cw > 34 && ch > 16) ctx.fillText(f(v.m), x + cw / 2, y + ch / 2);
    }));
    ctx.fillStyle = c("--muted"); ctx.textAlign = "center"; ctx.textBaseline = "top";
    xs.forEach((x, i) => ctx.fillText(String(x), L0 + (i + 0.5) * cw, H - B0 + 6));
    ctx.fillText(xlabel || "", L0 + (W - L0 - R0) / 2, H - B0 + 24);
    ctx.textAlign = "right"; ctx.textBaseline = "middle";
    ys.forEach((y, j) => ctx.fillText(String(y), L0 - 6, T0 + (ys.length - 1 - j + 0.5) * ch));
    ctx.save(); ctx.translate(12, T0 + (H - T0 - B0) / 2); ctx.rotate(-Math.PI / 2); ctx.textAlign = "center"; ctx.fillText(ylabel || "", 0, 0); ctx.restore();
    // pasek skali po prawej
    const bx = W - R0 + 14, bh = H - T0 - B0;
    for (let k = 0; k < bh; k++) { ctx.fillStyle = viridis(1 - k / bh); ctx.fillRect(bx, T0 + k, 10, 1); }
    ctx.fillStyle = c("--muted"); ctx.textAlign = "left"; ctx.textBaseline = "top"; ctx.fillText(f(hi), bx + 13, T0);
    ctx.textBaseline = "bottom"; ctx.fillText(f(lo), bx + 13, T0 + bh);
  }

  // recs: [{ x, y, v }] z wierszy wyników; wartości osi posortowane (liczby rosnąco)
  function heatFrom(canvas, recs, xlabel, ylabel, title) {
    const uniq = (k) => [...new Set(recs.map((r) => r[k]))].sort((a, b) => (typeof a === "number" && typeof b === "number" ? a - b : String(a).localeCompare(String(b))));
    const xs = uniq("x"), ys = uniq("y");
    heatmap(canvas, { xs, ys, xlabel, ylabel, title,
      cell: (x, y) => recs.filter((r) => r.x === x && r.y === y && typeof r.v === "number" && isFinite(r.v)).map((r) => r.v) });
  }

  // ---------- Q: dostępność ----------
  // link „Przejdź do treści”, zakładki ze strzałkami (wzorzec ARIA tabs), nazwy obszarów i obrazów, komunikaty czytane przez czytnik.
  // labels: [[element, pl, en, atrybut = "aria-label"]]
  function a11y(opts) {
    const { main, tabs, labels = [], live = [] } = opts;
    if (main) {
      const a = document.createElement("a"); a.className = "skip-link"; a.href = "#" + main.id;
      document.body.prepend(a);
      main.tabIndex = -1;
      labels.push([a, "Przejdź do treści", "Skip to content", "text"]);
    }
    if (tabs) {
      const list = [...tabs.querySelectorAll('[role="tab"]')];
      const sync = () => list.forEach((t) => { t.tabIndex = t.getAttribute("aria-selected") === "true" ? 0 : -1; });
      list.forEach((t) => {
        if (!t.id) t.id = "tab-" + t.dataset.tab;
        const panel = document.querySelector(`[data-panel="${t.dataset.tab}"]`);
        if (panel) {
          if (!panel.id) panel.id = "panel-" + t.dataset.tab;
          panel.setAttribute("role", "tabpanel"); panel.setAttribute("aria-labelledby", t.id);
          t.setAttribute("aria-controls", panel.id);
        }
        t.addEventListener("keydown", (ev) => {
          const i = list.indexOf(t), k = ev.key;
          let j = k === "ArrowRight" ? i + 1 : k === "ArrowLeft" ? i - 1 : k === "Home" ? 0 : k === "End" ? list.length - 1 : null;
          if (j === null) return;
          ev.preventDefault();
          j = (j + list.length) % list.length;
          list[j].click(); list[j].focus();
        });
      });
      new MutationObserver(sync).observe(tabs, { subtree: true, attributes: true, attributeFilter: ["aria-selected"] });
      sync();
    }
    live.forEach((el) => { if (el) { el.setAttribute("role", "status"); el.setAttribute("aria-live", "polite"); } });
    const lab = () => labels.forEach(([el, pl, en, attr = "aria-label"]) => {
      if (!el) return;
      if (attr === "text") el.textContent = L(pl, en); else el.setAttribute(attr, L(pl, en));
    });
    relabels.push(lab); lab();
  }

  // ---------- R: link do eksperymentu „Co wypróbować” ----------
  // ?try=<nr karty>.<nr wariantu> albo ?try=<nr karty>.reps (oba warianty × 5 seedów); numeracja od 1
  function tryLink(i, v) {
    const u = new URL(location.href);
    ["s", "lang", "try"].forEach((k) => u.searchParams.delete(k));
    u.searchParams.set("try", (i + 1) + "." + (v === "reps" ? "reps" : v + 1));
    return u.toString();
  }
  function tryFromURL(items) {
    const q = new URLSearchParams(location.search).get("try");
    if (!q) return null;
    const u = new URL(location.href); u.searchParams.delete("try"); history.replaceState(null, "", u);
    const m = /^(\d+)\.(\d+|reps)$/.exec(q);
    if (!m) return null;
    const it = items[+m[1] - 1];
    if (!it) return null;
    if (m[2] === "reps") return { it, reps: true };
    const v = +m[2] - 1;
    return v >= 0 && v < it.variants.length ? { it, v } : null;
  }
  // relabel: przycisk na stałe w stronie (przy zmianie języka); w pasku eksperymentu przycisk powstaje od nowa
  function linkButton(getUrl, relabel = false) {
    const b = document.createElement("button"); b.type = "button"; b.className = "btn small";
    const lab = () => { b.textContent = L("Kopiuj link", "Copy link"); b.title = L("Link otwiera stronę od razu na tym eksperymencie.", "The link opens the page straight on this experiment."); };
    lab(); if (relabel) relabels.push(lab);
    b.addEventListener("click", async () => {
      const ok = await copy(getUrl());
      if (ok) { b.textContent = L("Skopiowano", "Copied"); setTimeout(lab, 1500); }
    });
    return b;
  }

  // ---------- U: pamięć podręczna i praca bez sieci ----------
  // rejestruje sw.js; el dostaje krótką informację, gdy strona jest już zapisana w przeglądarce
  function offline(el) {
    if (!("serviceWorker" in navigator) || !window.isSecureContext) return;
    const say = () => {
      if (!el || !navigator.serviceWorker.controller) return;
      el.hidden = false;
      el.textContent = navigator.onLine
        ? L("Strona i Python są zapisane w tej przeglądarce: kolejne otwarcie będzie szybsze i zadziała bez internetu.",
            "The page and Python are stored in this browser: the next visit will be faster and will work without internet.")
        : L("Brak internetu: strona działa z kopii zapisanej w przeglądarce.", "No internet: the page runs from the copy stored in this browser.");
    };
    navigator.serviceWorker.register("sw.js").then(() => navigator.serviceWorker.ready).then(say).catch(() => {});
    navigator.serviceWorker.addEventListener("controllerchange", say);
    window.addEventListener("online", say); window.addEventListener("offline", say);
    relabels.push(say);
  }

  return { fileInputs, disabledHint, emptyNote, ready, loadFailed, settings, copy, paramHelp, fmtValue,
    basicAdvanced, sliders: slidersFor, refresh, compare, shortcuts, tryCards, tryBanner, hashText, downloadJSON,
    scaleBar, savePNG, pngButtons, boxPlot, repTable, groupTable, welchP, fileError, printButton, mean, sd, tour, mobileTabs, runBar, gallery,
    a11y, background, heatmap, heatFrom, tryLink, tryFromURL, linkButton, offline };
})();
