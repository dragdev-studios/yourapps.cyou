var last_shard_count = 1;
var BASE = "//api.yourapps.cyou";  // DO NOT CHANGE THIS unless you're experimenting.
var lock = false;  // used to block concurrent requests.
function createBox(id, status, latency) {
    const statuses = {
        "0": {
            "name": "offline",
            "colour": "#ff4d4d"
        },
        "1": {
            "name": "degraded performance",
            "colour": "#f5bd00"
        },
        "2": {
            "name": "very slow",
            "colour": "#f1c40f"
        },
        "5": {
            "name": "Online",
            "colour": "#43b581"
        }
    };
    // The reason for that sudden jump from 2 -> 5 is that 3 and 4 are reserved
    let entry = statuses[status.toString()];
    
    let box = document.createElement("div");
    box.classList.add("StatusBox");
    box.classList.add("_"+status);
    box.id = id;
    let hiddenText = document.createElement("span");
    hiddenText.hidden = true;
    hiddenText.textContent = `Shard ${id}\n${entry.name}\n${latency}ms ping`;
    box.appendChild(hiddenText);
    let visibleText = document.createElement("span");
    visibleText.textContent = id;
    box.appendChild(visibleText);
    box.addEventListener("click", () => {
        visibleText.hidden=!visibleText.hidden;
        hiddenText.hidden=!hiddenText.hidden;
        // if(!hiddenText.hidden) {
        //     lock = true; // this should stop any overwrites
        // }
    });
    existing = document.getElementById(id)
    if(existing) {
        existing.outerHTML = box.outerHTML;
    }
    else {
        document.getElementById("statuses").appendChild(box);
    };
};

async function query_status(shard_id=-1) {
    const updater = document.getElementById("last-updated");
    if(lock===true) {
        console.debug("Lock is active, stopping scheduled HTTP request.")
        return;
    }
    lock = true;
    var online = 0;
    try {
        const response = await fetch(BASE+"/meta/status");
        var data;
        if([500, 501, 502, 503, 504].includes(response.status)) {
            data = {"shards": {}};
            for(let i=0;i<=last_shard_count;i++) {
                data.shards[i.toString()] = {
                    "status": 0,
                    "id": i
                };
            };
        }
        else {
            data = await response.json();
            last_shard_count = Object.keys(data.shards).length;
        };
        
        if(shard_id==-1) {
            for(let key of Object.keys(data.shards)) {
                if(!data.shards[key].online) {
                    createBox(key, "0", 99999999);
                };
                let latency = data.shards[key].latency;
                if(latency>1000) {
                    createBox(key, "2", latency);
                }
                else if (latency > 200) {
                    createBox(key, "1", latency);
                }
                else {
                    createBox(key, "5", latency);
                };
            }
        }
    } 
    catch (e) {
        data = {"shards": {}};
        for(let i=0;i<last_shard_count;i++) {
            data.shards[i.toString()] = {
                "status": 0,
                "id": i
            };
        };
        console.warn("offline - Using cached values");
        console.debug("Cached values: ", JSON.stringify(data, null, 2))
        for(let key of Object.keys(data.shards)) {
            createBox(key, data.shards[key].status, data.shards[key].latency)
            console.debug(key, data.shards[key])
        }
    };
    lock = false;
    var now = new Date();
    updater.textContent = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
}

window.addEventListener(
    "load",
    () => {query_status().then(() => {window.timer = setInterval(query_status, 5000)})},
    {capture: false}
);