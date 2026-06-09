// ---- bootstrapping --------------------------------------------------------

if (window.cytoscapeFcose) cytoscape.use(window.cytoscapeFcose);

const CLUSTER_COLORS = [
  '#e07a5f', '#81b29a', '#f2cc8f', '#3d5a80', '#ee6c4d',
  '#98c1d9', '#bc4749', '#a7c957', '#6a4c93', '#f4a261',
];
function colorFor(cluster) {
  if (cluster < 0) return '#555';
  return CLUSTER_COLORS[cluster % CLUSTER_COLORS.length];
}
function colorBg(cluster) {
  if (cluster < 0) return 'rgba(80,80,80,0.10)';
  const c = colorFor(cluster);
  // hex → rgba with low alpha
  const n = parseInt(c.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},0.12)`;
}
function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

const panel = document.getElementById('panel-content');
const sidebar = document.getElementById('sidebar');
const notesList = document.getElementById('notes-list');
const notesCount = document.getElementById('notes-count');
const tooltip = document.getElementById('tooltip');
const ctxMenu = document.getElementById('context-menu');
const linkBanner = document.getElementById('link-banner');
const searchInput = document.getElementById('search');
const thresholdInput = document.getElementById('threshold');
const thresholdVal = document.getElementById('threshold-val');

let cy = null;
let allNotes = [];
let currentNoteId = null;
let linkMode = null; // { from: string } when picking a link target
const noteCache = new Map();

// ---- data fetch -----------------------------------------------------------

async function fetchGraph() {
  const minScore = parseFloat(thresholdInput.value || '0');
  const r = await fetch(`/api/graph?min_score=${minScore}`);
  return await r.json();
}

async function fetchNotes() {
  const r = await fetch('/api/notes');
  allNotes = await r.json();
  allNotes.forEach((n) => noteCache.set(String(n.id), n));
  renderNotesList();
}

// ---- render graph ---------------------------------------------------------

async function loadGraph() {
  const data = await fetchGraph();
  window._lastClusters = data.clusters || [];
  window._lastClusterIds = new Set((data.clusters || []).map((c) => c.id));

  const clusterParents = (data.clusters || []).map((c) => ({
    data: { id: `c${c.id}`, label: c.label, isCluster: true },
    selectable: false,
    grabbable: false,
    style: {
      'background-color': colorBg(c.id),
      'border-color': colorFor(c.id),
      'border-width': 1,
    },
  }));

  const nodeElems = data.nodes.map((n) => {
    const cluster = n.data.cluster;
    const inCluster = cluster >= 0 && window._lastClusterIds.has(cluster);
    return {
      data: { ...n.data, parent: inCluster ? `c${cluster}` : undefined },
      style: { 'background-color': colorFor(cluster) },
    };
  });

  const edgeElems = data.edges.map((e) => ({
    data: e.data,
    style: {
      'width': 1 + 6 * Math.max(0, e.data.score),
      'line-color': edgeColor(e.data.method),
      'line-style': e.data.method.includes('pinned') ? 'dashed' : 'solid',
    },
  }));

  const elements = [...clusterParents, ...nodeElems, ...edgeElems];

  if (cy) cy.destroy();
  cy = cytoscape({
    container: document.getElementById('cy'),
    elements,
    style: [
      {
        selector: 'node',
        style: {
          label: 'data(label)',
          color: '#eee',
          'font-size': 11,
          'text-valign': 'center',
          'text-halign': 'center',
          'text-outline-color': '#000',
          'text-outline-width': 1,
          width: 28, height: 28,
        },
      },
      {
        selector: 'node[?isCluster]',
        style: {
          label: 'data(label)',
          'text-valign': 'top',
          'text-halign': 'center',
          'text-margin-y': -4,
          color: '#aaa',
          'font-size': 11,
          'text-outline-width': 0,
          shape: 'round-rectangle',
          'padding': 12,
        },
      },
      {
        selector: 'edge',
        style: {
          'curve-style': 'straight',
          opacity: 0.75,
        },
      },
      { selector: ':selected', style: { 'border-width': 3, 'border-color': '#fff' } },
    ],
    layout: layoutOptions(),
    wheelSensitivity: 0.25,
  });

  cy.on('tap', 'node', onNodeTap);
  cy.on('tap', 'edge', (evt) => showEdge(evt.target.data('source'), evt.target.data('target')));
  cy.on('tap', (evt) => { if (evt.target === cy) onBackgroundTap(); });
  cy.on('cxttap', 'node', onNodeContext);
  cy.on('cxttap', 'edge', onEdgeContext);
  cy.on('mouseover', 'node', (evt) => {
    if (!evt.target.data('isCluster')) showTooltip(evt.target.data('id'));
  });
  cy.on('mouseout', 'node', hideTooltip);
  document.getElementById('cy').addEventListener('mousemove', moveTooltip);

  applySearch();
  if (!currentNoteId) renderLegend(window._lastClusters);
}

function layoutOptions() {
  if (cytoscape.prototype.layout && window.cytoscapeFcose) {
    return {
      name: 'fcose',
      animate: false,
      randomize: true,
      nodeRepulsion: 7000,
      idealEdgeLength: 80,
      nestingFactor: 0.25,
      gravity: 0.3,
      packComponents: true,
    };
  }
  return { name: 'cose', animate: false };
}

function edgeColor(method) {
  if (method.includes('pinned')) return '#ffd166';
  if (method.includes('tag-overlap')) return '#a7c957';
  if (method.includes('manual')) return '#bc4749';
  return '#888';
}

// ---- panels ---------------------------------------------------------------

function renderLegend(clusters) {
  const list = (clusters || [])
    .filter((c) => c.id >= 0)
    .map((c) => `
      <li>
        <span class="swatch" style="background:${colorFor(c.id)}" title="cluster ${c.id}"></span>
        <span class="cl-label">${escapeHtml(c.label)}</span>
        <span class="cl-size">${c.size}</span>
      </li>`)
    .join('');
  panel.innerHTML = `
    <p class="hint">Click a node to view/edit. Click an edge to see why. Right-click for more options.</p>
    <h3 class="legend-title">Clusters</h3>
    <ul class="legend">${list || '<li class="hint">No clusters yet — add and save notes.</li>'}</ul>
  `;
}

async function showNote(id) {
  currentNoteId = String(id);
  let note = noteCache.get(currentNoteId);
  if (!note) {
    const r = await fetch(`/api/notes/${id}`);
    if (!r.ok) return;
    note = await r.json();
    noteCache.set(currentNoteId, note);
  }
  panel.innerHTML = `
    <div class="row"><input id="n-title" type="text" placeholder="Title" /></div>
    <div class="row"><textarea id="n-body" placeholder="Body (use #tag to tag)"></textarea></div>
    <div class="row">
      <button class="primary" id="n-save">Save</button>
      <button class="danger" id="n-delete">Delete</button>
    </div>
    <p class="hint">Created ${escapeHtml(note.created_at)} · Updated ${escapeHtml(note.updated_at)}</p>
  `;
  document.getElementById('n-title').value = note.title;
  document.getElementById('n-body').value = note.body;
  document.getElementById('n-save').onclick = () => saveNote(id);
  document.getElementById('n-delete').onclick = () => deleteNote(id);
  highlightActive();
}

async function saveNote(id) {
  await fetch(`/api/notes/${id}`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      title: document.getElementById('n-title').value,
      body: document.getElementById('n-body').value,
    }),
  });
  noteCache.delete(String(id));
  await fetchNotes();
  await loadGraph();
  highlightActive();
}

async function deleteNote(id) {
  if (!confirm('Delete this note?')) return;
  await fetch(`/api/notes/${id}`, { method: 'DELETE' });
  noteCache.delete(String(id));
  currentNoteId = null;
  await fetchNotes();
  await loadGraph();
  renderLegend(window._lastClusters);
}

async function showEdge(a, b) {
  currentNoteId = null;
  highlightActive();
  const r = await fetch(`/api/edges/${a}/${b}`);
  if (!r.ok) return;
  const e = await r.json();
  const badge = e.override
    ? `<span class="badge ${e.override}">${e.override}</span>`
    : '';
  panel.innerHTML = `
    <div class="edge-explain">
      <div class="method">${escapeHtml(e.method)}${badge}</div>
      <div class="score">${e.score.toFixed(3)}</div>
      <div class="reason">${escapeHtml(e.reason)}</div>
      <p class="hint">Notes #${e.source_id} ↔ #${e.target_id}</p>
      <div class="row" style="margin-top:14px">
        <button id="e-pin">${e.override === 'pinned' ? 'Unpin' : 'Pin'}</button>
        <button id="e-suppress">${e.override === 'suppressed' ? 'Restore' : 'Suppress'}</button>
      </div>
    </div>
  `;
  document.getElementById('e-pin').onclick = async () => {
    if (e.override === 'pinned') {
      await fetch(`/api/edges/${e.source_id}/${e.target_id}/override`, { method: 'DELETE' });
    } else {
      await fetch(`/api/edges/${e.source_id}/${e.target_id}/pin`, { method: 'POST' });
    }
    await loadGraph();
    showEdge(e.source_id, e.target_id);
  };
  document.getElementById('e-suppress').onclick = async () => {
    if (e.override === 'suppressed') {
      await fetch(`/api/edges/${e.source_id}/${e.target_id}/override`, { method: 'DELETE' });
    } else {
      await fetch(`/api/edges/${e.source_id}/${e.target_id}/suppress`, { method: 'POST' });
    }
    await loadGraph();
    // After suppress, edge may not exist visually anymore — clear panel.
    renderLegend(window._lastClusters);
  };
}

// ---- sidebar --------------------------------------------------------------

function renderNotesList() {
  notesCount.textContent = `${allNotes.length}`;
  const q = (searchInput.value || '').toLowerCase().trim();
  notesList.innerHTML = allNotes
    .map((n) => {
      const hay = `${n.title} ${n.body}`.toLowerCase();
      const dim = q && !hay.includes(q);
      const snippet = (n.body || '').slice(0, 80).replace(/\n/g, ' ');
      return `
        <li data-id="${n.id}" class="${dim ? 'dim' : ''}">
          <div class="nl-title">${escapeHtml(n.title || `Note ${n.id}`)}</div>
          ${snippet ? `<div class="nl-snippet">${escapeHtml(snippet)}</div>` : ''}
        </li>`;
    })
    .join('');
  notesList.querySelectorAll('li').forEach((li) => {
    li.onclick = () => showNote(li.dataset.id);
  });
  highlightActive();
}

function highlightActive() {
  notesList.querySelectorAll('li').forEach((li) => {
    li.classList.toggle('active', li.dataset.id === currentNoteId);
  });
}

// ---- search ---------------------------------------------------------------

function applySearch() {
  const q = (searchInput.value || '').toLowerCase().trim();
  if (!cy) return;
  cy.batch(() => {
    cy.nodes().forEach((n) => {
      if (n.data('isCluster')) return;
      const note = noteCache.get(String(n.data('id')));
      const hay = note
        ? `${note.title} ${note.body}`.toLowerCase()
        : (n.data('label') || '').toLowerCase();
      const match = !q || hay.includes(q);
      n.toggleClass('cy-dimmed', !match);
      n.toggleClass('cy-match', !!q && match);
    });
    cy.edges().forEach((e) => {
      const src = cy.getElementById(e.data('source'));
      const tgt = cy.getElementById(e.data('target'));
      const dim = src.hasClass('cy-dimmed') || tgt.hasClass('cy-dimmed');
      e.toggleClass('cy-dimmed', dim);
    });
  });
  cy.style()
    .selector('.cy-dimmed').style({ opacity: 0.12 })
    .selector('.cy-match').style({ 'border-width': 3, 'border-color': '#ffd166' })
    .update();
}

searchInput.addEventListener('input', () => {
  renderNotesList();
  applySearch();
});

// ---- threshold ------------------------------------------------------------

thresholdInput.addEventListener('input', () => {
  thresholdVal.textContent = parseFloat(thresholdInput.value).toFixed(2);
});
thresholdInput.addEventListener('change', loadGraph);

// ---- tooltip --------------------------------------------------------------

let tooltipNoteId = null;
async function showTooltip(id) {
  tooltipNoteId = id;
  let note = noteCache.get(String(id));
  if (!note) {
    try {
      const r = await fetch(`/api/notes/${id}`);
      if (!r.ok) return;
      note = await r.json();
      noteCache.set(String(id), note);
    } catch { return; }
  }
  if (tooltipNoteId !== id) return;
  const title = note.title || '(untitled)';
  const body = (note.body || '').slice(0, 150);
  const truncated = (note.body || '').length > 150 ? '…' : '';
  tooltip.innerHTML = `
    <div class="tt-title">${escapeHtml(title)}</div>
    ${body
      ? `<div class="tt-body">${escapeHtml(body)}${truncated}</div>`
      : '<div class="tt-empty">(no body)</div>'}
  `;
  tooltip.hidden = false;
}
function hideTooltip() { tooltipNoteId = null; tooltip.hidden = true; }
function moveTooltip(e) {
  if (tooltip.hidden) return;
  const pad = 14;
  const w = tooltip.offsetWidth, h = tooltip.offsetHeight;
  let x = e.clientX + pad, y = e.clientY + pad;
  if (x + w > window.innerWidth) x = e.clientX - w - pad;
  if (y + h > window.innerHeight) y = e.clientY - h - pad;
  tooltip.style.left = `${x}px`;
  tooltip.style.top = `${y}px`;
}

// ---- context menu / link mode --------------------------------------------

function onNodeTap(evt) {
  hideContextMenu();
  const id = evt.target.data('id');
  if (linkMode) {
    const from = linkMode.from;
    linkMode = null;
    linkBanner.hidden = true;
    if (from && from !== id) {
      fetch(`/api/edges/${from}/${id}/pin`, { method: 'POST' })
        .then(loadGraph)
        .then(() => showEdge(from, id));
    }
    return;
  }
  showNote(id);
}

function onBackgroundTap() {
  hideContextMenu();
  if (linkMode) {
    linkMode = null;
    linkBanner.hidden = true;
  }
}

function onNodeContext(evt) {
  evt.preventDefault && evt.preventDefault();
  const id = evt.target.data('id');
  const { x, y } = evt.renderedPosition || cy.renderer().projectIntoViewport(evt.position.x, evt.position.y);
  const cyRect = document.getElementById('cy').getBoundingClientRect();
  const pageX = cyRect.left + (evt.renderedPosition ? evt.renderedPosition.x : 0);
  const pageY = cyRect.top + (evt.renderedPosition ? evt.renderedPosition.y : 0);
  showContextMenu(pageX, pageY, [
    { label: 'Edit note', fn: () => showNote(id) },
    { label: 'Add link from here…', fn: () => startLinkMode(id) },
    { sep: true },
    { label: 'Delete note', danger: true, fn: () => deleteNote(id) },
  ]);
}

function onEdgeContext(evt) {
  evt.preventDefault && evt.preventDefault();
  const a = evt.target.data('source'), b = evt.target.data('target');
  const cyRect = document.getElementById('cy').getBoundingClientRect();
  const pageX = cyRect.left + (evt.renderedPosition ? evt.renderedPosition.x : 0);
  const pageY = cyRect.top + (evt.renderedPosition ? evt.renderedPosition.y : 0);
  showContextMenu(pageX, pageY, [
    { label: 'Explain edge', fn: () => showEdge(a, b) },
    { label: 'Pin edge', fn: () => fetch(`/api/edges/${a}/${b}/pin`, { method: 'POST' }).then(loadGraph) },
    { label: 'Suppress edge', fn: () => fetch(`/api/edges/${a}/${b}/suppress`, { method: 'POST' }).then(loadGraph) },
    { label: 'Clear override', fn: () => fetch(`/api/edges/${a}/${b}/override`, { method: 'DELETE' }).then(loadGraph) },
  ]);
}

function showContextMenu(x, y, items) {
  ctxMenu.innerHTML = items
    .map((it, i) => it.sep
      ? '<div class="sep"></div>'
      : `<div class="item ${it.danger ? 'danger' : ''}" data-i="${i}">${escapeHtml(it.label)}</div>`)
    .join('');
  ctxMenu.style.left = `${x}px`;
  ctxMenu.style.top = `${y}px`;
  ctxMenu.hidden = false;
  ctxMenu.querySelectorAll('.item').forEach((el) => {
    el.onclick = () => {
      const it = items[parseInt(el.dataset.i, 10)];
      hideContextMenu();
      if (it && it.fn) it.fn();
    };
  });
}
function hideContextMenu() { ctxMenu.hidden = true; }
window.addEventListener('click', (e) => {
  if (!ctxMenu.contains(e.target)) hideContextMenu();
});
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') { hideContextMenu(); if (linkMode) { linkMode = null; linkBanner.hidden = true; } }
});

function startLinkMode(fromId) {
  linkMode = { from: fromId };
  linkBanner.hidden = false;
}

// ---- header actions -------------------------------------------------------

document.getElementById('new-note').onclick = async () => {
  const r = await fetch('/api/notes', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ title: 'Untitled', body: '' }),
  });
  const note = await r.json();
  await fetchNotes();
  await loadGraph();
  showNote(note.id);
};

document.getElementById('refresh').onclick = async () => {
  await fetchNotes();
  await loadGraph();
};

document.getElementById('toggle-sidebar').onclick = () => {
  sidebar.classList.toggle('collapsed');
};

document.getElementById('import-btn').onclick = () => {
  document.getElementById('import-input').click();
};
document.getElementById('import-input').onchange = async (e) => {
  const files = Array.from(e.target.files || []);
  if (!files.length) return;
  const fd = new FormData();
  files.forEach((f) => fd.append('files', f, f.name));
  await fetch('/api/import', { method: 'POST', body: fd });
  e.target.value = '';
  await fetchNotes();
  await loadGraph();
};

// ---- boot -----------------------------------------------------------------

(async () => {
  thresholdVal.textContent = parseFloat(thresholdInput.value).toFixed(2);
  await fetchNotes();
  await loadGraph();
})();
