"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User
from models import Planet, Character, Favorite

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Handle/serialize errors like a JSON object


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints


@app.route('/')
def sitemap():
    return generate_sitemap(app)


app = Flask(__name__)
app.url_map.strict_slashes = False

# Configure the database connection
db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace(
        "postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

# Error handler


@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code


@app.route('/')
def sitemap():
    return generate_sitemap(app)


@app.route('/people', methods=['GET'])
def get_all_people():
    characters = Character.query.all()
    results = [char.serialize() for char in characters]
    return jsonify(results), 200


@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_person(people_id):
    character = Character.query.get(people_id)
    if character is None:
        return jsonify({"error": "Character not found"}), 404
    return jsonify(character.serialize()), 200


@app.route('/planets', methods=['GET'])
def get_all_planets():
    planets = Planet.query.all()
    results = [planet.serialize() for planet in planets]
    return jsonify(results), 200


@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if planet is None:
        return jsonify({"error": "Planet not found"}), 404
    return jsonify(planet.serialize()), 200


@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify([user.serialize() for user in users]), 200


@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    current_user = User.query.first()
    if not current_user:
        return jsonify({"error": "No users found"}), 404

    favorites = [fav.serialize() for fav in current_user.favorites]
    return jsonify(favorites), 200


@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_favorite_planet(planet_id):
    current_user = User.query.first()
    if not current_user:
        return jsonify({"error": "No users found"}), 404

    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    existing = Favorite.query.filter_by(
        user_id=current_user.id, planet_id=planet_id).first()
    if existing:
        return jsonify({"msg": "Planet already in favorites"}), 400

    favorite = Favorite(user_id=current_user.id, planet_id=planet_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.serialize()), 201


@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_favorite_character(people_id):
    current_user = User.query.first()
    if not current_user:
        return jsonify({"error": "No users found"}), 404

    character = Character.query.get(people_id)
    if not character:
        return jsonify({"error": "Character not found"}), 404

    existing = Favorite.query.filter_by(
        user_id=current_user.id, character_id=people_id).first()
    if existing:
        return jsonify({"msg": "Character already in favorites"}), 400

    favorite = Favorite(user_id=current_user.id, character_id=people_id)
    db.session.add(favorite)
    db.session.commit()
    return jsonify(favorite.serialize()), 201


@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def delete_favorite_planet(planet_id):
    current_user = User.query.first()
    if not current_user:
        return jsonify({"error": "No users found"}), 404

    favorite = Favorite.query.filter_by(
        user_id=current_user.id, planet_id=planet_id).first()
    if not favorite:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite planet deleted"}), 200


@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def delete_favorite_character(people_id):
    current_user = User.query.first()
    if not current_user:
        return jsonify({"error": "No users found"}), 404

    favorite = Favorite.query.filter_by(
        user_id=current_user.id, character_id=people_id).first()
    if not favorite:
        return jsonify({"error": "Favorite not found"}), 404

    db.session.delete(favorite)
    db.session.commit()
    return jsonify({"msg": "Favorite character deleted"}), 200


@app.route('/planets', methods=['POST'])
def create_planet():
    data = request.get_json()
    required_fields = ['name', 'appearance', 'terrain', 'climate']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    planet = Planet(
        name=data['name'],
        appearance=data['appearance'],
        terrain=data['terrain'],
        climate=data['climate']
    )
    db.session.add(planet)
    db.session.commit()
    return jsonify(planet.serialize()), 201

@app.route('/planets/<int:planet_id>', methods=['PUT'])
def update_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    data = request.get_json()
    for field in ['name', 'appearance', 'terrain', 'climate']:
        if field in data:
            setattr(planet, field, data[field])

    db.session.commit()
    return jsonify(planet.serialize()), 200


@app.route('/planets/<int:planet_id>', methods=['DELETE'])
def delete_planet(planet_id):
    planet = Planet.query.get(planet_id)
    if not planet:
        return jsonify({"error": "Planet not found"}), 404

    db.session.delete(planet)
    db.session.commit()
    return jsonify({"msg": "Planet is deleted"}), 200



@app.route('/people', methods=['POST'])
def create_character():
    data = request.get_json()
    required_fields = ['name', 'appearance', 'affiliation']
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing fields"}), 400

    character = Character(
        name=data['name'],
        appearance=data['appearance'],
        affiliation=data['affiliation']
    )
    db.session.add(character)
    db.session.commit()
    return jsonify(character.serialize()), 201


@app.route('/people/<int:people_id>', methods=['PUT'])
def update_character(people_id):
    character = Character.query.get(people_id)
    if not character:
        return jsonify({"error": "Character not found"}), 404

    data = request.get_json()
    for field in ['name', 'appearance', 'affiliation']:
        if field in data:
            setattr(character, field, data[field])

    db.session.commit()
    return jsonify(character.serialize()), 200


@app.route('/people/<int:people_id>', methods=['DELETE'])
def delete_character(people_id):
    character = Character.query.get(people_id)
    if not character:
        return jsonify({"error": "Character not found"}), 404

    db.session.delete(character)
    db.session.commit()
    return jsonify({"msg": "Character is deleted"}), 200

# this only runs if `$ python src/app.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
