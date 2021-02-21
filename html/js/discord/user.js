const base = "https://discord.com/api/v8/users";

async function fetch_user(user_token, id=0) {
    // id: int = 0 - The ID of the user to fetch.
    if(!user_token) {
        throw new Error("No user token provided to fetch.");
    };
    id = parseInt(id);
    if(id!==0) {
        const response = await fetch(
            base+`/${id}`,
            {
                headers: {
                    "Content-Type": "text/json",
                    "Authorization": "Bearer "+user_token
                }
            }
        );
        if(!response.ok) {
            console.error(
                `Got unexpected error from discord API: ${response.status} ${response.statusText}.`
            );
            throw new Error("Got unexpected response from discord API.");
        };
        const json = await response.json();
        return json;
    };
};

class User {
    constructor(data={}) {
        if(!data) {
            raise Error("No data passed to user.")
        }
        
    }
};
