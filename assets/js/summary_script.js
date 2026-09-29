const SNAPSHOTS_BASE = '/assets/json/summaries';
const FALLBACK = '/assets/json/summary.json';
const CURRENT_KEY = 'current';

async function loadIndex() {
  try {
    const res = await fetch(`${SNAPSHOTS_BASE}/index.json`);
    if (!res.ok) return [];
    return await res.json();
  } catch {
    return [];
  }
}

async function loadSnapshot(date) {
  const res = await fetch(`${SNAPSHOTS_BASE}/${date}.json`);
  if (!res.ok) throw new Error(`Failed to load snapshot ${date}`);
  return await res.json();
}

async function loadFallback() {
  const res = await fetch(FALLBACK);
  if (!res.ok) throw new Error('Failed to load summary.json');
  return await res.json();
}

// Full nav list is [CURRENT_KEY, ...index] where CURRENT_KEY always loads summary.json.
// currentLabel is the period_end from summary.json, used to label the current entry.
function renderNav(index, currentKey, currentLabel) {
  const nav = document.getElementById('nav');
  if (!nav) return;
  nav.innerHTML = '';

  // All entries: current + weekly snapshots
  const allKeys = [CURRENT_KEY, ...index];
  if (allKeys.length <= 1) return; // only current, no snapshots yet

  const labels = { [CURRENT_KEY]: `${currentLabel} (current)` };
  index.forEach(d => { labels[d] = d; });

  const currentIdx = allKeys.indexOf(currentKey);

  // ← Prev (older = higher index)
  const prevKey = allKeys[currentIdx + 1];
  const prevLink = document.createElement('a');
  prevLink.textContent = '← Prev';
  if (prevKey) {
    prevLink.href = `#${prevKey}`;
    prevLink.addEventListener('click', e => { e.preventDefault(); navigate(prevKey, index, currentLabel); });
  } else {
    prevLink.classList.add('nav-disabled');
  }

  // dropdown
  const select = document.createElement('select');
  allKeys.forEach(key => {
    const opt = document.createElement('option');
    opt.value = key;
    opt.textContent = labels[key];
    if (key === currentKey) opt.selected = true;
    select.appendChild(opt);
  });
  select.addEventListener('change', () => navigate(select.value, index, currentLabel));

  // Next → (newer = lower index)
  const nextKey = allKeys[currentIdx - 1];
  const nextLink = document.createElement('a');
  nextLink.textContent = 'Next →';
  if (nextKey) {
    nextLink.href = `#${nextKey}`;
    nextLink.addEventListener('click', e => { e.preventDefault(); navigate(nextKey, index, currentLabel); });
  } else {
    nextLink.classList.add('nav-disabled');
  }

  nav.appendChild(prevLink);
  nav.appendChild(select);
  nav.appendChild(nextLink);
}

function renderSummary(data) {
  const periodEl = document.getElementById('period');
  if (periodEl) {
    periodEl.textContent = (data.period_start && data.period_end)
      ? `Period: ${data.period_start} to ${data.period_end}`
      : '';
  }

  const container = document.getElementById('summary-container');
  if (container) {
    const summaryText = Array.isArray(data.summary)
      ? data.summary.join('\n\n')
      : (data.summary || '');
    if (summaryText) {
      container.innerHTML = marked.parse(summaryText);
    } else {
      container.textContent = 'No summary available yet.';
    }
  }

  const omitted = data.omitted || [];
  const omittedSection = document.getElementById('omitted-section');
  if (omittedSection) {
    omittedSection.innerHTML = '';
    if (omitted.length > 0) {
      const details = document.createElement('details');
      const summary = document.createElement('summary');
      summary.textContent = `Omitted PRs (${omitted.length})`;
      details.appendChild(summary);
      const ul = document.createElement('ul');
      omitted.filter(item => item.url).forEach(item => {
        const li = document.createElement('li');
        const link = document.createElement('a');
        link.href = item.url || '#';
        link.textContent = item.pr;
        link.target = '_blank';
        li.appendChild(link);
        if (item.reason) li.appendChild(document.createTextNode(` — ${item.reason}`));
        ul.appendChild(li);
      });
      details.appendChild(ul);
      omittedSection.appendChild(details);
    }
  }
}

async function navigate(key, index, currentLabel) {
  try {
    let data;
    if (key === CURRENT_KEY) {
      data = await loadFallback();
      history.replaceState(null, '', window.location.pathname);
    } else {
      data = await loadSnapshot(key);
      history.replaceState(null, '', `#${key}`);
    }
    renderSummary(data);
    renderNav(index, key, currentLabel);
  } catch (e) {
    console.error(e);
  }
}

(async () => {
  const [index, currentData] = await Promise.all([loadIndex(), loadFallback()]);
  const currentLabel = currentData.period_end || '';

  const hash = window.location.hash.replace('#', '');
  const activeKey = (hash && index.includes(hash)) ? hash : CURRENT_KEY;

  let data;
  if (activeKey === CURRENT_KEY) {
    data = currentData;
  } else {
    try {
      data = await loadSnapshot(activeKey);
    } catch {
      data = currentData;
    }
  }

  renderSummary(data);
  renderNav(index, activeKey, currentLabel);
})();
