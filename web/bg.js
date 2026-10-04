// Obliczenia w tle (ten sam plik w psm-web i SIPD, web/bg.js): osobny Pyodide w Web Workerze.
// Strona wysyła plik modelu i kod startowy, potem zadania: wyrażenie Pythona zwracające generator.
// Każdy element generatora (tekst JSON) wraca do strony jako zdarzenie; zatrzymanie = zamknięcie workera przez stronę.
"use strict";
let py = null;
self.onmessage = async (ev) => {
  const m = ev.data;
  if (m.type === "init") {
    try {
      importScripts(m.pyodide + "pyodide.js");
      py = await loadPyodide({ indexURL: m.pyodide });
      for (const [p, t] of Object.entries(m.files)) py.FS.writeFile(p, t);
      py.runPython(m.setup);
      self.postMessage({ type: "ready" });
    } catch (e) {
      self.postMessage({ type: "init-error", message: String((e && e.message) || e) });
    }
    return;
  }
  if (m.type !== "job") return;
  let gen = null;
  try {
    for (const [p, d] of Object.entries(m.files || {})) py.FS.writeFile(p, d);
    for (const [k, v] of Object.entries(m.vars || {})) py.globals.set(k, v);
    gen = py.runPython(m.code);
    for (;;) {
      const r = gen.next();
      if (r.done) break;
      self.postMessage({ type: "event", id: m.id, data: r.value });
    }
    self.postMessage({ type: "done", id: m.id });
  } catch (e) {
    self.postMessage({ type: "error", id: m.id, message: String((e && e.message) || e) });
  } finally {
    if (gen && gen.destroy) gen.destroy();
  }
};
