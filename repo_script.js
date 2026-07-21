function generateRepoTable(data) {
  if (!data || data.length === 0) return "No data available.";
  // Create the table element
  const table = document.createElement('table');
  table.setAttribute('id', 'repo-table');
  
  const tbody = table.createTBody();
  var i=0;
  var isFirst=1;
  // Generate table rows
  var row = tbody.insertRow();
  data.forEach(item => {
    if (i==0 ) {
      if ( isFirst==0 ) {
        tbody.appendChild(row);
        row = tbody.insertRow();
      }
      else{ isFirst=0; } 
    }
    const td = document.createElement('td');
    td.innerHTML = item;
    row.appendChild(td)
  });    
  tbody.appendChild(row);

  return table;
}
 
import jsonData from './repo_data.json' with {type:'json'}
console.log("loaded data");
const container = document.getElementById('repo-table-container');
console.log("got container - calling function");
const table = generateRepoTable(jsonData.data);
if (table) { 
  console.log("Adding table");
  container.appendChild(table);
}
