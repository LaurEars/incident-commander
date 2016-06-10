from jinja2 import Template

CREATE_INCIDENT = Template("""
*INCIDENT CREATED!*

This incident is now being tracked and documented, but we still need your help!

When you have a moment, please use these commands to provide more information:
```
@commander set title <title>
@commander set reporter <@reporter>
@commander set severity <1-3>
@commander set description <description>
```
""")
CREATE_INCIDENT_FAILED = Template("Hey, did you forget to include an application name?")  # noqa

NAG = Template("Be a dear and run `@commander set {{key}} <value>`")

SET = Template("Set *{{field}}* to `{{value}}`")
GET = Template("*{{field}}*: {{value}}")

GET_LIST = Template("""
*{{field}}:*

>>> {% for val in value -%}
{{loop.index}}. {% if val is iterable -%}
        {% if val.removed is sameas false %} {{val.text}}
        {%- else %} ~{{val.text}}~ {% endif %} (<@{{val.user}}>)
{% else -%}
         {{val}}
    {% endif %}
{%- endfor %}
""")

NEW_CHANNEL_MESSAGE = Template("""
*When an incident occurs, follow these steps:*
   1. Email incident-response@zefr.com to alert about SEV

   2. Designate an Incident Commander (IC) for this incident. This is the leader of the response effort, and is responsible for managing the response.

   3. Update information about the incident in this channel, using @commander commands.

   4. Send an internal sitrep to this channel using @commander set status Status message

   5. Assess the problem.

   6. Mitigate the problem.
*Full Incident Response Instructions:* https://zefrinc.atlassian.net/wiki/display/ST/Incident+Response+Instructions
""")

def renderField(field, value):
    customRenderers = {
        'start_date': RENDER_DATE,
        'resolved_date': RENDER_DATE,
        'hypothesis': RENDER_HYPOTHESIS,
        'comment': RENDER_COMPLEX_LIST,
        'step': RENDER_COMPLEX_LIST
    }
    if field in customRenderers:
        return customRenderers[field].render(field=field, value=value)
    elif isinstance(value, list):
        return GET_LIST.render(field=field, value=value)
    else:
        return GET.render(field=field, value=value)