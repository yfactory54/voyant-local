from __future__ import annotations

import html
import json
from collections import Counter
from pathlib import Path

from . import analysis
from .corpus import Corpus

_PAGE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
@font-face { font-family:"Source Serif 4"; src:url("fonts/source-serif-4-500.woff2") format("woff2"); font-weight:500; font-display:swap; }
@font-face { font-family:"Source Serif 4"; src:url("fonts/source-serif-4-600.woff2") format("woff2"); font-weight:600; font-display:swap; }
@font-face { font-family:"Source Sans 3"; src:url("fonts/source-sans-3-400.woff2") format("woff2"); font-weight:400; font-display:swap; }
@font-face { font-family:"Source Sans 3"; src:url("fonts/source-sans-3-600.woff2") format("woff2"); font-weight:600; font-display:swap; }
:root {
  color-scheme:light dark;
  --paper:#f2efe8; --panel:#fffdf9; --sunk:#f7f4ee; --ink:#1c1a17; --ink2:#46423c; --muted:#7a746a; --faint:#a8a297;
  --line:#e6e0d4; --line2:#d6cfc1; --accent:#c2410c; --accent-ink:#9a3412; --accent-soft:rgba(194,65,12,.11); --mark:#fbd9b8;
  --serif:"Source Serif 4","Noto Serif KR","AppleMyungjo",Georgia,serif;
  --sans:"Source Sans 3","Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",system-ui,sans-serif;
}
@media (prefers-color-scheme:dark) { :root {
  --paper:#100f0d; --panel:#1a1815; --sunk:#141310; --ink:#f1ece3; --ink2:#cdc6ba; --muted:#9a9387; --faint:#6c665d;
  --line:#2a2622; --line2:#3a352f; --accent:#fb8f55; --accent-ink:#fdba8c; --accent-soft:rgba(251,143,85,.15); --mark:rgba(251,143,85,.34);
} }
* { box-sizing:border-box; }
html,body { margin:0; background:var(--paper); color:var(--ink); }
body { font:15px/1.45 var(--sans); font-variant-numeric:tabular-nums; -webkit-font-smoothing:antialiased; }
button,input { font:inherit; color:inherit; }
button { cursor:pointer; background:none; border:0; padding:0; }
:focus-visible { outline:2px solid var(--accent); outline-offset:2px; border-radius:3px; }
::selection { background:var(--mark); }
.app { max-width:1520px; margin:0 auto; padding:26px 28px 56px; }

.top { display:grid; grid-template-columns:minmax(0,1fr) auto; gap:20px 40px; align-items:end; padding-bottom:20px; border-bottom:1px solid var(--line2); }
.kicker { margin:0 0 8px; color:var(--muted); font-size:14px; }
h1 { margin:0; font:600 clamp(30px,3.4vw,46px)/1 var(--serif); letter-spacing:-.025em; overflow-wrap:anywhere; }
.stats { display:flex; flex-wrap:wrap; margin:18px 0 0; padding:0; list-style:none; }
.stats li { padding:0 22px; border-left:1px solid var(--line2); }
.stats li:first-child { padding-left:0; border-left:0; }
.stats b { display:block; font:600 24px/1.05 var(--serif); letter-spacing:-.01em; }
.stats span { color:var(--muted); font-size:12px; }
.controls { display:flex; flex-wrap:wrap; gap:14px 22px; align-items:flex-end; }
.control { display:grid; gap:6px; font-size:13px; font-weight:600; color:var(--muted); }
.control output { color:var(--ink); font:600 13px/1 var(--sans); }
.control .row { display:flex; align-items:center; gap:10px; }
.search { position:relative; }
.search input { width:220px; height:38px; padding:0 12px 0 34px; border:1px solid var(--line2); border-radius:8px; background:var(--panel); font-size:15px; }
.search input:focus { outline:none; border-color:var(--accent); box-shadow:0 0 0 3px var(--accent-soft); }
.search svg { position:absolute; left:11px; bottom:12px; width:14px; height:14px; stroke:var(--muted); fill:none; stroke-width:2; }
.search small { position:absolute; left:0; top:calc(100% + 4px); color:var(--accent-ink); font-weight:400; white-space:nowrap; }
input[type=range] { -webkit-appearance:none; appearance:none; width:130px; height:20px; background:transparent; }
input[type=range]::-webkit-slider-runnable-track { height:4px; border-radius:2px; background:var(--line2); }
input[type=range]::-webkit-slider-thumb { -webkit-appearance:none; width:16px; height:16px; margin-top:-6px; border-radius:50%; background:var(--panel); border:2px solid var(--accent); }
input[type=range]::-moz-range-track { height:4px; border-radius:2px; background:var(--line2); }
input[type=range]::-moz-range-thumb { width:12px; height:12px; border-radius:50%; background:var(--panel); border:2px solid var(--accent); }

.board { display:grid; grid-template-columns:repeat(12,minmax(0,1fr)); grid-template-rows:318px 318px auto auto; gap:14px; margin-top:18px; }
.panel { position:relative; display:flex; flex-direction:column; min-width:0; min-height:0; background:var(--panel); border:1px solid var(--line); border-radius:6px; overflow:hidden; }
.panel > header { display:flex; align-items:center; justify-content:space-between; gap:12px; min-height:46px; padding:8px 14px 8px 16px; border-bottom:1px solid var(--line); }
.panel h2 { margin:0; display:flex; align-items:baseline; gap:10px; font:600 14px/1 var(--sans); color:var(--ink); white-space:nowrap; }
.panel h2 em { font:400 12px/1 var(--sans); font-style:normal; color:var(--muted); white-space:normal; }
.panel .body { position:relative; flex:1; min-height:0; padding:14px 16px; }
.p-terms { grid-column:1 / 5; grid-row:1 / 3; }
.p-reader { grid-column:5 / 10; grid-row:1 / 3; }
.p-profile { grid-column:10 / 13; grid-row:1; }
.p-profile .body, .p-corr .body { overflow:auto; }
.p-corr { grid-column:10 / 13; grid-row:2; }
.p-trends { grid-column:1 / 8; grid-row:3; }
.p-links { grid-column:8 / 13; grid-row:3; }
.p-contexts { grid-column:1 / 13; grid-row:4; }
.tabs { display:flex; gap:2px; padding:3px; border-radius:8px; background:var(--sunk); border:1px solid var(--line); }
.tabs button { padding:5px 10px; border-radius:6px; font-size:12px; font-weight:600; color:var(--muted); }
.tabs button[aria-pressed=true] { background:var(--panel); color:var(--ink); box-shadow:0 1px 2px rgba(0,0,0,.08); }
svg text { font-family:var(--sans); }
.fill { display:block; width:100%; height:100%; }
.hot { cursor:pointer; }
.hot:hover { opacity:.75; }
.empty { color:var(--muted); font-size:13px; }

.p-terms .body { padding:6px; }
.cloud-word { font-family:var(--serif); font-weight:600; cursor:pointer; transition:opacity .15s; }
.ranked { height:100%; overflow:auto; padding:4px 10px; }
.ranked table { width:100%; border-collapse:collapse; font-size:13px; }
.ranked th { position:sticky; top:0; background:var(--panel); padding:6px 4px; color:var(--muted); font-size:11px; font-weight:600; text-align:left; border-bottom:1px solid var(--line); }
.ranked td { padding:5px 4px; border-bottom:1px solid var(--line); }
.ranked tr { cursor:pointer; }
.ranked tbody tr:hover td { background:var(--sunk); }
.ranked tr[aria-current=true] td { background:var(--accent-soft); }
.ranked .n { color:var(--faint); width:24px; }
.ranked .t { font:600 15px/1 var(--serif); }
.ranked .num { text-align:right; color:var(--ink2); white-space:nowrap; }
.bar { height:6px; border-radius:3px; background:var(--accent); opacity:.75; }

.doc-tabs { display:flex; gap:4px; overflow-x:auto; scrollbar-width:none; }
.doc-tabs button { display:flex; align-items:center; gap:7px; padding:5px 10px; border-radius:7px; font-size:13px; color:var(--muted); white-space:nowrap; }
.doc-tabs button i { width:8px; height:8px; border-radius:50%; flex:none; }
.doc-tabs button small { color:var(--faint); }
.doc-tabs button[aria-pressed=true] { background:var(--sunk); color:var(--ink); box-shadow:inset 0 0 0 1px var(--line2); }
.p-reader .body { display:flex; flex-direction:column; padding:0; }
.docmap { flex:none; padding:10px 16px 8px; border-bottom:1px solid var(--line); background:var(--sunk); }
.docmap .cap { display:flex; justify-content:space-between; margin-bottom:4px; font-size:11px; color:var(--muted); }
.docmap svg { display:block; width:100%; height:52px; overflow:visible; }
.reader { position:relative; flex:1; min-height:0; overflow:auto; padding:18px 28px 40px 56px; font:17px/1.75 var(--serif); white-space:pre-wrap; text-wrap:pretty; color:var(--ink); scroll-behavior:smooth; }
.reader .seg { border-radius:3px; transition:background .2s; }
.reader .seg.on { background:var(--accent-soft); box-shadow:0 0 0 3px var(--accent-soft); }
.reader .sm { position:absolute; left:14px; margin-top:6px; font:600 10px/1 var(--sans); color:var(--faint); letter-spacing:.04em; cursor:pointer; }
.reader .sm.on { color:var(--accent); }
.reader mark { background:var(--mark); color:inherit; border-radius:2px; padding:0 1px; box-shadow:0 1px 0 var(--accent); cursor:pointer; }
.reader mark.focus { background:var(--accent); color:#fff; box-shadow:0 0 0 3px var(--accent-soft); }

.term-head { display:flex; align-items:baseline; justify-content:space-between; gap:10px; }
.term-head b { font:600 38px/1 var(--serif); letter-spacing:-.02em; color:var(--accent-ink); overflow-wrap:anywhere; }
.term-head span { color:var(--muted); font-size:12px; white-space:nowrap; }
.metrics { display:grid; grid-template-columns:repeat(3,1fr); gap:1px; margin:14px 0 12px; background:var(--line); border:1px solid var(--line); border-radius:8px; overflow:hidden; }
.metrics div { padding:8px 10px; background:var(--panel); }
.metrics b { display:block; font:600 18px/1.1 var(--serif); }
.metrics span { color:var(--muted); font-size:11px; }
.docbars { display:grid; gap:7px; }
.docbar { display:grid; grid-template-columns:minmax(0,1fr) 72px; gap:3px 10px; align-items:center; font-size:12px; cursor:pointer; }
.docbar .lbl { display:flex; align-items:center; gap:6px; min-width:0; color:var(--ink2); }
.docbar .lbl i { width:8px; height:8px; border-radius:50%; flex:none; }
.docbar .lbl span { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.docbar .val { text-align:right; color:var(--muted); }
.docbar .track { grid-column:1 / 3; height:6px; border-radius:3px; background:var(--sunk); overflow:hidden; }
.docbar .track div { height:100%; border-radius:3px; }
.section-cap { margin:0 0 8px; color:var(--muted); font-size:12px; font-weight:600; }

.corr { display:grid; gap:3px; }
.corr button { display:grid; grid-template-columns:76px 1fr 1fr 42px; align-items:center; gap:0; height:22px; font-size:12.5px; text-align:left; border-radius:4px; }
.corr button:hover { background:var(--sunk); }
.corr .w { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; font-family:var(--serif); font-weight:600; font-size:14px; }
.corr .neg, .corr .pos { height:10px; display:flex; }
.corr .neg { justify-content:flex-end; border-right:1px solid var(--line2); }
.corr .neg div, .corr .pos div { height:100%; }
.corr .r { text-align:right; color:var(--muted); font-size:12px; }
.corr-axis { display:grid; grid-template-columns:76px 1fr 1fr 42px; font-size:10px; color:var(--faint); margin-bottom:6px; }
.corr-axis span:nth-child(3) { text-align:right; }

.p-trends .body, .p-links .body { padding:10px 14px 12px; }
.p-links .body { display:flex; }
.links-svg { display:block; width:100%; flex:1; min-height:320px; }

.kwic-wrap { max-height:380px; overflow:auto; }
.kwic { width:100%; border-collapse:collapse; font-size:14px; table-layout:fixed; }
.kwic th { position:sticky; top:0; z-index:1; background:var(--panel); padding:8px 10px; color:var(--muted); font-size:11px; font-weight:600; text-align:left; border-bottom:1px solid var(--line2); }
.kwic td { padding:7px 10px; border-bottom:1px solid var(--line); white-space:nowrap; }
.kwic tbody tr { cursor:pointer; }
.kwic tbody tr:hover td { background:var(--sunk); }
.kwic tr.on td { background:var(--accent-soft); }
.kwic .doc { width:180px; color:var(--ink2); overflow:hidden; text-overflow:ellipsis; font-size:12.5px; }
.kwic .doc i { display:inline-block; width:8px; height:8px; border-radius:50%; margin-right:7px; vertical-align:1px; }
.kwic .sg { width:52px; color:var(--faint); font-size:12px; }
.kwic .l { color:var(--muted); font-family:var(--serif); }
.kwic .l div { display:flex; justify-content:flex-end; overflow:hidden; }
.kwic th.k { width:150px; }
.kwic td.k { width:150px; text-align:center; font:600 15px/1 var(--serif); color:var(--accent-ink); }
.kwic .r { overflow:hidden; text-overflow:ellipsis; font-family:var(--serif); color:var(--ink2); }
.kwic th.l { text-align:right; } .kwic th.k { text-align:center; }

.tip { position:fixed; z-index:20; pointer-events:none; max-width:260px; padding:7px 10px; border-radius:7px; background:var(--ink); color:var(--paper); font-size:12px; line-height:1.35; box-shadow:0 8px 20px -8px rgba(0,0,0,.4); opacity:0; transform:translateY(4px); transition:opacity .12s, transform .12s; }
.tip.show { opacity:1; transform:none; }
.tip b { font-weight:600; }
.foot { margin-top:18px; color:var(--faint); font-size:12px; display:flex; justify-content:space-between; gap:20px; flex-wrap:wrap; }

@media (max-width:1180px) {
  .board { grid-template-columns:repeat(2,minmax(0,1fr)); grid-template-rows:auto; }
  .p-terms { grid-column:1; grid-row:auto; height:520px; }
  .p-reader { grid-column:2; grid-row:auto; height:520px; }
  .p-profile, .p-corr { grid-column:auto; grid-row:auto; }
  .p-trends, .p-links, .p-contexts { grid-column:1 / 3; grid-row:auto; }
}
@media (max-width:760px) {
  .app { padding:18px 14px 40px; }
  .top { grid-template-columns:1fr; }
  .stats li { padding:0 14px; } .stats b { font-size:20px; }
  .board { grid-template-columns:1fr; }
  .p-terms, .p-reader, .p-profile, .p-corr, .p-trends, .p-links, .p-contexts { grid-column:1; }
  .p-terms { height:420px; } .p-reader { height:560px; }
  .reader { padding:14px 16px 30px 40px; font-size:16px; }
  .reader .sm { left:8px; }
  .search input { width:100%; } .search { flex:1 1 100%; }
  .kwic .doc, .kwic .sg { display:none; } .kwic th.k, .kwic td.k { width:84px; }
  .links-svg { min-height:300px; }
}
@media (prefers-reduced-motion:reduce) { * { transition:none !important; scroll-behavior:auto !important; } }
</style>
</head>
<body>
<div class="app">
<header class="top">
  <div>
    <p class="kicker">Corpus reading</p>
    <h1>__TITLE__</h1>
    <ul class="stats" id="stats"></ul>
  </div>
  <div class="controls">
    <label class="control search">Term
      <svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="7" cy="7" r="5"/><path d="M11 11l3.5 3.5"/></svg>
      <input id="search" list="vocab" placeholder="Find any word" autocomplete="off" spellcheck="false">
      <small id="search-msg"></small>
    </label>
    <label class="control">Segments <span class="row"><input type="range" id="segments" min="2" max="40"><output id="segments-out"></output></span></label>
    <label class="control">Window &plusmn; <span class="row"><input type="range" id="window" min="1" max="15"><output id="window-out"></output></span></label>
  </div>
  <datalist id="vocab"></datalist>
</header>

<main class="board">
  <section class="panel p-terms">
    <header><h2 id="terms-title">Cirrus</h2>
      <div class="tabs" id="terms-tabs"><button data-view="cirrus">Cirrus</button><button data-view="berry">TermsBerry</button><button data-view="list">Terms</button></div></header>
    <div class="body" id="terms"></div>
  </section>
  <section class="panel p-reader">
    <header><h2>Reader</h2><div class="doc-tabs" id="doc-tabs"></div></header>
    <div class="body">
      <div class="docmap"><div class="cap"><span id="docmap-cap"></span><span id="docmap-legend"></span></div><svg id="docmap"></svg></div>
      <div class="reader" id="reader"></div>
    </div>
  </section>
  <section class="panel p-profile">
    <header><h2>Summary</h2></header>
    <div class="body" id="profile"></div>
  </section>
  <section class="panel p-corr">
    <header><h2>Correlations <em id="corr-hint"></em></h2></header>
    <div class="body" id="corr"></div>
  </section>
  <section class="panel p-trends">
    <header><h2>Trends &amp; Bubblelines <em id="trend-hint"></em></h2></header>
    <div class="body"><div id="trends"></div></div>
  </section>
  <section class="panel p-links">
    <header><h2>Links <em id="links-hint"></em></h2></header>
    <div class="body"><svg class="links-svg" id="links"></svg></div>
  </section>
  <section class="panel p-contexts">
    <header><h2>Contexts <em id="kwic-hint"></em></h2></header>
    <div class="body" style="padding:0"><div class="kwic-wrap"><table class="kwic" id="kwic"></table></div></div>
  </section>
</main>
<footer class="foot" id="foot-settings"></footer>
</div>
<div class="tip" id="tip" role="tooltip"></div>
<script id="data" type="application/json">__DATA__</script>
<script>
"use strict";
const D = JSON.parse(document.getElementById("data").textContent);
const NS = "http://www.w3.org/2000/svg";
const $ = (id) => document.getElementById(id);
const dark = matchMedia("(prefers-color-scheme: dark)");
const PALETTE = { light: ["#2563a8", "#1f8a70", "#b7791f", "#8e44ad", "#c0392b", "#127a96", "#6b7f1a", "#a8326e"], dark: ["#6ea8ec", "#4cc9a4", "#e6b45a", "#c38be0", "#f07a6a", "#4cc3e0", "#b4c95a", "#e47cb0"] };
const docColor = (i) => PALETTE[dark.matches ? "dark" : "light"][i % 8];
const css = (name) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();
const fmt = (n) => Math.round(n).toLocaleString("en-US");
const compact = (n) => n >= 10000 ? (n / 1000).toFixed(n >= 100000 ? 0 : 1) + "k" : fmt(n);
const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
function h(tag, attrs = {}, ...kids) {
  const node = tag.startsWith("svg:") ? document.createElementNS(NS, tag.slice(4)) : document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === null || v === undefined || v === false) continue;
    if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, String(v));
  }
  for (const kid of kids.flat()) if (kid !== null && kid !== undefined) node.append(kid);
  return node;
}
const svg = (tag, attrs, ...kids) => h("svg:" + tag, attrs, ...kids);

// Mirrors voyant.analysis, so slider-driven recomputation matches the CLI reports.
const vocabIndex = new Map(D.vocab.map((t, i) => [t, i]));
const stop = Uint8Array.from(D.stop);
const docs = D.documents.map((d, i) => ({ ...d, i, ids: Int32Array.from(d.ids), off: Int32Array.from(d.offsets), n: d.ids.length }));
const totalTokens = docs.reduce((s, d) => s + d.n, 0);
const corpusRaw = new Int32Array(D.vocab.length);
for (const d of docs) for (const id of d.ids) corpusRaw[id]++;
const topTerms = D.terms.map((t) => vocabIndex.get(t));
const state = { term: topTerms[0] ?? 0, doc: 0, seg: null, focus: null, S: D.settings.segments, W: D.settings.window, view: "cirrus" };
const segOf = (pos, total, S) => total <= 0 ? 0 : Math.min(S - 1, Math.floor(pos * S / total));
const bounds = (total, S) => { const b = [0]; for (let s = 1; s < S; s++) b.push(Math.min(total, Math.ceil(s * total / S))); b.push(total); return b; };
const posCache = new Map();
function positions(id) {
  if (!posCache.has(id)) posCache.set(id, docs.map((d) => { const out = []; for (let i = 0; i < d.n; i++) if (d.ids[i] === id) out.push(i); return out; }));
  return posCache.get(id);
}
function trend(id, d, S) {
  const doc = docs[d]; const b = bounds(doc.n, S); const counts = new Array(S).fill(0);
  for (const p of positions(id)[d]) counts[segOf(p, doc.n, S)]++;
  return counts.map((c, s) => ({ raw: c, rel: b[s + 1] > b[s] ? c / (b[s + 1] - b[s]) : 0 }));
}
const colCache = new Map();
function collocates(id, W) {
  const key = id + ":" + W;
  if (!colCache.has(key)) {
    const counts = new Map();
    docs.forEach((doc, d) => { for (const p of positions(id)[d]) {
      for (let j = Math.max(0, p - W); j < Math.min(doc.n, p + W + 1); j++) {
        if (j === p) continue; const t = doc.ids[j];
        if (!stop[t] && t !== id) counts.set(t, (counts.get(t) || 0) + 1);
      } } });
    colCache.set(key, [...counts].sort((a, b) => b[1] - a[1] || (D.vocab[a[0]] < D.vocab[b[0]] ? -1 : 1)));
  }
  return colCache.get(key);
}
function pearson(xs, ys) {
  const n = xs.length; if (n < 2) return null;
  let mx = 0, my = 0; for (let i = 0; i < n; i++) { mx += xs[i]; my += ys[i]; } mx /= n; my /= n;
  let num = 0, dx = 0, dy = 0;
  for (let i = 0; i < n; i++) { const a = xs[i] - mx, b = ys[i] - my; num += a * b; dx += a * a; dy += b * b; }
  return dx === 0 || dy === 0 ? null : num / Math.sqrt(dx * dy);
}
const segVector = (id) => docs.flatMap((_, d) => trend(id, d, state.S).map((s) => s.rel));
const term = () => D.vocab[state.term];
const select = (id) => { if (id === undefined || id === state.term) return; state.term = id; state.seg = null; state.focus = null; $("search").value = ""; $("search-msg").textContent = ""; render(); };
const openDocument = (d) => { state.doc = d; state.seg = null; state.focus = null; render(); };
const openSegment = (d, s) => { state.doc = d; state.seg = s; state.focus = null; render({ scroll: "seg" }); };
const openHit = (d, pos) => { state.doc = d; state.seg = segOf(pos, docs[d].n, state.S); state.focus = pos; render({ scroll: "focus" }); };

const tip = $("tip");
function showTip(event, htmlText) { tip.innerHTML = htmlText; tip.classList.add("show"); moveTip(event); }
function moveTip(event) { const w = tip.offsetWidth, hh = tip.offsetHeight; let x = event.clientX + 14, y = event.clientY + 14; if (x + w > innerWidth - 8) x = event.clientX - w - 14; if (y + hh > innerHeight - 8) y = event.clientY - hh - 14; tip.style.left = x + "px"; tip.style.top = y + "px"; }
const hideTip = () => tip.classList.remove("show");
function hover(node, fn) { node.addEventListener("pointerenter", (e) => showTip(e, fn())); node.addEventListener("pointermove", moveTip); node.addEventListener("pointerleave", hideTip); return node; }
function actionable(node, fn, label) { node.classList.add("hot"); node.setAttribute("tabindex", "0"); node.setAttribute("role", "button"); if (label) node.setAttribute("aria-label", label); node.addEventListener("click", fn); node.addEventListener("keydown", (e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); fn(); } }); return node; }

$("stats").append(...[
  [D.summary.documents, D.summary.documents === 1 ? "document" : "documents"],
  [fmt(D.summary.tokens), "tokens"], [fmt(D.summary.types), "word types"],
  [(D.summary.types / Math.max(1, D.summary.tokens)).toFixed(3), "type / token"],
  [fmt(D.summary.average_tokens), "tokens per doc"],
].map(([v, l]) => h("li", {}, h("b", { text: String(v) }), h("span", { text: l }))));
$("vocab").append(...D.vocab.filter((_, i) => !stop[i]).slice(0, 400).map((t) => h("option", { value: t })));
const segInput = $("segments"), winInput = $("window");
segInput.value = state.S; winInput.value = state.W;
segInput.addEventListener("input", () => { state.S = Number(segInput.value); state.seg = null; render(); });
winInput.addEventListener("input", () => { state.W = Number(winInput.value); render(); });
$("search").addEventListener("change", (e) => {
  const raw = e.target.value.trim(); if (!raw) return;
  const key = raw.toLowerCase().normalize("NFD").replace(/\p{Mn}/gu, "");
  if (vocabIndex.has(key)) select(vocabIndex.get(key)); else $("search-msg").textContent = `"${raw}" does not occur in this corpus`;
});
$("terms-tabs").addEventListener("click", (e) => { const v = e.target.closest("button")?.dataset.view; if (v) { state.view = v; drawTerms(); } });

const measure = document.createElement("canvas").getContext("2d");
let cloudCache = { key: "", words: [] };
function layoutCloud(w, hgt) {
  const key = w + "x" + hgt;
  if (cloudCache.key === key) return cloudCache.words;
  const items = topTerms.map((id) => ({ id, raw: corpusRaw[id] }));
  const max = items[0]?.raw || 1, big = Math.max(30, Math.min(78, w / 5.2)), small = 12;
  const boxes = [], placed = [];
  for (const [rank, it] of items.entries()) {
    const size = small + (big - small) * Math.pow(it.raw / max, .62);
    measure.font = `600 ${size}px ${css("--serif")}`;
    const tw = measure.measureText(D.vocab[it.id]).width + size * .22, th = size * .98;
    for (let t = 0; t < 4000; t++) {
      const a = t * .21, r = a * 1.25;
      const x = w / 2 + r * Math.cos(a) * 1.35 - tw / 2, y = hgt / 2 + r * Math.sin(a) * .85 - th / 2;
      if (r > Math.max(w, hgt)) break;
      if (x < 4 || y < 4 || x + tw > w - 4 || y + th > hgt - 4) continue;
      if (!boxes.some((b) => x < b[2] && x + tw > b[0] && y < b[3] && y + th > b[1])) { boxes.push([x, y, x + tw, y + th]); placed.push({ ...it, rank, size, x: x + tw / 2, y: y + th / 2 }); break; }
    }
  }
  cloudCache = { key, words: placed };
  return placed;
}
function linkedWeights() {
  const cols = collocates(state.term, state.W); const max = cols[0]?.[1] || 1;
  return new Map(cols.slice(0, 40).map(([id, c]) => [id, c / max]));
}
function drawTerms() {
  const root = $("terms"); root.replaceChildren(); hideTip();
  for (const b of $("terms-tabs").children) b.setAttribute("aria-pressed", String(b.dataset.view === state.view));
  $("terms-title").innerHTML = { cirrus: "Cirrus", berry: "TermsBerry <em>shade = co-occurrence</em>", list: "Terms" }[state.view];
  if (!topTerms.length) { root.append(h("p", { class: "empty", text: "No words outside the stoplist." })); return; }
  if (state.view === "list") return drawRanked(root);
  const w = root.clientWidth, hgt = root.clientHeight;
  const chart = svg("svg", { class: "fill", viewBox: `0 0 ${w} ${hgt}` }); root.append(chart);
  const linked = linkedWeights(), ink = css("--ink"), accent = css("--accent");
  if (state.view === "cirrus") {
    for (const wd of layoutCloud(w, hgt)) {
      const on = wd.id === state.term, link = linked.get(wd.id);
      const node = svg("text", { x: wd.x, y: wd.y, "text-anchor": "middle", "dominant-baseline": "central", class: "cloud-word", "font-size": wd.size.toFixed(1),
        fill: on || link ? accent : ink, "fill-opacity": on ? 1 : link ? (.5 + .45 * link).toFixed(2) : (.92 - .5 * wd.rank / topTerms.length).toFixed(2) });
      node.textContent = D.vocab[wd.id];
      if (on) node.setAttribute("text-decoration", "underline");
      hover(node, () => termTip(wd.id));
      chart.append(actionable(node, () => select(wd.id), D.vocab[wd.id]));
    }
    return;
  }
  // Axial hex coordinates, ring by ring, so the most frequent term sits at the centre.
  const berry = topTerms.slice(0, 37);
  const cells = [[0, 0]];
  for (let ring = 1; cells.length < berry.length; ring++) {
    let q = ring, r = 0; const dirs = [[-1, 1], [-1, 0], [0, -1], [1, -1], [1, 0], [0, 1]];
    for (const [dq, dr] of dirs) for (let k = 0; k < ring; k++) { cells.push([q, r]); q += dq; r += dr; }
  }
  const used = cells.slice(0, berry.length); const rings = Math.max(...used.map(([q, r]) => Math.max(Math.abs(q), Math.abs(r), Math.abs(q + r))));
  const step = Math.min((w - 12) / (2 * rings + 1), (hgt - 12) / (2 * rings * .866 + 1));
  const max = corpusRaw[berry[0]];
  berry.forEach((id, i) => {
    const [q, r] = used[i]; const x = w / 2 + step * (q + r / 2), y = hgt / 2 + step * .866 * r;
    const radius = step / 2 * (.55 + .43 * Math.sqrt(corpusRaw[id] / max));
    const on = id === state.term, link = linked.get(id);
    const g = svg("g", {});
    g.append(svg("circle", { cx: x, cy: y, r: radius, fill: on ? accent : link ? accent : css("--sunk"), "fill-opacity": on ? 1 : link ? (.18 + .62 * link).toFixed(2) : 1, stroke: on ? accent : css("--line2"), "stroke-width": 1 }));
    const fs = Math.max(9, Math.min(radius * .62, (radius * 2.1) / Math.max(3, D.vocab[id].length) * 1.25));
    const label = svg("text", { x, y, "text-anchor": "middle", "dominant-baseline": "central", "font-size": fs.toFixed(1), "font-weight": 600, fill: on ? "#fff" : link && link > .55 ? (dark.matches ? "#1a1815" : "#fff") : ink });
    label.textContent = D.vocab[id]; g.append(label);
    hover(g, () => termTip(id)); chart.append(actionable(g, () => select(id), D.vocab[id]));
  });
}
function termTip(id) {
  const cols = collocates(state.term, state.W); const shared = cols.find(([t]) => t === id);
  return `<b>${esc(D.vocab[id])}</b><br>${fmt(corpusRaw[id])}&times; &middot; ${fmt(corpusRaw[id] / totalTokens * 1e6)} per million` + (id !== state.term ? `<br>${shared ? shared[1] : 0}&times; within &plusmn;${state.W} of <b>${esc(term())}</b>` : "");
}
function drawRanked(root) {
  const wrap = h("div", { class: "ranked" }); const max = corpusRaw[topTerms[0]];
  const tbody = h("tbody");
  topTerms.forEach((id, i) => {
    const counts = docs.map((d) => positions(id)[d.i].length / Math.max(1, d.n));
    const peak = Math.max(...counts, 1e-9);
    const spark = svg("svg", { width: Math.min(90, 16 * docs.length), height: 16, viewBox: `0 0 ${docs.length * 10} 16`, preserveAspectRatio: "none" },
      ...counts.map((c, d) => svg("rect", { x: d * 10 + 1, y: 16 - 15 * c / peak, width: 8, height: Math.max(1, 15 * c / peak), fill: docColor(d) })));
    const tr = h("tr", { "aria-current": String(id === state.term), onclick: () => select(id) },
      h("td", { class: "n", text: String(i + 1) }), h("td", { class: "t", text: D.vocab[id] }),
      h("td", { style: "width:34%" }, h("div", { class: "bar", style: `width:${(corpusRaw[id] / max * 100).toFixed(1)}%` })),
      h("td", { class: "num", text: fmt(corpusRaw[id]) }), h("td", { class: "num" }, spark));
    tbody.append(tr);
  });
  wrap.append(h("table", {}, h("thead", {}, h("tr", {}, h("th", { text: "#" }), h("th", { text: "term" }), h("th", { text: "frequency" }), h("th", { class: "num", text: "count" }), h("th", { class: "num", text: "by doc" }))), tbody));
  root.append(wrap);
}

function drawReader(opts) {
  const tabs = $("doc-tabs"); tabs.replaceChildren();
  docs.forEach((d) => tabs.append(h("button", { "aria-pressed": String(d.i === state.doc), title: d.title, onclick: () => openDocument(d.i) },
    h("i", { style: `background:${docColor(d.i)}` }), d.title.length > 22 ? d.title.slice(0, 21) + "\u2026" : d.title, h("small", { text: String(positions(state.term)[d.i].length) }))));
  const doc = docs[state.doc], S = state.S, b = bounds(doc.n, S), hits = positions(state.term)[doc.i];
  const rows = trend(state.term, doc.i, S), peak = Math.max(...docs.flatMap((_, d) => trend(state.term, d, S).map((s) => s.rel)), 1e-9);
  $("docmap-cap").textContent = `${doc.title} \u00b7 ${fmt(doc.n)} tokens \u00b7 ${hits.length} \u00d7 \u201c${term()}\u201d`;
  $("docmap-legend").textContent = `shared scale`;
  const map = $("docmap"); map.replaceChildren(); const w = map.clientWidth || 600, top = 34;
  map.setAttribute("viewBox", `0 0 ${w} 52`);
  const cw = w / S, color = docColor(doc.i);
  rows.forEach((s, i) => {
    const bh = s.rel / peak * (top - 4); const on = state.seg === i;
    const g = svg("g", {});
    g.append(svg("rect", { x: i * cw, y: 0, width: cw, height: 52, fill: on ? css("--accent-soft") : "transparent" }));
    g.append(svg("rect", { x: i * cw + 2, y: top - bh, width: Math.max(1, cw - 4), height: Math.max(s.raw ? 2 : .5, bh), rx: 2, fill: s.raw ? color : css("--line2") }));
    if (S <= 24 || i % Math.ceil(S / 12) === 0) g.append(Object.assign(svg("text", { x: i * cw + cw / 2, y: 50, "text-anchor": "middle", "font-size": 9.5, fill: on ? css("--accent") : css("--faint") }), { textContent: String(i + 1) }));
    hover(g, () => `<b>\u00a7${i + 1}</b> of ${esc(doc.title)}<br>${s.raw}&times; &middot; ${fmt(s.rel * 1e6)} per million`);
    map.append(actionable(g, () => openSegment(doc.i, i), `segment ${i + 1}`));
  });
  map.append(svg("line", { x1: 0, x2: w, y1: top + 3.5, y2: top + 3.5, stroke: css("--line2") }));
  for (const p of hits) map.append(svg("line", { x1: (p + .5) / doc.n * w, x2: (p + .5) / doc.n * w, y1: top + 1, y2: top + 6, stroke: p === state.focus ? css("--accent") : color, "stroke-width": p === state.focus ? 2.5 : 1.4, "pointer-events": "none" }));

  const reader = $("reader"); const text = doc.text; const start = (k) => k >= doc.n ? text.length : (k === 0 ? 0 : doc.off[2 * k]);
  let out = "", next = 0;
  for (let s = 0; s < S; s++) {
    const from = s === 0 ? 0 : start(b[s]), to = s === S - 1 ? text.length : start(b[s + 1]);
    if (to <= from && s > 0) continue;
    out += `<span class="sm${state.seg === s ? " on" : ""}" data-seg="${s}">\u00a7${s + 1}</span><span class="seg${state.seg === s ? " on" : ""}" data-seg="${s}">`;
    let cur = from;
    while (next < hits.length && doc.off[2 * hits[next]] < to) {
      const p = hits[next], a = doc.off[2 * p], z = doc.off[2 * p + 1];
      out += esc(text.slice(cur, a)) + `<mark data-pos="${p}"${p === state.focus ? ' class="focus"' : ""}>${esc(text.slice(a, z))}</mark>`; cur = z; next++;
    }
    out += esc(text.slice(cur, to)) + "</span>";
  }
  reader.innerHTML = out;
  const target = opts.scroll === "focus" ? reader.querySelector("mark.focus") : opts.scroll === "seg" ? reader.querySelector(".seg.on") : null;
  if (target) reader.scrollTop = Math.max(0, target.offsetTop - reader.clientHeight / 3);
  else if (opts.scroll !== "keep") reader.scrollTop = 0;
}
$("reader").addEventListener("click", (e) => {
  const mark = e.target.closest("mark"); if (mark) return openHit(state.doc, Number(mark.dataset.pos));
  const sm = e.target.closest(".sm"); if (sm) openSegment(state.doc, Number(sm.dataset.seg));
});

function drawProfile() {
  const root = $("profile"); root.replaceChildren();
  const hits = positions(state.term), raw = corpusRaw[state.term], inDocs = hits.filter((p) => p.length).length;
  const perDoc = docs.map((d) => ({ d, raw: hits[d.i].length, ppm: hits[d.i].length / Math.max(1, d.n) * 1e6 }));
  const maxPpm = Math.max(...perDoc.map((x) => x.ppm), 1e-9);
  const rank = topTerms.indexOf(state.term);
  root.append(h("div", { class: "term-head" }, h("b", { text: term() }), h("span", { text: rank >= 0 ? `#${rank + 1} of ${topTerms.length}` : stop[state.term] ? "stopword" : "" })));
  root.append(h("div", { class: "metrics" },
    h("div", {}, h("b", { text: fmt(raw) }), h("span", { text: "occurrences" })),
    h("div", {}, h("b", { text: compact(raw / totalTokens * 1e6) }), h("span", { text: "per million" })),
    h("div", {}, h("b", { text: `${inDocs}/${docs.length}` }), h("span", { text: "documents" }))));
  root.append(h("p", { class: "section-cap", text: "Relative frequency by document" }));
  const bars = h("div", { class: "docbars" });
  for (const x of perDoc) bars.append(h("div", { class: "docbar", onclick: () => openDocument(x.d.i), title: x.d.title },
    h("div", { class: "lbl" }, h("i", { style: `background:${docColor(x.d.i)}` }), h("span", { text: x.d.title })), h("div", { class: "val", text: `${compact(x.ppm)} \u00b7 ${x.raw}\u00d7` }),
    h("div", { class: "track" }, h("div", { style: `width:${(x.ppm / maxPpm * 100).toFixed(1)}%;background:${docColor(x.d.i)}` }))));
  root.append(bars);
}

function drawCorrelations() {
  const root = $("corr"); root.replaceChildren();
  const base = segVector(state.term); const n = base.length;
  $("corr-hint").textContent = `Pearson r over ${n} segments`;
  const scored = topTerms.filter((id) => id !== state.term).map((id) => ({ id, r: pearson(base, segVector(id)) })).filter((x) => x.r !== null);
  if (!scored.length) { root.append(h("p", { class: "empty", text: "Not enough variation across segments to correlate." })); return; }
  const pos = scored.filter((x) => x.r > 0).sort((a, b) => b.r - a.r).slice(0, 5);
  const neg = scored.filter((x) => x.r < 0).sort((a, b) => a.r - b.r).slice(0, 4);
  root.append(h("div", { class: "corr-axis" }, h("span"), h("span", { text: "\u22121 apart" }), h("span", { text: "together +1" }), h("span")));
  const list = h("div", { class: "corr" }); const accent = css("--accent"), cool = dark.matches ? "#6ea8ec" : "#2563a8";
  for (const x of [...pos, ...neg]) {
    const btn = h("button", { onclick: () => select(x.id) }, h("span", { class: "w", text: D.vocab[x.id] }),
      h("span", { class: "neg" }, x.r < 0 ? h("div", { style: `width:${(-x.r * 100).toFixed(1)}%;background:${cool};border-radius:3px 0 0 3px` }) : null),
      h("span", { class: "pos" }, x.r > 0 ? h("div", { style: `width:${(x.r * 100).toFixed(1)}%;background:${accent};border-radius:0 3px 3px 0` }) : null),
      h("span", { class: "r", text: (x.r > 0 ? "+" : "\u2212") + Math.abs(x.r).toFixed(2) }));
    hover(btn, () => `<b>${esc(term())}</b> and <b>${esc(D.vocab[x.id])}</b><br>r = ${x.r.toFixed(3)} across ${n} segments`);
    list.append(btn);
  }
  root.append(list);
}

function drawTrends() {
  const root = $("trends"); root.replaceChildren();
  const S = state.S, w = Math.max(320, root.clientWidth), labelW = w < 560 ? 92 : 150, plotW = w - labelW - 12, rowH = 70, gap = 12;
  $("trend-hint").textContent = `per million tokens, ${S} segments`;
  const series = docs.map((d) => trend(state.term, d.i, S));
  const peak = Math.max(...series.flat().map((s) => s.rel), 1e-9);
  const H = docs.length * (rowH + gap) + 22;
  const chart = svg("svg", { viewBox: `0 0 ${w} ${H}`, width: "100%", height: H, style: "display:block" });
  const x = (s) => labelW + (s + .5) * plotW / S;
  docs.forEach((d, i) => {
    const y0 = i * (rowH + gap), base = y0 + rowH - 18, ampl = rowH - 26, color = docColor(i), rows = series[i];
    const g = svg("g", {});
    g.append(svg("rect", { x: labelW, y: y0, width: plotW, height: rowH, rx: 6, fill: css("--sunk") }));
    if (state.doc === i && state.seg !== null) g.append(svg("rect", { x: labelW + state.seg * plotW / S, y: y0, width: plotW / S, height: rowH, fill: css("--accent-soft") }));
    const title = svg("text", { x: 0, y: y0 + 22, "font-size": 13, "font-weight": 600, fill: css("--ink") }); title.textContent = d.title.length > (labelW < 120 ? 11 : 19) ? d.title.slice(0, labelW < 120 ? 10 : 18) + "\u2026" : d.title;
    const sub = svg("text", { x: 0, y: y0 + 40, "font-size": 11.5, fill: css("--muted") }); sub.textContent = `${positions(state.term)[i].length}\u00d7 \u00b7 ${fmt(d.n)} tok`;
    g.append(title, sub);
    const pts = rows.map((s, k) => [x(k), base - s.rel / peak * ampl]);
    const line = pts.map(([px, py], k) => (k ? "L" : "M") + px.toFixed(1) + " " + py.toFixed(1)).join(" ");
    g.append(svg("path", { d: `${line} L${pts[pts.length - 1][0].toFixed(1)} ${base} L${pts[0][0].toFixed(1)} ${base} Z`, fill: color, "fill-opacity": .16 }));
    g.append(svg("line", { x1: labelW + 6, x2: labelW + plotW - 6, y1: base, y2: base, stroke: css("--line2") }));
    g.append(svg("path", { d: line, fill: "none", stroke: color, "stroke-width": 2, "stroke-linejoin": "round" }));
    pts.forEach(([px, py], k) => { if (rows[k].raw) g.append(svg("circle", { cx: px, cy: py, r: state.doc === i && state.seg === k ? 4.5 : 2.6, fill: color, stroke: css("--panel"), "stroke-width": 1.2 })); });
    const by = y0 + rowH - 8;
    for (const p of positions(state.term)[i]) g.append(svg("circle", { cx: labelW + (p + .5) / d.n * plotW, cy: by, r: p === state.focus ? 4 : 3, fill: p === state.focus ? css("--accent") : color, "fill-opacity": p === state.focus ? 1 : .55, "pointer-events": "none" }));
    rows.forEach((s, k) => {
      const hit = svg("rect", { x: labelW + k * plotW / S, y: y0, width: plotW / S, height: rowH, fill: "transparent" });
      hover(hit, () => `<b>${esc(d.title)}</b> \u00a7${k + 1}<br>${s.raw}&times; \u201c${esc(term())}\u201d &middot; ${fmt(s.rel * 1e6)} per million`);
      g.append(actionable(hit, () => openSegment(i, k), `${d.title} segment ${k + 1}`));
    });
    chart.append(g);
  });
  const axisY = docs.length * (rowH + gap) + 8;
  for (let k = 0; k < S; k++) if (S <= 20 || k % Math.ceil(S / 12) === 0) chart.append(Object.assign(svg("text", { x: x(k), y: axisY, "text-anchor": "middle", "font-size": 10, fill: css("--faint") }), { textContent: "\u00a7" + (k + 1) }));
  const top = svg("text", { x: labelW + plotW, y: axisY + 12, "text-anchor": "end", "font-size": 10, fill: css("--faint") }); top.textContent = `scale peak ${fmt(peak * 1e6)} per million`;
  chart.append(top);
  root.append(chart);
}

function drawLinks() {
  const chart = $("links"); chart.replaceChildren();
  const w = chart.clientWidth || 600, hgt = chart.clientHeight || 360; chart.setAttribute("viewBox", `0 0 ${w} ${hgt}`);
  $("links-hint").textContent = `words within \u00b1${state.W} tokens`;
  const first = collocates(state.term, state.W).slice(0, 9);
  if (!first.length) { chart.append(Object.assign(svg("text", { x: w / 2, y: hgt / 2, "text-anchor": "middle", fill: css("--muted"), "font-size": 13 }), { textContent: "No word shares this window." })); return; }
  const nodes = [{ id: state.term, ring: 0 }], index = new Map([[state.term, 0]]), edges = [];
  for (const [id, c] of first) { index.set(id, nodes.length); nodes.push({ id, ring: 1 }); edges.push([0, index.get(id), c]); }
  for (const [id] of first) for (const [other, c] of collocates(id, state.W).slice(0, 4)) {
    if (other === state.term) continue;
    if (!index.has(other)) { if (nodes.length >= 22) continue; index.set(other, nodes.length); nodes.push({ id: other, ring: 2 }); }
    const a = index.get(id), z = index.get(other);
    if (!edges.some(([p, q]) => (p === a && q === z) || (p === z && q === a))) edges.push([a, z, c]);
  }
  const cx = w / 2, cy = hgt / 2, R = Math.min(w, hgt) * .3;
  nodes.forEach((n, i) => { const a = i * 2.399963; const r = n.ring === 0 ? 0 : n.ring === 1 ? R * .7 : R * 1.3; n.x = cx + Math.cos(a) * r * 1.3; n.y = cy + Math.sin(a) * r; n.vx = 0; n.vy = 0; });
  for (let it = 0; it < 360; it++) {
    const cool = 1 - it / 360;
    for (let i = 0; i < nodes.length; i++) for (let j = i + 1; j < nodes.length; j++) {
      const a = nodes[i], b = nodes[j]; let dx = b.x - a.x, dy = b.y - a.y; const d2 = Math.max(dx * dx + dy * dy, 25), d = Math.sqrt(d2);
      const f = 2600 / d2; dx /= d; dy /= d; a.vx -= dx * f; a.vy -= dy * f; b.vx += dx * f; b.vy += dy * f;
    }
    for (const [p, q] of edges) { const a = nodes[p], b = nodes[q]; const dx = b.x - a.x, dy = b.y - a.y, d = Math.sqrt(dx * dx + dy * dy) || 1; const target = p === 0 ? R * .75 : R * .55; const f = (d - target) * .04; a.vx += dx / d * f; a.vy += dy / d * f; b.vx -= dx / d * f; b.vy -= dy / d * f; }
    for (const n of nodes) { n.vx += (cx - n.x) * .006; n.vy += (cy - n.y) * .009; n.x += n.vx * cool; n.y += n.vy * cool; n.vx *= .55; n.vy *= .55; }
    nodes[0].x = cx; nodes[0].y = cy;
  }
  const pad = 44, xs = nodes.map((n) => n.x), ys = nodes.map((n) => n.y);
  const [x0, x1, y0, y1] = [Math.min(...xs), Math.max(...xs), Math.min(...ys), Math.max(...ys)];
  const sx = Math.min(1.4, (w - pad * 2.6) / Math.max(1, x1 - x0)), sy = Math.min(1.4, (hgt - pad * 1.4) / Math.max(1, y1 - y0)), s = Math.min(sx, sy);
  for (const n of nodes) { n.x = cx + (n.x - cx) * s; n.y = cy + (n.y - cy) * s; }
  const maxC = Math.max(...edges.map((e) => e[2])), maxRaw = Math.max(...nodes.map((n) => corpusRaw[n.id]));
  const accent = css("--accent"), ink = css("--ink"), line = css("--line2");
  for (const [p, q, c] of edges) chart.append(svg("line", { x1: nodes[p].x, y1: nodes[p].y, x2: nodes[q].x, y2: nodes[q].y, stroke: p === 0 ? accent : line, "stroke-opacity": p === 0 ? .25 + .5 * c / maxC : 1, "stroke-width": (1 + 4 * c / maxC).toFixed(2), "stroke-linecap": "round" }));
  const labels = svg("g", { "pointer-events": "none" });
  nodes.slice().reverse().forEach((n) => {
    const r = n.ring === 0 ? 10 : 4 + 9 * Math.sqrt(corpusRaw[n.id] / maxRaw);
    const g = svg("g", {});
    g.append(svg("circle", { cx: n.x, cy: n.y, r, fill: n.ring === 0 ? accent : n.ring === 1 ? css("--panel") : css("--sunk"), stroke: n.ring === 2 ? line : accent, "stroke-width": n.ring === 1 ? 2 : 1 }));
    const right = n.x >= cx - 2;
    const label = svg("text", { x: n.x + (right ? r + 5 : -r - 5), y: n.y, "dominant-baseline": "central", "text-anchor": right ? "start" : "end", "font-size": n.ring === 0 ? 17 : n.ring === 1 ? 13.5 : 12, "font-weight": n.ring === 2 ? 400 : 600, fill: n.ring === 2 ? css("--muted") : ink, style: `font-family:${css("--serif")};paint-order:stroke;stroke:${css("--panel")};stroke-width:4px` });
    label.textContent = D.vocab[n.id]; labels.append(label);
    const edge = edges.find(([p, q]) => p === 0 && q === index.get(n.id));
    hover(g, () => n.ring === 0 ? termTip(n.id) : `<b>${esc(D.vocab[n.id])}</b> ${edge ? `&middot; ${edge[2]}&times; within &plusmn;${state.W} of <b>${esc(term())}</b>` : "&middot; linked through a neighbour"}`);
    chart.append(n.ring === 0 ? g : actionable(g, () => select(n.id), D.vocab[n.id]));
  });
  chart.append(labels);
}

function drawContexts() {
  const table = $("kwic"); table.replaceChildren();
  const W = state.W, rows = [];
  docs.forEach((d) => { for (const p of positions(state.term)[d.i]) rows.push([d, p]); });
  $("kwic-hint").textContent = `${rows.length} \u00d7 \u201c${term()}\u201d, \u00b1${W} tokens`;
  table.append(h("thead", {}, h("tr", {}, h("th", { class: "doc", text: "document" }), h("th", { class: "sg", text: "seg" }), h("th", { class: "l", text: "left" }), h("th", { class: "k", text: "term" }), h("th", { class: "r", text: "right" }))));
  const body = h("tbody"); const clean = (s) => s.replace(/\s+/g, " ");
  for (const [d, p] of rows.slice(0, 400)) {
    const a = d.off[2 * p], z = d.off[2 * p + 1], l = d.off[2 * Math.max(0, p - W)], r = d.off[2 * Math.min(d.n - 1, p + W) + 1];
    const tr = h("tr", { class: d.i === state.doc && p === state.focus ? "on" : null, tabindex: 0, onclick: () => openHit(d.i, p), onkeydown: (e) => { if (e.key === "Enter") openHit(d.i, p); } },
      h("td", { class: "doc", title: d.title }, h("i", { style: `background:${docColor(d.i)}` }), d.title),
      h("td", { class: "sg", text: "\u00a7" + (segOf(p, d.n, state.S) + 1) }),
      h("td", { class: "l" }, h("div", {}, h("span", { text: clean(d.text.slice(l, a)) }))),
      h("td", { class: "k", text: d.text.slice(a, z) }),
      h("td", { class: "r", text: clean(d.text.slice(z, r)) }));
    body.append(tr);
  }
  table.append(body);
}

function render(opts = {}) {
  $("segments-out").value = state.S; $("window-out").value = state.W;
  $("foot-settings").textContent = `${state.S} equal segments per document \u00b7 co-occurrence window \u00b1${state.W} tokens \u00b7 stoplist: ${D.settings.stopwords} \u00b7 per million tokens`;
  drawTerms(); drawReader(opts); drawProfile(); drawCorrelations(); drawTrends(); drawLinks(); drawContexts();
}
let lastWidth = 0, pending = 0;
new ResizeObserver(() => { if (Math.abs(document.body.clientWidth - lastWidth) < 4) return; lastWidth = document.body.clientWidth; cancelAnimationFrame(pending); pending = requestAnimationFrame(() => { cloudCache.key = ""; render({ scroll: "keep" }); }); }).observe(document.body);
dark.addEventListener("change", () => render({ scroll: "keep" }));
render();
document.fonts.ready.then(() => { cloudCache.key = ""; render({ scroll: "keep" }); });
</script>
</body>
</html>
"""


def _utf16_offsets(text: str, offsets: list[tuple[int, int]]) -> list[int]:
    """Flatten offsets into the UTF-16 units JavaScript strings index by."""
    if all(ord(ch) <= 0xFFFF for ch in text):
        return [n for pair in offsets for n in pair]
    units = [0]
    for ch in text:
        units.append(units[-1] + (2 if ord(ch) > 0xFFFF else 1))
    return [units[n] for pair in offsets for n in pair]


def build_view(corpus: Corpus, *, segments: int = 12, window: int = 5, stopwords: str = "en", term_limit: int = 60) -> dict[str, object]:
    if segments < 2:
        raise ValueError("the view needs at least two segments")
    if window < 1:
        raise ValueError("the co-occurrence window must contain at least one token")
    stops = analysis.stopword_set(stopwords)
    totals: Counter[str] = Counter()
    for document in corpus.documents:
        totals.update(document.tokens)
    vocab = [term for term, _raw in sorted(totals.items(), key=lambda item: (-item[1], item[0]))]
    index = {term: position for position, term in enumerate(vocab)}
    terms = analysis.corpus_terms(corpus, stopwords=stopwords, limit=term_limit)
    summary = analysis.summary(corpus)
    return {
        "summary": {"documents": summary.documents, "tokens": summary.tokens, "types": summary.types, "average_tokens": summary.average_tokens},
        "settings": {"segments": segments, "window": window, "stopwords": stopwords},
        "vocab": vocab,
        "stop": [1 if term in stops else 0 for term in vocab],
        "terms": [row.term for row in terms],
        "documents": [
            {
                "title": document.title,
                "text": document.text,
                "ids": [index[token] for token in document.tokens],
                "offsets": _utf16_offsets(document.text, document.offsets),
            }
            for document in corpus.documents
        ],
    }


def render_view(payload: dict[str, object], *, title: str) -> str:
    data = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    page = _PAGE.replace("__TITLE__", html.escape(title)).replace("__DATA__", data)
    if not all(_font_bytes(name) for name in _FONT_FILES):
        return page.replace('src:url("fonts/', 'src:local("')
    return page


_FONT_FILES = (
    "source-sans-3-400.woff2",
    "source-sans-3-600.woff2",
    "source-serif-4-500.woff2",
    "source-serif-4-600.woff2",
)


def _font_bytes(name: str) -> bytes:
    path = Path(__file__).with_name("fonts") / name
    return path.read_bytes() if path.is_file() else b""


def write_view(corpus: Corpus, output: str, *, segments: int = 12, window: int = 5, stopwords: str = "en") -> Path:
    path = Path(output).expanduser()
    payload = build_view(corpus, segments=segments, window=window, stopwords=stopwords)
    page = render_view(payload, title=path.stem)
    _ = path.parent.mkdir(parents=True, exist_ok=True)
    font_dir = path.parent / "fonts"
    for name in (*_FONT_FILES, "OFL.txt"):
        content = _font_bytes(name)
        if content:
            destination = font_dir / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            _ = destination.write_bytes(content)
    _ = path.write_text(page, encoding="utf-8")
    return path
