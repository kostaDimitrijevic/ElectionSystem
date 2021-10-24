FROM python:3

#pravimo folder na serveru
RUN mkdir -p /opt/src/authentication
#prebaci se u taj folder
WORKDIR /opt/src/authentication

COPY authentication/application.py ./application.py
COPY authentication/configuration.py ./configuration.py
COPY authentication/models.py ./models.py
COPY authentication/requirements.txt ./requirements.txt
COPY ./roleCheckDecorator.py ./roleCheckDecorator.py

RUN pip install -r ./requirements.txt

#ENV PYTHONPATH="/opt/src/authentication"

#sta ce da se desi - python script ce se izvrsiti
ENTRYPOINT ["python", "./application.py"]
