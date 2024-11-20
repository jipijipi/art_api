from flask import Flask, jsonify
from dotenv import load_dotenv
from sqlalchemy import create_engine, Table, Column, String, Integer, Boolean, DateTime, MetaData, select, func, text
import random
from urllib.parse import quote_plus
import os

app = Flask(__name__)

load_dotenv()
password = os.getenv('PASSWORD')

engine = create_engine(f'mysql+pymysql://root:{password}@localhost/art_and_food_db')

@app.route('/', methods=['GET'])
def welcome():
    """Welcome endpoint with API information"""
    return jsonify({
        'message': 'Welcome to the Food in Art API',
        'endpoints': {
            'random_food_paintings': '/api/paintings/random - Get 10 random paintings containing food',
            'painting_details': '/api/painting/<id> - Get details of a specific painting',
            'author_details': '/api/author/<id> - Get details of a specific author and their food-related paintings'
        }
    })

@app.route('/api/painting/<painting_id>', methods=['GET'])
def get_painting_details(painting_id):
    """Get detailed information about a specific painting"""
    try:
        query = text("""
            SELECT 
                p.painting_id,
                p.title,
                p.image_url,
                p.creation_date,
                p.time_period,
                f.food_detected,
                a.painter AS artist_name,
                a.author_country,
                l.location_name,
                l.location_country
            FROM paintings p
            LEFT JOIN food_detected f ON p.painting_id = f.painting_id
            LEFT JOIN correspondence c ON p.painting_id = c.painting_id
            LEFT JOIN authors a ON c.author_id = a.author_id
            LEFT JOIN locations l ON c.location_id = l.location_id
            WHERE p.painting_id = :painting_id
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query, {'painting_id': painting_id}).fetchone()
            
            if not result:
                return jsonify({
                    'error': f'No painting found with id: {painting_id}'
                }), 404
            
            painting = {
                'painting_id': result[0],
                'title': result[1],
                'image_url': result[2],
                'creation_date': result[3],
                'time_period': result[4],
                'contains_food': bool(result[5]) if result[5] is not None else None,
                'artist': result[6],
                'artist_country': result[7],
                'location': result[8],
                'location_country': result[9]
            }
            
            return jsonify(painting)
            
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500

@app.route('/api/author/<author_id>', methods=['GET'])
def get_author_food_paintings(author_id):
    """Get all food-related paintings by a specific author"""
    try:
        query = text("""
            SELECT 
                p.painting_id,
                p.title,
                p.image_url,
                p.creation_date,
                p.time_period,
                a.painter AS artist_name,
                a.author_country,
                l.location_name,
                l.location_country
            FROM paintings p 
            JOIN correspondence c ON p.painting_id = c.painting_id
            JOIN authors a ON c.author_id = a.author_id
            JOIN food_detected f ON p.painting_id = f.painting_id
            LEFT JOIN locations l ON c.location_id = l.location_id
            WHERE c.author_id = :author_id 
            AND f.food_detected = 1
            ORDER BY p.creation_date ASC
        """)
        
        with engine.connect() as conn:
            # First check if author exists
            author_check = text("""
                SELECT painter, author_country, date_of_birth 
                FROM authors 
                WHERE author_id = :author_id
            """)
            author_result = conn.execute(author_check, {'author_id': author_id}).fetchone()
            
            if not author_result:
                return jsonify({
                    'error': f'No author found with id: {author_id}'
                }), 404

            # Get the paintings
            result = conn.execute(query, {'author_id': author_id})
            paintings = []
            for row in result:
                paintings.append({
                    'painting_id': row[0],
                    'title': row[1],
                    'image_url': row[2],
                    'creation_date': row[3],
                    'time_period': row[4],
                    'artist_name': row[5],
                    'artist_country': row[6],
                    'location_name': row[7],
                    'location_country': row[8]
                })
            
            response = {
                'author': {
                    'id': author_id,
                    'name': author_result[0],
                    'country': author_result[1],
                    'birth_date': author_result[2],
                },
                'total_food_paintings': len(paintings),
                'paintings': paintings
            }
            
            if not paintings:
                response['message'] = 'No food-related paintings found for this author'
            
            return jsonify(response)
            
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500
        
@app.route('/api/paintings/random', methods=['GET'])
def get_random_paintings_with_food():
    """Get 10 random paintings containing food"""
    try:
        query = text("""
            SELECT p.painting_id, p.title, p.image_url
            FROM paintings p
            JOIN food_detected f ON p.painting_id = f.painting_id
            WHERE f.food_detected = 1
            ORDER BY RAND()
            LIMIT 10
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            paintings = []
            for row in result:
                paintings.append({
                    'painting_id': row[0],
                    'title': row[1],
                    'image_url': row[2]
                })
            
            if not paintings:
                return jsonify({
                    'error': 'No paintings with food detected found in database'
                }), 404
            
            return jsonify(paintings)
            
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500




if __name__ == '__main__':
    app.run(debug=True, port=8080)