function processAuthInfo(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to proccess AuthInfo request") == number) {
        location.href=url;
    }
}

function closeAuthInfo(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to close AuthInfo request") == number) {
        location.href=url;
    }
}
