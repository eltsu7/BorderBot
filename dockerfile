FROM python:3
ADD main.py /
ADD settings.json /
RUN pip3 install python-telegram-bot
RUN pip3 install Pillow
CMD [ "python3", "./main.py" ]
