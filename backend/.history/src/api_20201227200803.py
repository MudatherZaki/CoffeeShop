import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
# db_drop_and_create_all()

# Error Func

def Error(status_code, message):
    return jsonify({
        "success": False, 
        "error": status_code,
        "message": message
    }), status_code

# ROUTES

@app.route('/drinks')
def get_drinks():
    drinks = Drink.query.all()
    if len(drinks) < 1:
        abort(404)
    short_drinks = [drink.short() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": short_drinks
    }), 200

@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    drinks = Drink.query.all()
    if len(drinks) < 1:
        abort(404)
    short_drinks = [drink.long() for drink in drinks]
    return jsonify({
        "success": True,
        "drinks": short_drinks
    }), 200

@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def add_drink(payload):
    body = request.get_json()
    new_title = body.get('title', None)
    if not new_title:
        abort(400)
    if len(Drink.query.filter(Drink.title == new_title).all()) > 0:
        return Error(400, "Title already exists.")
    new_recipe = body.get('recipe', None)
    if not new_recipe:
        return Error(400, "Recipe is required")
    
    new_drink = Drink(title=new_title, recipe=json.dumps([new_recipe]))
    try:
        print(new_drink.long())
        new_drink.insert()
        return jsonify({
            "success": True,
            "drinks": [new_drink.long()]
        }), 200
    except:
        abort(422)

@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def edit_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    body = request.get_json()
    new_title = body.get('title', None)
    new_recipe = body.get('recipe', None)
    if new_title:
        drink.title = new_title
    if new_recipe:
        drink.recipe = new_recipe
    
    try:
        drink.update()
        return jsonify({
            "success": True,
            "drinks": [drink.long()]
        }), 200
    except:
        abort(422)
    
@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    drink = Drink.query.filter(Drink.id == id).one_or_none()
    if not drink:
        abort(404)
    try:
        drink.delete()
        return jsonify({
            "success": True,
            "delete": id
        }), 200
    except:
        abort(422)

# Error Handling

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False, 
        "error": 422,
        "message": "unprocessable"
        }), 422

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False, 
        "error": 400,
        "message": "bad request"
        }), 400

@app.errorhandler(404)
def bad_request(error):
    return jsonify({
        "success": False, 
        "error": 404,
        "message": "Not found"
        }), 404

@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False, 
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code

