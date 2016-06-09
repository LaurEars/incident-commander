import datetime


class Incident:
    def __init__(self, app_name):
        self.start_date = datetime.date.today()
        self.resolved_date = None
        self.status = 'Identified'  # should be an enum-type thing
        self.name = "{today_format}-{app_name}"\
            .format(today_format=self.start_date.strftime("%Y-%m-%d"),
                    app_name=app_name)
        self.app = app_name
        self.severity = None  # should be another enum-like thing
        self.slack_channel = None
        self.description = None
        self.tasks = []
        # todo: add rest of attributes from planning session
        # todo: needs some database saving stuff

    def add_task(self, task):
        self.tasks.append(task)
        # todo: needs some database saving stuff
