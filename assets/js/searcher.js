function searcher() {
  // Declare variables
  var input, filter, table, tr, td, i, txtValue, tds, matches;
  input = document.getElementById("myInput");
  filter = input.value.toUpperCase();
  table = document.getElementById("pr-table");
  tr = table.getElementsByTagName("tr");
  console.log(tr.length);
  // Loop through all table rows, and hide those who don't match the search query
  for (i = 0; i < tr.length; i++) {
    tds = tr[i].getElementsByTagName("td") //[0];
    matches=0;
    if ( tds.length == 0 ) { matches = 1; } //header
    for (j = 0; j< tds.length; j++ ) {
      td = tds[j];
      if (td) {
        txtValue = td.textContent || td.innerText;
        if (txtValue.toUpperCase().indexOf(filter) > -1) {
          matches=1;
        }
      }
    }
    if ( matches==1 ) {
      tr[i].style.display = "";
    } else {
      tr[i].style.display = "none";
    }
  }
}
