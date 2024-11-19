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

@app.route('/api/paintings/food/random', methods=['GET'])
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

@app.route('/api/paintings/food/count', methods=['GET'])
def get_paintings_with_food_count():
    """Get the total count of paintings containing food"""
    try:
        query = text("""
            SELECT COUNT(*) as total
            FROM paintings p
            JOIN food_detected f ON p.painting_id = f.painting_id
            WHERE f.food_detected = 1
        """)
        
        with engine.connect() as conn:
            result = conn.execute(query)
            count = result.scalar()
            
            return jsonify({
                'total_paintings_with_food': count
            })
            
    except Exception as e:
        return jsonify({
            'error': f'An error occurred: {str(e)}'
        }), 500



if __name__ == '__main__':
    app.run(debug=True)