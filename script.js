// Function to generate the table
function generateTable(data) {
  if (!data || data.length === 0) return "No data available.";
  // Create the table element
  const table = document.createElement('table');
  table.setAttribute('id', 'pr-table');
  //table.classList.add("searchable", "sortable");
  table.classList.add('searchable');
  //table.classList.add('sortable');
  
  // Generate table headers
  const thead = table.createTHead();
  const headerRow = thead.insertRow();

  const keys = Object.keys(data[0]); // Get keys from the first object
  keys.forEach(headerText => {
    const th = document.createElement("th");
    th.textContent = headerText.charAt(0).toUpperCase() + headerText.slice(1);
    //th.textContent = headerText;
    headerRow.appendChild(th);
  });

  const tbody = table.createTBody();
  
  // Generate table rows
  data.forEach(item => {
    const row = tbody.insertRow();
    keys.forEach(key => {
      //const th = document.createElement("th");
      const td = document.createElement('td');
      td.innerHTML = item[key] || ""; // Fill empty fields with blank
      row.appendChild(td);
    });
    tbody.appendChild(row);
  });
  return table;
}

 
import jsonData from './sample.json' with {type:'json'}
//var jsonStr = JSON.stringify(jsonData);
//const newParagraph = document.createElement("p");
//newParagraph.textContent = "Hi " + jsonStr;
//document.body.appendChild(newParagraph);

const container = document.getElementById('table-container');
const table = generateTable(jsonData.data);
if (table) container.appendChild(table);
