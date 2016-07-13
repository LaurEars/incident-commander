FROM python:3.5.1-onbuild

RUN pip install -r requirements.txt

CMD [ "python", "./rtmbot.py" ]
