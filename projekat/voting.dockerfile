FROM python:3

#pravimo folder na serveru
RUN mkdir -p /opt/src/applications/voting
#prebaci se u taj folder
WORKDIR /opt/src/applications/voting

COPY applications/voting/application.py ./application.py
COPY applications/voting/configuration.py ./configuration.py
COPY applications/voting/models.py ./models.py
COPY applications/voting/requirements.txt ./requirements.txt
COPY applications/voting/roleCheckDecorator.py ./roleCheckDecorator.py

RUN pip install -r ./requirements.txt

#ENV PYTHONPATH="/opt/src/authentication"

#sta ce da se desi - python script ce se izvrsiti
ENTRYPOINT ["python", "./application.py"]
