import jsonData from '../json/sample.json' with {type: 'json'};
import commentsData from '../json/comments.json' with {type: 'json'};

// Pending comments: key -> [{text}]
const pendingComments = {};

// Derive a stable key from the repo HTML string and PR number.
// repo field looks like "key4hep/<br>k4geo" — strip tags and whitespace.
function makeKey(repo, num) {
  return repo.replace(/<[^>]+>/g, '').trim() + '_' + num;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function totalPending() {
  return Object.values(pendingComments).reduce((n, a) => n + a.length, 0);
}

function updateSubmitButton() {
  const btn = document.getElementById('submit-pr-btn');
  if (!btn) return;
  const n = totalPending();
  if (n > 0) {
    btn.textContent = `Prepare PR (${n} comment${n !== 1 ? 's' : ''})`;
    btn.classList.remove('hidden');
  } else {
    btn.classList.add('hidden');
  }
}

function renderComment(author, date, text, isPending) {
  const div = document.createElement('div');
  div.className = 'pr-comment' + (isPending ? ' pr-comment--pending' : '');
  const badge = isPending ? ' <span class="pr-comment-badge">pending</span>' : '';
  div.innerHTML =
    `<div class="pr-comment-meta">${escapeHtml(author)} · ${escapeHtml(date)}${badge}</div>` +
    `<div class="pr-comment-text">${escapeHtml(text)}</div>`;
  return div;
}

function generateTable(data, comments) {
  if (!data || data.length === 0) return null;

  const table = document.createElement('table');
  table.id = 'pr-table';
  table.classList.add('sortable');

  const keys = Object.keys(data[0]);
  const colCount = keys.length + 1;

  // Header row
  const thead = table.createTHead();
  const headerRow = thead.insertRow();
  // Comment toggle column comes first
  const thExtra = document.createElement('th');
  thExtra.className = 'no-sort';
  headerRow.appendChild(thExtra);
  keys.forEach(k => {
    const th = document.createElement('th');
    th.textContent = k.charAt(0).toUpperCase() + k.slice(1);
    headerRow.appendChild(th);
  });

  const tbody = table.createTBody();

  data.forEach(item => {
    const key = makeKey(item.repo, item.num);
    const existing = comments.data?.[key] ?? [];

    // --- data row ---
    const row = tbody.insertRow();
    row.dataset.prKey = key;

    keys.forEach(k => {
      const td = document.createElement('td');
      td.innerHTML = item[k] ?? '';
      row.appendChild(td);
    });

    // Toggle cell — shows comment count and opens the expand row
    const tdToggle = document.createElement('td');
    tdToggle.className = 'comment-toggle-cell';
    const toggleBtn = document.createElement('button');
    toggleBtn.className = 'comment-toggle-btn';
    toggleBtn.setAttribute('aria-expanded', 'false');

    const refreshToggleLabel = () => {
      const pending = pendingComments[key]?.length ?? 0;
      const total = existing.length + pending;
      toggleBtn.textContent = total > 0 ? `💬 ${total}` : '💬';
      toggleBtn.title = `${total} comment${total !== 1 ? 's' : ''}`;
    };
    refreshToggleLabel();

    tdToggle.appendChild(toggleBtn);
    row.insertBefore(tdToggle, row.firstChild);

    // --- expandable comment row (kept off-table until opened) ---
    const expandRow = document.createElement('tr');
    expandRow.className = 'comment-expand-row';
    expandRow.dataset.prKey = key;

    const expandTd = document.createElement('td');
    expandTd.colSpan = colCount;
    expandTd.className = 'comment-expand-cell';

    // Existing (committed) comments
    const commentList = document.createElement('div');
    commentList.className = 'comment-list';
    existing.forEach(c => {
      commentList.appendChild(renderComment(c.author, c.date, c.text, false));
    });
    expandTd.appendChild(commentList);

    // Add-comment form
    const form = document.createElement('div');
    form.className = 'comment-form';

    const textarea = document.createElement('textarea');
    textarea.className = 'comment-textarea';
    textarea.placeholder = 'Add a comment…';
    textarea.rows = 2;

    const addBtn = document.createElement('button');
    addBtn.className = 'comment-add-btn';
    addBtn.type = 'button';
    addBtn.textContent = 'Add';
    addBtn.addEventListener('click', () => {
      const text = textarea.value.trim();
      if (!text) return;
      if (!pendingComments[key]) pendingComments[key] = [];
      pendingComments[key].push({ text });
      const today = new Date().toISOString().slice(0, 10);
      commentList.appendChild(renderComment('(you)', today, text, true));
      textarea.value = '';
      refreshToggleLabel();
      updateSubmitButton();
    });

    form.appendChild(addBtn);
    form.appendChild(textarea);
    expandTd.appendChild(form);
    expandRow.appendChild(expandTd);
    // expandRow is NOT added to tbody here — inserted on demand by the toggle

    // Toggle open/close
    toggleBtn.addEventListener('click', () => {
      if (expandRow.parentNode) {
        expandRow.remove();
        toggleBtn.setAttribute('aria-expanded', 'false');
      } else {
        row.after(expandRow);
        toggleBtn.setAttribute('aria-expanded', 'true');
      }
    });
  });

  return table;
}

// Build the merged comments.json content to be submitted via PR.
function buildMergedJson(username) {
  const merged = JSON.parse(JSON.stringify(commentsData));
  const today = new Date().toISOString().slice(0, 10);
  const author = username.trim() || '(anonymous)';
  for (const [key, comments] of Object.entries(pendingComments)) {
    if (!merged.data[key]) merged.data[key] = [];
    for (const c of comments) {
      merged.data[key].push({ author, date: today, text: c.text });
    }
  }
  return JSON.stringify(merged, null, 2);
}

function pendingSummaryText() {
  return Object.entries(pendingComments)
    .map(([key, arr]) => `• ${key}: ${arr.length} comment${arr.length !== 1 ? 's' : ''}`)
    .join('\n');
}

// --- modal wiring ---
const GITHUB_EDIT_URL =
  'https://github.com/fcc-prs/fcc-prs.github.io/edit/main/assets/json/comments.json';

function openModal() {
  document.getElementById('pr-modal-summary').textContent = pendingSummaryText();
  document.getElementById('pr-modal-copy-btn').textContent = 'Copy JSON to Clipboard';
  document.getElementById('pr-modal-json-area').classList.add('hidden');
  document.getElementById('pr-modal-status').textContent = '';
  document.getElementById('pr-modal').classList.remove('hidden');
}

function closeModal() {
  document.getElementById('pr-modal').classList.add('hidden');
}

// --- init ---
const container = document.getElementById('table-container');
const table = generateTable(jsonData.data, commentsData);
if (table) {
  container.appendChild(table);
  const tbody = table.querySelector('tbody');
  // Close any open expand rows before sorting — they're off-table when closed
  // so the sort library never sees them.
  table.querySelectorAll('th').forEach(th => {
    th.addEventListener('click', () => {
      table.querySelectorAll('tr.comment-expand-row').forEach(r => r.remove());
      table.querySelectorAll('.comment-toggle-btn').forEach(btn => btn.setAttribute('aria-expanded', 'false'));
    });
  });
}

updateSubmitButton();

document.getElementById('submit-pr-btn').addEventListener('click', openModal);

document.getElementById('pr-modal-close').addEventListener('click', closeModal);
document.getElementById('pr-modal').addEventListener('click', e => {
  if (e.target === document.getElementById('pr-modal')) closeModal();
});

document.getElementById('pr-modal-copy-btn').addEventListener('click', async () => {
  const username = document.getElementById('pr-modal-username').value;
  const json = buildMergedJson(username);
  const statusEl = document.getElementById('pr-modal-status');
  const copyBtn = document.getElementById('pr-modal-copy-btn');
  try {
    await navigator.clipboard.writeText(json);
    copyBtn.textContent = '✓ Copied!';
    statusEl.textContent = 'JSON copied to clipboard. Now open the GitHub editor and paste it in.';
  } catch {
    // Clipboard API unavailable — show a fallback textarea
    const area = document.getElementById('pr-modal-json-area');
    area.value = json;
    area.classList.remove('hidden');
    area.select();
    statusEl.textContent = 'Could not copy automatically. Select all text in the box above and copy manually (Ctrl+A, Ctrl+C).';
  }
});

document.getElementById('pr-modal-open-btn').addEventListener('click', () => {
  window.open(GITHUB_EDIT_URL, '_blank', 'noopener');
});
