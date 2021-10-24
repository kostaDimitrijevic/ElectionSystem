FROM python:3

#pravimo folder na serveru
RUN mkdir -p /opt/src/applications/dameon
#prebaci se u taj folder
WORKDIR /opt/src/applications/dameon

COPY applications/dameon/application.py ./application.py
COPY applications/dameon/configuration.py ./configuration.py
COPY applications/dameon/models.py ./models.py
COPY applications/dameon/requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

#ENV PYTHONPATH="/opt/src/authentication"

#sta ce da se desi - python script ce se izvrsiti
ENTRYPOINT ["python", "./application.py"]
