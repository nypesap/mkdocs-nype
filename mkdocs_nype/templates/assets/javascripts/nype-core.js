const _gNypeDebug = function () {
    if (["127.0.0.1", "localhost"].includes(window.location.hostname)) {
        console.debug("Nype Debug:", arguments);
    }
};

const _gNypeConvertHexToString = (hexData) => {
    return atob(String.fromCharCode(...hexData.match(/.{1,2}/g).map(byte => parseInt(byte, 16))));
};

const _gNypeDisplayErrorInHTML = (errorMessage) => {
    console.error(errorMessage);
    const el = document.createElement("div");
    el.style = "font-size: 1rem; color: red;";
    el.innerText = errorMessage;
    document.querySelector("article").insertAdjacentElement("afterbegin", el);
};

/**
 * Send Google Tag events
 */
const _gNypeSendT = function () {
    _gNypeDebug(...arguments);
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push(arguments);
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
    // Get form status based on the given options
    const contactForm = !!config["contact_form"] || !!config["contact_form_action_hex"] || !!config["contact_form_email_hex"];
    const contactFormSuccess = config["contact_form_success"];
    _gNypeDebug("contactForm", contactForm);
    _gNypeDebug("contactFormSuccess", contactFormSuccess);

    if (!contactForm && !contactFormSuccess) {
        _gNypeDebug("contact_form not enabled");
        return;
    }

    if (contactFormSuccess) {
        _gNypeSendT("event", "sign_up_success");
        return;
    }

    const actionHex = config["contact_form_action_hex"];  // URL -> base64 -> HEX
    const emailHex = config["contact_form_email_hex"];  // HTML <a> with mailto: -> base64 -> HEX
    const allowPersonalEmails = config["contact_form_allow_personal_emails"];
    // Support legacy option free_subject
    const freeSubject = config["contact_form_free_subject"] ?? config["contact_form_subject"];
    _gNypeDebug("actionHex", actionHex);
    _gNypeDebug("emailHex", emailHex);
    _gNypeDebug("freeSubject", freeSubject);

    const form = document.querySelector(".nype-form");

    if (form) {

        // Use Set instead of Array for faster lookup?
        const blockedEmailDomains = new Set([
            "gmail.com", "googlemail.com", "yahoo.com", "yahoo.co.uk", "yahoo.fr", "yahoo.in",
            "yahoo.ca", "yahoo.com.au", "yahoo.it", "yahoo.de", "yahoo.be", "yahoo.at",
            "hotmail.com", "hotmail.co.uk", "hotmail.fr", "hotmail.it", "hotmail.de", "hotmail.nl",
            "hotmail.be", "hotmail.ca", "hotmail.at", "hotmail.pl", "outlook.com", "outlook.co.uk",
            "outlook.fr", "outlook.it", "outlook.de", "outlook.nl", "outlook.be", "outlook.ca",
            "outlook.at", "outlook.pl", "icloud.com", "aol.com", "live.com", "live.co.uk", "live.fr",
            "live.nl", "live.ca", "live.de", "live.it", "live.be", "live.at", "live.in", "msn.com",
            "mail.com", "yandex.com", "qq.com", "163.com", "126.com", "sina.com", "sina.cn", "aliyun.com",
            "web.de", "gmx.de", "freenet.de", "t-online.de", "btinternet.com", "sky.com",
            "virginmedia.com", "laposte.net", "orange.fr", "free.fr", "sfr.fr", "bbox.fr",
            "rediffmail.com", "sify.com", "in.com", "wp.pl", "o2.pl", "interia.pl", "onet.pl",
            "tlen.pl", "bell.net", "rogers.com", "sympatico.ca", "shaw.ca", "bigpond.com",
            "optusnet.com.au", "aapt.net.au", "internode.on.net", "tiscali.it", "libero.it",
            "virgilio.it", "tin.it", "alice.it", "kpnmail.nl", "ziggo.nl", "planet.nl", "tiscali.be",
            "skynet.be", "gmx.at", "aon.at", "chello.at"
        ]);

        // Probably not needed in the function scope, as the user doesn't have access to the variable anyway?
        blockedEmailDomains.add = undefined;
        blockedEmailDomains.delete = undefined;
        Object.freeze(blockedEmailDomains);

        if (!actionHex) {
            _gNypeDisplayErrorInHTML("Contact form action is missing");
        }

        const email = form.querySelector('[type="email"]');

        // E-mail validation
        if (email && !allowPersonalEmails) {
            email.addEventListener("input", (e) => {
                const parts = email.value.trim().split("@");
                if (parts.length != 2 || !parts[1]) {
                    return;
                }
                const domain = parts[1];
                let errorSpan = form.querySelector(".email-error");
                if (blockedEmailDomains.has(domain)) {
                    const errorMessage = `Please provide a @company.domain e-mail instead of the personal @${domain} e-mail`;
                    email.setCustomValidity(errorMessage);
                    email.reportValidity();
                    if (!errorSpan) {
                        errorSpan = document.createElement("span");
                        errorSpan.className = "email-error";
                        errorSpan.style = "color: red; font-weight: 700; font-size: .7rem; display: block;";
                        email.insertAdjacentElement("afterend", errorSpan);
                    }
                    errorSpan.innerText = errorMessage;
                } else {
                    email.setCustomValidity("");
                    if (errorSpan) {
                        errorSpan.remove();
                    }
                }
            });
            // Invoke the function to validate input after page refresh
            if (email.value) {
                email.dispatchEvent(new Event("input", {}));
            }
        }

        form.addEventListener("submit", (e) => {
            e.preventDefault();

            if (!form.reportValidity()) {
                return;
            }

            _gNypeSendT("event", "sign_up", { method: "Contact Form" });

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
            _gNypeDisplayErrorInHTML("Contact show email value is missing");
        }

        showEmailToggle.addEventListener("click", (e) => {
            e.preventDefault();
            _gNypeSendT("event", "show_email");
            const span = document.createElement("span");
            span.innerHTML = _gNypeConvertHexToString(emailHex);
            const anchor = span.querySelector("a");
            if (anchor && freeSubject) {
                anchor.href = anchor.href.split("?subject=")[0] + `?subject=${freeSubject}`;
            }
            showEmailToggle.replaceWith(span);
        });
    }
});

/**
 * Handle FAQ Details processing
 */
document.addEventListener("DOMContentLoaded", () => {
    "use strict";

    const faqDetails = document.querySelectorAll("details.faq");

    if (!faqDetails) {
        return;
    }

    const eventHandler = (e) => {
        e.preventDefault();
        const el = e.target;

        if (el.tagName !== "SUMMARY") {
            return;
        }

        const details = el.closest("details");

        if (details.open === false) {
            for (const faq of faqDetails) {
                faq.open = faq === details;
            }
        } else {
            details.open = false;
        }
    };

    for (const faq of faqDetails) {
        faq.addEventListener("click", eventHandler);
    }

});