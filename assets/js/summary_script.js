import jsonData from '../json/summary.json' with {type: 'json'};

const updatedEl = document.getElementById('last-updated');
if (updatedEl && jsonData.updated_at) {
  updatedEl.textContent = 'Last updated: ' + new Date(jsonData.updated_at).toUTCString();
}

const periodEl = document.getElementById('period');
if (periodEl && jsonData.period_start && jsonData.period_end) {
  periodEl.textContent = `Period: ${jsonData.period_start} to ${jsonData.period_end}`;
}

const container = document.getElementById('summary-container');
if (container) {
  const summaryText = Array.isArray(jsonData.summary)
    ? jsonData.summary.join('\n\n')
    : jsonData.summary;
  if (summaryText) {
    container.innerHTML = marked.parse(summaryText);
  } else {
    container.textContent = 'No summary available yet. Check back after the next Monday run.';
  }
}

const omitted = jsonData.omitted || [];
const omittedSection = document.getElementById('omitted-section');
if (omittedSection && omitted.length > 0) {
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
    if (item.reason) {
      li.appendChild(document.createTextNode(` — ${item.reason}`));
    }
    ul.appendChild(li);
  });
  details.appendChild(ul);
  omittedSection.appendChild(details);
}
