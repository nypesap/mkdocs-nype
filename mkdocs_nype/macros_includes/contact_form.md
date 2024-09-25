{#- 
    !!!NOTE: This macro is included in all contact.md / offer.md / free-offer.md files. Edit with caution. 
-#}

{%- include 'setup_vars.md' -%}

{#- nype_config is the reference to page.meta.nype_config, so modify this to pass data to the theme templates. -#}
{%- set _ = nype_config.required_js_keys.update({ 'contact_form_action_hex': {} }) -%}

{%- set email_label = "E-mail:" if nype_config.js.contact_form_allow_personal_emails else "Company E-mail:" -%}
{%- set email_placeholder = "Input your e-mail" if nype_config.js.contact_form_allow_personal_emails else "Input your company e-mail" -%}

<div class="nype-form-wrapper">
    <form class="nype-form" method="POST">
        <label for="fullname">Full Name:</label>
        <input 
            class="md-input" 
            id="fullname"
            name="fullname"
            placeholder="Input your name"
            required
            type="text"
        >
        <label for="companyname">Company Name:</label>
        <input 
            class="md-input" 
            id="companyname"
            name="companyname"
            placeholder="Input your company name"
            required
            type="text"
        >
        <label for="email">{{- email_label -}}</label>
        <input
            autocomplete="email"
            class="md-input"
            id="email"
            name="email"
            placeholder="{{- email_placeholder -}}"
            required
            type="email"
        >
        <label for="message">What can we do for you?:</label>
        <textarea
            class="md-input"
            id="message"
            name="message"
            placeholder="Input your message"
            required
        ></textarea>
        <button 
            class="md-button md-button--primary"
            type="submit"
        >Submit</button>
    </form>
</div>