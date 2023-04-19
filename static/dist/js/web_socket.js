"use strict";

function connect() {
    print_warn("connect WebSocket in page");
    const host_server = location.host;
    let ws_str = "wss://";
    if (location.protocol !== "https:") {
        // debug("http")
        ws_str = "ws://";
    }
    let ws = new WebSocket(ws_str + host_server + "/ws");
    ws.onopen = function () {
        // subscribe to some channels
        // ws.send(JSON.stringify({
        // }));
    };

    ws.onclose = function (e) {
        console.log("Socket is closed. Reconnect will be attempted in 5 second.", e.reason);
        toastMixin.fire({
            background: bg_mode_theme,
            title: `Server Reload`,
            text: "reload......",
            icon: "warning",
        });
        location.reload();
    };

    ws.onerror = function (err) {
        console.error("Socket encountered error: ", err.message, "Closing socket");
        ws.close();
    };
    console.log(host_server);
    ws.onmessage = function (event) {
        let msg_from_ws = event.data;
        let json_msg = null;
        // debug(event);
        try {
            json_msg = JSON.parse(event.data);
        } catch (error) {
            console.info("ws.onmessage:" + msg_from_ws);
            if (msg_from_ws == "Connect to Server Success") {
                debug("ON LINE");
            }
            if (msg_from_ws == "location.reload()") {
                location.reload();
            }
        }
        if (json_msg == null) {
            return;
        }
    };

    function sendMessage(event) {
        var input = document.getElementById("messageText");
        ws.send(input.value);
        input.value = "";
        event.preventDefault();
    }
}
connect();
