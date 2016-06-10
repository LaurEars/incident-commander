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