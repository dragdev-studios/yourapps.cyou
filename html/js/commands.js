function getCommands() {
    function highlightReferencedCmd() {
        if (window.location.hash) {
            let hash = location.hash.replace("%20", " ");
            const el = document.getElementById(hash.slice(1));
            if (el) {
                el.scrollIntoView();console.log("Scrolled ito view.");
            };
        } else {console.log("No hash");};
    };
    var request = new XMLHttpRequest();
    request.onreadystatechange = function () {
        let o = document.getElementById("offline");
        let lb = document.getElementById("loadingimg");
        console.log(`Request state change: now ${this.readyState}.\nStatus: ${this.status}`);
        if (this.readyState == 1) {
            lb.hidden = false;
            o.hidden = true;
        }
        else if ((this.status == 0 || this.status != 200) && this.readyState == 4) {
            if(lb){lb.hidden=true;};
            if(o) {o.innerHTML = "The YourApps API is offline. Please use the in-discord ya?help command.";o.hidden=false;};
        }
        else if(this.readyState >= 2) {
            if (this.status == 200) {
                if (o) {o.hidden = true;};
                if(lb) {o.hidden = false;};
            };
        }
    };
    request.onload = function() {
        if (this.readyState == 4 && this.status == 200) {
            let data = JSON.parse(this.responseText);
            let load = document.getElementById("loading");
            let offline = document.getElementById("offline");
            if (load) {
                load.hidden = true;
                load.remove();
            } else {
                console.warn("No loading element. Assuming already deleted.");
            };
            if(offline){offline.remove();};
            let container = document.getElementById("container");
            if (!container) {
                alert("Unable to display commands: No container element.");
            };
            let commands = Object.keys(data);
            for (var key of commands) {
                container.appendChild(document.createElement("hr"));
                var _e = document.createElement("div", {
                    id: key
                });
                _e.id = key;
                if (location.hash.includes(key)) {
                    _e.classList.add("highlighted");
                };
                var c = container.appendChild(_e);
                let e = data[key];
                if (!e.desc) {
                    e.desc = "No Description"
                };
                let desc = e.desc.replace("<", "&lt").replace(">", "&gt").replace("\n", "<br>");
                let content = `<h2><a class='copyme' href="#${key}">🔗</a> Name: ${key}</h2>`;
                if (e.args && e.args.length !== 0) {
                    content += `<p>Arguments: ${'['+e.args.join('] [')+']'}</p>`;
                } else {
                    content += "<hp>Arguments: None</hp>";
                };
                content += `<p>Description: ${desc}</p>`;
                if (e.nice) {
                    var nice = `ya?${key} ` + e.nice.replace('\`', '').replace("ya?", ""); // my b
                } else {
                    var nice = `ya?help ${key}`;
                };
                content += `<p>Usage: <code class="inline plaintext">${nice}</code></p>`;
                content += "<br><br>";
                c.innerHTML = content;
            };
            container.hidden = false;
            console.log("Loaded - scrolling into view")
            highlightReferencedCmd();
        }
        else if ((this.status == 0 || this.status != 200) && this.readyState == 4) {
            let o = document.getElementById("offline");
            if(o) {o.innerHTML = "The YourApps API is offline. Please use the in-discord ya?help command.";};
        };
    };
    request.open("GET", "https://ya.clicksminuteper.net/api/bot/commands.json", true);
    request.send();
};
getCommands();