'use strict';
async function main() {
    const pw = prompt("Password: ");
    if(!pw) {
        alert("You didn't supply a password. Thats kinda needed.")
    }
    else {
        const correct = (await (await fetch("/checkpw?p="+pw)).json()).value;
        var content = document.getElementById("content");
        if(!correct) {
            alert("Incorrect password.");
            content.innerHTML = "<h1>You tried.</h1>";
        }
        else {
            const insertable = await (
                await fetch(
                    "/statistics",
                    {
                        headers: {
                            "Authorization": pw
                        }
                    }
                )
            ).text();
            if(content) {
                content.innerHTML = insertable;
            }
        };
    };
};

main();