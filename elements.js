// get html element info string from server (via do_GET "/Elements")
function loadElements() {
    $.get('http://localhost:53333/Elements', function(data) {
        //clear table body
        $("#element_body").empty();
        //fill with response from server
        $("#element_body").html(data);
    });
}

//delete chosen element and update table via do_POST "/delete_element"
function deleteElement(element_code) {
    $.post("/delete_element",
        //dictionary with element to delete
        {
            code: element_code
        },
        function (data, status) {
            alert(data + "\nStatus: " + status);
            //re-load element table html
            loadElements();
        }
    );
}

// executes once element.html page loads - load and add elements
$(document).ready(  
  /* this defines a function that gets called after the document is in memory */
  function() {
    loadElements();

    /* add a click handler for our button */
    $("#add_element").click(
        function() {
            /* creates an ajax post request - new connection from browser to server */
            $.post("/Elements",
                /* pass a JavaScript dictionary - data browser sending to post request */
                {
                    element_no: $("#element_no").val() || 1,
                    element_code: $("#element_code").val() || "H",
                    element_name: $("#element_name").val() || "Hydrogen",
                    radius: $("#radius").val().substring() || 40,
                    colour1: $("#colour1").val().substring(1) || "FFFFFF",
                    colour2: $("#colour2").val().substring(1) || "050505",
                    colour3: $("#colour3").val().substring(1) || "020202",
                }, //js dictionary ends here, first key is id with tag name and value assoc'd with it gets retrieved

                //callback function: gets called when data gets back from server, shows user something is happening
                function(data, status)
                {
                    //gets message back from ajax server and status (ex. 200 -> translates to "success")
                    alert(data + "\nStatus: " + status);
                    //reload element table in html
                    loadElements();
                    //clear form submission once element added to db
                    if (data.includes("Invalid") == false) {
                        list = ['#element_no', '#element_code', '#element_name', '#radius', '#colour1', '#colour2', '#colour3'];
                        list.forEach(item => {
                            $(item).val("");
                        });
                    }
                }
            );
        }
    );
  }
);
