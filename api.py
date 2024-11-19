from flask import Flask, jsonify, request
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, DateTime, text
from datetime import datetime

app = Flask(__name__)

# Database configuration
engine = create_engine('sqlite:///local.db', echo=True)
metadata = MetaData()

# Define items table
items = Table('items', metadata,
    Column('id', Integer, primary_key=True),
    Column('name', String(100), nullable=False),
    Column('description', String(200)),
    Column('created_at', DateTime, default=datetime.utcnow)
)

# Create all tables
metadata.create_all(engine)

def row_to_dict(row):
    return {
        'id': row.id,
        'name': row.name,
        'description': row.description,
        'created_at': row.created_at.isoformat() if row.created_at else None
    }

@app.route('/')
def home():
    return "Welcome to the Flask API!"

@app.route('/api/items', methods=['GET'])
def get_items():
    with engine.connect() as conn:
        result = conn.execute(items.select())
        items_list = [row_to_dict(row) for row in result]
        return jsonify(items_list)

@app.route('/api/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    with engine.connect() as conn:
        result = conn.execute(
            items.select().where(items.c.id == item_id)
        ).first()
        
        if result is None:
            return jsonify({'error': 'Item not found'}), 404
            
        return jsonify(row_to_dict(result))

@app.route('/api/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    if not data or 'name' not in data:
        return jsonify({'error': 'Name is required'}), 400
    
    with engine.connect() as conn:
        # Insert new item
        result = conn.execute(
            items.insert().values(
                name=data['name'],
                description=data.get('description', ''),
                created_at=datetime.utcnow()
            )
        )
        conn.commit()
        
        # Fetch the created item
        new_item = conn.execute(
            items.select().where(items.c.id == result.inserted_primary_key[0])
        ).first()
        
        return jsonify(row_to_dict(new_item)), 201

@app.route('/api/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    with engine.connect() as conn:
        # Check if item exists
        existing_item = conn.execute(
            items.select().where(items.c.id == item_id)
        ).first()
        
        if existing_item is None:
            return jsonify({'error': 'Item not found'}), 404
        
        # Prepare update values
        update_values = {}
        if 'name' in data:
            update_values['name'] = data['name']
        if 'description' in data:
            update_values['description'] = data['description']
        
        # Update item
        conn.execute(
            items.update()
            .where(items.c.id == item_id)
            .values(**update_values)
        )
        conn.commit()
        
        # Fetch updated item
        updated_item = conn.execute(
            items.select().where(items.c.id == item_id)
        ).first()
        
        return jsonify(row_to_dict(updated_item))

@app.route('/api/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    with engine.connect() as conn:
        # Check if item exists
        existing_item = conn.execute(
            items.select().where(items.c.id == item_id)
        ).first()
        
        if existing_item is None:
            return jsonify({'error': 'Item not found'}), 404
        
        # Delete item
        conn.execute(items.delete().where(items.c.id == item_id))
        conn.commit()
        
        return jsonify({'message': 'Item deleted successfully'}), 200

@app.route('/api/search', methods=['GET'])
def search_items():
    search_term = request.args.get('q', '')
    
    with engine.connect() as conn:
        query = items.select().where(
            items.c.name.ilike(f'%{search_term}%') |
            items.c.description.ilike(f'%{search_term}%')
        )
        result = conn.execute(query)
        items_list = [row_to_dict(row) for row in result]
        return jsonify(items_list)

if __name__ == '__main__':
    app.run(debug=True, port=5001)