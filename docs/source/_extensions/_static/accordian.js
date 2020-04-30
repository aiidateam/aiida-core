// This should simply add / remove the collapsed class and change the button text
var initAccordion = (button) => {
    var acc = document.getElementsByClassName("accordion");
    var i;

    for (i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {
            this.classList.toggle("active");
            var panel = this.nextElementSibling;
            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
                panel.style.display = "none";
            } else {
                panel.style.display = "block";
                panel.style.maxHeight = panel.scrollHeight + "px";
            }
        });
    }
}

// Helper function to run when the DOM is finished
const sphinxAccordionRunWhenDOMLoaded = cb => {
    if (document.readyState != 'loading') {
        cb()
    } else if (document.addEventListener) {
        document.addEventListener('DOMContentLoaded', cb)
    } else {
        document.attachEvent('onreadystatechange', function () {
            if (document.readyState == 'complete') cb()
        })
    }
}

sphinxAccordionRunWhenDOMLoaded(initAccordion)
