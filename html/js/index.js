async function fetch_json(url, init) {
    const response = await fetch(url, init);
    const data = await response.json();
    data._meta = {"status": response.status};
    return data;
};

function createWarning(e) {
    let warning = document.createElement("div");
    warning.innerHTML = 'Non-fatal error: ' + '<code class="inline">{}</code>'.replace('{}', e) + "<br>Some of the site may not function as intended.";
    warning.style.color = "#fff";
    warning.style.border = "1px solid black";
    warning.style.backgroundColor = "#f04747";
    warning.style.borderRadius = "12px";
    warning.style.padding = "8px";
    warning.style.zIndex = 999;
    warning.style.position = "sticky";
    warning.style.width = "90vw";
    warning.style.margin = "0.1px auto";
    warning.style.top = "0";
    document.body.prepend(warning);
    console.error(e);
}

function setServers() {
    try {
        const response = fetch_json("https://ya.clicksminuteper.net/api/v1/bot/stats");
        response.then(
            (data) => {document.getElementById("count").textContent = data.guilds + " servers!"}
        );
        response.catch((e) => {createWarning(e)});
    }
    catch (e) {
        return createWarning(e);
    };
};

async function setIcon() {
    try {
        const data = await fetch_json("https://ya.clicksminuteper.net/api/bot/icon");
        const icon = document.getElementById("icon");
        icon.src = data.url;
        icon.onerror = (e) => {console.log("Icon error"); createWarning(e)};
        icon.addEventListener("load", () => {icon.classList.remove("notloaded")}, {capture: false});
    }
    catch (e) {
        return createWarning(e);
    };
}

window.addEventListener("load", () => {setServers(); setIcon()}, {capture: false});
