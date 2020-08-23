import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random
from functools import wraps
from jose import jwt
from urllib.request import urlopen
import json

from models import setup_db, Account


def create_app(test_config=None):
  # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    # @app.after_request
    # def after_request(response):
    #     response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
    #     response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    #     return response
    # __________________________________________________AUTH0__________________________________________________

    AUTH0_DOMAIN = 'DOMAIN_HERE'
    ALGORITHMS = ['RS256']
    API_AUDIENCE = 'AUDIENCE'

    class AuthError(Exception):
        def __init__(self, error, status_code):
            self.error = error
            self.status_code = status_code

    def verify_decode_jwt(token):
        # GET THE PUBLIC KEY FROM AUTH0
        jsonurl = urlopen(f'https://{AUTH0_DOMAIN}/.well-known/jwks.json')
        jwks = json.loads(jsonurl.read())
        # GET THE DATA IN THE HEADER
        unverified_header = jwt.get_unverified_header(token)

        # CHOOSE OUR KEY
        rsa_key = {}
        if 'kid' not in unverified_header:
            raise AuthError({
                'code': 'invalid_header',
                'description': 'Authorization malformed.'
            }, 401)

        for key in jwks['keys']:
            if key['kid'] == unverified_header['kid']:
                rsa_key = {
                    'kty': key['kty'],
                    'kid': key['kid'],
                    'use': key['use'],
                    'n': key['n'],
                    'e': key['e']
                }

        # Finally, verify!!!
        if rsa_key:
            try:
                # USE THE KEY TO VALIDATE THE JWT
                payload = jwt.decode(
                    token,
                    rsa_key,
                    algorithms=ALGORITHMS,
                    audience=API_AUDIENCE,
                    issuer='https://' + AUTH0_DOMAIN + '/'
                )

                return payload

            except jwt.ExpiredSignatureError:
                raise AuthError({
                    'code': 'token_expired',
                    'description': 'Token expired.'
                }, 401)

            except jwt.JWTClaimsError:
                raise AuthError({
                    'code': 'invalid_claims',
                    'description': 'Incorrect claims. Please, check the audience and issuer.'
                }, 401)
            except Exception:
                raise AuthError({
                    'code': 'invalid_header',
                    'description': 'Unable to parse authentication token.'
                }, 400)
        raise AuthError({
            'code': 'invalid_header',
                    'description': 'Unable to find the appropriate key.'
        }, 400)
        # ____________________________________________________________________________________________________

    # ___________________________________________________AUTH___________________________________________________

    def get_token_auth_header():
        # Check if Authorization is present in the header or not
        if 'Authorization' not in request.headers:
            abort(401)

        # 'Authorization': 'Bearer <TOKEN>'
        # ['Bearer', '<TOKEN>']
        auth_header = request.headers['Authorization'].split(' ')
        # print(auth_header)

        if len(auth_header) != 2:
            abort(401)
        elif auth_header[0].lower() != 'bearer':
            abort(401)

        return auth_header[1]

    def check_permission(permissions, payload):
        if 'permissions' not in payload:
            abort(400)
        

        for permission in permissions:
            if permission not in payload['permissions']:
                abort(403)
        
        return True
        
    
    def requires_auth(permissions=[]):

        def requires_auth_sub(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                jwt = get_token_auth_header()
                try:
                    payload = verify_decode_jwt(jwt)
                except:
                    abort(401)
                
                check_permission(permissions, payload)
                return f(payload, *args, **kwargs)
            return wrapper
        return requires_auth_sub

    # ______________________________________________________________________________________________________

    # token = eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCIsImtpZCI6Ikt1RTdhaHEtdjIyQnhJLUhKZlhoUSJ9.eyJpc3MiOiJodHRwczovL3dkbmQtdGVzdGluZy51cy5hdXRoMC5jb20vIiwic3ViIjoiYXV0aDB8NWYzNmFiMDdhMWI0MWYwMDY3ODE3OThmIiwiYXVkIjoic2Vzc2lvbiIsImlhdCI6MTU5NzUxNzcyOCwiZXhwIjoxNTk3NTI0OTI4LCJhenAiOiJ0cHNRdk9vNFpVdXluTzdVanhYRzloVjdHdUZzT0pGNyIsInNjb3BlIjoiIn0.rAvqDU-Hc91BKGrWcORucZbJOF3bXzhqdZTJlP_po4lzA78El_QDRj2wglJPCe69uEI1taVIwRHPVI8AEH5SNSZDrI1m9HVEYtAC6iGSP5JsCURlWooUwHOk8AKHs7FS2fJtK89SG6_GfXz-o1EUuKhjg10BuuucNod2BkTZ2VjU6fWjvy5AzjO3LSMt8Qrz5xNGzKv5SWce_ArrBFwfgww-15nGlQTl9JVLH8XifNb2XeIFzslQrnD0m9Z3n8ZdUjfBCUXvYfaUyXoeZkm93QDSRQc2B5_ZSto5_TgqBa0UJCneUKzAzQQZIf0j02-Q9Xhr0hSpt9JpBqdw3hLkDw
    @app.route('/')
    @requires_auth(['get:greeting'])
    def index(jwt):
        return jsonify({
            'success': True,
            'message': 'Hello Udacians'
        })

    @app.route('/accounts')
    @requires_auth
    def retrieve_accounts(jwt):

        user_accounts = Account.query.count()

        # if user_accounts == 0:
        #     abort(404)

        return jsonify({
            'success': True,
            'total_accounts': user_accounts
        })

    @app.route('/accounts/<account_id>', methods=['PATCH'])
    def edit_account_first_name(account_id):
        account = Account.query.get(account_id)
        body = request.get_json()
        first_name = body.get("first_name", None)
        account.first_name = first_name
        account.update()
        return jsonify({'success': True, 'first_name': first_name})

    @app.route('/accounts/create', methods=['POST'])
    def create_account():
        body = request.get_json()
        first_name = body.get("first_name", None)
        last_name = body.get("last_name", None)
        init_balance = body.get("balance", None)
        search = body.get('search', None)

        # if first_name is None or last_name is None or init_balance is None:
        #     abort(400)

        res_body = {}

        # TDD Example
        if search:
            selection = Account.query.filter(
                Account.first_name.contains(search)).count()

            return jsonify({
                "success": True,
                "total_records": selection
            })

        else:
            error = False
            if first_name is None or init_balance is None:
                error = True
                abort(400)
            else:
                try:
                    new_account = Account(first_name=first_name,
                                          last_name=last_name, balance=init_balance)
                    new_account.insert()
                    res_body['created'] = new_account.id
                    res_body['first_name'] = new_account.first_name
                    res_body['last_name'] = new_account.last_name
                    res_body['balance'] = new_account.balance
                    res_body['success'] = True

                    return jsonify(res_body)

                except:
                    abort(422)

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "Resource Not Found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "Unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad Request"
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "error": 401,
            "message": "Unauthorized"
        }), 401
    
    @app.errorhandler(403)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "error": 403,
            "message": "Forbidden Access"
        }), 403

    return app
