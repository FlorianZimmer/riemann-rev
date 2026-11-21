/* The atlas: master map, component and declaration drawers, blueprint graph, tours.
   Data: <script id="atlas-data" type="application/json"> written by scripts/build_atlas.py. */
(() => {
  'use strict';
  const A = JSON.parse(document.getElementById('atlas-data').textContent);
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const NS = 'http://www.w3.org/2000/svg';
  const comp = Object.fromEntries(A.components.map(c => [c.id, c]));
  const node = Object.fromEntries(A.nodes.map(n => [n.id, n]));
  const strat = Object.fromEntries(A.strata.map(s => [s.id, s]));
  const T = A.tiers;

  /* ---------------------------------------------------------------- text helpers */
  const esc = s => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
  function md(s) {
    const parts = String(s ?? '').split(/(\$\$[\s\S]+?\$\$|\$[^$\n]+\$)/g);
    return parts.map((p, i) => i % 2 ? esc(p) : esc(p)
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>')
      .replace(/(^|[\s(])\*([^*\n]+)\*/g, '$1<em>$2</em>')).join('');
  }
  const KW = /^(theorem|lemma|def|structure|where|fun|by|exact|intro|have|obtain|rcases|with|match|namespace|end|variable|inductive|example|import|rw|at|refine|generalize|subst|change|apply|let|show|from|if|then|else|calc|noncomputable|section|open|instance|class|abbrev|private|protected|deriving|set_option|simp|simpa|omega|decide|exists|use)$/;
  function hl(code) {
    if (!code) return '';
    const re = /(--[^\n]*|\/-[\s\S]*?-\/|"(?:[^"\\]|\\.)*"|[A-Za-z_][A-Za-z0-9_'.₀-₉]*|\d+)/g;
    let out = '', last = 0, m;
    while ((m = re.exec(code))) {
      out += esc(code.slice(last, m.index));
      const t = m[0];
      if (t.startsWith('--') || t.startsWith('/-')) out += `<span class="c">${esc(t)}</span>`;
      else if (t.startsWith('"')) out += `<span class="s">${esc(t)}</span>`;
      else if (KW.test(t)) out += `<span class="k">${esc(t)}</span>`;
      else if (/^(Type|Prop|Sort|True|False|RiemannHypothesis)$/.test(t)) out += `<span class="t">${esc(t)}</span>`;
      else if (/^\d+$/.test(t)) out += `<span class="n">${esc(t)}</span>`;
      else out += esc(t);
      last = m.index + t.length;
    }
    return out + esc(code.slice(last));
  }
  const tierBadge = t => `<span class="tier" style="--tc:${T[t].color}" title="${esc(T[t].meaning)}"><i>${esc(T[t].icon)}</i>${esc(T[t].label)}</span>`;
  const typeset = el => { if (window.MathJax && MathJax.typesetPromise) MathJax.typesetPromise([el]).catch(() => {}); };
  const compChip = id => { const c = comp[id], s = strat[c.stratum];
    return `<button class="chip" data-open-comp="${id}"><span class="dot" style="background:${s.color}"></span>${c.n}. ${esc(c.title)}</button>`; };
  const nodeChip = id => { const n = node[id];
    return `<button class="chip" data-open-node="${id}" title="${esc(n.declaration || n.title)}"><span class="dot" style="background:${T[n.tier].color}"></span>${esc(n.title)}</button>`; };

  /* ---------------------------------------------------------------- drawer */
  const drawer = $('#drawer'), back = $('#drawer-back'), dc = $('#drawer-content');
  function openDrawer(html) {
    dc.innerHTML = html;
    drawer.classList.add('show'); back.classList.add('show');
    drawer.setAttribute('aria-hidden', 'false');
    dc.scrollTop = 0; $('.drawer-body', dc) && ($('.drawer-body', dc).scrollTop = 0);
    typeset(dc);
    const btn = $('.close', dc); if (btn) { btn.onclick = closeDrawer; btn.focus({ preventScroll: true }); }
  }
  function closeDrawer() { drawer.classList.remove('show'); back.classList.remove('show'); drawer.setAttribute('aria-hidden', 'true'); }
  back.addEventListener('click', closeDrawer);
  document.addEventListener('keydown', e => { if (e.key === 'Escape') closeDrawer(); });

  function componentHTML(id) {
    const c = comp[id], s = strat[c.stratum];
    const ups = A.interfaces.filter(i => i.to === id), downs = A.interfaces.filter(i => i.from === id);
    const fig = c.figure && document.getElementById('fig-' + c.figure);
    const cuts = A.cuts.filter(k => k.components.includes(id));
    const tl = A.timeline.filter(t => t.component === id);
    return `<div class="drawer-head"><button class="close" aria-label="Close">×</button>
      <div class="strat" style="color:${s.color}">${esc(s.title)} · component ${c.n} of ${A.components.length}</div>
      <h3>${esc(c.title)}</h3><div class="mono small muted">${esc(c.kicker)}</div>
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap">${tierBadge(c.tier)}${cuts.map(k => `<span class="tier" style="--tc:${T[k.tier].color}"><i>⊢</i>inside the cut “${esc(k.title)}”</span>`).join('')}</div></div>
      <div class="drawer-body">
      <p><b>${md(c.gist)}</b></p>
      <h5>Statement</h5><div class="stmt">$$${esc(c.statement)}$$</div>
      <h5>The idea</h5>${c.explanation.map(p => `<p>${md(p)}</p>`).join('')}
      ${fig ? `<h5>Illustration</h5><div class="fig">${fig.innerHTML}</div>` : ''}
      <h5>Lean declarations · pinned source</h5><ul class="lean">${c.lean.map(l =>
        `<li><a href="${esc(l.url)}" target="_blank" rel="noopener"><code>${esc(l.name)}</code> ↗</a>${l.note ? `<span class="nt">${esc(l.note)}</span>` : ''}</li>`).join('')}</ul>
      <h5>Verification status</h5><p class="status">${md(c.status)}</p><p class="small muted">${tierBadge(c.tier)} ${esc(T[c.tier].meaning)}</p>
      <h5>What remains to check</h5><div class="check">${md(c.check)}</div>
      ${ups.length ? `<h5>Receives</h5><div class="chips">${ups.map(i => compChip(i.from) + `<span class="small muted" style="align-self:center">→ ${esc(i.label)}</span>`).join('')}</div>` : ''}
      ${downs.length ? `<h5>Supplies</h5><div class="chips">${downs.map(i => `<span class="small muted" style="align-self:center">${esc(i.label)} →</span>` + compChip(i.to)).join('')}</div>` : ''}
      <h5>Blueprint declarations (${c.nodes.length})</h5><div class="chips">${c.nodes.map(nodeChip).join('')}</div>
      ${tl.length ? `<h5>Announcement timeline</h5><ul>${tl.map(t => `<li><b>${t.number}.</b> ${esc(t.topic)} <span class="relation">${esc(t.relation)}</span>${t.date ? ` <span class="small muted">${esc(t.date)}</span>` : ''}</li>`).join('')}</ul>` : ''}
      </div>`;
  }
  function nodeHTML(id) {
    const n = node[id], c = comp[n.component], s = strat[c.stratum];
    const uses = A.edges.filter(e => e.from === id), usedBy = A.edges.filter(e => e.to === id);
    const ev = (n.evidence || []).map(e => A.evidence[e] || e);
    const lines = n.lines ? `lines ${n.lines[0]}–${n.lines[1]}` : '';
    return `<div class="drawer-head"><button class="close" aria-label="Close">×</button>
      <div class="strat" style="color:${s.color}">Blueprint declaration · ${esc(n.kind)} · ${esc(c.title)}</div>
      <h3>${esc(n.title)}</h3>
      ${n.declaration ? `<div class="mono small">${esc(n.module ? n.module + ' · ' : '')}<b>${esc(n.declaration)}</b></div>` : ''}
      <div style="margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center">${tierBadge(n.tier)}
      ${n.url ? `<a class="btn light" style="padding:4px 10px;font-size:.8rem" href="${esc(n.url)}" target="_blank" rel="noopener">Pinned source ${esc(lines)} ↗</a>` : ''}
      <button class="btn light" style="padding:4px 10px;font-size:.8rem" data-graph-node="${id}">Show in graph</button>
      <button class="btn light" style="padding:4px 10px;font-size:.8rem" data-trace="down" data-node="${id}" title="Highlight everything this declaration rests on">Rests on ↓</button>
      <button class="btn light" style="padding:4px 10px;font-size:.8rem" data-trace="up" data-node="${id}" title="Highlight everything that uses it, up to the endpoints">Used by ↑</button></div></div>
      <div class="drawer-body">
      <h5>In standard mathematics</h5><p>${md(n.contract)}</p>
      <h5>What the proof does</h5><p>${md(n.idea)}</p>
      ${n.assumptions && n.assumptions.length ? `<h5>Explicit hypotheses</h5><ul>${n.assumptions.map(a => `<li>${md(typeof a === 'string' ? a : (a.text || a.name || JSON.stringify(a)))}</li>`).join('')}</ul>` : ''}
      ${n.lean_head ? `<h5>Lean statement</h5><pre class="lean">${hl(n.lean_head)}</pre>` : ''}
      ${n.excerpt && n.excerpt !== n.lean_head ? `<h5>Source excerpt</h5><pre class="lean">${hl(n.excerpt)}</pre>` : ''}
      <h5>Rests on (${uses.length})</h5><div class="chips">${uses.map(e => nodeChip(e.to)).join('') || '<span class="small muted">no selected callees</span>'}</div>
      <h5>Used by (${usedBy.length})</h5><div class="chips">${usedBy.map(e => nodeChip(e.from)).join('') || '<span class="small muted">an endpoint or a motivation</span>'}</div>
      <h5>Component</h5><div class="chips">${compChip(c.id)}</div>
      <h5>Evidence</h5><ul class="small">${ev.map(e => `<li>${esc(e)}</li>`).join('')}</ul>
      <p class="small muted">${esc(T[n.tier].meaning)}</p>
      </div>`;
  }
  const openComponent = id => openDrawer(componentHTML(id));
  const openNode = id => openDrawer(nodeHTML(id));

  document.addEventListener('click', e => {
    const c = e.target.closest('[data-open-comp]');
    if (c) { e.preventDefault(); openComponent(c.dataset.openComp); return; }
    const n = e.target.closest('[data-open-node]');
    if (n) { e.preventDefault(); openNode(n.dataset.openNode); if (graph) graph.select(n.dataset.openNode, { center: true, open: false }); return; }
    const g = e.target.closest('[data-graph-node]');
    if (g) { e.preventDefault(); closeDrawer(); $('#blueprint').scrollIntoView({ behavior: 'smooth' });
      setTimeout(() => graph.select(g.dataset.graphNode, { center: true, open: false }), 350); }
  });

  /* ---------------------------------------------------------------- master map */
  const map = $('#map'), msvg = $('#map-svg');
  $$('.comp', map).forEach(el => {
    el.addEventListener('click', () => openComponent(el.dataset.id));
    el.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openComponent(el.dataset.id); } });
  });
  function mk(tag, attrs, parent) { const e = document.createElementNS(NS, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); if (parent) parent.appendChild(e); return e; }
  function drawMap() {
    if (getComputedStyle(msvg).display === 'none') return;
    const R = map.getBoundingClientRect();
    while (msvg.firstChild) msvg.removeChild(msvg.firstChild);
    const defs = mk('defs', {}, msvg);
    const mrk = mk('marker', { id: 'mh', viewBox: '0 0 10 10', refX: '8.5', refY: '5', markerWidth: '7', markerHeight: '7', orient: 'auto-start-reverse' }, defs);
    mk('path', { d: 'M0,0 L10,5 L0,10 z', fill: '#475569' }, mrk);
    const rect = id => { const r = $(`.comp[data-id="${id}"]`, map).getBoundingClientRect();
      return { x: r.left - R.left, y: r.top - R.top, w: r.width, h: r.height, col: +$(`.comp[data-id="${id}"]`, map).dataset.col, row: +$(`.comp[data-id="${id}"]`, map).dataset.row }; };
    // strata bands
    A.strata.forEach((s, i) => {
      const cards = $$(`.comp[data-col="${i + 1}"]`, map).map(el => el.getBoundingClientRect());
      const head = $(`.map-col-head[data-col="${i + 1}"]`, map).getBoundingClientRect();
      const x0 = Math.min(...cards.map(r => r.left), head.left) - R.left - 10, x1 = Math.max(...cards.map(r => r.right), head.right) - R.left + 10;
      const y0 = head.top - R.top - 8, y1 = Math.max(...cards.map(r => r.bottom)) - R.top + 12;
      mk('rect', { x: x0, y: y0, width: x1 - x0, height: y1 - y0, rx: 18, fill: s.color, opacity: 0.055 }, msvg);
    });
    const labels = [];
    A.interfaces.forEach(it => {
      const a = rect(it.from), b = rect(it.to);
      let d, mx, my, rot = 0;
      if (a.col === b.col && Math.abs(a.row - b.row) === 1) {
        const down = b.row > a.row, x1 = a.x + a.w / 2, x2 = b.x + b.w / 2;
        const y1 = down ? a.y + a.h : a.y, y2 = down ? b.y : b.y + b.h;
        d = `M${x1},${y1} L${x2},${y2 + (down ? -2 : 2)}`; mx = (x1 + x2) / 2; my = (y1 + y2) / 2;
      } else if (a.col === b.col) {
        // skip over the cards in between along the outer side of the column
        const side = a.col === 1 ? -1 : 1, xa = side < 0 ? a.x : a.x + a.w, xb = side < 0 ? b.x : b.x + b.w;
        const ya = a.y + a.h * 0.62, yb = b.y + b.h * 0.38, xo = xa + 30 * side;
        d = `M${xa},${ya} C${xo},${ya} ${xo},${ya} ${xo},${(ya + yb) / 2} S${xo},${yb} ${xb + 2 * side},${yb}`;
        mx = xo - 11; my = (ya + yb) / 2; rot = -90;
      } else if (a.row === b.row) {
        // same row: a U-shaped connector through the gap below the two cards
        const x1 = a.x + a.w * 0.82, x2 = b.x + b.w * 0.18, y1 = a.y + a.h, y2 = b.y + b.h, yg = Math.max(y1, y2) + 16;
        d = `M${x1},${y1} C${x1},${yg} ${x1},${yg} ${(x1 + x2) / 2},${yg} S${x2},${yg} ${x2},${y2 + 2}`;
        mx = (x1 + x2) / 2; my = yg;
      } else {
        const x1 = a.x + a.w, y1 = a.y + a.h / 2, x2 = b.x, y2 = b.y + b.h / 2, dx = Math.max(18, (x2 - x1) / 2);
        d = `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2 - 2},${y2}`; mx = (x1 + x2) / 2; my = (y1 + y2) / 2;
      }
      mk('path', { d, fill: 'none', stroke: '#475569', 'stroke-width': 1.6, 'marker-end': 'url(#mh)', opacity: 0.8,
        'data-from': it.from, 'data-to': it.to, class: 'iface' }, msvg);
      labels.push({ x: mx, y: my, text: it.label, rot, lean: it.lean });
    });
    labels.forEach(l => {
      const g = mk('g', l.rot ? { transform: `rotate(${l.rot},${l.x},${l.y})` } : {}, msvg);
      const bg = mk('rect', { class: 'lblbg', rx: 6, ry: 6 }, g);
      const t = mk('text', { class: 'lbl', x: l.x, y: l.y + 3.5, 'text-anchor': 'middle' }, g);
      t.textContent = l.text;
      const tt = mk('title', {}, g); tt.textContent = `${l.text} — Lean: ${l.lean}`;
      const w = t.getComputedTextLength ? t.getComputedTextLength() : l.text.length * 6;
      bg.setAttribute('x', l.x - w / 2 - 6); bg.setAttribute('y', l.y - 9); bg.setAttribute('width', w + 12); bg.setAttribute('height', 18);
    });
  }
  window.addEventListener('resize', () => { clearTimeout(drawMap.t); drawMap.t = setTimeout(drawMap, 120); });
  (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(drawMap);
  window.addEventListener('mathjax-ready', () => { drawMap(); });
  drawMap();

  // verified cuts on the map
  const callout = $('#cut-callout');
  $$('[data-cut]').forEach(btn => btn.addEventListener('click', () => {
    const id = btn.dataset.cut, on = !btn.classList.contains('on');
    $$('[data-cut]').forEach(b => b.classList.remove('on'));
    $$('.comp', map).forEach(el => el.classList.remove('in', 'out'));
    map.classList.toggle('cutmode', on && id !== 'none');
    callout.classList.remove('show');
    if (!on || id === 'none') return;
    btn.classList.add('on');
    const k = A.cuts.find(x => x.id === id);
    $$('.comp', map).forEach(el => el.classList.add(k.components.includes(el.dataset.id) ? 'in' : 'out'));
    callout.innerHTML = `<div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">${tierBadge(k.tier)}<b>${esc(k.title)}</b> <code>${esc(k.lean)}</code></div>
      <div class="prem">$$\\Bigl[\\,${esc(k.premise)}\\,\\Bigr]\\ \\Longrightarrow\\ \\text{${esc(k.conclusion)}}$$</div>
      <div class="small">${esc(k.evidence)} Highlighted: the components inside the checked closure. Dimmed: the components that would have to supply the premise, and the archive's own five exports, whose proof terms run through that supply.</div>`;
    callout.classList.add('show'); typeset(callout);
  }));

  /* ---------------------------------------------------------------- guided tour of the map */
  (() => {
    const start = $('#story-start'); if (!start || !A.story) return;
    let i = 0, on = false;
    function show() {
      const st = A.story[i], c = comp[st.comp], s = strat[c.stratum];
      $$('[data-cut]').forEach(b => b.classList.remove('on'));
      map.classList.add('cutmode');
      $$('.comp', map).forEach(el => { el.classList.remove('in', 'out'); el.classList.add(el.dataset.id === st.comp ? 'in' : 'out'); });
      callout.style.background = '#eef2ff'; callout.style.borderColor = '#c7d2fe'; callout.style.color = '#1e1b4b';
      callout.innerHTML = `<div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap"><span class="chip on">${i + 1} / ${A.story.length}</span>
        <span class="dot" style="background:${s.color}"></span><b>${c.n}. ${esc(c.title)}</b><span class="small muted">${esc(s.title)}</span>
        <span style="margin-left:auto;display:flex;gap:6px"><button class="btn light" data-st="prev">←</button><button class="btn light" data-st="next">→</button>
        <button class="btn light" data-open-comp="${c.id}">Details</button><button class="btn light" data-st="stop">Exit</button></span></div>
        <p style="margin:10px 0 0;font-size:1.02rem">${md(st.text)}</p>`;
      callout.classList.add('show'); typeset(callout);
      callout.querySelector('[data-st=prev]').onclick = () => { i = Math.max(0, i - 1); show(); };
      callout.querySelector('[data-st=next]').onclick = () => { i = Math.min(A.story.length - 1, i + 1); show(); };
      callout.querySelector('[data-st=stop]').onclick = stop;
      const el = $(`.comp[data-id="${st.comp}"]`, map);
      const r = el.getBoundingClientRect();
      if (r.top < 120 || r.bottom > innerHeight - 20) window.scrollTo({ top: scrollY + r.top - innerHeight / 2 + r.height / 2, behavior: 'smooth' });
    }
    function stop() { on = false; map.classList.remove('cutmode'); $$('.comp', map).forEach(el => el.classList.remove('in', 'out'));
      callout.classList.remove('show'); callout.removeAttribute('style'); start.textContent = '▶ Guided tour: from RH backwards'; }
    start.addEventListener('click', () => { if (on) { stop(); return; } on = true; i = 0; start.textContent = '■ Stop the tour';
      $('#map-section').scrollIntoView({ behavior: 'smooth' }); setTimeout(show, 250); });
    document.addEventListener('keydown', e => { if (!on || drawer.classList.contains('show')) return;
      if (e.key === 'ArrowRight') { i = Math.min(A.story.length - 1, i + 1); show(); }
      if (e.key === 'ArrowLeft') { i = Math.max(0, i - 1); show(); } });
    $$('[data-cut]').forEach(b => b.addEventListener('click', () => { if (on) { on = false; start.textContent = '▶ Guided tour: from RH backwards'; callout.removeAttribute('style'); } }, true));
    const m = location.hash.match(/^#tour-?(\d*)$/);
    if (m) { on = true; i = Math.max(0, Math.min(A.story.length - 1, (+m[1] || 1) - 1)); start.textContent = '■ Stop the tour'; setTimeout(show, 50); }
  })();

  /* ---------------------------------------------------------------- blueprint graph */
  const graph = (() => {
    const svg = $('#bp-svg'), vp = $('#bp-vp'), shell = $('#bp-shell');
    if (!svg) return null;
    const L = A.layout, NW = L.nw, NH = L.nh;
    const defs = mk('defs', {}, svg);
    const mrk = mk('marker', { id: 'bh', viewBox: '0 0 10 10', refX: '9', refY: '5', markerWidth: '6', markerHeight: '6', orient: 'auto' }, defs);
    mk('path', { d: 'M0,0 L10,5 L0,10 z', fill: '#94a3b8' }, mrk);
    const eG = mk('g', {}, vp), nG = mk('g', {}, vp);
    const edgeEls = A.edges.map(e => {
      const a = node[e.to], b = node[e.from];                 // supplier a feeds consumer b
      const x1 = a.x + NW, y1 = a.y + NH / 2, x2 = b.x, y2 = b.y + NH / 2, dx = Math.max(36, Math.abs(x2 - x1) / 2);
      const p = mk('path', { d: `M${x1},${y1} C${x1 + dx},${y1} ${x2 - dx},${y2} ${x2 - 3},${y2}`, class: `bp-edge ${e.relation}`, 'marker-end': 'url(#bh)' }, eG);
      p.dataset.from = e.from; p.dataset.to = e.to; return p;
    });
    const nodeEls = {};
    A.nodes.forEach(n => {
      const c = comp[n.component], col = strat[c.stratum].color;
      const g = mk('g', { class: 'bp-node', transform: `translate(${n.x},${n.y})`, tabindex: '0' }, nG);
      g.dataset.id = n.id;
      mk('rect', { class: 'box', width: NW, height: NH, rx: 9 }, g);
      mk('rect', { x: 0, y: 0, width: 6, height: NH, rx: 3, fill: col }, g);
      mk('circle', { cx: NW - 12, cy: 12, r: 6, fill: T[n.tier].color }, g);
      const t = mk('text', { class: 't', x: 14, y: 19 }, g); t.textContent = n.short;
      const d = mk('text', { class: 'd', x: 14, y: 35 }, g); d.textContent = n.decl_short || n.kind;
      const tt = mk('title', {}, g); tt.textContent = `${n.title}\n${n.declaration || ''}\n${T[n.tier].label}`;
      g.addEventListener('click', ev => { ev.stopPropagation(); select(n.id, { open: true }); });
      g.addEventListener('keydown', ev => { if (ev.key === 'Enter') select(n.id, { open: true }); });
      nodeEls[n.id] = g;
    });
    // pan & zoom
    let view = { k: 0.5, x: 20, y: 20 };
    let apply = () => vp.setAttribute('transform', `translate(${view.x},${view.y}) scale(${view.k})`);
    function fit() { const r = svg.getBoundingClientRect(); const k = Math.min(r.width / (L.w + 60), r.height / (L.h + 60));
      view = { k, x: (r.width - L.w * k) / 2, y: (r.height - L.h * k) / 2 }; apply(); }
    function zoomAt(f, mx, my) { const nk = Math.min(2.6, Math.max(0.15, view.k * f)); view.x = mx - (mx - view.x) * nk / view.k; view.y = my - (my - view.y) * nk / view.k; view.k = nk; apply(); }
    svg.addEventListener('wheel', e => { e.preventDefault(); const r = svg.getBoundingClientRect(); zoomAt(Math.exp(-e.deltaY * 0.0016), e.clientX - r.left, e.clientY - r.top); }, { passive: false });
    let drag = null;
    svg.addEventListener('pointerdown', e => { if (e.target.closest('.bp-node')) return; drag = { x: e.clientX, y: e.clientY, vx: view.x, vy: view.y }; svg.classList.add('dragging'); svg.setPointerCapture(e.pointerId); });
    svg.addEventListener('pointermove', e => { if (!drag) return; view.x = drag.vx + e.clientX - drag.x; view.y = drag.vy + e.clientY - drag.y; apply(); });
    svg.addEventListener('pointerup', e => { if (drag && Math.abs(e.clientX - drag.x) + Math.abs(e.clientY - drag.y) < 4) clear(); drag = null; svg.classList.remove('dragging'); });
    $('#bp-in').onclick = () => { const r = svg.getBoundingClientRect(); zoomAt(1.25, r.width / 2, r.height / 2); };
    $('#bp-out').onclick = () => { const r = svg.getBoundingClientRect(); zoomAt(0.8, r.width / 2, r.height / 2); };
    $('#bp-fit').onclick = fit;
    function centerOn(id, k) {
      const n = node[id], r = svg.getBoundingClientRect(), kk = k || Math.max(view.k, 0.85);
      const target = { k: kk, x: r.width / 2 - (n.x + NW / 2) * kk, y: r.height / 2 - (n.y + NH / 2) * kk };
      const from = { ...view }, t0 = performance.now();
      const step = now => { const u = Math.min(1, (now - t0) / 420), e = u < .5 ? 2 * u * u : 1 - Math.pow(-2 * u + 2, 2) / 2;
        view = { k: from.k + (target.k - from.k) * e, x: from.x + (target.x - from.x) * e, y: from.y + (target.y - from.y) * e }; apply();
        if (u < 1) requestAnimationFrame(step); };
      requestAnimationFrame(step);
    }
    function clear() { shell.classList.remove('bp-dim'); Object.values(nodeEls).forEach(g => g.classList.remove('sel', 'hl', 'match')); edgeEls.forEach(p => p.classList.remove('hl')); }
    function mark(ids, edgesToo) {
      clear(); shell.classList.add('bp-dim');
      ids.forEach(i => nodeEls[i] && nodeEls[i].classList.add('hl'));
      if (edgesToo) edgeEls.forEach(p => { if (ids.has(p.dataset.from) && ids.has(p.dataset.to)) p.classList.add('hl'); });
    }
    function select(id, opts = {}) {
      clear(); shell.classList.add('bp-dim');
      nodeEls[id].classList.add('sel');
      edgeEls.forEach(p => { if (p.dataset.from === id || p.dataset.to === id) { p.classList.add('hl'); nodeEls[p.dataset.from].classList.add('hl'); nodeEls[p.dataset.to].classList.add('hl'); } });
      nodeEls[id].classList.remove('hl'); nodeEls[id].classList.add('sel');
      if (opts.center) centerOn(id);
      if (opts.open) openNode(id);
    }
    function cone(id, dir) { // dir 'down' = everything it rests on; 'up' = everything that uses it
      const seen = new Set([id]), q = [id];
      while (q.length) { const u = q.shift(); A.edges.forEach(e => { const [a, b] = dir === 'down' ? [e.from, e.to] : [e.to, e.from];
        if (a === u && !seen.has(b)) { seen.add(b); q.push(b); } }); }
      return seen;
    }
    // search
    const search = $('#bp-search'); let hits = [], hi = 0;
    search.addEventListener('input', () => {
      const q = search.value.trim().toLowerCase(); clear(); hits = []; hi = 0;
      if (!q) return;
      A.nodes.forEach(n => { if ((n.title + ' ' + (n.declaration || '') + ' ' + n.contract + ' ' + comp[n.component].title).toLowerCase().includes(q)) hits.push(n.id); });
      shell.classList.add('bp-dim'); hits.forEach(i => nodeEls[i].classList.add('match'));
      $('#bp-count').textContent = hits.length ? `${hits.length} match${hits.length > 1 ? 'es' : ''} · Enter to visit` : 'no match';
    });
    search.addEventListener('keydown', e => { if (e.key === 'Enter' && hits.length) { centerOn(hits[hi % hits.length]); hi++; } });
    // highlight by component or tier
    $('#bp-filter').addEventListener('change', e => {
      const v = e.target.value; if (!v) { clear(); return; }
      const [kind, key] = v.split(':');
      const ids = new Set(A.nodes.filter(n => kind === 'c' ? n.component === key : kind === 's' ? comp[n.component].stratum === key : n.tier === key).map(n => n.id));
      mark(ids, true);
    });
    // tours
    const bar = $('#tour'); let tour = null, ti = 0;
    function showStep() {
      const id = tour.nodes[ti], n = node[id];
      select(id, { center: true });
      bar.innerHTML = `<b>${esc(tour.title)}</b><span class="small">${esc(tour.question)}</span>
        <span class="chip on">${ti + 1} / ${tour.nodes.length}</span><span><b>${esc(n.title)}</b> — <span class="small">${md(n.contract)}</span></span>
        <span style="margin-left:auto;display:flex;gap:6px"><button class="btn light" data-t="prev">←</button><button class="btn light" data-t="next">→</button>
        <button class="btn light" data-open-node="${id}">Details</button><button class="btn light" data-t="stop">Exit</button></span>`;
      bar.classList.add('show'); typeset(bar);
      bar.querySelector('[data-t=prev]').onclick = () => { ti = Math.max(0, ti - 1); showStep(); };
      bar.querySelector('[data-t=next]').onclick = () => { ti = Math.min(tour.nodes.length - 1, ti + 1); showStep(); };
      bar.querySelector('[data-t=stop]').onclick = () => { bar.classList.remove('show'); tour = null; clear(); };
    }
    $$('[data-tour]').forEach(b => b.addEventListener('click', () => { tour = A.itineraries[+b.dataset.tour]; ti = 0; showStep(); }));
    $$('[data-cone]').forEach(b => b.addEventListener('click', () => { mark(cone(b.dataset.node, b.dataset.cone), true); }));
    // minimap: the whole graph in miniature, with the current viewport
    const mm = $('#bp-mini');
    let mmView = null;
    if (mm) {
      const MW = 300, MH = Math.max(46, Math.round(MW * L.h / L.w)), sc = MW / L.w;
      mm.setAttribute('viewBox', `0 0 ${MW} ${MH}`); mm.style.width = MW + 'px'; mm.style.height = MH + 'px';
      A.nodes.forEach(n => mk('rect', { x: n.x * sc, y: n.y * MH / L.h, width: Math.max(2, NW * sc), height: Math.max(2, NH * MH / L.h * 0.7),
        fill: strat[comp[n.component].stratum].color, opacity: 0.85, rx: 1 }, mm));
      mmView = mk('rect', { fill: 'rgba(79,70,229,.08)', stroke: '#4f46e5', 'stroke-width': 1.2, rx: 2 }, mm);
      const goto = e => { const r = mm.getBoundingClientRect(), gx = (e.clientX - r.left) / MW * L.w, gy = (e.clientY - r.top) / MH * L.h;
        const s = svg.getBoundingClientRect(); view.x = s.width / 2 - gx * view.k; view.y = s.height / 2 - gy * view.k; apply(); };
      let mdrag = false;
      mm.addEventListener('pointerdown', e => { mdrag = true; mm.setPointerCapture(e.pointerId); goto(e); e.stopPropagation(); });
      mm.addEventListener('pointermove', e => { if (mdrag) goto(e); });
      mm.addEventListener('pointerup', () => { mdrag = false; });
      const MWH = { MW, MH };
      const upd = () => { const r = svg.getBoundingClientRect();
        const x0 = -view.x / view.k, y0 = -view.y / view.k, w = r.width / view.k, h = r.height / view.k;
        mmView.setAttribute('x', x0 * MWH.MW / L.w); mmView.setAttribute('y', y0 * MWH.MH / L.h);
        mmView.setAttribute('width', w * MWH.MW / L.w); mmView.setAttribute('height', h * MWH.MH / L.h); };
      const apply0 = apply;
      apply = () => { apply0(); upd(); };
    }
    // open on the endpoints at a readable scale; ⤢ fits everything
    function home() { const r = svg.getBoundingClientRect(), k = Math.min(0.92, r.width / 1100);
      const ends = A.nodes.filter(n => n.section === 'exports');
      const cx = Math.max(...ends.map(n => n.x)) + NW, cy = ends.reduce((a, n) => a + n.y, 0) / ends.length + NH / 2;
      view = { k, x: r.width - 40 - cx * k, y: r.height / 2 - cy * k }; apply(); }
    home();
    $('#bp-home').onclick = home;
    window.addEventListener('resize', () => { clearTimeout(home.t); home.t = setTimeout(home, 150); });
    return { select, centerOn, cone, mark, fit };
  })();

  // "rests on" / "path to endpoints" buttons inside the node drawer
  document.addEventListener('click', e => {
    const b = e.target.closest('[data-trace]'); if (!b || !graph) return;
    closeDrawer(); $('#blueprint').scrollIntoView({ behavior: 'smooth' });
    graph.mark(graph.cone(b.dataset.node, b.dataset.trace), true);
  });

  // deep links: #c-<component> or #n-<node>
  function fromHash() { const h = decodeURIComponent(location.hash.slice(1));
    if (h.startsWith('c-') && comp[h.slice(2)]) openComponent(h.slice(2));
    if (h.startsWith('n-') && node[h.slice(2)]) { openNode(h.slice(2)); if (graph) graph.select(h.slice(2), { center: true, open: false }); }
    if (h.startsWith('cut-')) { const b = document.querySelector(`[data-cut="${h}"]`); if (b && !b.classList.contains('on')) b.click(); } }
  window.addEventListener('hashchange', fromHash); fromHash();
})();
