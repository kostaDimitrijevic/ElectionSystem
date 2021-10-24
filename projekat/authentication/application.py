from flask import Flask, request, jsonify, make_response, Response

from roleCheckDecorator import roleCheck
from configuration import Configuration
from models import database, User
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt, get_jwt_identity
from sqlalchemy import and_
import re

application = Flask(__name__)
application.config.from_object(Configuration)

@application.route("/register", methods=["POST"])
def register():
    jmbg = request.json.get("jmbg", "")
    email = request.json.get("email", "")
    password = request.json.get("password", "")
    forename = request.json.get("forename", "")
    surname = request.json.get("surname", "")

    if len(jmbg) == 0:
        return make_response(jsonify(message="Field jmbg is missing."), 400)
    if len(forename) == 0:
        return make_response(jsonify(message="Field forename is missing."), 400)
    if len(surname) == 0:
        return make_response(jsonify(message="Field surname is missing."), 400)
    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400)
    if len(password) == 0:
        return make_response(jsonify(message="Field password is missing."), 400)

    if len(jmbg) != 13:
        return make_response(jsonify(message="Invalid jmbg."), 400)

    try:
        dd = int(jmbg[0:2])
        mm = int(jmbg[2:4])
        yyy = int(jmbg[4:7])
        rr = int(jmbg[7:9])
        bbb = int(jmbg[9:12])
    except ValueError as error:
        return make_response(jsonify(message="Invalid jmbg."), 400)

    if dd < 1 or dd > 31 or mm < 1 or mm > 12 or yyy < 0 or yyy > 999 \
            or rr < 0 or rr > 99 or bbb < 0 or bbb > 999:
        return make_response(jsonify(message="Invalid jmbg."), 400)

    k = int(jmbg[12])

    m = 11 - ((7 * (int(jmbg[0]) + int(jmbg[6])) + 6 * (int(jmbg[1]) + int(jmbg[7])) + 5 * (int(jmbg[2]) + int(jmbg[8]))
               + 4 * (int(jmbg[3]) + int(jmbg[9])) + 3 * (int(jmbg[4]) + int(jmbg[10])) + 2 * (int(jmbg[5]) + int(jmbg[11]))) % 11)

    if 1 <= m <= 9 and k != m:
        return make_response(jsonify(message="Invalid jmbg."), 400)
    if k != 0 and m == 10 or m == 11:
        return make_response(jsonify(message="Invalid jmbg."), 400)

    valid = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+([.]\w{2,3})+$", email)

    if not valid:
        return make_response(jsonify(message="Invalid email."), 400)

    if not (re.search("[a-z]", password) and re.search("[A-Z]", password) and re.search("[0-9]", password) and len(password) >=8):
        return make_response(jsonify(message="Invalid password."), 400)

    user = User.query.filter(User.email == email).first()

    if user:
        return make_response(jsonify(message="Email already exists."), 400)

    user = User(jmbg=jmbg, email=email, password=password, forename=forename, surname=surname, roleId=2)
    database.session.add(user)
    database.session.commit()

    return Response(status = 200)

jwt = JWTManager(application)

@application.route("/login", methods=["POST"])
def login():
    email = request.json.get("email", "")
    password = request.json.get("password", "")

    if len(email) == 0:
        return make_response(jsonify(message="Field email is missing."), 400)
    if len(password) == 0:
        return make_response(jsonify(message="Field password is missing."), 400)

    valid = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+([.]\w{2,3})+$", email)

    if not valid:
        return make_response(jsonify(message="Invalid email."), 400)

    user = User.query.filter(and_(User.email == email, User.password == password)).first()

    if not user:
        return make_response(jsonify(message="Invalid credentials."), 400)

    additionalClaims = {
        "jmbg": user.jmbg,
        "forename": user.forename,
        "surname": user.surname,
        "role": str(user.role)
    }

    accessToken = create_access_token(identity=user.email, additional_claims=additionalClaims)
    refreshToken = create_refresh_token(identity=user.email, additional_claims=additionalClaims)

    return make_response(jsonify(accessToken=accessToken, refreshToken=refreshToken), 200)

@application.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    refreshClaims = get_jwt()

    additionalClaims = {
        "jmbg": refreshClaims["jmbg"],
        "forename": refreshClaims["forename"],
        "surname": refreshClaims["surname"],
        "role": refreshClaims["role"]
    }

    return make_response(jsonify(accessToken=create_access_token(identity=identity, additional_claims=additionalClaims)), 200)

@application.route("/delete", methods=["POST"])
@roleCheck(role="admin")
def delete():

    toDelete = request.json.get("email", "")

    if len(toDelete) == 0:
        return make_response(jsonify(message="Field email is missing."), 400)

    valid = re.search("^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+([.]\w{2,3})+$", toDelete)

    if not valid:
        return make_response(jsonify(message="Invalid email."), 400)

    user = User.query.filter(User.email==toDelete).first()

    if not user:
        return make_response(jsonify(message="Unknown user."), 400)

    database.session.delete(user)
    database.session.commit()

    return Response(status=200)

if ( __name__ == "__main__" ):
    database.init_app ( application );
    application.run ( debug = True, host = "0.0.0.0", port = 5002 )

