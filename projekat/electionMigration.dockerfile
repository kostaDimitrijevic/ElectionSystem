FROM python:3

#pravimo folder na serveru
RUN mkdir -p /opt/src/applications
#prebaci se u taj folder
WORKDIR /opt/src/applications

COPY applications/migrate.py ./migrate.py
COPY applications/configuration.py ./configuration.py
COPY applications/models.py ./models.py
COPY applications/requirements.txt ./requirements.txt


RUN pip install -r ./requirements.txt

#ENV PYTHONPATH="/opt/src/authentication"

#sta ce da se desi - python script ce se izvrsiti
ENTRYPOINT ["python", "./migrate.py"]
