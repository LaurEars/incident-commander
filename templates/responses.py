from jinja2 import Template

CREATE_INCIDENT = Template("""
INCIDENT CREATED!

When you have a moment, please use these commands to provide more information:
@commander set-title <title>
@commander set-reporter <@reporter>
....

""")
CREATE_INCIDENT_FAILED = Template("Hey, did you forget to include an application name?")

TITLE = Template("Title set to {{ title }}")

# TODO: Add more
