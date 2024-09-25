{#- 
    !!!NOTE: This macro is included in all contact.md / offer.md / free-offer.md files. Edit with caution. 
-#}

{%- include 'setup_vars.md' -%}

{#- nype_config is the reference to page.meta.nype_config, so modify this to pass data to the theme templates. -#}
{%- set _ = nype_config.required_js_keys.update({ 'contact_form_email_hex': {} }) -%}

{#- Whitespace #} <span class="nype-code-button nype-show-email">`Show e-mail`</span> {# Whitespace -#}