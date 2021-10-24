import ast
import datetime

from flask import Flask
from flask_jwt_extended import JWTManager
from configuration import Configuration
from models import database, Vote, Election, ParticipantElection
from redis import Redis
from sqlalchemy import and_

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

if __name__ == "__main__":
    database.init_app(application);
with application.app_context ( ) as context:
    with Redis(host=Configuration.REDIS_HOST) as redis:
        while True:
            data = redis.blpop(Configuration.REDIS_VOTING_LIST)
            vote = data[1].decode("utf-8")
            vote = ast.literal_eval(vote)
            active = Election.query.filter(and_(Election.start <= datetime.datetime.now(), datetime.datetime.now() <= Election.end)).first()

            if not active:
                continue

            v = Vote.query.filter(vote["guid"] == Vote.guid).first()

            if v:
                newVote = Vote(guid= vote["guid"], jmbg=vote["jmbg"], comment="Duplicate ballot.", pollNum=int(vote["number"]), electionId=active.id)
                database.session.add(newVote)
                database.session.commit()
                continue

            check = ParticipantElection.query.filter(and_(ParticipantElection.electionId == active.id, ParticipantElection.pollNum == int(vote["number"]))).first()

            if not check:
                newVote = Vote(guid=vote["guid"], jmbg=vote["jmbg"], comment="Invalid poll number.", pollNum=int(vote["number"]), electionId=active.id)
                database.session.add(newVote)
                database.session.commit()
                continue

            newVote = Vote(guid=vote["guid"], jmbg=vote["jmbg"], pollNum=int(vote["number"]), comment="VALID", electionId=active.id)
            database.session.add(newVote)
            database.session.commit()