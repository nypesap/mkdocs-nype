const _gNypeDebug = function() {
    if (["127.0.0.1", "localhost"].includes(window.location.hostname)) {
        console.debug("Nype Debug:", arguments);
    }
};

const _gNypeConvertHexToString = (hexData) => {
    return atob(String.fromCharCode(...hexData.match(/.{1,2}/g).map(byte => parseInt(byte, 16))));
};

const _gNypeDisplayErrorInHTML = (errorMessage) => {
    const el = document.createElement("div");
    el.style = "font-size: 1rem; color: red;";
    el.innerText = errorMessage;
    document.querySelector("article").insertAdjacentElement("afterbegin", el);
};

/**
 * Validate template rendering.
 */
document.addEventListener("DOMContentLoaded", () => {
    "use strict";
    if (nypeScriptConfig === undefined) {
        console.error("window.nypeScriptConfig is not defined, check template overrides");
    }
});

/**
 * Handle Contact Form processing.
 */
document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const config = nypeScriptConfig;
    const contactForm = config["contact_form"];
    const contactFormSuccess = config["contact_form_succes"];
    _gNypeDebug("contactForm", contactForm);
    _gNypeDebug("contactFormSuccess", contactFormSuccess);

    if (!contactForm && !contactFormSuccess) {
        _gNypeDebug("contact_form not enabled");
        return;
    }

    window.dataLayer = window.dataLayer || [];
    function gtag() { dataLayer.push(arguments); }

    if (contactFormSuccess) {
        gtag("event", "sign_up_success");
        return;
    }
    
    const actionHex = config["contact_form_action_hex"];  // URL -> base64 -> HEX
    const emailHex = config["contact_form_email_hex"];  // HTML <a> with mailto: -> base64 -> HEX
    const freeSubject = config["contact_form_free_subject"];
    _gNypeDebug("actionHex", actionHex);
    _gNypeDebug("emailHex", emailHex);
    _gNypeDebug("freeSubject", freeSubject);
    
    const form = document.querySelector(".nype-form");

    if (form) {

        if (!actionHex) {
            const errorMessage = "Contact form action is missing";
            _gNypeDisplayErrorInHTML(errorMessage)
            console.error(errorMessage);
        }

        form.addEventListener("submit", (e) => {
            e.preventDefault();

            if (!form.reportValidity()) {
                return;
            }

            gtag("event", "sign_up", { method: "Contact Form" });

            if (!["127.0.0.1", "localhost"].includes(window.location.hostname)) {
                form.action = _gNypeConvertHexToString(actionHex);
            }

            form.submit();
        });

        const messageElement = form.querySelector('[name="message"]');
        if (messageElement) {
            if (freeSubject && !messageElement.value.trim()) {
                messageElement.value = freeSubject;
            }
        }
    }

    const showEmailToggle = document.querySelector(".nype-show-email");

    if (showEmailToggle) {

        if (!emailHex) {
            const errorMessage = "Contact show email value is missing";
            _gNypeDisplayErrorInHTML(errorMessage);
            console.error(errorMessage);
        }

        showEmailToggle.addEventListener("click", (e) => {
            e.preventDefault();
            gtag("event", "show_email");
            const span = document.createElement("span");
            span.innerHTML = _gNypeConvertHexToString(emailHex);
            const anchor = span.querySelector("a");
            if (anchor && freeSubject) {
                anchor.href = anchor.href.split("subject=")[0] + `subject=${freeSubject}`;
            }
            showEmailToggle.replaceWith(span);
        });
    }
});