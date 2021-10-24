import json

from flask import Flask, request, make_response, jsonify, Response
from flask_jwt_extended import JWTManager, get_jwt
from configuration import Configuration
from models import database
from roleCheckDecorator import roleCheck
from redis import Redis
import io
import csv

application = Flask(__name__)
application.config.from_object(Configuration)
jwt = JWTManager(application)

@application.route("/vote", methods=["POST"])
@roleCheck(role="user")
def vote():
    jmbg = get_jwt()["jmbg"]

    if "file" not in request.files:
        return make_response(jsonify(message="Field file is missing."), 400)

    content = request.files["file"].stream.read().decode("utf-8")
    stream = io.StringIO(content)
    reader = csv.reader(stream)

    with Redis(host=Configuration.REDIS_HOST) as redis:
        num = 0
        for row in reader:
            if len(row) != 2:
                return make_response(jsonify(message="Incorrect number of values on line " + str(num) + "."), 400)

            if not row[1].isnumeric():
                return make_response(jsonify(message="Incorrect poll number on line " + str(num) + "."), 400)
            else:
                if int(row[1]) < 0:
                    return make_response(jsonify(message="Incorrect poll number on line " + str(num) + "."), 400)
            toSave={
                "jmbg": jmbg,
                "guid": row[0],
                "number": row[1]
            }

            redis.rpush(Configuration.REDIS_VOTING_LIST, json.dumps(toSave))
            num += 1
    return Response(status=200)
if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5003)