const SNAPSHOTS_BASE = '/assets/json/summaries';
const FALLBACK = '/assets/json/summary.json';

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

function renderNav(index, currentDate) {
  const nav = document.getElementById('nav');
  if (!nav) return;
  nav.innerHTML = '';
  if (index.length <= 1) return;

  const currentIdx = index.indexOf(currentDate);

  // ← Prev (older = higher index)
  const prevDate = index[currentIdx + 1];
  const prevLink = document.createElement('a');
  prevLink.textContent = '← Prev';
  if (prevDate) {
    prevLink.href = `#${prevDate}`;
    prevLink.addEventListener('click', e => { e.preventDefault(); navigate(prevDate, index); });
  } else {
    prevLink.classList.add('nav-disabled');
  }

  // dropdown
  const select = document.createElement('select');
  index.forEach(date => {
    const opt = document.createElement('option');
    opt.value = date;
    opt.textContent = date;
    if (date === currentDate) opt.selected = true;
    select.appendChild(opt);
  });
  select.addEventListener('change', () => navigate(select.value, index));

  // Next → (newer = lower index)
  const nextDate = index[currentIdx - 1];
  const nextLink = document.createElement('a');
  nextLink.textContent = 'Next →';
  if (nextDate) {
    nextLink.href = `#${nextDate}`;
    nextLink.addEventListener('click', e => { e.preventDefault(); navigate(nextDate, index); });
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
      container.textContent = 'No summary available yet. Check back after the next Monday run.';
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
      omitted.forEach(item => {
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

async function navigate(date, index) {
  try {
    const data = await loadSnapshot(date);
    renderSummary(data);
    renderNav(index, date);
    history.replaceState(null, '', `#${date}`);
  } catch (e) {
    console.error(e);
  }
}

(async () => {
  const index = await loadIndex();
  const hash = window.location.hash.replace('#', '');
  const currentDate = (hash && index.includes(hash)) ? hash : (index[0] || null);

  let data;
  if (currentDate) {
    try {
      data = await loadSnapshot(currentDate);
    } catch {
      data = await loadFallback();
    }
  } else {
    data = await loadFallback();
  }

  renderSummary(data);
  if (currentDate) renderNav(index, currentDate);
})();
