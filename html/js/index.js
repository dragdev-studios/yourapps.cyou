async function fetch_json(url, init) {
    const response = await fetch(url, init);
    const data = await response.json();
    data._meta = {"status": response.status};
    return data;
};

function createWarning(e, fatal = false) {
    if(fatal) {
        var pre = "Fatal"
    }
    else {
        var pre = "Non-fatal"
    }
    let warning = document.createElement("div");
    warning.innerHTML = pre + ' error: ' + '<code class="inline">{}</code>'.replace('{}', e) + "<br>Some of the site may not function as intended.";
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
        const response = fetch_json("https://api.yourapps.cyou/meta/stats");
        response.then(
            (data) => {document.getElementById("count").textContent = data.guilds + " servers!"}
        );
        response.catch((e) => {createWarning(e)});
    }
    catch (e) {
        return createWarning(e);
    };
};
