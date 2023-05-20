/* display selected molecule on the same page */
function displayMol(mol_name) {
    $.post('http://localhost:53333/display',
        {mol: mol_name},
        function (data, status) {
            /* empty div window before filling it with html data */
            $("#svg_window").empty();
            $("#svg_window").html(data);
        }
    );
}

/* load molecule into the displayed table */
function loadMols() {
    $.get('http://localhost:53333/Molecules', function(data, status) {
        $("#mol_body").empty();
        //fill body with response (data) from the server
        $("#mol_body").html(data);
    });
}

$(document).ready(
    /* this defines a function that gets called after the document is in memory */
    function () {
        loadMols();
    }
);

/* delete selected molecule */
function deleteMols(mol_name) {
    alert("Molecule " + mol_name + " will be deleted.");
}
