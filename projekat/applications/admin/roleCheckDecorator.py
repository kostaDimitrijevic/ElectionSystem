from functools import wraps

from flask import make_response, jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt;

def roleCheck ( role ):
    def innerRole ( function ):
        @wraps ( function )
        def decorator ( *arguments, **keywordArguments ):
            verify_jwt_in_request ( )
            claims = get_jwt ( )
            if ( ( "role" in claims ) and ( role in claims["role"] ) ):
                return function ( *arguments, **keywordArguments )
            else:
                return make_response(jsonify(msg="Missing Authorization Header"), 401)

        return decorator

    return innerRole


