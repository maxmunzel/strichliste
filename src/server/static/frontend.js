var requestQueue = [];
var ready = true;
function commitRequests() {
    if (ready && requestQueue.length > 0) {
        ready = false; // only one request at a time
        var url = requestQueue[0];
        var jqxhr = $.ajax(url)
            .done(function () {
                requestQueue.shift();
                if (requestQueue.length == 0) {
                    document.getElementById("network_problem").style.visibility = "hidden";
                }
            })
            .fail(function () {
                document.getElementById("network_problem").style.visibility = "visible";
            })
            .always(function (a,b) {
                ready = true;
            });
    }
    setTimeout(commitRequests, 500);
}
commitRequests(); // start commit handler
function book(human_id, category_id, amount, increment_button) {
    if (typeof increment_button === "undefined") {
        increment_button = true
    }

    if (increment_button) {
        //increment button locally
        var id = "bt-" + human_id + "%" + category_id;
        var button = document.getElementById(id);
        button.textContent = Number(button.textContent) + amount;
    }

    var url = "add_transaction/" + human_id + "/" + category_id + "/" + String(amount);
    requestQueue.push(url)
}

function undo() {
    $.ajax("undo")
        .done(function () {
            location.reload();
        })
        .fail(function () {
            alert("Error. Couldn't undo");
        })
}

function batch_order(human_id, category_id) {
    BootstrapDialog.show({
        title: 'Kastengröße wählen',
        // message: 'Click buttons below.',
        buttons: [{
            label: '24 (Rothaus)',
            action: function () {
                book(human_id, category_id, 24);
                BootstrapDialog.closeAll()
            }
        }, {
            label: '20 (Ötti/Flens)',
            action: function () {
                book(human_id, category_id, 20);
                BootstrapDialog.closeAll()
            }
        }, {
            label: '12 (Wasser)',
            action: function () {
                book(human_id, category_id, 6);
                BootstrapDialog.closeAll()
            }
        }]
    });
}

function addUserDialog() {
    BootstrapDialog.show({
        title: 'Neuen Nutzer ',
        message: $('<input type="text" id="newUserName" value="" maxlength="100" />'),
        buttons: [{
            label: 'anlegen',
            cssClass: 'btn-primary',
            hotkey: 13, // Enter.
            action: function () {
                var url = ("add_user/" + document.getElementById("newUserName").value);
                var jqxhr = $.ajax(url)
                    .done(function () {
                        location.reload();
                    })
            }
        }]
    });
}