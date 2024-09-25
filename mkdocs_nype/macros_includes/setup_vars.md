{%- if page.meta and not page.meta.nype_config -%}
    {%- set _ = page.meta.update({ 'nype_config': {} }) -%}
{%- endif -%}

{%- if not nype_config -%}
    {%- set nype_config = page.meta.nype_config -%}
{%- endif -%}

{%- if not nype_config.js -%}
    {%- set _ = nype_config.update({ 'js': {} }) -%}
{%- endif -%}

{%- if not nype_config.required_js_keys -%}
    {%- set _ = nype_config.update({ 'required_js_keys': {} }) -%}
{%- endif -%}