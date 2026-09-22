import jsonData from '../json/merged_data.json' with {type: 'json'};

function buildTable(prs) {
  if (!prs || prs.length === 0) {
    return Object.assign(document.createElement('p'), {textContent: 'No merged pull requests in the last 7 days.'});
  }

  const table = document.createElement('table');
  table.className = 'sortable';

  const thead = table.createTHead();
  const headerRow = thead.insertRow();
  ['Repository', '#', 'Title', 'Author', 'Merged', 'Merged by', 'Labels'].forEach(text => {
    const th = document.createElement('th');
    th.textContent = text;
    headerRow.appendChild(th);
  });

  const tbody = table.createTBody();
  prs.forEach(pr => {
    const row = tbody.insertRow();

    const repoCell = row.insertCell();
    const repoLink = document.createElement('a');
    repoLink.href = `https://github.com/${pr.org}/${pr.repo}`;
    repoLink.innerHTML = `${pr.org}/<br>${pr.repo}`;
    repoCell.appendChild(repoLink);

    row.insertCell().textContent = pr.num;

    const titleCell = row.insertCell();
    const titleLink = document.createElement('a');
    titleLink.href = pr.url;
    titleLink.textContent = pr.title;
    titleCell.appendChild(titleLink);

    row.insertCell().textContent = pr.author;
    row.insertCell().textContent = pr.mergedAt;
    row.insertCell().textContent = pr.mergedBy;
    row.insertCell().textContent = pr.labels.join('\n');
  });

  return table;
}

const container = document.getElementById('table-container');
if (container) {
  container.appendChild(buildTable(jsonData.data));
}

const updatedEl = document.getElementById('last-updated');
if (updatedEl && jsonData.updated_at) {
  updatedEl.textContent = 'Last updated: ' + new Date(jsonData.updated_at).toUTCString();
}
