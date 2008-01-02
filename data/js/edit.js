var ESCAPE = 27
var ENTER = 13
var TAB = 9


function join(name, num) {
    if (isNaN(num)) {
        n = ''
    } else {
        n = num
    }
    var view = document.getElementById(name + "View" + n)
    view.editor = document.getElementById(name + "Editor" + n)
    view.final = document.getElementById(name + "Final" + n)
    view.edit = document.getElementById(name + "Edit" + n)
    view.reset = document.getElementById(name + "Reset" + n)

    view.editor.value = view.textContent
    view.final.value = view.textContent


    var showEditor = function(event) {
        view.style['backgroundColor'] = 'lightgreen'
        view.editor.style['backgroundColor'] = ''
        view.edit.style['display'] = 'none'
//        view.reset.style['display'] = 'inline'
        view.editor.style['visibility'] = 'visible'
        view.editor.focus()
        return false
    }

    var hideEditor = function(event) {
        view.style['backgroundColor'] = ''
        view.reset.style['display'] = 'none'
        view.edit.style['display'] = 'inline'
        view.editor.style['visibility'] = 'hidden'
        return false
    }

    view.reset.onclick = function(event) {
        view.editor.value = view.textContent
        view.final.value = view.textContent
        event = fixEvent(event)
        hideEditor()
    }

    view.edit.onclick = function(event) {
        event = fixEvent(event)
        showEditor()
    }

    view.editor.onkeydown = function(event) {
        event = fixEvent(event)
        var editor = event.target
        if (event.keyCode == TAB) {
            editor.blur()
            return false
        }
    }

    view.editor.onblur = function(event) {
        event = fixEvent(event)
        if (view.editor.value == view.textContent) {
            view.final.value = view.textContent
            hideEditor()
        } else {
            view.final.value = view.editor.value
            view.editor.style['backgroundColor'] = '#FF3300'
            view.reset.style['display'] = 'inline'
        }
    }

    function fixEvent(event) {
        if (!event) event = window.event
        if (event.target) {
            if (event.target.nodeType == 3) event.target = event.target.parentNode
        } else if (event.srcElement) {
            event.target = event.srcElement
        }
        return event
    }
}

function certClone(name, origcount) {

    var template = document.getElementById(name)
    var adder = document.getElementById('certAdd')
    var certCount = origcount
    lastrow = template.parentNode.lastChild.previousSibling

    function cloneTemplate(template) {
        var clone = template.cloneNode(true)
        clone.number = certCount
        inputs = clone.getElementsByTagName('input')
        for (i=0; i<inputs.length; i++) { 
            origid = inputs[i].getAttribute('id')
            newid = origid + clone.number
            inputs[i].setAttribute('id', newid)
            if (inputs[i].hasAttribute('name')) {
                origname = inputs[i].getAttribute('name')
                newname = origname + clone.number
                inputs[i].setAttribute('name', newname)
            }
        }
        spans = clone.getElementsByTagName('span')
        for (i=0; i<spans.length; i++) { 
            origid = spans[i].getAttribute('id')
            newid = origid + clone.number
            spans[i].setAttribute('id', newid)
        }
        clone.setAttribute('id', 'certRow' + clone.number)
        clone.removeAttribute('class')
        template.parentNode.insertBefore(clone, lastrow)

        clone.delButton = document.getElementById('delPair' + clone.number)
        clone.delButton.onclick = function(event) {
            // smaz radku, ve ktery jsi
            parent = clone.parentNode
            parent.removeChild(clone)
        }
        clone.certField = document.getElementById('md5Cert' + clone.number)
        clone.certField.onblur = function(event) {
            target = event.target
            if (target.value != '') {
                target.style['backgroundColor'] = '#FF3300'
            } else {
                target.style['backgroundColor'] = ''
            }
        }
        join('password', clone.number)
        certCount++
    }

    adder.onclick = function(event) {
        cloneTemplate(template)
    }

}

function registrarSubmit(obj) {
    form = document.getElementById('modifyRegistrar')
    template = document.getElementById('certTableTemplate')
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to change registrar data") == number) {
        template.parentNode.removeChild(template)
        form.submit()
    }
}

function processAuthInfo(obj) {
    form = document.getElementById('processAuthInfo')
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to proccess AuthInfo request") == number) {
        form.submit()
    }
}

function closeAuthInfo(obj) {
    form = document.getElementById('closeAuthInfo')
    number = Math.floor(Math.random()*1000)
    if (prompt("Type "+number+" to close AuthInfo request") == number) {
        form.submit()
    }
}
