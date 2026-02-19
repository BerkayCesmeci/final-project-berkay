import os
import urllib.parse
import pyodbc
from flask import Flask, render_template, request, redirect, url_for
from models import db, Post
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Veritabanı Değişkenleri
DB_USER = os.getenv('DB_USER')
DB_PASS = os.getenv('DB_PASSWORD')
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')

# Sistemdeki sürücüyü bul (18, 17 veya default)
try:
    drivers = [d for d in pyodbc.drivers() if 'SQL Server' in d]
    current_driver = drivers[0] if drivers else '{ODBC Driver 18 for SQL Server}'
except:
    current_driver = '{ODBC Driver 18 for SQL Server}'

# MSSQL Bağlantı Cümlesi
params = urllib.parse.quote_plus(
    f"DRIVER={current_driver};"
    f"SERVER={DB_HOST};"
    f"DATABASE={DB_NAME};"
    f"UID={DB_USER};"
    f"PWD={DB_PASS};"
    "Encrypt=yes;"
    "TrustServerCertificate=no;"
    "Connection Timeout=30;"
)

app.config['SQLALCHEMY_DATABASE_URI'] = f"mssql+pyodbc:///?odbc_connect={params}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    try:
        db.create_all()
    except Exception as e:
        print(f"Tablo oluşturma hatası (Yerelde sürücü yoksa normaldir): {e}")

@app.route('/')
def index():
    posts = Post.query.order_by(Post.id.desc()).all()
    # Azure Storage için sadece ana URL (Örn: https://hesap.blob.core.windows.net/konteynir)
    storage_url = os.getenv('AZURE_STORAGE_CONNECTION_STRING', '').split(';')[0].replace('DefaultEndpointsProtocol=https;AccountName=', 'https://').split(';')[0]
    # Eğer yukarıdaki karmaşık gelirse direkt tırnak içine URL'ni de yazabilirsin:
    # storage_url = "https://berkaystorage.blob.core.windows.net/resimler"
    return render_template('index.html', posts=posts, storage_url=storage_url)

@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    content = request.form.get('content')
    image_name = request.form.get('image_name')
    
    if title and content:
        new_post = Post(title=title, content=content, image_url=image_name)
        db.session.add(new_post)
        db.session.commit()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)