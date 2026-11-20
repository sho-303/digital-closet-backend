# ==========================================
# File: app.py
# Date: 2026-11-09
# Creator: K025C2093 吉川蔣
# ==========================================

import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
CORS(app)

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'closet.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'

# フロントエンド（frontendフォルダ）のファイルを配信する設定
@app.route('/')
def index():
    return send_from_directory('frontend', 'login.html')

@app.route('/<path:filename>')
def serve_frontend(filename):
    return send_from_directory('frontend', filename)

db = SQLAlchemy(app)
os.makedirs(os.path.join(basedir, app.config['UPLOAD_FOLDER']), exist_ok=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    def to_dict(self):
        return {"id": self.id, "username": self.username}

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    pattern = db.Column(db.String(50))
    brand = db.Column(db.String(50))
    season = db.Column(db.String(50))
    style = db.Column(db.String(50))
    image_url = db.Column(db.String(200))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "category": self.category,
            "color": self.color, "pattern": self.pattern, "brand": self.brand,
            "season": self.season, "style": self.style, "image_url": self.image_url, "user_id": self.user_id
        }

class Coordinate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    image_url = db.Column(db.String(200))
    season = db.Column(db.String(50))
    style = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    def to_dict(self):
        return {
            "id": self.id, "title": self.title, "image_url": self.image_url,
            "season": self.season, "style": self.style, "user_id": self.user_id
        }

class PurchaseItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, default=0.0)
    category = db.Column(db.String(50), nullable=False)
    memo = db.Column(db.String(200))
    image = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "price": self.price,
            "category": self.category,
            "memo": self.memo,
            "image": self.image,
            "user_id": self.user_id
        }

with app.app_context():
    db.create_all()

# アップロード画像配信用ルート
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(os.path.join(basedir, app.config['UPLOAD_FOLDER']), filename)

@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({"error": "ユーザー名とパスワードを入力してください"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "このメールアドレスはすでに登録されています"}), 400
    hashed_password = generate_password_hash(password)
    new_user = User(username=username, password_hash=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "ユーザー登録が完了しました", "user": new_user.to_dict()}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        return jsonify({"message": "ログイン成功", "user": user.to_dict()}), 200
    return jsonify({"error": "メールアドレスまたはパスワードが間違っています"}), 401

@app.route('/items', methods=['GET'])
def get_items():
    user_id = request.args.get('user_id')
    if user_id:
        items = Item.query.filter_by(user_id=user_id).all()
    else:
        items = Item.query.all()
    return jsonify([item.to_dict() for item in items])

@app.route('/items', methods=['POST'])
def add_item():
    name = request.form.get('name')
    category = request.form.get('category')
    color = request.form.get('color')
    pattern = request.form.get('pattern', '')
    brand = request.form.get('brand', '')
    season = request.form.get('season', '')
    style = request.form.get('style', '')
    user_id = request.form.get('user_id')
    if not name or not category or not color:
        return jsonify({"error": "Invalid data"}), 400
    
    image_url = ""
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1].lower()
            if not ext:
                ext = '.jpg'
            filename = f"{uuid.uuid4().hex}{ext}"
            
            upload_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            image_url = f"/{app.config['UPLOAD_FOLDER']}/{filename}"
            
    new_item = Item(
        name=name, category=category, color=color, pattern=pattern,
        brand=brand, season=season, style=style, image_url=image_url,
        user_id=int(user_id) if user_id else None
    )
    db.session.add(new_item)
    db.session.commit()
    return jsonify(new_item.to_dict()), 201

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    user_id = request.args.get('user_id')
    query = Item.query.filter_by(id=item_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    item = query.first()
    if not item:
        return jsonify({"error": "Item not found"}), 404
    return jsonify(item.to_dict())

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    user_id = request.form.get('user_id')
    query = Item.query.filter_by(id=item_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    item = query.first()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    item.name = request.form.get('name', item.name)
    item.category = request.form.get('category', item.category)
    item.color = request.form.get('color', item.color)
    item.pattern = request.form.get('pattern', item.pattern)
    item.brand = request.form.get('brand', item.brand)
    item.season = request.form.get('season', item.season)
    item.style = request.form.get('style', item.style)

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1].lower()
            if not ext:
                ext = '.jpg'
            filename = f"{uuid.uuid4().hex}{ext}"
            
            upload_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            item.image_url = f"/{app.config['UPLOAD_FOLDER']}/{filename}"

    db.session.commit()
    return jsonify(item.to_dict())

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    user_id = request.args.get('user_id')
    query = Item.query.filter_by(id=item_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    item = query.first()
    if not item:
        return jsonify({"error": "Item not found"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted successfully"})

@app.route('/coordinates', methods=['GET'])
def get_coordinates():
    user_id = request.args.get('user_id')
    if user_id:
        coordinates = Coordinate.query.filter_by(user_id=user_id).all()
    else:
        coordinates = Coordinate.query.all()
    return jsonify([c.to_dict() for c in coordinates])

@app.route('/coordinates', methods=['POST'])
def add_coordinate():
    title = request.form.get('title')
    season = request.form.get('season', '')
    style = request.form.get('style', '')
    user_id = request.form.get('user_id')
    if not title:
        return jsonify({"error": "Title is required"}), 400
        
    image_url = ""
    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename != '':
            ext = os.path.splitext(file.filename)[1].lower()
            if not ext:
                ext = '.jpg'
            filename = f"{uuid.uuid4().hex}{ext}"
            
            upload_dir = os.path.join(basedir, app.config['UPLOAD_FOLDER'])
            os.makedirs(upload_dir, exist_ok=True)
            filepath = os.path.join(upload_dir, filename)
            file.save(filepath)
            image_url = f"/{app.config['UPLOAD_FOLDER']}/{filename}"
            
    new_coordinate = Coordinate(
        title=title, season=season, style=style, image_url=image_url,
        user_id=int(user_id) if user_id else None
    )
    db.session.add(new_coordinate)
    db.session.commit()
    return jsonify(new_coordinate.to_dict()), 201

# 購入候補リストの取得・追加
@app.route('/purchase-items', methods=['GET', 'POST'])
def handle_purchase_items():
    user_id = request.args.get('user_id') or (request.json.get('user_id') if request.is_json else None)
    
    if request.method == 'GET':
        if user_id:
            items = PurchaseItem.query.filter_by(user_id=user_id).all()
        else:
            items = PurchaseItem.query.all()
        return jsonify([item.to_dict() for item in items])
    
    elif request.method == 'POST':
        data = request.get_json() or {}
        name = data.get('name')
        if not name:
            return jsonify({"error": "商品名は必須です"}), 400
            
        new_item = PurchaseItem(
            name=name,
            price=data.get('price', 0),
            category=data.get('category', '未分類'),
            memo=data.get('memo', ''),
            image=data.get('image', ''),
            user_id=int(data.get('user_id')) if data.get('user_id') else None
        )
        db.session.add(new_item)
        db.session.commit()
        return jsonify(new_item.to_dict()), 201

# 購入候補の編集・削除
@app.route('/purchase-items/<int:item_id>', methods=['PUT', 'DELETE'])
def handle_purchase_item_detail(item_id):
    user_id = request.args.get('user_id') or (request.json.get('user_id') if request.is_json else None)
    query = PurchaseItem.query.filter_by(id=item_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    item = query.first()
    
    if not item:
        return jsonify({"error": "Item not found"}), 404
        
    if request.method == 'PUT':
        data = request.get_json() or {}
        item.name = data.get('name', item.name)
        item.price = data.get('price', item.price)
        item.category = data.get('category', item.category)
        item.memo = data.get('memo', item.memo)
        if 'image' in data:
            item.image = data.get('image')
            
        db.session.commit()
        return jsonify(item.to_dict())
        
    elif request.method == 'DELETE':
        db.session.delete(item)
        db.session.commit()
        return jsonify({"message": "Deleted successfully"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)