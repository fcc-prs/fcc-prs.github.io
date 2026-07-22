function searcher() {
  var input, filter, table, tr, td, tds, matches, i, j, txtValue;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("pr-table");
  tr = table.getElementsByTagName("tr");
  console.log(tr.length);
  for (i = 0; i < tr.length; i++) {
    // Expand rows are handled below alongside their parent — skip them here
    if (tr[i].classList.contains('comment-expand-row')) continue;

    tds = tr[i].getElementsByTagName("td");
    matches = 0;
    if (tds.length === 0) { matches = 1; } // header row — always show
    for (j = 0; j < tds.length; j++) {
      td = tds[j];
      if (td) {
        txtValue = td.textContent || td.innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          matches = 1;
        }
      }
    }
    if (matches === 1) {
      tr[i].style.display = "";
      // Restore expand row to its CSS-controlled state (open or closed per toggle)
      if (i + 1 < tr.length && tr[i + 1].classList.contains('comment-expand-row')) {
        tr[i + 1].style.display = "";
      }
    } else {
      tr[i].style.display = "none";
      // Force-hide the expand row when its parent is filtered out
      if (i + 1 < tr.length && tr[i + 1].classList.contains('comment-expand-row')) {
        tr[i + 1].style.display = "none";
      }
    }
  }
}
