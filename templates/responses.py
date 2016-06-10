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

SET = Template("Set *{{field}}* to `{{value}}`")
GET = Template("*{{field}}*: {{value}}")

GET_LIST = Template("""
*{{field}}:*
```
{% for val in value %}
    {{loop.index}}: {{val}}
{% endfor %}
```
""")
