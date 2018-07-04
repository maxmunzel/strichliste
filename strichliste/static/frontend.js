var barn = new Barn(localStorage);
const queueKey = "requestQueue";
const reloadEvery = "300"; // reload timeout in seconds
var psk = barn.get("psk");
if (psk === null) {
    psk = "";
    barn.set("psk", "");
}
var ready = true;
function sign(url){
    var challenge = $.ajax({
            type: "GET",
            url: "challenge",
            async: false
        }).responseText;
    return url + "/" + sha512(url + challenge + psk);
}
function commitRequests() {
    if (ready && barn.llen(queueKey) > 0) {
        ready = false; // only one request at a time
        var url = barn.lrange(queueKey, 0, 0)[0];
        var jqxhr = $.ajax(sign(url))
            .done(function () {
                barn.lpop(queueKey);
                
            })
            .always(function (a,b) {
                ready = true;
                if (barn.llen(queueKey) > 0) {
                    document.getElementById("network_problem").style.visibility = "visible";
                } else {
                    document.getElementById("network_problem").style.visibility = "hidden";
                }
            });
    }
    // should you ever increase this rate, make sure to tweak
    // ../tests/test_strichliste.py->test_chrome_buffering()
    // accordingly as it expects high frequency bookings to be
    // buffered (to test the client-side buffering mechanism)
    setTimeout(commitRequests, 100);
}

function reloadWhenOnline() {
    // reloads the page, but waits for server to be online
    $.ajax("")
        .done(function () {
            location.reload()
        })
        .always(function () {
            setTimeout(reloadWhenOnline, 2000)
        });
}

$(function(){
    commitRequests(); // start commit handler
    setTimeout(reloadWhenOnline, reloadEvery * 1000);
});

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

    var url = "/add_transaction/" + human_id + "/" + category_id + "/" + String(amount);
    barn.rpush(queueKey, url);
}

function undo() {
    $.ajax(sign("undo"))
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
                var jqxhr = $.ajax(sign(url))
                    .done(function () {
                        location.reload();
                    })
            }
        }]
    });
}