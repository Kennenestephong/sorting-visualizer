"use strict";

const COLORS = { normal: "#B0B0B0", compare: "#F2C037", move: "#E5484D", sorted: "#46A758" };

async function api(path, body, method) {
  const opts = { method: method || (body ? "POST" : "GET"), headers: { "Content-Type": "application/json" } };
  if (body !== undefined) opts.body = JSON.stringify(body);
  const res = await fetch(path, opts);
  if (!res.ok) {
    let msg = res.status + " " + res.statusText;
    try { const j = await res.json(); if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch (e) {}
    throw new Error(msg);
  }
  return res.json();
}

function showError(err) {
  const el = document.getElementById("error");
  el.textContent = "Error: " + err.message;
  el.classList.remove("hidden");
}
function clearError() { document.getElementById("error").classList.add("hidden"); }

class Timeline {
  constructor(recording) { this.rec = recording; this.reset(); }
  get length() { return this.rec.events.length; }
  get atEnd() { return this.index >= this.length; }
  reset() {
    this.index = 0;
    this.state = { data: this.rec.initial.slice(), sorted: new Set(), highlight: [], kind: "" };
  }
  _apply(e) {
    const s = this.state;
    if (e.type === "compare") { s.highlight = [e.i, e.j]; s.kind = "compare"; }
    else if (e.type === "swap") { const t = s.data[e.i]; s.data[e.i] = s.data[e.j]; s.data[e.j] = t; s.highlight = [e.i, e.j]; s.kind = "move"; }
    else if (e.type === "overwrite") { s.data[e.i] = e.value; s.highlight = [e.i]; s.kind = "move"; }
    else if (e.type === "marksorted") { s.sorted.add(e.i); s.highlight = []; s.kind = ""; }
  }
  _revert(e) {
    const s = this.state;
    if (e.type === "swap") { const t = s.data[e.i]; s.data[e.i] = s.data[e.j]; s.data[e.j] = t; }
    else if (e.type === "overwrite") { s.data[e.i] = e.old; }
    else if (e.type === "marksorted") { s.sorted.delete(e.i); }
    s.highlight = []; s.kind = "";
  }
  stepForward() { if (this.atEnd) return false; this._apply(this.rec.events[this.index]); this.index++; return true; }
  stepBack() { if (this.index <= 0) return false; this.index--; this._revert(this.rec.events[this.index]); return true; }
}

function role(i, state) {
  if (state.sorted.has(i)) return "sorted";
  if (state.highlight.includes(i)) return state.kind || "normal";
  return "normal";
}

function drawBars(canvas, state) {
  const ctx = canvas.getContext("2d");
  const w = canvas.width, h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const data = state.data, n = data.length;
  if (!n) return;
  const maxv = Math.max.apply(null, data) || 1;
  const bw = w / n;
  for (let i = 0; i < n; i++) {
    const bh = (data[i] / maxv) * h;
    ctx.fillStyle = COLORS[role(i, state)];
    ctx.fillRect(i * bw, h - bh, Math.max(1, bw - 1), bh);
  }
}

// ---- shared UI state ----
const els = {};
["play", "stepBack", "stepFwd", "reset", "speed", "size", "fill", "algo",
 "save", "load", "export", "tab-single", "tab-race",
 "single-view", "race-view", "single-canvas", "single-stats"].forEach((id) => { els[id] = document.getElementById(id); });

let currentData = [];
let currentFill = "random";
let mode = "single";              // "single" | "race"
let single = null;                // Timeline
let race = {};                    // {name: Timeline}
let timer = null;

function statsText(rec) {
  return `comparisons: ${rec.stats.comparisons}  writes: ${rec.stats.writes}  time: ${rec.elapsed_ms.toFixed(1)} ms`;
}

function renderSingle() {
  if (!single) return;
  drawBars(els["single-canvas"], single.state);
  els["single-stats"].textContent = statsText(single.rec);
}

function renderRace() {
  document.querySelectorAll(".race-canvas").forEach((c) => {
    const tl = race[c.dataset.algo];
    if (tl) drawBars(c, tl.state);
  });
  document.querySelectorAll(".stats[data-algo]").forEach((d) => {
    const tl = race[d.dataset.algo];
    if (tl) d.textContent = `${d.dataset.algo}: ${tl.index} ops / ${tl.length}`;
  });
}

function render() { mode === "single" ? renderSingle() : renderRace(); }

function stopPlay() {
  if (timer) { clearInterval(timer); timer = null; }
  els.play.textContent = "Play";
}

function tick() {
  if (mode === "single") {
    if (!single.stepForward()) { stopPlay(); return; }
  } else {
    const anyMoved = Object.values(race).map((tl) => tl.stepForward()).some(Boolean);
    if (!anyMoved) { stopPlay(); return; }
  }
  render();
}

function togglePlay() {
  if (timer) { stopPlay(); return; }
  els.play.textContent = "Pause";
  timer = setInterval(tick, parseInt(els.speed.value, 10));
}

async function rebuild() {
  clearError();
  try {
    if (mode === "single") {
      single = new Timeline(await api("/api/record", { algorithm: els.algo.value, data: currentData }));
    } else {
      const resp = await api("/api/race", { data: currentData });
      race = {};
      for (const name of Object.keys(resp.recordings)) race[name] = new Timeline(resp.recordings[name]);
    }
    render();
  } catch (err) { showError(err); }
}

async function regenerate() {
  stopPlay();
  clearError();
  try {
    const resp = await api("/api/generate", { size: parseInt(els.size.value, 10), fill: els.fill.value });
    currentData = resp.data;
    currentFill = els.fill.value;
    await rebuild();
  } catch (err) { showError(err); }
}

function collectStatsRows() {
  const size = currentData.length;
  if (mode === "single") {
    const s = single.rec;
    return [{ algorithm: els.algo.value, size, fill: currentFill,
              comparisons: s.stats.comparisons, writes: s.stats.writes, time_ms: s.elapsed_ms }];
  }
  return Object.keys(race).map((name) => {
    const s = race[name].rec;
    return { algorithm: name, size, fill: currentFill,
             comparisons: s.stats.comparisons, writes: s.stats.writes, time_ms: s.elapsed_ms };
  });
}

// ---- event wiring ----
els.play.onclick = () => togglePlay();
els.stepFwd.onclick = () => { stopPlay(); mode === "single" ? single.stepForward() : Object.values(race).forEach((t) => t.stepForward()); render(); };
els.stepBack.onclick = () => { stopPlay(); mode === "single" ? single.stepBack() : Object.values(race).forEach((t) => t.stepBack()); render(); };
els.reset.onclick = () => { stopPlay(); mode === "single" ? single.reset() : Object.values(race).forEach((t) => t.reset()); render(); };
els.speed.onchange = () => { if (timer) { stopPlay(); togglePlay(); } };
els.size.onchange = () => regenerate();
els.fill.onchange = () => regenerate();
els.algo.onchange = () => { stopPlay(); rebuild(); };

els["tab-single"].onclick = () => switchMode("single");
els["tab-race"].onclick = () => switchMode("race");

function switchMode(m) {
  stopPlay();
  mode = m;
  els["tab-single"].classList.toggle("active", m === "single");
  els["tab-race"].classList.toggle("active", m === "race");
  els["single-view"].classList.toggle("hidden", m !== "single");
  els["race-view"].classList.toggle("hidden", m !== "race");
  document.querySelectorAll(".single-only").forEach((e) => e.classList.toggle("hidden", m !== "single"));
  rebuild();
}

els.save.onclick = async () => {
  const name = prompt("Save array as (letters/digits/_/- only):");
  if (!name) return;
  clearError();
  try { await api("/api/arrays/" + encodeURIComponent(name), { data: currentData, fill: currentFill }, "PUT"); }
  catch (err) { showError(err); }
};

els.load.onclick = async () => {
  stopPlay();
  clearError();
  try {
    const list = (await api("/api/arrays")).names;
    if (!list.length) { alert("No saved arrays."); return; }
    const name = prompt("Load which array?\n" + list.join(", "), list[0]);
    if (!name) return;
    const body = await api("/api/arrays/" + encodeURIComponent(name));
    currentData = body.data;
    currentFill = body.fill;
    els.size.value = currentData.length;
    if (["random", "reversed", "nearly_sorted"].includes(body.fill)) els.fill.value = body.fill;
    await rebuild();
  } catch (err) { showError(err); }
};

els.export.onclick = async () => {
  clearError();
  try {
    const res = await fetch("/api/export-stats", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ rows: collectStatsRows() }),
    });
    if (!res.ok) {
      let msg = res.status + " " + res.statusText;
      try { const j = await res.json(); if (j.detail) msg = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail); } catch (e) {}
      throw new Error(msg);
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "stats.csv"; a.click();
    URL.revokeObjectURL(url);
  } catch (err) { showError(err); }
};

// ---- boot ----
regenerate();
