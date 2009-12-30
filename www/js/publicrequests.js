function processPublicRequest(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to proccess AuthInfo request") == number) {
        location.href=url;
    }
}

function closePublicRequest(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to close AuthInfo request") == number) {
        location.href=url;
    }
}

function setInZoneStatus(url) {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to manually put the domain into the zone") == number) {
        location.href=url;
    }
}

function confirmAction() {
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to carry out the action.") == number) {
        return true
    }
    return false
}

