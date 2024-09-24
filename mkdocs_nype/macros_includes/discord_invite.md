{%- if not nype_config -%}
    {%- set nype_config = {} -%}
{%- endif -%}

{%- if not nype_config.js -%}
    {%- set _ = nype_config.update({ 'js': {} }) -%}
{%- endif -%}

{%- set discord_invite = nype_config.js.discord_invite or "" -%}
{%- set discord_header = nype_config.discord_header or "" -%}
{%- set discord_logo = nype_config.discord_logo or "" -%}
{%- set discord_title = nype_config.discord_title or "" -%}
{%- set discord_button = nype_config.discord_button or "Join" -%}

<div class="nype-discord-invite not-loaded" markdown>

<p class="nype-discord-invite-loading">Loading...</p>

<noscript>Your browser does not support JavaScript! Use the direct link <a href="{{ discord_invite }}">{{ discord_invite }}</a></noscript>

<p class="nype-discord-invite-header">{{- discord_header -}}</p>

<p class="nype-discord-invite-logo">{{- discord_logo -}}</p>

<p class="nype-discord-invite-title">{{- discord_title -}}</p>

<p class="nype-discord-invite-stats">

<span class="online-members"></span> Online <span class="all-members"></span> Members

</p>

<button class="nype-discord-invite-join md-button md-button--primary">{{- discord_button -}}</button>

</div>