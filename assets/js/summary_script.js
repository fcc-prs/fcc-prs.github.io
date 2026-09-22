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
    ? jsonData.summary.join('\n')
    : jsonData.summary;
  if (summaryText) {
    container.innerHTML = marked.parse(summaryText);
  } else {
    container.textContent = 'No summary available yet. Check back after the next Monday run.';
  }
}
