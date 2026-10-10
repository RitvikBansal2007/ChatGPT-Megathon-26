/* ==========================================================================
   greendash · app.js
   Shared behaviour for every page (vanilla JS, no build step, works on file://).
     1  Utilities and context (persona, pathway, formatting)
     2  Icon sprite (inline SVG symbols, 24 grid, 1.75px stroke)
     3  Theme, backdrop, tab bar, toasts
     4  Overlays: sheets, side panels, modals (scrim, focus trap, Esc)
     5  Tabs, segmented controls, accordions
     6  Engine: status rules, eligibility rules, impact, confidence (mirrors the orchestrator)
     7  Scenario Lab: mutations, diff, cause, invariance
     8  Claim-Check: NUM, FIELD, BAN, VERDICT, METRIC, PRODUCT, IMPLIED
     9  Renderers: badges, verdicts, evidence, impact, Proof Card, tiles, KPI tiles, sheets
     10 Charts: quadrant, funnel, bars, lines, calibration, confusion matrix, data tables
     11 Hydration and boot
   The engine and Claim-Check here are client-side stand-ins for the Python
   engines so the prototype is clickable offline. They never edit a verdict:
   they recompute from inputs only.
   ========================================================================== */
(function () {
  "use strict";
  var GD = (window.GD = window.GD || {});

  /* =============================================== 1 Utilities and context */
  var $ = function (sel, root) { return (root || document).querySelector(sel); };
  var $$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  GD.$ = $; GD.$$ = $$;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  GD.esc = esc;

  var nf = new Intl.NumberFormat("en-GB");
  GD.fmt = {
    num: function (n) { return n == null ? "–" : nf.format(n); },
    pct: function (n, d) { return n == null ? "–" : (n * 100).toFixed(d == null ? 0 : d) + "%"; },
    range: function (lo, hi) { return nf.format(lo) + " to " + nf.format(hi); },
    dec: function (n, d) { return n == null ? "–" : Number(n).toFixed(d == null ? 2 : d); }
  };

  function param(name) {
    try { return new URLSearchParams(window.location.search).get(name); } catch (e) { return null; }
  }
  GD.param = param;

  function store(key, val) {
    try {
      if (val === undefined) return window.sessionStorage.getItem(key);
      window.sessionStorage.setItem(key, val);
    } catch (e) { return null; }
    return val;
  }
  GD.store = store;

  GD.ctx = function () {
    var body = document.body || {};
    var ds = body.dataset || {};
    var p = param("p") || ds.persona || "priya";
    if (!GD.personas[p]) p = "priya";
    var path = param("path") || ds.pathway || "GP01";
    if (!GD.pathways.some(function (x) { return x.id === path; })) path = "GP01";
    return { persona: p, pathway: path };
  };
  GD.persona = function (key) { return GD.personas[key || GD.ctx().persona]; };
  GD.pathway = function (id) { return GD.pathways.filter(function (p) { return p.id === id; })[0]; };
  GD.opp = function (key, gp) { var p = GD.persona(key); return p && p.opp[gp]; };
  GD.withCtx = function (href, key, gp) {
    var q = [];
    if (key) q.push("p=" + encodeURIComponent(key));
    if (gp) q.push("path=" + encodeURIComponent(gp));
    return href + (q.length ? (href.indexOf("?") > -1 ? "&" : "?") + q.join("&") : "");
  };
  function band(p) { return p >= 0.66 ? "HIGH" : p >= 0.4 ? "MEDIUM" : "LOW"; }
  GD.band = band;

  /* Routes: which mobile screen shows a card in a given status */
  GD.routes = {
    mobileCard: function (key, gp) {
      var o = GD.opp(key, gp);
      var page = {
        RECOMMEND: gp === "GP04" ? "paperless-card.html" : "proof-card-recommend.html",
        ABSTAIN: "proof-card-abstain.html",
        REVIEW: "proof-card-review.html",
        RULED_OUT: "proof-card-ruled-out.html",
        SOFT_SURFACE: gp === "GP04" ? "paperless-card.html" : "proof-card-soft-surface.html"
      }[o ? o.status : "SOFT_SURFACE"];
      return GD.withCtx(page, key, gp);
    }
  };

  /* =============================================== 2 Icon sprite */
  var ICONS = {
    "car": '<path d="m21 8-2 2-1.5-3.7A2 2 0 0 0 15.646 5H8.4a2 2 0 0 0-1.903 1.257L5 10 3 8"/><path d="M7 14h.01"/><path d="M17 14h.01"/><rect width="18" height="8" x="3" y="10" rx="2"/><path d="M5 18v2"/><path d="M19 18v2"/><path d="M12 12.5 11 14.5h2l-1 2"/>',
    "home-cut": '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9v11a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V9"/><path d="M9 21v-5a3 3 0 0 1 6 0v5"/><path d="M8 11h8"/>',
    "sun-roof": '<path d="M3 21 12 14l9 7"/><path d="M6 18.7V21"/><path d="M18 18.7V21"/><circle cx="12" cy="7.5" r="2.75"/><path d="M12 2v1"/><path d="M6.5 7.5h-1"/><path d="M18.5 7.5h-1"/><path d="m8.1 3.6.7.7"/><path d="m15.9 3.6-.7.7"/>',
    "sheet-check": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="m9 15 2 2 4-4"/>',
    "check-circle": '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
    "check-circle-fill": '<circle cx="12" cy="12" r="10" fill="currentColor" stroke="currentColor"/><path d="m8.5 12 2.5 2.5 4.5-5" fill="none" style="stroke:var(--surface-1)" stroke-width="2"/>',
    "check": '<path d="M20 6 9 17l-5-5"/>',
    "lightbulb": '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/><path d="M9 18h6"/><path d="M10 22h4"/>',
    "help-circle": '<circle cx="12" cy="12" r="10"/><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/><path d="M12 17h.01"/>',
    "git-compare": '<circle cx="18" cy="18" r="3"/><circle cx="6" cy="6" r="3"/><path d="M13 6h3a2 2 0 0 1 2 2v7"/><path d="M11 18H8a2 2 0 0 1-2-2V9"/>',
    "shield-check": '<path d="M20 13c0 5-3.5 7.5-7.66 8.95a1 1 0 0 1-.67-.01C7.5 20.5 4 18 4 13V6a1 1 0 0 1 1-1c2 0 4.5-1.2 6.24-2.72a1.17 1.17 0 0 1 1.52 0C14.51 3.81 17 5 19 5a1 1 0 0 1 1 1z"/><path d="m9 12 2 2 4-4"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "clipboard-check": '<rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="m9 14 2 2 4-4"/>',
    "gauge": '<path d="m12 14 4-4"/><path d="M3.34 19a10 10 0 1 1 17.32 0"/>',
    "clock": '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    "user": '<path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "receipt": '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
    "chevron-left": '<path d="m15 18-6-6 6-6"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "x": '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "bell": '<path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10.3 21a1.94 1.94 0 0 0 3.4 0"/>',
    "home": '<path d="M15 21v-8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v8"/><path d="M3 10a2 2 0 0 1 .709-1.528l7-5.999a2 2 0 0 1 2.582 0l7 5.999A2 2 0 0 1 21 10v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "grid": '<rect width="7" height="7" x="3" y="3" rx="1.5"/><rect width="7" height="7" x="14" y="3" rx="1.5"/><rect width="7" height="7" x="14" y="14" rx="1.5"/><rect width="7" height="7" x="3" y="14" rx="1.5"/>',
    "trending-up": '<path d="M22 7 13.5 15.5 8.5 10.5 2 17"/><path d="M16 7h6v6"/>',
    "life-buoy": '<circle cx="12" cy="12" r="10"/><path d="m4.93 4.93 4.24 4.24"/><path d="m14.83 9.17 4.24-4.24"/><path d="m14.83 14.83 4.24 4.24"/><path d="m9.17 14.83-4.24 4.24"/><circle cx="12" cy="12" r="4"/>',
    "circle-user": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="10" r="3"/><path d="M7 20.662V19a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v1.662"/>',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    "moon": '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
    "search": '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-left": '<path d="M19 12H5"/><path d="m12 19-7-7 7-7"/>',
    "lock": '<rect width="18" height="11" x="3" y="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "wifi-off": '<path d="M12 20h.01"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/><path d="M5 12.859a10 10 0 0 1 5.17-2.69"/><path d="M19 12.859a10 10 0 0 0-2.007-1.523"/><path d="M2 8.82a15 15 0 0 1 4.177-2.643"/><path d="M22 8.82a15 15 0 0 0-11.288-3.764"/><path d="m2 2 20 20"/>',
    "wifi": '<path d="M12 20h.01"/><path d="M2 8.82a15 15 0 0 1 20 0"/><path d="M5 12.859a10 10 0 0 1 14 0"/><path d="M8.5 16.429a5 5 0 0 1 7 0"/>',
    "battery": '<rect width="16" height="10" x="2" y="7" rx="2" ry="2"/><path d="M22 11v2"/><path d="M6 11v2"/><path d="M10 11v2"/>',
    "signal": '<path d="M2 20h.01"/><path d="M7 20v-4"/><path d="M12 20v-8"/><path d="M17 20V8"/>',
    "refresh": '<path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"/><path d="M21 3v5h-5"/><path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"/><path d="M8 16H3v5"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "phone": '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"/>',
    "message": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "map-pin": '<path d="M20 10c0 4.993-5.539 10.193-7.399 11.799a1 1 0 0 1-1.202 0C9.539 20.193 4 14.993 4 10a8 8 0 0 1 16 0"/><circle cx="12" cy="10" r="3"/>',
    "calendar": '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    "download": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m7 10 5 5 5-5"/><path d="M12 15V3"/>',
    "upload": '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><path d="m17 8-5-5-5 5"/><path d="M12 3v12"/>',
    "sliders": '<path d="M21 4h-7"/><path d="M10 4H3"/><path d="M21 12h-9"/><path d="M8 12H3"/><path d="M21 20h-5"/><path d="M12 20H3"/><path d="M14 2v4"/><path d="M8 10v4"/><path d="M16 18v4"/>',
    "flask": '<path d="M10 2v7.527a2 2 0 0 1-.211.896L4.72 20.55a1 1 0 0 0 .9 1.45h12.76a1 1 0 0 0 .9-1.45l-5.069-10.127A2 2 0 0 1 14 9.527V2"/><path d="M8.5 2h7"/><path d="M7 16h10"/>',
    "file-text": '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/>',
    "bar-chart": '<path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/>',
    "scatter": '<path d="M3 3v18h18"/><circle cx="8" cy="14" r="1.5"/><circle cx="12" cy="9" r="1.5"/><circle cx="17" cy="12" r="1.5"/><circle cx="16" cy="6" r="1.5"/>',
    "scale": '<path d="m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z"/><path d="M7 21h10"/><path d="M12 3v18"/><path d="M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"/>',
    "list": '<path d="M8 6h13"/><path d="M8 12h13"/><path d="M8 18h13"/><path d="M3 6h.01"/><path d="M3 12h.01"/><path d="M3 18h.01"/>',
    "log-out": '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    "plus": '<path d="M5 12h14"/><path d="M12 5v14"/>',
    "minus": '<path d="M5 12h14"/>',
    "menu": '<path d="M4 12h16"/><path d="M4 6h16"/><path d="M4 18h16"/>',
    "eye": '<path d="M2.062 12.348a1 1 0 0 1 0-.696 10.75 10.75 0 0 1 19.876 0 1 1 0 0 1 0 .696 10.75 10.75 0 0 1-19.876 0"/><circle cx="12" cy="12" r="3"/>',
    "eye-off": '<path d="M10.733 5.076a10.744 10.744 0 0 1 11.205 6.575 1 1 0 0 1 0 .696 10.747 10.747 0 0 1-1.444 2.49"/><path d="M14.084 14.158a3 3 0 0 1-4.242-4.242"/><path d="M17.479 17.499a10.75 10.75 0 0 1-15.417-5.151 1 1 0 0 1 0-.696 10.75 10.75 0 0 1 4.446-5.143"/><path d="m2 2 20 20"/>',
    "ladder": '<path d="M8 2v20"/><path d="M16 2v20"/><path d="M8 6h8"/><path d="M8 11h8"/><path d="M8 16h8"/>',
    "external": '<path d="M15 3h6v6"/><path d="M10 14 21 3"/><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/>',
    "link": '<path d="M9 17H7A5 5 0 0 1 7 7h2"/><path d="M15 7h2a5 5 0 1 1 0 10h-2"/><path d="M8 12h8"/>',
    "smartphone": '<rect width="14" height="20" x="5" y="2" rx="2" ry="2"/><path d="M12 18h.01"/>',
    "monitor": '<rect width="20" height="14" x="2" y="3" rx="2"/><path d="M8 21h8"/><path d="M12 17v4"/>',
    "briefcase": '<path d="M16 20V4a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/><rect width="20" height="14" x="2" y="6" rx="2"/>',
    "palette": '<circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z"/>',
    "pause": '<circle cx="12" cy="12" r="10"/><path d="M10 15V9"/><path d="M14 15V9"/>',
    "play": '<path d="M6 3 20 12 6 21Z"/>',
    "settings": '<path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z"/><circle cx="12" cy="12" r="3"/>',
    "accessibility": '<circle cx="16" cy="4" r="1"/><path d="m18 19 1-7-6 1"/><path d="m5 8 3-3 5.5 3-2.36 3.5"/><path d="M4.24 14.5a5 5 0 0 0 6.88 6"/><path d="M13.76 17.5a5 5 0 0 0-6.88-6"/>',
    "fingerprint": '<path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/><path d="M14 13.12c0 2.38 0 6.38-1 8.88"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M2 12a10 10 0 0 1 18-6"/><path d="M2 16h.01"/><path d="M21.8 16c.2-2 .131-5.354 0-6"/><path d="M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2"/><path d="M8.65 22c.21-.66.45-1.32.57-2"/><path d="M9 6.8a6 6 0 0 1 9 5.2v2"/>',
    "mail": '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    "zap-off": '<path d="M10.513 4.856 13.12 2.17a.5.5 0 0 1 .86.46l-1.377 4.317"/><path d="M15.656 10H20a1 1 0 0 1 .78 1.63l-1.72 1.773"/><path d="M16.273 16.273 10.88 21.83a.5.5 0 0 1-.86-.46l1.92-6.02A1 1 0 0 0 11 14H4a1 1 0 0 1-.78-1.63l4.507-4.643"/><path d="m2 2 20 20"/>'
  };
  GD.iconNames = Object.keys(ICONS);
  function mountSprite() {
    if (document.getElementById("gd-sprite")) return;
    var s = '<svg id="gd-sprite" xmlns="http://www.w3.org/2000/svg" style="position:absolute;width:0;height:0;overflow:hidden" aria-hidden="true">';
    for (var k in ICONS) s += '<symbol id="i-' + k + '" viewBox="0 0 24 24">' + ICONS[k] + "</symbol>";
    s += "</svg>";
    document.body.insertAdjacentHTML("afterbegin", s);
  }
  function icon(name, cls, label) {
    return '<svg class="gd-icon' + (cls ? " " + cls : "") + '"' + (label ? ' role="img" aria-label="' + esc(label) + '"' : ' aria-hidden="true" focusable="false"') + '><use href="#i-' + name + '"></use></svg>';
  }
  GD.icon = icon;

  /* =============================================== 3 Theme, backdrop, tab bar, toasts */
  function surfaceKey() { return "gd-theme:" + ((document.body && document.body.dataset.surface) || "hub"); }
  GD.setTheme = function (t, persist) {
    document.documentElement.setAttribute("data-theme", t);
    if (persist) store(surfaceKey(), t);
    $$("[data-gd-theme-toggle]").forEach(function (b) {
      b.setAttribute("aria-pressed", t === "dark" ? "true" : "false");
      b.setAttribute("aria-label", t === "dark" ? "Switch to light theme" : "Switch to dark theme");
      var use = b.querySelector("use");
      if (use) use.setAttribute("href", t === "dark" ? "#i-sun" : "#i-moon");
      var lbl = b.querySelector("[data-gd-theme-label]");
      if (lbl) lbl.textContent = t === "dark" ? "Light" : "Dark";
    });
  };
  function initTheme() {
    var stored = store(surfaceKey());
    var forced = param("theme");
    var t = forced || stored || document.documentElement.getAttribute("data-theme") || "light";
    GD.setTheme(t, !!forced);
    document.addEventListener("click", function (e) {
      var b = e.target.closest("[data-gd-theme-toggle]");
      if (!b) return;
      var cur = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
      GD.setTheme(cur === "dark" ? "light" : "dark", true);
    });
  }

  GD.backdropHTML = function (local) {
    return '<div class="gd-backdrop' + (local ? " is-local" : "") + '" aria-hidden="true"><span class="gd-orb gd-orb--1"></span><span class="gd-orb gd-orb--2"></span><span class="gd-orb gd-orb--3"></span><span class="gd-grain"></span></div>';
  };
  function initBackdrop() {
    if (!$("body > .gd-backdrop")) document.body.insertAdjacentHTML("afterbegin", GD.backdropHTML(false));
    $$(".gd-device__screen").forEach(function (scr) {
      if (!scr.querySelector(":scope > .gd-backdrop")) scr.insertAdjacentHTML("afterbegin", GD.backdropHTML(true));
    });
  }

  /* Mobile bottom tab bar: Home · Pathways · Progress · Help · Profile */
  GD.tabbarHTML = function (current) {
    var tabs = [["home", "home", "Home"], ["pathways", "grid", "Pathways"], ["progress", "trending-up", "Progress"], ["help", "life-buoy", "Help"], ["profile-privacy", "circle-user", "Profile"]];
    var ctx = GD.ctx();
    return '<nav class="gd-tabbar gd-glass-3" aria-label="Main">' + tabs.map(function (t) {
      var cur = t[0] === current;
      return '<a href="' + GD.withCtx(t[0] + ".html", ctx.persona) + '"' + (cur ? ' aria-current="page"' : "") + '><span class="gd-tabbar__ind">' + icon(t[1]) + "</span>" + t[2] + "</a>";
    }).join("") + "</nav>";
  };
  function initTabbar() {
    $$("[data-gd-tabbar]").forEach(function (slot) { slot.outerHTML = GD.tabbarHTML(slot.getAttribute("data-gd-tabbar")); });
  }

  function toastHost() {
    var scope = $(".gd-device__screen") || document.body;
    var host = scope.querySelector(".gd-toast-region");
    if (!host) {
      host = document.createElement("div");
      host.className = "gd-toast-region";
      host.setAttribute("role", "status");
      host.setAttribute("aria-live", "polite");
      scope.appendChild(host);
    }
    return host;
  }
  GD.toast = function (msg, iconName) {
    var host = toastHost();
    var t = document.createElement("div");
    t.className = "gd-toast gd-glass-3";
    t.innerHTML = icon(iconName || "check-circle") + "<span>" + esc(msg) + "</span>";
    host.appendChild(t);
    setTimeout(function () { t.classList.add("is-leaving"); setTimeout(function () { t.remove(); }, 300); }, 4500);
  };

  /* =============================================== 4 Overlays */
  var openStack = [];
  var FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';
  function scrimFor(el) {
    var scope = el.closest(".gd-device__screen") || document.body;
    var s = scope.querySelector(":scope > .gd-scrim");
    if (!s) {
      s = document.createElement("div");
      s.className = "gd-scrim";
      s.setAttribute("aria-hidden", "true");
      scope.appendChild(s);
      s.addEventListener("click", function () { if (openStack.length) GD.close(openStack[openStack.length - 1].el); });
    }
    return s;
  }
  GD.open = function (id, opener) {
    var el = typeof id === "string" ? document.getElementById(id) : id;
    if (!el) return false;
    if (el.classList.contains("is-open")) return true;
    el.classList.add("is-open");
    el.removeAttribute("aria-hidden");
    if (!el.hasAttribute("role")) el.setAttribute("role", "dialog");
    el.setAttribute("aria-modal", "true");
    scrimFor(el).classList.add("is-open");
    openStack.push({ el: el, opener: opener || document.activeElement });
    setTimeout(function () {
      var f = el.querySelector("[data-gd-autofocus]") || el.querySelector(FOCUSABLE);
      if (f) f.focus({ preventScroll: true });
    }, 60);
    el.dispatchEvent(new CustomEvent("gd:open", { bubbles: true }));
    return true;
  };
  GD.close = function (id) {
    var el = typeof id === "string" ? document.getElementById(id) : id;
    if (!el) return;
    el.classList.remove("is-open");
    el.setAttribute("aria-hidden", "true");
    var idx = -1;
    openStack.forEach(function (o, i) { if (o.el === el) idx = i; });
    var rec = idx > -1 ? openStack.splice(idx, 1)[0] : null;
    var scope = el.closest(".gd-device__screen") || document.body;
    var still = openStack.some(function (o) { return (o.el.closest(".gd-device__screen") || document.body) === scope; });
    if (!still) { var s = scope.querySelector(":scope > .gd-scrim"); if (s) s.classList.remove("is-open"); }
    if (rec && rec.opener && rec.opener.focus) rec.opener.focus({ preventScroll: true });
    el.dispatchEvent(new CustomEvent("gd:close", { bubbles: true }));
  };
  function initOverlays() {
    $$(".gd-sheet, .gd-sidepanel, .gd-modal").forEach(function (el) {
      if (!el.classList.contains("is-open") && !el.classList.contains("is-static")) el.setAttribute("aria-hidden", "true");
    });
    document.addEventListener("click", function (e) {
      var o = e.target.closest("[data-gd-open]");
      if (o) {
        e.preventDefault();
        var ok = GD.open(o.getAttribute("data-gd-open"), o);
        if (!ok && o.getAttribute("data-gd-href")) window.location.href = o.getAttribute("data-gd-href");
        return;
      }
      var c = e.target.closest("[data-gd-close]");
      if (c) {
        e.preventDefault();
        var target = c.getAttribute("data-gd-close");
        GD.close(target ? target : c.closest(".gd-sheet, .gd-sidepanel, .gd-modal"));
      }
    });
    document.addEventListener("keydown", function (e) {
      if (!openStack.length) return;
      var top = openStack[openStack.length - 1].el;
      if (e.key === "Escape" && !top.hasAttribute("data-gd-critical")) { e.preventDefault(); GD.close(top); }
      if (e.key === "Tab") {
        var f = $$(FOCUSABLE, top).filter(function (x) { return x.offsetParent !== null; });
        if (!f.length) return;
        var first = f[0], last = f[f.length - 1];
        if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
        else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
      }
    });
    var auto = param("open");
    if (auto) setTimeout(function () { GD.open(auto); }, 120);
    $$("[data-gd-open-on-load]").forEach(function (el) { setTimeout(function () { GD.open(el); }, 120); });
  }

  /* =============================================== 5 Tabs, segmented, accordions */
  function initTabs() {
    $$('[role="tablist"]').forEach(function (list) {
      var tabs = $$('[role="tab"]', list);
      function select(t, focus) {
        tabs.forEach(function (x) {
          var on = x === t;
          x.setAttribute("aria-selected", on ? "true" : "false");
          x.tabIndex = on ? 0 : -1;
          var p = document.getElementById(x.getAttribute("aria-controls"));
          if (p) p.hidden = !on;
        });
        if (focus) t.focus();
        list.dispatchEvent(new CustomEvent("gd:tab", { bubbles: true, detail: { tab: t } }));
      }
      tabs.forEach(function (t, i) {
        t.addEventListener("click", function () { select(t); });
        t.addEventListener("keydown", function (e) {
          var k = e.key, n = null;
          if (k === "ArrowRight") n = tabs[(i + 1) % tabs.length];
          if (k === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
          if (k === "Home") n = tabs[0];
          if (k === "End") n = tabs[tabs.length - 1];
          if (n) { e.preventDefault(); select(n, true); }
        });
      });
      var sel = tabs.filter(function (t) { return t.getAttribute("aria-selected") === "true"; })[0] || tabs[0];
      if (sel) select(sel);
    });
    document.addEventListener("click", function (e) {
      var b = e.target.closest(".gd-seg button[aria-pressed]");
      if (!b) return;
      $$("button[aria-pressed]", b.closest(".gd-seg")).forEach(function (x) { x.setAttribute("aria-pressed", x === b ? "true" : "false"); });
      b.closest(".gd-seg").dispatchEvent(new CustomEvent("gd:seg", { bubbles: true, detail: { value: b.value || b.dataset.value || b.textContent.trim() } }));
    });
  }

  /* =============================================== 6 Engine (mirror of the orchestrator) */
  var W = { completeness: 0.35, recency: 0.15, stability: 0.3, inDist: 0.2 };
  function geo(c) {
    var s = 0;
    for (var k in W) s += W[k] * Math.log(Math.max(0.01, c[k]));
    return Math.exp(s);
  }
  function round(n, step) { return Math.round(n / step) * step; }
  function clone(o) { return JSON.parse(JSON.stringify(o)); }
  GD.clone = clone;

  /* Evaluate one persona's facts. `orig` is the persona's original facts, used
     to rescore propensity when an input that the model reads has changed. */
  GD.engine = {
    evaluate: function (f, orig, personaKey) {
      var out = {};
      GD.pathways.forEach(function (p) { out[p.id] = GD.engine.one(p.id, f, orig || f, personaKey); });
      return out;
    },
    one: function (gp, f, orig, personaKey) {
      var r = { gp: gp, rule: null, eligibility: "PASSED", missing: [], conflict: false, stale: f.staleDays > GD.meta.freshnessDays, rescored: [] };
      var prop = f.base[gp];
      var c = clone((f.confByProduct && f.confByProduct[gp]) || f.conf);

      if (gp === "GP01") {
        if (!f.vehicle) { r.rule = "GP01-R2"; if (orig.vehicle) { prop = 0.05; r.rescored.push("vehicle_on_record"); } }
        else {
          if (f.vehicle.fuel === "bev" && (!orig.vehicle || orig.vehicle.fuel !== "bev")) { prop = Math.round(prop * 38) / 100; r.rescored.push("vehicle_fuel_type"); }
          if (f.vehicle.fuel === "bev") {
            if (f.fuelSpend >= 20 && !f.secondCar) r.conflict = true;
            else if (!f.secondCar) r.rule = "GP01-R1";
          }
          if (!r.rule && f.carFinanceActive) r.rule = "GP01-V1";
          if (f.historyWeeks < 8) r.missing.push("transaction_history");
          if (f.vehicle.mileage == null) r.missing.push("annual_mileage");
        }
      }
      if (gp === "GP02") {
        if (!f.homeowner) { r.rule = "GP02-R1"; if (orig.homeowner) { prop = Math.round(prop * 40) / 100; r.rescored.push("home_ownership"); } }
        else if (f.existingGreenHome) r.rule = "GP02-R2";
        if (f.historyWeeks < 8) r.missing.push("transaction_history");
        if (!f.energy) r.missing.push("gas_kwh");
        else if (!f.epcKnown) r.missing.push("epc_rating");
      }
      if (gp === "GP03") {
        if (!f.homeowner) { r.rule = "GP03-R1"; if (orig.homeowner) { prop = Math.round(prop * 40) / 100; r.rescored.push("home_ownership"); } }
        else if (f.solar) r.rule = "GP03-R2";
        if (f.historyWeeks < 8) r.missing.push("transaction_history");
        if (!f.energy) r.missing.push("electricity_kwh");
        else if (!f.roofKnown) r.missing.push("roof_suitability");
      }
      if (gp === "GP04") {
        if (f.paperNeed) r.rule = "GP04-R2";
        else if (f.digitalShare >= 1) r.rule = "GP04-R1";
      }
      if (r.rule) r.eligibility = GD.rules[r.rule].result;

      /* Confidence components, validated in the eval report; weights tuned on validation only */
      if (r.missing.length) c.completeness = Math.max(0.1, c.completeness - 0.3 * r.missing.length);
      if (r.conflict) c.completeness = Math.max(0.1, c.completeness - 0.25);
      if (r.stale) c.recency = 0.2;
      r.confidence = c;
      r.confidenceOverall = geo(c);
      r.propensity = prop;
      r.likelihood = band(prop);

      /* Status rules, in order (Architecture 1.7) */
      if (r.eligibility === "NOT_ELIGIBLE") r.status = "RULED_OUT";
      else if (r.conflict) r.status = "REVIEW";
      else if (r.missing.length || r.stale) r.status = "ABSTAIN";
      else if (prop >= 0.5 && r.confidenceOverall >= 0.6) r.status = "RECOMMEND";
      else r.status = "SOFT_SURFACE";

      /* Impact from the carbon engine stand-in */
      r.impact = GD.engine.impact(gp, f, r, personaKey);
      r.quality = r.impact.status === "ESTIMATED" || r.impact.status === "PAPER" ? r.impact.quality : null;
      return r;
    },
    impact: function (gp, f, r, personaKey) {
      if (r.status === "RULED_OUT") return { status: "NOT_APPLICABLE" };
      if (r.status === "REVIEW") return { status: "HIDDEN" };
      if (r.status === "ABSTAIN") return { status: "INSUFFICIENT_DATA", missing: r.stale && !r.missing.length ? ["fresh_confirmation"] : r.missing.slice() };
      var authored = personaKey && GD.personas[personaKey] ? GD.personas[personaKey].opp[gp] : null;
      if (gp === "GP01" && f.vehicle && f.vehicle.mileage) {
        var m = f.vehicle.mileage, k = GD.coef;
        return {
          status: "ESTIMATED", family: "co2", unit: "kg CO₂e a year",
          central: round(m * k.evNetKgPerMile, 50), low: round(m * k.evNetKgPerMile * k.rangeLow, 50), high: round(m * k.evNetKgPerMile * k.rangeHigh, 50),
          bills: "About £" + nf.format(round(m * k.evFuelSavingPerMile, 10)) + " a year less on fuel and servicing, central estimate.",
          formula: "Yearly miles × (petrol car factor − EV energy per mile × grid electricity factor)",
          baseline: "Your current " + (f.vehicle.fuel === "diesel" ? "diesel" : "petrol") + " car, same yearly mileage (" + nf.format(m) + " miles, " + (f.vehicle.mileageSource === "declared" ? "you told us" : "estimated from your fuel spend") + ")",
          horizon: "12 months", factor: GD.meta.factorLabel, missing: [],
          quality: f.vehicle.mileageSource === "declared" ? "HIGH" : "MEDIUM"
        };
      }
      if (authored && authored.impact && (authored.impact.status === "ESTIMATED" || authored.impact.status === "PAPER")) {
        var a = clone(authored.impact); a.quality = authored.impactQuality || "MEDIUM"; return a;
      }
      if (gp === "GP04") {
        var sheets = (f.statementsPerYear - f.digitalStatements) * GD.coef.sheetsPerStatement;
        return { status: "PAPER", quality: "HIGH", paper: { value: sheets, unit: "sheets a year" }, digital: { value: Math.round(f.digitalShare * 100) + "%", unit: "of your statements are digital" } };
      }
      return { status: "ESTIMATED", quality: "MEDIUM" };
    }
  };

  /* Self-check: the engine must reproduce every authored status. */
  GD.engine.selfCheck = function () {
    var bad = [];
    GD.personaOrder.forEach(function (k) {
      var res = GD.engine.evaluate(GD.personas[k].facts, GD.personas[k].facts, k);
      GD.pathways.forEach(function (p) {
        if (res[p.id].status !== GD.personas[k].opp[p.id].status) bad.push(k + " " + p.id + ": engine " + res[p.id].status + " vs authored " + GD.personas[k].opp[p.id].status);
      });
    });
    return bad;
  };

  /* =============================================== 7 Scenario Lab */
  GD.mutate = function (facts, ids) {
    var f = clone(facts);
    ids.forEach(function (id) {
      switch (id) {
        case "SET_VEHICLE_BEV":
          f.vehicle = f.vehicle || { ageYears: 1, mileage: null, mileageSource: null };
          f.vehicle.fuel = "bev"; f.fuelSpend = 0; f.carFinanceActive = false; break;
        case "REMOVE_MILEAGE":
          if (f.vehicle) { f.vehicle.mileage = null; f.vehicle.mileageSource = null; } break;
        case "REMOVE_ENERGY":
          f.energy = null; break;
        case "ADD_CONFLICT_FUEL":
          f.vehicle = f.vehicle || { ageYears: 1, mileage: 8000, mileageSource: "declared" };
          f.vehicle.fuel = "bev"; f.fuelSpend = Math.max(f.fuelSpend || 0, 88); f.secondCar = false; f.carFinanceActive = false; break;
        case "MAKE_STALE":
          f.staleDays = (f.staleDays || 0) + 200; break;
        case "SET_RENTER":
          f.homeowner = false; break;
        case "SELL_CAR":
          f.vehicle = null; f.fuelSpend = 0; f.carFinanceActive = false; break;
      }
    });
    return f;
  };

  var MISSING_LABEL = {
    annual_mileage: "yearly mileage", transaction_history: "enough account history", gas_kwh: "gas usage",
    electricity_kwh: "electricity usage", epc_rating: "home energy rating", roof_suitability: "roof suitability",
    fresh_confirmation: "a check that your details are still right"
  };
  GD.missingLabel = function (m) { return MISSING_LABEL[m] || m; };

  function causeFor(before, after) {
    if (after.rule && after.rule !== before.rule && GD.rules[after.rule].result === "NOT_ELIGIBLE") return "Rule " + after.rule + " fired: " + GD.rules[after.rule].text;
    if (after.conflict && !before.conflict) return "Conflict flag set: vehicle record says electric while fuel spend continues";
    if (after.stale && !before.stale) return "Data older than " + GD.meta.freshnessDays + " days: impact hidden until confirmed";
    var newMissing = after.missing.filter(function (m) { return before.missing.indexOf(m) < 0; });
    if (newMissing.length) return "Critical input missing: " + newMissing.join(", ");
    if (after.rescored.length) return "Model rescored: " + after.rescored.join(", ") + " changed";
    if (after.rule && after.rule !== before.rule) return "Rule " + after.rule + ": " + GD.rules[after.rule].text;
    if (before.rule && !after.rule) return "Rule " + before.rule + " no longer applies";
    return "No change";
  }

  GD.lab = {
    run: function (personaKey, ids) {
      var t0 = performance.now();
      var p = GD.personas[personaKey];
      var before = GD.engine.evaluate(p.facts, p.facts, personaKey);
      var mutated = GD.mutate(p.facts, ids);
      var after = GD.engine.evaluate(mutated, p.facts, personaKey);
      var fresh = GD.engine.evaluate(GD.mutate(clone(p.facts), ids), clone(p.facts), personaKey);
      var invariance = JSON.stringify(after) === JSON.stringify(fresh);
      var diff = [];
      GD.pathways.forEach(function (pw) {
        var b = before[pw.id], a = after[pw.id];
        var fields = [
          ["Status", b.status, a.status],
          ["Likelihood", b.likelihood + " (" + b.propensity.toFixed(2) + ")", a.likelihood + " (" + a.propensity.toFixed(2) + ")"],
          ["Eligibility", b.eligibility + (b.rule ? " · " + b.rule : ""), a.eligibility + (a.rule ? " · " + a.rule : "")],
          ["Impact", b.impact.status, a.impact.status],
          ["Confidence", b.confidenceOverall.toFixed(2), a.confidenceOverall.toFixed(2)]
        ];
        fields.forEach(function (fld) {
          if (fld[1] !== fld[2]) diff.push({ product: pw.id, name: pw.name, field: fld[0], from: fld[1], to: fld[2], cause: causeFor(b, a) });
        });
      });
      return { persona: personaKey, mutations: ids, facts: mutated, before: before, after: after, diff: diff, invariance: invariance, elapsedMs: performance.now() - t0 };
    }
  };

  /* =============================================== 8 Claim-Check */
  var NUM_RE = /(£\s?)?\d[\d,]*(?:\.\d+)?\s?(%|kg|tonnes?|t\b|kwh|miles?|sheets?|days?|months?|years?)?/gi;
  function normNum(tok) {
    var unit = (tok.match(/(%|kg|tonnes?|t\b|kwh|miles?|sheets?|days?|months?|years?)\s*$/i) || [""])[0].toLowerCase().trim();
    var n = parseFloat(tok.replace(/[£,\s]|%|kg|tonnes?|t\b|kwh|miles?|sheets?|days?|months?|years?/gi, ""));
    if (isNaN(n)) return null;
    if (unit === "t" || unit === "tonne" || unit === "tonnes") n = n * 1000;
    return Math.round(n * 1000) / 1000;
  }
  function stripChem(s) { return s.replace(/CO[2₂]e?/g, function (m) { return "CO" + "_".repeat(m.length - 2); }); } /* keeps string length so spans line up */

  GD.claim = {
    allowList: function (opp) {
      var bag = [];
      (opp.evidence || []).forEach(function (e) { bag.push(e.label, e.date); });
      if (opp.whyNow) bag.push(opp.whyNow.text, opp.whyNow.date);
      var im = opp.impact || {};
      ["low", "central", "high"].forEach(function (k) { if (im[k] != null) bag.push(String(im[k])); });
      if (im.secondary) ["low", "central", "high"].forEach(function (k) { bag.push(String(im.secondary[k])); });
      bag.push(im.bills || "", im.baseline || "", im.horizon || "");
      if (im.paper) bag.push(String(im.paper.value), im.paper.note || "");
      if (im.digital) bag.push(String(im.digital.value), im.digital.note || "");
      var set = {};
      bag.forEach(function (s) {
        (stripChem(String(s)).match(NUM_RE) || []).forEach(function (t) { var n = normNum(t); if (n != null) set[n] = true; });
      });
      return set;
    },
    check: function (text, personaKey, gp, cited) {
      var opp = GD.opp(personaKey, gp);
      var allow = GD.claim.allowList(opp);
      var src = stripChem(text);
      var violations = [];
      var taken = [];
      function overlaps(a, b) { return taken.some(function (t) { return a < t[1] && b > t[0]; }); }
      function add(rule, start, end, detail) {
        if (overlaps(start, end)) return;
        taken.push([start, end]);
        violations.push({ rule: rule, start: start, end: end, span: text.slice(start, end), detail: detail });
      }
      /* BAN: longest phrases first so "pre-approved" is not also counted as "approved" */
      var banned = GD.redteam.banned.slice().sort(function (a, b) { return b.length - a.length; });
      banned.forEach(function (w) {
        var re = new RegExp("\\b" + w.replace(/[-]/g, "[-\\s]?") + "\\b", "gi"), m;
        while ((m = re.exec(src))) add("BAN", m.index, m.index + m[0].length, "Banned phrase");
      });
      if (opp.eligibility.result !== "PASSED") {
        var re2 = /\b(eligible|you are eligible)\b/gi, m2;
        while ((m2 = re2.exec(src))) add("BAN", m2.index, m2.index + m2[0].length, "'eligible' only when eligibility has passed");
      }
      /* NUM: every numeric token must be in the Evidence Pack allow-list */
      var m3; NUM_RE.lastIndex = 0;
      while ((m3 = NUM_RE.exec(src))) {
        var tok = m3[0].trim();
        if (!/\d/.test(tok)) continue;
        var n = normNum(tok);
        if (n != null && !allow[n]) add("NUM", m3.index, m3.index + m3[0].replace(/\s+$/, "").length, "Not in Evidence Pack allow-list");
      }
      /* VERDICT: no recommending verbs on RULED_OUT or REVIEW */
      if (opp.status === "RULED_OUT" || opp.status === "REVIEW") {
        GD.redteam.recommendingVerbs.concat(["worth exploring", "go for it"]).forEach(function (v) {
          var re = new RegExp("\\b" + v + "\\b", "gi"), m;
          while ((m = re.exec(src))) add("VERDICT", m.index, m.index + m[0].length, "Recommending language on a " + opp.status + " card");
        });
      }
      /* METRIC: Paperless sentences carry no carbon terms */
      if (gp === "GP04") {
        var re4 = /\b(CO__?|carbon|emissions?)\b/gi, m4;
        while ((m4 = re4.exec(src))) add("METRIC", m4.index, m4.index + m4[0].length, "Paperless reports paper and digital adoption only");
      }
      /* PRODUCT: product names must match the catalogue */
      var catalogue = ["EV Finance", "Green Home Loan", "Green Home", "Solar Finance", "Paperless Banking", "Paperless"];
      var re5 = /\b((?:[A-Z][A-Za-z]+ ){1,2}(?:Loan|Finance|Mortgage|Account|Saver))\b/g, m5;
      while ((m5 = re5.exec(text))) {
        var nm = m5[1];
        if (!catalogue.some(function (c) { return nm === c || nm.slice(-(c.length + 1)) === " " + c; })) add("PRODUCT", m5.index, m5.index + m5[0].length, "Not a catalogue product name");
      }
      /* IMPLIED: implied quantities need a backing field */
      var re6 = /\b(halve[sd]?|halving|double[sd]?|doubling|triple[sd]?|\d+\s?x|\d+ times)\b/gi, m6;
      while ((m6 = re6.exec(src))) add("IMPLIED", m6.index, m6.index + m6[0].length, "Implied quantity without a backing field");
      /* FIELD: cited fields must exist in the pack */
      (cited || []).forEach(function (fld) {
        var root = fld.split(".")[0];
        if (["evidence", "impact", "why_now", "eligibility", "catalogue", "policy"].indexOf(root) < 0) violations.push({ rule: "FIELD", span: fld, detail: "Cited field not in the Evidence Pack" });
      });
      violations.sort(function (a, b) { return (a.start || 0) - (b.start || 0); });
      return { text: text, status: violations.length ? "BLOCKED" : "PASS", violations: violations };
    },
    highlight: function (res) {
      var out = "", i = 0;
      res.violations.filter(function (v) { return v.start != null; }).forEach(function (v) {
        out += esc(res.text.slice(i, v.start)) + '<mark class="gd-violation" data-rule="' + v.rule + '" title="' + esc(v.detail) + '">' + esc(res.text.slice(v.start, v.end)) + "</mark>";
        i = v.end;
      });
      return out + esc(res.text.slice(i));
    },
    blockedCount: function (inc) {
      var base = GD.governance.claimsBlocked;
      var extra = parseInt(store("gd-blocked-extra") || "0", 10) || 0;
      if (inc) { extra += inc; store("gd-blocked-extra", String(extra)); }
      return base + extra;
    }
  };

  /* =============================================== 9 Renderers */
  var R = (GD.render = {});

  R.status = function (status, size) {
    var s = GD.statuses[status];
    return '<span class="gd-status gd-status--' + s.cls + (size ? " gd-status--" + size : "") + '">' + icon(s.icon) + esc(s.label) + "</span>";
  };
  R.statusWord = function (status) { return { RECOMMEND: "Recommend", REVIEW: "Review", ABSTAIN: "Abstain", SOFT_SURFACE: "Soft surface", RULED_OUT: "Ruled out" }[status]; };
  R.estimateTag = function () { return '<span class="gd-tag gd-tag--estimate">Estimate</span>'; };

  R.prov = function (source) {
    return source === "declared"
      ? '<span class="gd-prov gd-prov--declared">' + icon("user") + "You told us</span>"
      : '<span class="gd-prov gd-prov--inferred">' + icon("receipt") + "From your transactions</span>";
  };

  R.meter = function (q) {
    var on = GD.quality[q] || 0;
    return '<span class="gd-meter" aria-hidden="true"><i class="' + (on >= 1 ? "is-on" : "") + '"></i><i class="' + (on >= 2 ? "is-on" : "") + '"></i><i class="' + (on >= 3 ? "is-on" : "") + '"></i></span>';
  };

  /* Three separate verdict badges. `opts.sheets` = open sheets (mobile) instead of static chips. */
  R.verdicts = function (opp, opts) {
    opts = opts || {};
    var tag = opts.sheets ? "button" : "div";
    var lk = GD.likelihood[opp.likelihood];
    var el = GD.eligibility[opp.eligibility.result];
    var q = opp.impactQuality;
    function attrs(sheet, label) { return opts.sheets ? ' type="button" data-gd-open="' + sheet + '" aria-label="' + esc(label) + '"' : ""; }
    var h = '<div class="gd-verdicts' + (opts.mini ? " gd-verdicts--mini" : "") + '" role="group" aria-label="Three separate verdicts">';
    h += "<" + tag + ' class="gd-verdict gd-verdict--' + lk.cls + '"' + attrs("sheet-likelihood", "Likelihood: " + lk.label + ". Open details") + '><span class="gd-verdict__head">' + icon("target") + 'Likelihood</span><span class="gd-verdict__value">' + lk.label + '</span><span class="gd-verdict__src">ML model</span></' + tag + ">";
    h += "<" + tag + ' class="gd-verdict gd-verdict--' + el.cls + '"' + attrs("sheet-eligibility", "Eligibility: " + el.label + ". Open details") + '><span class="gd-verdict__head">' + icon("clipboard-check") + 'Eligibility</span><span class="gd-verdict__value">' + el.label + '</span><span class="gd-verdict__src">' + GD.meta.rulesVersion + "</span></" + tag + ">";
    if (q) h += "<" + tag + ' class="gd-verdict gd-verdict--impact"' + attrs("sheet-impact", "Impact quality: " + q.toLowerCase() + ". Open details") + '><span class="gd-verdict__head">' + icon("gauge") + 'Impact quality</span><span class="gd-verdict__row"><span class="gd-verdict__value">' + q.charAt(0) + q.slice(1).toLowerCase() + "</span>" + R.meter(q) + '</span><span class="gd-verdict__src">carbon engine</span></' + tag + ">";
    else h += '<div class="gd-verdict gd-verdict--na"><span class="gd-verdict__head">' + icon("gauge") + 'Impact quality</span><span class="gd-verdict__value">Not estimated</span><span class="gd-verdict__src">carbon engine</span></div>';
    return h + "</div>";
  };

  R.range = function (im, family) {
    var lo = im.low, hi = im.high, mid = im.central;
    var max = hi * 1.15, min = Math.max(0, lo - (hi - lo) * 0.6);
    function pct(v) { return ((v - min) / (max - min)) * 100; }
    return '<div class="gd-range gd-fam-' + (family || im.family || "co2") + '" role="img" aria-label="Range ' + GD.fmt.range(lo, hi) + ", central " + GD.fmt.num(mid) + '"><div class="gd-range__track"><span class="gd-range__band" style="left:' + pct(lo) + "%;width:" + (pct(hi) - pct(lo)) + '%"></span><span class="gd-range__mid" style="left:' + pct(mid) + '%"></span></div><div class="gd-range__labels"><span>Low ' + GD.fmt.num(lo) + "</span><span>Central " + GD.fmt.num(mid) + "</span><span>High " + GD.fmt.num(hi) + "</span></div></div>";
  };

  function unitParts(unit) { var i = unit.indexOf(" "); return [unit.slice(0, i), unit.slice(i + 1)]; }

  R.impactBlock = function (opp, opts) {
    opts = opts || {};
    var im = opp.impact;
    if (!im) return "";
    var openBtn = opts.sheets ? '<button type="button" class="gd-impact__open" data-gd-open="sheet-impact" data-gd-href="' + GD.withCtx("impact-sheet.html", opts.persona, opts.gp) + '">How we worked this out' + icon("chevron-right", "gd-icon--20") + "</button>" : "";
    if (im.status === "ESTIMATED") {
      var u = unitParts(im.unit);
      var h = '<section class="gd-impact" aria-label="Estimated yearly impact"><div class="gd-impact__label"><span>Estimated yearly impact</span>' + R.estimateTag() + "</div>";
      h += '<p class="gd-impact__kpi">' + GD.fmt.range(im.low, im.high) + " <small>" + esc(u[0]) + " " + esc(u[1].replace(" a year", "")) + "</small></p>";
      h += '<p class="gd-impact__bills">' + esc(im.bills || "") + "</p>";
      h += R.range(im, "co2");
      if (im.secondary) h += '<p class="t-label t-muted" style="margin-top:var(--s-2)">Energy, reported separately</p><p class="t-data">' + GD.fmt.range(im.secondary.low, im.secondary.high) + " " + esc(im.secondary.unit) + "</p>" + R.range(im.secondary, "energy");
      if (im.firstStep) h += '<p class="t-body">' + esc(im.firstStep) + "</p>";
      return h + openBtn + "</section>";
    }
    if (im.status === "PAPER") {
      return '<section class="gd-impact" aria-label="Paper and digital, reported separately"><div class="gd-impact__label"><span>Paper and digital, reported separately</span>' + R.estimateTag() + "</div>" +
        '<div class="gd-metrics-pair"><div class="gd-metric gd-fam-paper" style="background:var(--surface-1)"><span class="gd-metric__label"><i class="gd-dot"></i>Paper</span><span class="gd-metric__value">' + GD.fmt.num(im.paper.value) + '</span><span class="t-label t-muted">' + esc(im.paper.unit) + "</span></div>" +
        '<div class="gd-metric gd-fam-digital" style="background:var(--surface-1)"><span class="gd-metric__label"><i class="gd-dot"></i>Digital adoption</span><span class="gd-metric__value">' + esc(im.digital.value) + '</span><span class="t-label t-muted">' + esc(im.digital.unit) + "</span></div></div>" +
        '<p class="t-label t-muted">Digital adoption is tracked separately from carbon. No CO₂e figure is claimed for paperless.</p>' + openBtn + "</section>";
    }
    if (im.status === "INSUFFICIENT_DATA") {
      return '<section class="gd-impact gd-impact--locked" aria-label="Impact not estimated"><div class="gd-impact__label"><span class="gd-row" style="gap:var(--s-2)">' + icon("lock", "gd-icon--16") + "Not enough information to estimate</span></div>" +
        '<span class="gd-skeleton-line" aria-hidden="true"></span><p class="t-body t-muted">We need ' + esc((im.missing || []).map(GD.missingLabel).join(" and ")) + " before we show a number. We never fill the gap with a made-up value.</p></section>";
    }
    if (im.status === "HIDDEN") {
      return '<section class="gd-impact gd-impact--locked" aria-label="Impact hidden"><div class="gd-impact__label"><span class="gd-row" style="gap:var(--s-2)">' + icon("eye-off", "gd-icon--16") + "Impact hidden for now</span></div><p class=\"t-body t-muted\">We'll show an estimate once the mixed signals are cleared up.</p></section>";
    }
    return "";
  };

  R.evidence = function (opp) {
    if (!opp.evidence || !opp.evidence.length) return '<p class="t-muted">No evidence rows for this card.</p>';
    return '<ul class="gd-evidence">' + opp.evidence.map(function (e) {
      return '<li class="gd-evidence__row"><div class="gd-evidence__meta">' + R.prov(e.source) + '<span class="gd-tag gd-tag--code">' + esc(e.code) + '</span></div><p class="gd-evidence__text">' + esc(e.label) + '</p><span class="gd-evidence__date">DATA AS OF ' + esc(e.date).toUpperCase() + "</span></li>";
    }).join("") + "</ul>";
  };

  R.ladderRow = function (opp, opts) {
    if (!opp.ladder) return "";
    opts = opts || {};
    return '<div class="gd-ladder-row">' + icon("ladder") + "<p>" + esc(opp.ladder.prompt) + '</p><button type="button" class="gd-btn gd-btn--ghost gd-btn--sm" data-gd-open="sheet-ladder" data-gd-href="' + GD.withCtx("confidence-ladder-sheet.html", opts.persona, opts.gp) + '">' + esc(opp.ladder.cta) + "</button></div>";
  };

  R.claimStamp = function (opp, opts) {
    opts = opts || {};
    var n = opp.claim.sentences.length;
    var llm = opp.claim.source === "llm";
    return '<button type="button" class="gd-claim-stamp' + (llm ? "" : " gd-claim-stamp--template") + '" data-gd-open="sheet-claim" data-gd-href="' + GD.withCtx("claim-check-sheet.html", opts.persona, opts.gp) + '">' + icon("shield-check") + "<span>" +
      (llm ? "Every statement above was checked against our calculation engine. Tap to see which data backs each sentence." : "Standard summary: same facts, fixed wording, checked against our calculation engine.") +
      '</span><span class="gd-claim-stamp__count">' + (llm ? n + " OF " + n + " VERIFIED" : "STANDARD") + "</span></button>";
  };

  R.confidence = function (c) {
    var rows = [["Data completeness", c.completeness], ["Data recency", c.recency], ["Model stability", c.stability], ["In-distribution", c.inDist]];
    var ov = geo(c);
    return '<div class="gd-conf">' + rows.map(function (r) {
      return '<div class="gd-conf__row"><span>' + r[0] + '</span><span class="gd-conf__bar" role="img" aria-label="' + r[0] + " " + Math.round(r[1] * 100) + '%"><i style="width:' + Math.round(r[1] * 100) + '%"></i></span><span class="t-data t-right">' + r[1].toFixed(2) + "</span></div>";
    }).join("") + '<div class="gd-conf__row gd-conf__row--overall"><span>How sure we are</span><span class="gd-conf__bar"><i style="width:' + Math.round(ov * 100) + '%"></i></span><span class="t-data t-right">' + ov.toFixed(2) + "</span></div></div>";
  };

  R.whyNot = function (opp) {
    if (!opp.whyNot) return "";
    return '<section class="gd-whynot" aria-label="Why not?"><h3 class="gd-whynot__title">' + icon("shield-check", "gd-icon--20") + "Why not?</h3><p>" + esc(opp.whyNot.text) + '</p><p class="t-label t-muted">What would change this: ' + esc(opp.whyNot.change) + '</p><p class="gd-disclaimer">RULE ' + esc(opp.whyNot.rule) + " · " + GD.meta.rulesVersion.toUpperCase() + "</p></section>";
  };

  R.review = function (opp) {
    if (!opp.review) return "";
    var r = opp.review;
    return '<section class="gd-question" aria-label="One confirming question"><p>' + esc(r.message) + '</p><div class="gd-question__facts">' + (opp.evidence || []).map(function (e) {
      return '<div class="gd-row gd-row--wrap" style="gap:var(--s-2)">' + R.prov(e.source) + '<span class="t-body">' + esc(e.label) + '</span><span class="gd-evidence__date">' + esc(e.date).toUpperCase() + "</span></div>";
    }).join("") + '</div><p class="t-h3" style="font-size:16px;line-height:22px">' + esc(r.question) + '</p><div class="gd-options" role="radiogroup" aria-label="' + esc(r.question) + '">' + r.options.map(function (o, i) {
      return '<button type="button" class="gd-option" role="radio" aria-checked="false" data-gd-review-option="' + i + '">' + esc(o) + "</button>";
    }).join("") + '</div><button type="button" class="gd-linkbtn" data-gd-review-skip>Skip for now</button></section>';
  };

  R.feedbackRow = function () {
    return '<div class="gd-proof__feedback" role="group" aria-label="Feedback"><button type="button" data-gd-open="sheet-feedback" data-gd-feedback="not_relevant">Not relevant</button><button type="button" data-gd-open="sheet-feedback" data-gd-feedback="wrong">This is wrong</button><button type="button" data-gd-open="sheet-feedback" data-gd-feedback="remind">Remind me later</button></div>';
  };

  /* Full Proof Card (brand 10.2 anatomy) */
  R.proofCard = function (key, gp, opts) {
    opts = opts || {};
    var opp = GD.opp(key, gp), pw = GD.pathway(gp), st = GD.statuses[opp.status];
    var glass = opp.status === "SOFT_SURFACE" || opp.status === "RULED_OUT" ? "gd-glass-1" : "gd-glass-2";
    var o = { sheets: opts.sheets !== false, persona: key, gp: gp };
    var h = '<article class="gd-proof ' + glass + " gd-proof--" + st.cls + '" aria-labelledby="pc-' + key + "-" + gp + '">';
    h += '<div class="gd-proof__top">' + R.status(opp.status) + '<span class="gd-tag">AS OF ' + esc(GD.meta.asOfShort) + "</span></div>";
    h += '<div class="gd-proof__pathway">' + icon(pw.icon) + esc(pw.name) + "</div>";
    h += '<h2 class="gd-proof__headline" id="pc-' + key + "-" + gp + '">' + esc(opp.headline) + "</h2>";
    if (opp.whyNow) h += '<span class="gd-chip gd-chip--why-now" style="align-self:flex-start">' + icon("clock") + "Why now: " + esc(opp.whyNow.text.charAt(0).toLowerCase() + opp.whyNow.text.slice(1)) + "</span>";

    if (opp.status === "RULED_OUT") {
      h += R.whyNot(opp);
      h += R.verdicts(opp, { sheets: o.sheets });
      h += '<a class="gd-btn gd-btn--ghost gd-btn--block" href="' + GD.withCtx("pathways.html", key) + '">See what else fits' + icon("arrow-right", "gd-icon--20") + "</a>";
    } else {
      h += R.impactBlock(opp, o);
      if (opp.status === "REVIEW") h += R.review(opp);
      h += R.verdicts(opp, { sheets: o.sheets });
      if (opp.status !== "ABSTAIN") h += R.ladderRow(opp, o);
      h += '<details class="gd-accordion"' + (opts.evidenceOpen ? " open" : "") + "><summary>" + "Why you're seeing this" + icon("chevron-down") + '</summary><div class="gd-accordion__body">' + R.evidence(opp) + "</div></details>";
      h += R.claimStamp(opp, o);
      h += '<div class="gd-proof__actions">';
      if (opp.status === "ABSTAIN" && opp.ladder) {
        h += '<button type="button" class="gd-btn gd-btn--primary gd-btn--lg gd-btn--block" data-gd-open="sheet-ladder" data-gd-href="' + GD.withCtx("confidence-ladder-sheet.html", key, gp) + '">' + icon("ladder") + esc(opp.ladder.cta) + "</button>";
        h += '<p class="t-label t-muted t-center">' + esc(opp.ladder.prompt) + "</p>";
      } else if (opp.status === "REVIEW") {
        h += '<p class="t-label t-muted t-center">Answer the question above and we\'ll re-check this card.</p>';
      } else if (opp.status === "SOFT_SURFACE") {
        h += '<a class="gd-btn gd-btn--ghost gd-btn--lg gd-btn--block" href="../web/pathways.html#' + pw.slug + '">Learn more' + icon("arrow-right", "gd-icon--20") + "</a>";
      } else {
        h += '<button type="button" class="gd-btn gd-btn--primary gd-btn--lg gd-btn--block" data-gd-action="primary">' + esc(opp.actions.primary) + "</button>";
        if (opp.actions.secondary) h += '<button type="button" class="gd-btn gd-btn--ghost gd-btn--block" data-gd-action="secondary">' + esc(opp.actions.secondary) + "</button>";
      }
      h += '<a class="gd-btn gd-btn--text gd-proof__human" href="' + GD.withCtx(opts.helpHref || "help.html", key) + '">' + icon("message", "gd-icon--20") + GD.meta.humanPath + "</a></div>";
    }
    h += '<div class="gd-proof__foot"><p class="gd-disclaimer">' + GD.meta.disclaimer.toUpperCase().replace(".", "") + " · " + GD.meta.likelihoodNote.toUpperCase().replace(".", "") + "</p></div>";
    if (opp.status !== "RULED_OUT") h += R.feedbackRow();
    return h + "</article>";
  };

  /* Preview card for the Home feed */
  R.preview = function (key, gp, opts) {
    opts = opts || {};
    var opp = GD.opp(key, gp), pw = GD.pathway(gp), st = GD.statuses[opp.status];
    var glass = opp.status === "RECOMMEND" ? "gd-glass-2" : "gd-glass-1";
    var href = opts.href || GD.routes.mobileCard(key, gp);
    var h = '<a class="gd-preview ' + glass + " is-interactive gd-preview--" + st.cls + '" href="' + href + '">';
    h += '<div class="gd-proof__top">' + R.status(opp.status, "sm") + '<span class="gd-proof__pathway">' + icon(pw.icon) + esc(pw.name) + "</span></div>";
    h += '<p class="gd-preview__headline">' + esc(opp.status === "RULED_OUT" ? opp.whyNot.text : opp.headline) + "</p>";
    if (opp.whyNow) h += '<span class="gd-chip gd-chip--why-now" style="align-self:flex-start">' + icon("clock") + esc(opp.whyNow.text) + "</span>";
    if (!opts.noBadges && opp.status !== "RULED_OUT") h += R.verdicts(opp, { mini: true });
    h += '<span class="gd-preview__go">' + (opp.status === "RULED_OUT" ? "Why not?" : opp.status === "ABSTAIN" ? "Add one detail" : opp.status === "REVIEW" ? "Answer one question" : "See the receipt") + icon("chevron-right", "gd-icon--20") + "</span></a>";
    return h;
  };

  /* Pathway tiles: always four */
  R.tiles = function (key, opts) {
    opts = opts || {};
    var p = GD.persona(key);
    return '<div class="gd-tiles' + (opts.wide ? " gd-tiles--4" : "") + '">' + GD.pathways.map(function (pw) {
      var opp = p.opp[pw.id];
      var quiet = opp.status === "RULED_OUT" || opp.status === "SOFT_SURFACE";
      var line = { RECOMMEND: "Worth exploring: see the receipt", REVIEW: "Mixed signals: one question", ABSTAIN: "Need one detail to estimate", SOFT_SURFACE: "Good to know", RULED_OUT: "Not for you right now" }[opp.status];
      var href = opts.hrefFor ? opts.hrefFor(key, pw.id) : GD.routes.mobileCard(key, pw.id);
      return '<a class="gd-tile ' + (opp.status === "RECOMMEND" ? "gd-glass-2" : "gd-glass-1") + " is-interactive" + (quiet ? " gd-tile--quiet" : "") + '" href="' + href + '"><span class="gd-tile__icon">' + icon(pw.icon) + '</span><span class="gd-tile__name">' + esc(pw.name) + "</span>" + R.status(opp.status, "sm") + '<span class="gd-tile__line">' + line + "</span></a>";
    }).join("") + "</div>";
  };

  /* KPI tile (business): four separate families, estimate vs realised */
  R.kpi = function (k) {
    var est = k.status === "estimate";
    var h = '<article class="gd-kpi gd-glass-2 gd-fam-' + k.family + (est ? " is-estimate" : "") + (k.status === "pending" ? " gd-kpi--pending" : "") + '">';
    h += '<div class="gd-kpi__head"><span class="gd-kpi__name"><i class="gd-dot"></i>' + esc(k.name) + "</span>" + (est ? R.estimateTag() : k.status === "realised" ? '<span class="gd-tag gd-tag--realised">Realised</span>' : '<span class="gd-tag">Pending</span>') + "</div>";
    if (k.status === "pending") h += '<p class="gd-kpi__value">Not yet measurable</p>';
    else if (k.low != null) h += '<p class="gd-kpi__value">' + GD.fmt.num(k.central) + ' <span class="gd-kpi__unit">' + esc(k.unit) + '</span></p><p class="gd-kpi__range">Range ' + GD.fmt.range(k.low, k.high) + " · central estimate</p>";
    else if (k.family === "digital") h += '<p class="gd-kpi__value">' + GD.fmt.pct(k.central) + ' <span class="gd-kpi__unit">' + esc(k.unit) + "</span></p>";
    else h += '<p class="gd-kpi__value">' + GD.fmt.num(k.central) + ' <span class="gd-kpi__unit">' + esc(k.unit) + "</span></p>";
    h += '<p class="t-label t-muted">' + esc(k.note) + "</p>";
    return h + "</article>";
  };

  /* ---------------- Standard sheets mounted next to a Proof Card ---------------- */
  function sheet(id, title, body, opts) {
    opts = opts || {};
    return '<section class="gd-sheet gd-glass-3" id="' + id + '" aria-labelledby="' + id + '-t"><span class="gd-sheet__grab" aria-hidden="true"></span><header class="gd-sheet__head"><h2 class="gd-sheet__title" id="' + id + '-t">' + title + '</h2><button type="button" class="gd-btn gd-btn--icon gd-btn--quiet" data-gd-close aria-label="Close">' + icon("x") + '</button></header><div class="gd-sheet__body">' + body + "</div></section>";
  }
  GD.sheetHTML = sheet;

  R.sheetBodies = {
    evidence: function (key, gp) {
      var opp = GD.opp(key, gp);
      return '<p class="t-muted">Each fact shows where it came from and when. You can correct anything that looks wrong.</p><div class="gd-solid" style="padding:0 var(--s-4)">' + R.evidence(opp) + '</div><button type="button" class="gd-btn gd-btn--ghost gd-btn--block" data-gd-open="sheet-feedback" data-gd-feedback="wrong">' + icon("alert-triangle", "gd-icon--20") + "This is wrong</button>";
    },
    impact: function (key, gp, imOverride) {
      var opp = GD.opp(key, gp), im = imOverride || opp.impact;
      if (!im || (im.status !== "ESTIMATED" && im.status !== "PAPER")) return '<p class="t-body">' + (im && im.status === "HIDDEN" ? "The estimate is hidden until the mixed signals are cleared up." : "Not enough information to estimate. We never show a made-up number.") + "</p>";
      var h = "";
      if (im.status === "ESTIMATED") {
        h += '<div class="gd-impact"><div class="gd-impact__label"><span>Estimated yearly impact</span>' + R.estimateTag() + '</div><p class="gd-impact__kpi">' + GD.fmt.range(im.low, im.high) + ' <small>kg CO₂e</small></p><p class="gd-impact__bills">Central estimate ' + GD.fmt.num(im.central) + " kg CO₂e a year. " + esc(im.bills || "") + "</p>" + R.range(im, "co2") + "</div>";
        if (im.secondary) h += '<div class="gd-impact"><div class="gd-impact__label"><span class="gd-row" style="gap:var(--s-2)"><i class="gd-dot gd-fam-energy"></i>Energy, reported separately</span>' + R.estimateTag() + '</div><p class="t-h3">' + GD.fmt.range(im.secondary.low, im.secondary.high) + " " + esc(im.secondary.unit) + "</p>" + R.range(im.secondary, "energy") + "</div>";
      } else {
        h += R.impactBlock(opp, {});
      }
      h += '<dl class="gd-kv"><dt>Formula</dt><dd>' + esc(im.formula) + "</dd><dt>Baseline</dt><dd>" + esc(im.baseline) + "</dd><dt>Time horizon</dt><dd>" + esc(im.horizon) + '</dd><dt>Factor source</dt><dd class="t-mono">' + esc(im.factor) + "</dd></dl>";
      if (im.firstStep) h += '<p class="t-body"><strong>Staged, not overwhelming.</strong> ' + esc(im.firstStep) + "</p>";
      h += '<p class="gd-banner"><span class="gd-tag">Estimate</span>' + GD.meta.estimateLabel + " Calculated by the carbon engine, never by the AI. Avoided emissions are never netted against the bank's own footprint.</p>";
      return h;
    },
    claim: function (key, gp) {
      var opp = GD.opp(key, gp);
      var llm = opp.claim.source === "llm";
      var h = '<p class="t-muted">' + (llm ? "The AI wrote these sentences from structured results only. Each one was checked against the engine before you saw it." : "This card uses a standard summary: the same facts in fixed wording.") + '</p><ol class="gd-claim-list">';
      opp.claim.sentences.forEach(function (s, i) {
        h += '<li class="gd-claim-item"><p><span class="gd-claim-sent" data-gd-claim-sent="' + i + '">' + esc(s.text) + '</span><span class="gd-claim-check">' + icon("check", "gd-icon--16") + '</span></p><div class="gd-claim-fields">' + s.fields.map(function (f) { return '<span class="gd-tag gd-tag--code">' + esc(f) + "</span>"; }).join("") + "</div></li>";
      });
      return h + '</ol><p class="gd-disclaimer">CHECKS: NUMBERS · CITED FIELDS · BANNED PHRASES · VERDICT · METRIC · PRODUCT · IMPLIED QUANTITIES</p>';
    },
    likelihood: function (key, gp) {
      var opp = GD.opp(key, gp);
      var c = opp.confidence || GD.persona(key).facts.conf;
      return '<div class="gd-verdict gd-verdict--' + GD.likelihood[opp.likelihood].cls + '"><span class="gd-verdict__head">' + icon("target") + 'Likelihood</span><span class="gd-verdict__value">' + GD.likelihood[opp.likelihood].label + "</span></div>" +
        '<p class="t-body">How likely this suits you, from patterns in your own data. Shown as High, Medium or Low, never as a score.</p><h3 class="t-label t-muted">How sure we are</h3>' + R.confidence(c) +
        '<p class="gd-banner">' + icon("info") + "Likelihood is not creditworthiness, and it is not a credit decision.</p>";
    },
    eligibility: function (key, gp) {
      var opp = GD.opp(key, gp), el = GD.eligibility[opp.eligibility.result], rule = opp.eligibility.rule;
      return '<div class="gd-verdict gd-verdict--' + el.cls + '"><span class="gd-verdict__head">' + icon("clipboard-check") + 'Eligibility</span><span class="gd-verdict__value">' + el.label + '</span><span class="gd-verdict__src">Checked by product rules (' + GD.meta.rulesVersion + ")</span></div>" +
        (rule ? '<p class="t-body">' + esc(GD.rules[rule].text) + '</p><p class="gd-disclaimer">RULE ' + esc(rule) + "</p>" : '<p class="t-body">Product rules found nothing that rules this out for you.</p>') +
        '<p class="gd-banner">' + icon("info") + "Product rules decide eligibility, never the AI. Not a credit decision: the bank's own checks still apply.</p>";
    },
    ladder: function (key, gp) {
      var opp = GD.opp(key, gp), l = opp.ladder;
      if (!l) return '<p class="t-body">Nothing missing for this card.</p>';
      var rungs = '<div class="gd-ladder" aria-label="Impact quality ladder"><span class="gd-ladder__rung' + (opp.impactQuality ? " is-reached" : "") + '">' + icon("gauge", "gd-icon--20") + 'Low</span><span class="gd-ladder__rung' + (opp.impactQuality === "MEDIUM" || opp.impactQuality === "HIGH" ? " is-reached" : " is-next") + '" data-gd-rung="MEDIUM">' + icon("gauge", "gd-icon--20") + 'Medium</span><span class="gd-ladder__rung' + (opp.impactQuality === "HIGH" ? " is-reached" : opp.impactQuality === "MEDIUM" ? " is-next" : "") + '" data-gd-rung="HIGH">' + icon("gauge", "gd-icon--20") + "High</span></div>";
      var input = "";
      if (l.input.type === "number") {
        input = '<form class="gd-stack" data-gd-ladder-form novalidate><div class="gd-field"><label for="ladder-in">Yearly mileage</label><div class="gd-input-unit"><input class="gd-input" id="ladder-in" name="value" inputmode="numeric" placeholder="' + esc(l.input.placeholder) + '" data-gd-autofocus aria-describedby="ladder-hint ladder-err"><span>' + esc(l.input.unit) + '</span></div><p class="gd-field__hint" id="ladder-hint">Your MOT certificate shows recent mileage.</p><p class="gd-field__error" id="ladder-err" hidden></p></div><button class="gd-btn gd-btn--primary gd-btn--lg gd-btn--block" type="submit">Update my estimate</button></form>';
      } else if (l.input.type === "choice") {
        input = '<div class="gd-stack" data-gd-ladder-choice>' + (l.question ? '<p class="t-subtitle">' + esc(l.question) + "</p>" : "") + '<div class="gd-options" role="radiogroup">' + l.input.options.map(function (o, i) { return '<button type="button" class="gd-option" role="radio" aria-checked="false" data-gd-choice="' + i + '">' + esc(o) + "</button>"; }).join("") + "</div></div>";
      } else {
        input = '<div class="gd-stack"><button type="button" class="gd-btn gd-btn--primary gd-btn--lg gd-btn--block" data-gd-ladder-upload>' + icon("upload") + "Upload a bill</button><p class=\"t-label t-muted\">We read the yearly kWh only. The file is encrypted and never sent to the AI.</p></div>";
      }
      return '<p class="t-body">' + esc(l.prompt) + "</p>" + rungs + input + '<div data-gd-ladder-result aria-live="polite"></div>';
    },
    feedback: function () {
      return '<p class="t-muted">Your choice changes when and how we show this card. It never changes the likelihood, eligibility or impact numbers.</p>' +
        '<div class="gd-options" role="radiogroup" aria-label="Feedback">' +
        '<button type="button" class="gd-option" role="radio" aria-checked="false" data-gd-fb="not_relevant">' + icon("eye-off", "gd-icon--20") + "Not relevant to me</button>" +
        '<button type="button" class="gd-option" role="radio" aria-checked="false" data-gd-fb="wrong">' + icon("alert-triangle", "gd-icon--20") + "This is wrong</button>" +
        '<button type="button" class="gd-option" role="radio" aria-checked="false" data-gd-fb="remind">' + icon("calendar", "gd-icon--20") + "Remind me later</button></div>" +
        '<div class="gd-field" data-gd-fb-wrong hidden><label for="fb-reason">What looks wrong?</label><select class="gd-select" id="fb-reason"><option>My fuel spend</option><option>My vehicle</option><option>My home</option><option>My energy use</option><option>Something else</option></select><p class="gd-field__hint">Stored encrypted. Never sent to the AI.</p></div>' +
        '<button type="button" class="gd-btn gd-btn--primary gd-btn--lg gd-btn--block" data-gd-fb-submit disabled>Send feedback</button>';
    }
  };

  /* Mount every standard sheet for one card into a container (phone screen or body) */
  GD.mountSheets = function (container, key, gp, which) {
    which = which || ["evidence", "impact", "claim", "likelihood", "eligibility", "ladder", "feedback"];
    var titles = { evidence: "Why you're seeing this", impact: "Impact calculation", claim: "Claim-Check", likelihood: "Likelihood", eligibility: "Eligibility", ladder: "Confidence Ladder", feedback: "Feedback" };
    var html = which.map(function (w) { return sheet("sheet-" + w, titles[w], R.sheetBodies[w](key, gp)); }).join("");
    container.insertAdjacentHTML("beforeend", html);
    $$(".gd-sheet", container).forEach(function (s) { if (!s.classList.contains("is-open")) s.setAttribute("aria-hidden", "true"); });
  };

  /* Sheet behaviours: Claim-Check animation, ladder input, feedback, review options */
  function initCardBehaviours() {
    document.addEventListener("gd:open", function (e) {
      var el = e.target;
      if (el.id === "sheet-claim" || el.hasAttribute("data-gd-claim-animate")) {
        $$(".gd-claim-sent", el).forEach(function (s, i) {
          s.classList.remove("is-pass");
          setTimeout(function () { s.classList.add("is-pass"); }, 200 + i * 260);
        });
      }
    });
    document.addEventListener("submit", function (e) {
      var form = e.target.closest("[data-gd-ladder-form]");
      if (!form) return;
      e.preventDefault();
      var ctx = GD.ctx();
      var input = form.querySelector("input");
      var err = form.querySelector(".gd-field__error");
      var v = parseInt(String(input.value).replace(/[^\d]/g, ""), 10);
      if (isNaN(v) || v <= 0 || v > 100000) {
        input.setAttribute("aria-invalid", "true");
        err.hidden = false;
        err.innerHTML = icon("alert-triangle", "gd-icon--16") + "Enter a yearly mileage between 1 and 100,000 miles.";
        return;
      }
      input.removeAttribute("aria-invalid"); err.hidden = true;
      var f = clone(GD.persona(ctx.persona).facts);
      if (f.vehicle) { f.vehicle.mileage = v; f.vehicle.mileageSource = "declared"; }
      f.historyWeeks = Math.max(f.historyWeeks, 8);
      var res = GD.engine.one(ctx.pathway, f, GD.persona(ctx.persona).facts, ctx.persona);
      ladderResult(form.closest(".gd-sheet__body") || form.parentNode, res.impact, res.quality || "HIGH", ctx);
    });
    document.addEventListener("click", function (e) {
      var ch = e.target.closest("[data-gd-choice]");
      if (ch) {
        var group = ch.closest(".gd-options");
        $$(".gd-option", group).forEach(function (x) { x.setAttribute("aria-checked", x === ch ? "true" : "false"); });
        var ctx = GD.ctx(), opp = GD.opp(ctx.persona, ctx.pathway);
        var body = ch.closest(".gd-sheet__body") || ch.closest("[data-gd-ladder-host]") || document.body;
        var idx = +ch.getAttribute("data-gd-choice");
        var last = opp.ladder.input.options.length - 1;
        if (idx === last || /north|not sure/i.test(ch.textContent)) {
          var out = $("[data-gd-ladder-result]", body);
          out.innerHTML = '<div class="gd-banner gd-banner--warning">' + icon("help-circle") + "<span>We'll keep this as \"Need one thing\" for now. A photo of a recent bill or a quick roof check from an installer would let us estimate it.</span></div>";
        } else if (opp.ladderResult) {
          ladderResult(body, opp.ladderResult.impact, opp.ladderResult.impactQuality, ctx);
        } else {
          ladderResult(body, null, "MEDIUM", ctx);
        }
        return;
      }
      if (e.target.closest("[data-gd-ladder-upload]")) {
        GD.toast("Bill received. We'll read the yearly kWh only.", "upload");
        return;
      }
      var ro = e.target.closest("[data-gd-review-option]");
      if (ro) {
        var g = ro.closest(".gd-options");
        $$(".gd-option", g).forEach(function (x) { x.setAttribute("aria-checked", x === ro ? "true" : "false"); });
        var sec = ro.closest(".gd-question");
        var msg = sec.querySelector("[data-gd-review-msg]") || document.createElement("div");
        msg.setAttribute("data-gd-review-msg", "");
        msg.className = "gd-banner gd-banner--info";
        msg.setAttribute("role", "status");
        var i = +ro.getAttribute("data-gd-review-option");
        msg.innerHTML = icon("refresh") + "<span>" + (i === 0 ? "Thanks. With a second car on record, we'll re-run this card for the petrol car." : i === 1 ? "Thanks. Plug-in hybrids still use fuel, so we'll re-run this card with that in mind." : i === 2 ? "Thanks. We'll ask you to confirm your vehicle record before we re-check." : "No problem. The card stays as \"Mixed signals\" and a person can help if you'd like.") + "</span>";
        sec.appendChild(msg);
        return;
      }
      if (e.target.closest("[data-gd-review-skip]")) { GD.toast("Skipped. The impact estimate stays hidden for now.", "info"); return; }
      var fbOpen = e.target.closest("[data-gd-feedback]");
      if (fbOpen) {
        setTimeout(function () {
          var target = $('[data-gd-fb="' + fbOpen.getAttribute("data-gd-feedback") + '"]');
          if (target) target.click();
        }, 80);
      }
      var fb = e.target.closest("[data-gd-fb]");
      if (fb) {
        var grp = fb.closest(".gd-options");
        $$(".gd-option", grp).forEach(function (x) { x.setAttribute("aria-checked", x === fb ? "true" : "false"); });
        var host = fb.closest(".gd-sheet__body");
        var wrong = $("[data-gd-fb-wrong]", host);
        if (wrong) wrong.hidden = fb.getAttribute("data-gd-fb") !== "wrong";
        var sub = $("[data-gd-fb-submit]", host);
        if (sub) sub.disabled = false;
        return;
      }
      if (e.target.closest("[data-gd-fb-submit]")) {
        var sh = e.target.closest(".gd-sheet, .gd-modal, .gd-sidepanel");
        if (sh) GD.close(sh);
        GD.toast("Thanks. We'll adjust when and how we show this card.");
        return;
      }
      var act = e.target.closest("[data-gd-action]");
      if (act) {
        GD.toast(act.getAttribute("data-gd-action") === "primary" ? "Opening the next step. Nothing is submitted without your confirmation." : "Suitability check started: 3 to 5 questions.", "arrow-right");
      }
    });
  }
  function ladderResult(host, im, quality, ctx) {
    var out = $("[data-gd-ladder-result]", host) || host;
    $$("[data-gd-rung]", host).forEach(function (r) {
      var q = r.getAttribute("data-gd-rung");
      r.classList.toggle("is-reached", GD.quality[q] <= GD.quality[quality]);
      r.classList.remove("is-next");
    });
    if (!im || im.status !== "ESTIMATED") { out.innerHTML = '<div class="gd-banner gd-banner--success">' + icon("check-circle") + "<span>Thanks. Impact quality is now " + quality.toLowerCase() + ".</span></div>"; return; }
    out.innerHTML = '<div class="gd-impact" style="background:var(--surface-1)"><div class="gd-impact__label"><span>Your updated estimate</span>' + R.estimateTag() + '</div><p class="gd-impact__kpi">' + GD.fmt.range(im.low, im.high) + ' <small>kg CO₂e</small></p><p class="gd-impact__bills">' + esc(im.bills || "") + "</p>" + R.range(im, "co2") + '<p class="t-label t-muted">Impact quality is now ' + quality.toLowerCase() + ". " + GD.meta.estimateLabel + "</p></div>";
    GD.toast("Estimate updated. Impact quality: " + quality.toLowerCase() + ".", "gauge");
  }

  /* =============================================== 10 Charts */
  var C = (GD.charts = {});
  function svgOpen(w, h, label) { return '<svg class="gd-chart" viewBox="0 0 ' + w + " " + h + '" role="img" aria-label="' + esc(label) + '" preserveAspectRatio="xMidYMid meet">'; }

  C.dataTable = function (headers, rows, caption) {
    return '<details class="gd-chart-alt"><summary>' + icon("list", "gd-icon--16") + 'Show data table</summary><div class="gd-table-wrap" style="margin-top:var(--s-2)"><table class="gd-table gd-table--compact">' + (caption ? "<caption>" + esc(caption) + "</caption>" : "") + "<thead><tr>" + headers.map(function (h, i) { return "<th" + (i ? ' class="num"' : "") + ">" + esc(h) + "</th>"; }).join("") + "</tr></thead><tbody>" +
      rows.map(function (r) { return "<tr>" + r.map(function (c, i) { return "<td" + (i ? ' class="num"' : "") + ">" + esc(c) + "</td>"; }).join("") + "</tr>"; }).join("") + "</tbody></table></div></details>";
  };

  /* Opportunity quadrant: x = propensity, y = estimated impact per customer (whisker = range),
     circle area = cohort size, opacity = confidence, dashed amber outline = low confidence. */
  C.quadrant = function (el, gp, opts) {
    opts = opts || {};
    var all = GD.portfolio.cohorts[gp];
    var cs = all.filter(function (c) { return !c.suppressed; });
    var hidden = all.length - cs.length;
    var w = 720, h = 420, L = 64, B = 48, T = 24, Rr = 24;
    var maxY = Math.max.apply(null, cs.map(function (c) { return c.high || c.central || 1; })) * 1.12 || 1;
    function x(v) { return L + v * (w - L - Rr); }
    function y(v) { return h - B - (v / maxY) * (h - B - T); }
    var unit = gp === "GP04" ? "sheets a year" : "kg CO₂e a year";
    var s = svgOpen(w, h, "Opportunity quadrant for " + GD.pathway(gp).name + ". " + cs.length + " cohorts plotted.");
    for (var i = 0; i <= 4; i++) {
      var gy = y((maxY / 4) * i);
      s += '<line class="grid" x1="' + L + '" x2="' + (w - Rr) + '" y1="' + gy + '" y2="' + gy + '"/><text x="' + (L - 8) + '" y="' + (gy + 4) + '" text-anchor="end">' + GD.fmt.num(Math.round((maxY / 4) * i)) + "</text>";
      var gx = x(i / 4);
      s += '<text x="' + gx + '" y="' + (h - B + 18) + '" text-anchor="middle">' + (i / 4).toFixed(2) + "</text>";
    }
    s += '<line class="axis" x1="' + L + '" x2="' + (w - Rr) + '" y1="' + (h - B) + '" y2="' + (h - B) + '"/><line class="axis" x1="' + L + '" x2="' + L + '" y1="' + T + '" y2="' + (h - B) + '"/>';
    s += '<line class="cross" x1="' + x(0.5) + '" x2="' + x(0.5) + '" y1="' + T + '" y2="' + (h - B) + '"/><line class="cross" x1="' + L + '" x2="' + (w - Rr) + '" y1="' + y(maxY / 2) + '" y2="' + y(maxY / 2) + '"/>';
    s += '<text class="lbl-mono" x="' + (L + 10) + '" y="' + (T + 14) + '">EDUCATE, NO HARD SELL</text>';
    s += '<text class="lbl-mono" x="' + (w - Rr - 10) + '" y="' + (T + 14) + '" text-anchor="end">RM CALL LIST</text>';
    s += '<text class="lbl-mono" x="' + (w - Rr - 10) + '" y="' + (h - B - 10) + '" text-anchor="end">DIGITAL NUDGE</text>';
    s += '<text class="lbl-mono" x="' + (L + 10) + '" y="' + (h - B - 10) + '">LOW PRIORITY</text>';
    s += '<text x="' + ((L + w - Rr) / 2) + '" y="' + (h - 6) + '" text-anchor="middle">Propensity (low to high)</text>';
    s += '<text transform="translate(16 ' + ((T + h - B) / 2) + ') rotate(-90)" text-anchor="middle">Estimated impact per customer (' + unit + ")</text>";
    cs.forEach(function (c) {
      var fam = gp === "GP04" ? "s-paper" : c.status === "RECOMMEND" ? "s-co2" : "s-neutral";
      var r = Math.max(7, Math.min(26, Math.sqrt(c.n) * 0.95));
      var cx = x(c.propensity), cy = y(c.central || 0);
      var low = c.conf < 0.6;
      s += '<g class="cohort' + (low ? " is-lowconf" : "") + '" tabindex="0" role="button" data-cohort="' + c.id + '" aria-label="' + esc(c.name + ", " + c.n + " customers, propensity " + c.propensity.toFixed(2) + ", confidence " + c.conf.toFixed(2) + (c.central ? ", estimated " + GD.fmt.range(c.low, c.high) + " " + unit + " per customer" : ", impact not estimated")) + '" style="opacity:' + (0.4 + c.conf * 0.6).toFixed(2) + '">';
      if (c.high) s += '<line class="whisker ' + fam + '" x1="' + cx + '" x2="' + cx + '" y1="' + y(c.low) + '" y2="' + y(c.high) + '"/>';
      s += '<circle class="' + fam + ' is-estimate dot-pt" cx="' + cx + '" cy="' + cy + '" r="' + r.toFixed(1) + '"/></g>';
    });
    s += "</svg>";
    var legend = '<div class="gd-legend"><span class="' + (gp === "GP04" ? "gd-fam-paper" : "gd-fam-co2") + '"><i class="swatch-est"></i>RECOMMEND cohort (estimate)</span><span class="gd-fam-neutral"><i class="swatch-est"></i>Other statuses</span><span>Whisker: low to high range</span><span>Dashed amber outline: low confidence, enrich data</span>' + (hidden ? "<span>" + hidden + " cohort hidden to protect privacy (fewer than 10 customers)</span>" : "") + "</div>";
    var table = C.dataTable(["Cohort", "Customers", "Propensity", "Confidence", "Impact low", "Central", "High"], cs.map(function (c) { return [c.name, GD.fmt.num(c.n), c.propensity.toFixed(2), c.conf.toFixed(2), c.high ? GD.fmt.num(c.low) : "–", c.high ? GD.fmt.num(c.central) : "Not estimated", c.high ? GD.fmt.num(c.high) : "–"]; }), "Impact in " + unit + " per customer");
    el.innerHTML = '<div class="gd-plot-well">' + s + "</div>" + legend + table;
    $$(".cohort", el).forEach(function (g) {
      function pick() {
        $$(".cohort", el).forEach(function (o) { o.classList.toggle("is-selected", o === g); });
        var c = cs.filter(function (k) { return k.id === g.getAttribute("data-cohort"); })[0];
        el.dispatchEvent(new CustomEvent("gd:cohort", { bubbles: true, detail: { cohort: c, gp: gp } }));
      }
      g.addEventListener("click", pick);
      g.addEventListener("keydown", function (e) { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); pick(); } });
    });
    if (opts.select !== false && cs.length) { var first = el.querySelector(".cohort"); if (first) setTimeout(function () { first.dispatchEvent(new Event("click")); }, 0); }
  };

  C.funnel = function (el, gp) {
    var f = GD.portfolio.funnel[gp], max = f[0][1];
    var fam = gp === "GP04" ? "gd-fam-paper" : "gd-fam-co2";
    var h = '<div class="gd-funnel ' + fam + '" role="list" aria-label="Opportunity funnel for ' + esc(GD.pathway(gp).name) + '">';
    f.forEach(function (row, i) {
      h += '<div class="gd-funnel__row" role="listitem"><span>' + esc(row[0]) + '</span><span class="gd-funnel__bar" style="width:' + Math.max(2, (row[1] / max) * 100) + '%;opacity:' + (1 - i * 0.12) + '"></span><span class="t-data t-right">' + GD.fmt.num(row[1]) + "</span></div>";
      if (i < f.length - 1) h += '<p class="gd-funnel__drop">− ' + GD.fmt.num(row[1] - f[i + 1][1]) + " (" + GD.fmt.pct(1 - f[i + 1][1] / row[1]) + " drop-off)</p>";
    });
    el.innerHTML = h + "</div>" + C.dataTable(["Stage", "Customers"], f.map(function (r) { return [r[0], GD.fmt.num(r[1])]; }));
  };

  /* Horizontal bars. rows: [{label, value, display, family, suppressed}] */
  C.bars = function (el, rows, opts) {
    opts = opts || {};
    var max = opts.max || Math.max.apply(null, rows.map(function (r) { return r.suppressed ? 0 : r.value; }));
    var w = 640, rowH = 34, L = opts.labelW || 200, h = rows.length * rowH + 12;
    var s = svgOpen(w, h, opts.label || "Bar chart");
    rows.forEach(function (r, i) {
      var y0 = 6 + i * rowH;
      s += '<text x="' + (L - 10) + '" y="' + (y0 + 20) + '" text-anchor="end">' + esc(r.label) + "</text>";
      if (r.suppressed) { s += '<text class="lbl-mono" x="' + (L + 6) + '" y="' + (y0 + 20) + '">&lt;10 · HIDDEN TO PROTECT PRIVACY</text>'; return; }
      var bw = Math.max(2, (r.value / max) * (w - L - 80));
      s += '<rect class="s-' + (r.family || opts.family || "neutral") + (opts.estimate ? " is-estimate" : "") + '" x="' + L + '" y="' + (y0 + 6) + '" width="' + bw.toFixed(1) + '" height="20" rx="3"/>';
      s += '<text class="lbl-strong" x="' + (L + bw + 8) + '" y="' + (y0 + 21) + '">' + esc(r.display || GD.fmt.num(r.value)) + "</text>";
    });
    el.innerHTML = s + "</svg>" + (opts.table !== false ? C.dataTable([opts.labelHead || "Item", opts.valueHead || "Value"], rows.map(function (r) { return [r.label, r.suppressed ? "<10 (hidden)" : r.display || GD.fmt.num(r.value)]; })) : "");
  };

  /* Lines. series: [{name, values, family, dashed}] */
  C.lines = function (el, labels, series, opts) {
    opts = opts || {};
    var w = 640, h = 260, L = 48, B = 32, T = 16, Rr = 16;
    var max = Math.max.apply(null, series.reduce(function (a, s) { return a.concat(s.values); }, [])) * 1.1;
    function x(i) { return L + (i / (labels.length - 1)) * (w - L - Rr); }
    function y(v) { return h - B - (v / max) * (h - B - T); }
    var s = svgOpen(w, h, opts.label || "Trend");
    for (var g = 0; g <= 4; g++) { var gy = y((max / 4) * g); s += '<line class="grid" x1="' + L + '" x2="' + (w - Rr) + '" y1="' + gy + '" y2="' + gy + '"/><text x="' + (L - 8) + '" y="' + (gy + 4) + '" text-anchor="end">' + GD.fmt.num(Math.round((max / 4) * g)) + "</text>"; }
    labels.forEach(function (l, i) { s += '<text x="' + x(i) + '" y="' + (h - 10) + '" text-anchor="middle">' + esc(l) + "</text>"; });
    series.forEach(function (sr) {
      s += '<polyline class="line s-' + sr.family + (sr.dashed ? " is-dashed" : "") + '" style="fill:none" points="' + sr.values.map(function (v, i) { return x(i).toFixed(1) + "," + y(v).toFixed(1); }).join(" ") + '"/>';
      sr.values.forEach(function (v, i) { s += '<circle class="s-' + sr.family + ' dot-pt" cx="' + x(i).toFixed(1) + '" cy="' + y(v).toFixed(1) + '" r="3.5"/>'; });
    });
    s += "</svg>";
    var legend = '<div class="gd-legend">' + series.map(function (sr) { return '<span class="gd-fam-' + sr.family + '"><i class="' + (sr.dashed ? "swatch-est" : "swatch-real") + '"></i>' + esc(sr.name) + "</span>"; }).join("") + "</div>";
    el.innerHTML = s + legend + C.dataTable(["Month"].concat(series.map(function (s) { return s.name; })), labels.map(function (l, i) { return [l].concat(series.map(function (s) { return GD.fmt.num(s.values[i]); })); }));
  };

  C.calibration = function (el, pts) {
    var w = 360, h = 300, L = 44, B = 40, T = 12, Rr = 12;
    function x(v) { return L + v * (w - L - Rr); }
    function y(v) { return h - B - v * (h - B - T); }
    var s = svgOpen(w, h, "Calibration curve: predicted against observed take-up");
    for (var i = 0; i <= 4; i++) { var v = i / 4; s += '<line class="grid" x1="' + L + '" x2="' + (w - Rr) + '" y1="' + y(v) + '" y2="' + y(v) + '"/><text x="' + (L - 6) + '" y="' + (y(v) + 4) + '" text-anchor="end">' + v.toFixed(2) + '</text><text x="' + x(v) + '" y="' + (h - B + 16) + '" text-anchor="middle">' + v.toFixed(2) + "</text>"; }
    s += '<line class="diag" x1="' + x(0) + '" y1="' + y(0) + '" x2="' + x(1) + '" y2="' + y(1) + '"/>';
    s += '<polyline class="line s-co2" style="fill:none" points="' + pts.map(function (p) { return x(p[0]).toFixed(1) + "," + y(p[1]).toFixed(1); }).join(" ") + '"/>';
    pts.forEach(function (p) { s += '<circle class="s-co2 dot-pt" cx="' + x(p[0]).toFixed(1) + '" cy="' + y(p[1]).toFixed(1) + '" r="4"/>'; });
    s += '<text x="' + ((L + w - Rr) / 2) + '" y="' + (h - 4) + '" text-anchor="middle">Predicted propensity</text><text transform="translate(12 ' + ((T + h - B) / 2) + ') rotate(-90)" text-anchor="middle">Observed take-up</text></svg>';
    el.innerHTML = s + '<div class="gd-legend"><span class="gd-fam-co2"><i class="swatch-real"></i>Calibrated LightGBM</span><span>Dotted: perfect calibration</span></div>' + C.dataTable(["Predicted", "Observed"], pts.map(function (p) { return [p[0].toFixed(2), p[1].toFixed(2)]; }));
  };

  C.confusion = function (el, labels, m) {
    var n = labels.length, cell = 44, L = 132, T = 96, w = L + n * cell + 8, h = T + n * cell + 8;
    var s = svgOpen(w, h, "Categoriser confusion matrix on merchants unseen in training");
    labels.forEach(function (l, i) {
      s += '<text x="' + (L - 8) + '" y="' + (T + i * cell + cell / 2 + 4) + '" text-anchor="end">' + esc(l) + "</text>";
      s += '<text transform="translate(' + (L + i * cell + cell / 2 + 4) + " " + (T - 8) + ') rotate(-45)" text-anchor="start">' + esc(l) + "</text>";
    });
    m.forEach(function (row, i) {
      var tot = row.reduce(function (a, b) { return a + b; }, 0);
      row.forEach(function (v, j) {
        var share = tot ? v / tot : 0;
        s += '<rect class="heat-cell ' + (i === j ? "s-co2" : "s-neutral") + '" x="' + (L + j * cell) + '" y="' + (T + i * cell) + '" width="' + cell + '" height="' + cell + '" rx="4" style="fill-opacity:' + (v ? 0.12 + share * 0.88 : 0.04).toFixed(2) + '"/>';
        if (v) s += '<text x="' + (L + j * cell + cell / 2) + '" y="' + (T + i * cell + cell / 2 + 4) + '" text-anchor="middle"' + (i === j ? ' class="lbl-strong"' : "") + ">" + v + "</text>";
      });
    });
    el.innerHTML = s + '</svg><p class="gd-chart-summary">Rows are true categories, columns are predicted. Diagonal cells are correct.</p>' + C.dataTable(["True \\ Predicted"].concat(labels), m.map(function (r, i) { return [labels[i]].concat(r.map(String)); }));
  };

  /* =============================================== 11 Hydration and boot */
  GD.hydrate = function (root) {
    $$("[data-gd-render]", root).forEach(function (el) {
      var kind = el.getAttribute("data-gd-render");
      var ctx = GD.ctx();
      var key = el.getAttribute("data-persona") || ctx.persona;
      var gp = el.getAttribute("data-pathway") || ctx.pathway;
      switch (kind) {
        case "proof-card": el.innerHTML = R.proofCard(key, gp, { sheets: el.getAttribute("data-sheets") !== "false", evidenceOpen: el.hasAttribute("data-evidence-open"), helpHref: el.getAttribute("data-help-href") }); break;
        case "preview": el.innerHTML = R.preview(key, gp, { href: el.getAttribute("data-href") || null }); break;
        case "tiles": el.innerHTML = R.tiles(key, { wide: el.hasAttribute("data-wide") }); break;
        case "status": el.innerHTML = R.status(el.getAttribute("data-status") || GD.opp(key, gp).status); break;
        case "verdicts": el.innerHTML = R.verdicts(GD.opp(key, gp), { sheets: el.hasAttribute("data-sheets") }); break;
        case "evidence": el.innerHTML = R.evidence(GD.opp(key, gp)); break;
        case "impact": el.innerHTML = R.impactBlock(GD.opp(key, gp), { sheets: el.hasAttribute("data-sheets"), persona: key, gp: gp }); break;
        case "confidence": el.innerHTML = R.confidence(GD.opp(key, gp).confidence || GD.persona(key).facts.conf); break;
        case "claim": el.innerHTML = R.sheetBodies.claim(key, gp); break;
        case "kpi": el.innerHTML = R.kpi(GD.portfolio.kpis[el.getAttribute("data-kpi")]); break;
        case "quadrant": C.quadrant(el, el.getAttribute("data-product") || gp); break;
        case "funnel": C.funnel(el, el.getAttribute("data-product") || gp); break;
        case "persona-name": el.textContent = GD.persona(key).name; break;
        case "sheets": GD.mountSheets(el.closest(".gd-device__screen") || document.body, key, gp, el.getAttribute("data-which") ? el.getAttribute("data-which").split(",") : null); el.remove(); break;
      }
    });
  };

  function boot() {
    mountSprite();
    initTheme();
    initBackdrop();
    initTabbar();
    GD.hydrate(document);
    initOverlays();
    initTabs();
    initCardBehaviours();
    $$("[data-gd-blocked-count]").forEach(function (el) { el.textContent = GD.fmt.num(GD.claim.blockedCount()); });
    $$("[data-gd-core-rule]").forEach(function (el) { el.innerHTML = "<strong>" + esc(GD.meta.coreRule) + "</strong>"; });
    $$("[data-gd-synthetic]").forEach(function (el) { el.innerHTML = '<span class="gd-tag">Demo data</span>' + esc(GD.meta.synthetic); });
    $$(".gd-shell__main > .gd-content, .gd-screen-scroll").forEach(function (m) { m.classList.add("gd-enter"); });
    var problems = GD.engine.selfCheck();
    if (problems.length && window.console) console.warn("greendash engine self-check:", problems);
    document.dispatchEvent(new CustomEvent("gd:ready"));
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
