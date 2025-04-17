# migrate.py

from app import app
from src.models import db

with app.app_context():
    db.create_all()
    print("✅ Database tables created/updated successfully.")
