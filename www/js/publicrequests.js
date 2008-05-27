function processPublicRequest(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to proccess this request") == number) {
        location.href=url;
    }
}

function closePublicRequest(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to close this request") == number) {
        location.href=url;
    }
}
