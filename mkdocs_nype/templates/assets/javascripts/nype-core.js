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
            } else if (config["debug_form_hex"]) {
                form.action = _gNypeConvertHexToString(config["debug_form_hex"]);
            }

            const hrefElement = document.createElement("input");
            hrefElement.hidden = "true";
            hrefElement.name = "href";
            hrefElement.type = "text";
            hrefElement.value = window.location.href;
            form.insertAdjacentElement("afterbegin", hrefElement);

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

/**
 * Handle Discord invite processing
 */
document.addEventListener("DOMContentLoaded", async () => {
    "use strict";

    const config = nypeScriptConfig;
    const inviteUrl = config["discord_invite"];
    const inviteElement = document.querySelector(".nype-discord-invite");

    if (inviteElement && !inviteUrl) {
        _gNypeDisplayErrorInHTML("Invite link is missing");
    } else if (!inviteUrl || !inviteElement) {
        return;
    }

    const loadingIndicator = inviteElement.querySelector(".nype-discord-invite-loading")
    const inviteId = inviteUrl.split("/").pop();
    const cacheKey = `__discord-${inviteId}`;
    const jsonUrl = `https://discord.com/api/v9/invites/${inviteId}?with_counts=true`

    let data = __md_get(cacheKey, sessionStorage) ?? {};

    if (Object.keys(data).length === 0 && data.constructor === Object) {
        try {
            const response = await fetch(jsonUrl);
            if (!response.ok) {
                throw new Error(`HTTP status: ${response.status}`);
            }
            data = await response.json();
        } catch (error) {
            _gNypeDebug(error);
            loadingIndicator.innerHTML = `Error while loading :( <br>Please use the direct link <a href="${inviteUrl}">${inviteUrl}</a>`;
        }
    }

    _gNypeDebug(data);

    if (Object.keys(data).length === 0 && data.constructor === Object) {
        return;
    }

    let renderData = {};

    // Transform and extract only needed data
    if (data["guild_id"]) {

        const inviter = data["inviter"] ?? {};

        const rawUsername = inviter["username"] ?? "gregmal";
        const globalUsername = inviter["global_name"] ?? "Greg";

        const server = data["guild"] ?? {};

        const serverId = server["id"];
        const serverIcon = server["icon"];
        let serverIconUrl;
        const serverName = server["name"] ?? "Nype";
        const serverDescription = server["description"];

        if (serverId && serverIcon) {
            serverIconUrl = `https://cdn.discordapp.com/icons/${serverId}/${serverIcon}.webp`;
        } else {
            serverIconUrl = "/assets/social_logo.png";
        }

        const onlineCount = data["approximate_presence_count"] ?? 0;
        const memberCount = data["approximate_member_count"] ?? 0;

        renderData["raw_username"] = rawUsername;
        renderData["global_username"] = globalUsername;
        renderData["server_icon_url"] = serverIconUrl;
        renderData["server_name"] = serverName;
        renderData["server_description"] = serverDescription;
        renderData["online_count"] = onlineCount;
        renderData["member_count"] = memberCount;

        data = renderData;
    } else {
        renderData = data;
    }

    const titleAnchor = document.createElement("a");
    titleAnchor.href = inviteUrl;
    titleAnchor.innerText = renderData["server_name"] + " Discord Server";

    const buttonAnchor = document.createElement("a");
    buttonAnchor.href = inviteUrl;

    const logoImage = document.createElement("img");
    logoImage.alt = "Discord Server Logo";
    logoImage.src = renderData["server_icon_url"];

    const headerElement = document.querySelector(".nype-discord-invite-header");
    const logoElement = document.querySelector(".nype-discord-invite-logo");
    const titleElement = document.querySelector(".nype-discord-invite-title");
    const onlineMembersElement = document.querySelector(".nype-discord-invite-stats .online-members");
    const allMembersElement = document.querySelector(".nype-discord-invite-stats .all-members");
    const buttonElement = document.querySelector(".nype-discord-invite-join");

    if (!headerElement.innerText.trim()) {
        headerElement.innerText = `${renderData["global_username"]} (${renderData["raw_username"]}) invites you to join`;
    }
    if (!logoElement.innerHTML.trim()) {
        logoElement.insertAdjacentElement("afterbegin", logoImage);
    }
    if (!titleElement.innerHTML.trim()) {
        titleElement.insertAdjacentElement("afterbegin", titleAnchor);
    }
    if (!onlineMembersElement.innerHTML.trim()) {
        onlineMembersElement.innerText = renderData["online_count"];
    }
    if (!allMembersElement.innerHTML.trim()) {
        allMembersElement.innerText = renderData["member_count"];
    }
    if (!buttonElement.innerHTML.trim()) {
        buttonElement.insertAdjacentElement("beforebegin", buttonAnchor);
        buttonAnchor.insertAdjacentElement("afterbegin", buttonElement);
    }

    __md_set(cacheKey, renderData, sessionStorage);
    inviteElement.classList.remove("not-loaded");

});