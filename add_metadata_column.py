"""
Migration script to add project_metadata column to projects table
Run this once to update the database schema
"""
from app import create_app, db
from sqlalchemy import text

app = create_app()

with app.app_context():
    try:
        # Check if project_metadata column exists
        result = db.session.execute(text("PRAGMA table_info(projects)"))
        columns = [row[1] for row in result]

        if 'project_metadata' not in columns:
            print("Adding 'project_metadata' column to projects table...")
            db.session.execute(text("ALTER TABLE projects ADD COLUMN project_metadata TEXT"))
            db.session.commit()
            print("✅ Successfully added 'project_metadata' column!")
        else:
            print("✅ 'project_metadata' column already exists!")

    except Exception as e:
        print(f"❌ Error: {e}")
        db.session.rollback()

