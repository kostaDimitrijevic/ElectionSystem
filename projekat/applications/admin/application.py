import datetime

from flask import Flask, request, make_response, jsonify
from roleCheckDecorator import roleCheck
from configuration import Configuration
from models import database, Participant, Election, ParticipantElection, Vote
from flask_jwt_extended import JWTManager
from dateutil import parser
from sqlalchemy import and_, column

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)


@application.route("/createParticipant", methods=["POST"])
@roleCheck(role="admin")
def createParticipant():
    name = request.json.get("name", "")
    individual = request.json.get("individual", "")

    if len(name) == 0:
        return make_response(jsonify(message="Field name is missing."), 400)
    if type(individual) != bool:
        return make_response(jsonify(message="Field individual is missing."), 400)

    participant = Participant(name=name, individual=individual)

    database.session.add(participant)
    database.session.commit()

    return make_response(jsonify(id=participant.id), 200)

@application.route("/getParticipants", methods=["GET"])
@roleCheck(role="admin")
def getParticipants():

    participants = Participant.query.all()

    toSend=[]
    for participant in participants:
        toSend.append(
            {
                "id": participant.id,
                "name": participant.name,
                "individual": participant.individual
            }
        )

    return make_response(jsonify(participants=toSend), 200)

@application.route("/createElection", methods=["POST"])
@roleCheck(role="admin")
def createElection():
    start = request.json.get("start", "")
    end = request.json.get("end", "")
    individual = request.json.get("individual", "")
    participants = request.json.get("participants", "")

    if len(start)==0:
        return make_response(jsonify(message="Field start is missing."), 400)
    if len(end)==0:
        return make_response(jsonify(message="Field end is missing."), 400)
    if type(individual)!=bool:
        return make_response(jsonify(message="Field individual is missing."), 400)
    if len(participants)==0 and type(participants)==str:
        return make_response(jsonify(message="Field participants is missing."), 400)

    try:
        startISO = parser.isoparse(start)
        endISO = parser.isoparse(end)
    except Exception as ex:
        return make_response(jsonify(message="Invalid date and time."), 400)

    if  endISO <= startISO:
        return make_response(jsonify(message="Invalid date and time."), 400)

    elections = Election.query.all()

    badElection = Election.query.filter(and_(Election.end >= startISO, Election.start <= endISO)).first()

    if badElection:
        return make_response(jsonify(message="Invalid date and time."), 400)

    if len(participants) < 2:
        return make_response(jsonify(message="Invalid participants."), 400)

    if individual==False:
        for part in participants:
            participant = Participant.query.filter(Participant.id == int(part)).first()
            if participant.individual:
                return make_response(jsonify(message="Invalid participants."), 400)
    else:
        for part in participants:
            participant = Participant.query.filter(Participant.id == int(part)).first()
            if not participant.individual:
                return make_response(jsonify(message="Invalid participants."), 400)

    for part in participants:
        participant = Participant.query.filter(Participant.id == int(part)).first()
        if not participant:
            return make_response(jsonify(message="Invalid participants."), 400)

    election = Election(start=startISO, end=endISO, individual=individual)
    database.session.add(election)
    database.session.commit()

    pollNumbers = []
    i = 1
    for p in participants:
        participantElection = ParticipantElection(electionId=election.id, participantId=p, pollNum=i)
        pollNumbers.append(i)
        i = i + 1
        database.session.add(participantElection)
        database.session.commit()

    return make_response(jsonify(pollNumbers=pollNumbers), 200)

@application.route("/getElections", methods=["GET"])
@roleCheck(role="admin")
def getElections():
    participants = []

    toSend = []

    elections = Election.query.all()
    for e in elections:
        part = e.participants
        for p in part:
            participant = Participant.query.filter(p.id==Participant.id).first()
            participants.append({
                "id": p.id,
                "name": participant.name
            })
        toSend.append({
            "id": e.id,
            "start": e.start.isoformat(),
            "end": e.end.isoformat(),
            "individual": e.individual,
            "participants": participants
        })
        participants = []

    return make_response(jsonify(elections=toSend), 200)

@application.route("/getResults", methods=["GET"])
@roleCheck(role="admin")
def getResults():

    if "id" not in request.args:
        return make_response(jsonify(message="Field id is missing."), 400)

    id = request.args["id"]

    election = Election.query.filter(id==Election.id).first()

    if not election:
        return make_response(jsonify(message="Election does not exist."), 400)

    check = Election.query.filter(and_(and_(Election.start <= datetime.datetime.now(), datetime.datetime.now() <= Election.end), id == Election.id)).first()

    if check:
        return make_response(jsonify(message="Election is ongoing."), 400)

    participants = election.participants

    votes = []
    seats = []
    quotients = []
    rounds = 250

    num = ParticipantElection.query.filter(ParticipantElection.electionId == id).all()

    for i in range(len(num)):
        votes.append(0)
        seats.append(0)
        quotients.append(0)

    for p in participants:
        part = ParticipantElection.query.filter(
            and_(ParticipantElection.electionId == id, p.id == ParticipantElection.participantId)).first()
        partVotes = Vote.query.filter(and_(Vote.electionId == id, part.pollNum == Vote.pollNum, Vote.comment=="VALID")).all()
        allVotes = Vote.query.filter(and_(Vote.electionId == id, Vote.comment=="VALID")).all()

        census = len(partVotes)/len(allVotes)

        if not election.individual:
            if census >= 0.05:
                census = True
            else:
                census = False

            votes[part.pollNum - 1] = {
                "numVotes": len(partVotes),
                "census": census
            }
        else:
            votes[part.pollNum - 1] = {
                "numVotes": len(partVotes),
                "census": round(census, 2)
            }

    participantsToSend = []

    if not election.individual:
        for r in range(rounds):
            for i in range(len(votes)):
                if votes[i]["census"]:
                    quot = votes[i]["numVotes"]/(seats[i] + 1)
                    quotients[i] = quot

            seats[quotients.index(max(quotients))] += 1

        for p in range(len(seats)):
            participantId = ParticipantElection.query.filter(and_(ParticipantElection.electionId == id, ParticipantElection.pollNum == (p + 1))).first()
            participant = Participant.query.filter(Participant.id == participantId.participantId).first()

            participantsToSend.append({
                "pollNumber": p + 1,
                "name": participant.name,
                "result": seats[p]
            })
    else:
        for v in range(len(votes)):
            participantId = ParticipantElection.query.filter(
                and_(ParticipantElection.electionId == id, (v + 1) == ParticipantElection.pollNum)).first()
            participant = Participant.query.filter(Participant.id == participantId.participantId).first()

            participantsToSend.append({
                "pollNumber": v + 1,
                "name": participant.name,
                "result": votes[v]["census"]
            })

    invalidVotes = Vote.query.filter(and_(Vote.electionId == id, Vote.comment != "VALID")).all()
    invalidVotesToSend = []
    for vote in invalidVotes:
        invalidVotesToSend.append({
            "electionOfficialJmbg": vote.jmbg,
            "ballotGuid": vote.guid,
            "pollNumber": vote.pollNum,
            "reason": vote.comment
        })

    return make_response(jsonify(participants=participantsToSend, invalidVotes=invalidVotesToSend), 200)


if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5001 )