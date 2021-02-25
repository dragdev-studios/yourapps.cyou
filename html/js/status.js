var last_shard_count = 1;
function createBox(id, status) {
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
    hiddenText.textContent = `Shard ${id} - ${entry.name}`;
    box.appendChild(hiddenText);
    let visibleText = document.createElement("span");
    visibleText.textContent = id;
    box.appendChild(visibleText);
    box.addEventListener("click", () => {visibleText.hidden=!visibleText.hidden;hiddenText.hidden=!hiddenText.hidden});
    existing = document.getElementById(id)
    if(existing) {
        existing.outerHTML = box.outerHTML;
    }
    else {
        document.getElementById("statuses").appendChild(box);
    };
};

async function query_status(shard_id=-1) {
    var online = 0;
    try {
        const response = await fetch("http://localhost:9123/status?shard"+shard_id);
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
                if (data.shards[key].status !== 0) {
                    online++;
                };
                createBox(key, data.shards[key].status)
            }
        }
    } 
    catch (e) {
        // createWarning(e, false);
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
            createBox(key, data.shards[key].status)
            console.debug(key, data.shards[key])
        }
        return;
    };
}

window.addEventListener(
    "load",
    () => {window.timer = setInterval(query_status, 5000)},
    {capture: false}
);