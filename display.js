// rotate molecule, set svg html data returned into #molecule
function rotate() {
    mol = $("#mol_name").val();
    axis = $("#axis").val();
    degrees = $("#degrees").val();

    $.post('http://localhost:53333/rotate',
        {
            mol_name: mol,
            axis: axis,
            degrees: degrees
        },

        function (data, status) {
            $("#molecule").empty();
            $("#molecule").html(data);
        }
    );
}

// save molecule's rotation
function save() {
    $.post("/save",
      { mol_name: $("#mol_name").val() },
      function (data, status) {
        alert(data);
      }
    );
}

// reset molecule's rotation
function reset() {
    $.post('http://localhost:53333/reset'),
      { mol_name: $("#mol_name") },
      function (data, status) {
        alert("k");
        $("#molecule").empty();
        $("#molecule").html(data);
      }
  }