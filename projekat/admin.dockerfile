FROM python:3

#pravimo folder na serveru
RUN mkdir -p /opt/src/applications/admin
#prebaci se u taj folder
WORKDIR /opt/src/applications/admin

COPY applications/admin/application.py ./application.py
COPY applications/admin/configuration.py ./configuration.py
COPY applications/admin/models.py ./models.py
COPY applications/admin/requirements.txt ./requirements.txt
COPY applications/admin/roleCheckDecorator.py ./roleCheckDecorator.py

RUN pip install -r ./requirements.txt

#ENV PYTHONPATH="/opt/src/authentication"

#sta ce da se desi - python script ce se izvrsiti
ENTRYPOINT ["python", "./application.py"]
