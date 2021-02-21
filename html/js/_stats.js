'use strict';  // use stonks idk
const warning = '<i class="fas fa-exclamation-triangle"></i>';
const offline = '<i class="fas fa-plug"></i>';

async function main() {
    var status = document.getElementById("statustext");
    var result;
    try {
        result = await fetch(
        "https://ya.clicksminuteper.net/api/bot/stats"
    )}
    catch (error) {
        if(error instanceof TypeError) {    
            status.innerHTML = `${offline} Unable to connect to the yourapps API.`;
            return;
        };
    };
    if(result.status==512) {
        status.innerHTML = `${warning} YourApps is not currently able to take requests. Try <a href="javascript:location.reload(true)">reloading</a> after a minute or so.`;
        return;
    }
    else if(!result.ok) {
        status.innerHTML = `${warning} Unexpected response from yourapps: ${result.status} ${result.statusText}`;
        return;
    }
    else {
        const json = await result.json();
        /*
        Example Response:
        {
            "users": 1,
            "guilds": 3,
            "channels": 141,
            "emojis": 66,
            "commands": 94,
            "positions": 723
        }
        */
        status.remove();
        let _ = document.createElement("div");
        _.id = "container2"
        var element = document.getElementById("container").appendChild(
            _
        );
        function add_element(name, innerHTML, where) {
            let d = document.createElement(name);
            d.innerHTML = innerHTML;
            let parent = document.getElementById(where);
            parent.appendChild(d)
        }
        var formatted = [
            `<p><span style="font-size: 24px">Loaded Users:</span> ${json.users}</p><br>`,
            `<p><span style="font-size: 24px">Servers:</span> ${json.guilds}</p><br>`,
            `<p><span style="font-size: 24px">Channels:</span> ${json.channels}</p><br>`,
            `<p><span style="font-size: 24px">Commands:</span> ${json.commands}</p><br>`,
            `<p><span style="font-size: 24px">Total Applications:</span> ${json.positions}</p><br>`,
            `<p><span style="font-size: 24px">Emojis:</span> ${json.emojis}</p>`
        ];
        for(const f of formatted) {
            add_element("div", f, "container2");
        };
    };
};

function refresh(f=true) {
    window.location.refresh(f);
};

main().then().catch((error)=>{
    alert("Error while fetching content. If you understand javascript code, it's been logged to console.");
    console.log("== Error while fetching stats: ==");
    console.error(error);
    throw error;
    console.log("== /end error/ ==");
});