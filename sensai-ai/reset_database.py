#!/usr/bin/env python3
"""
Database reset script for Sensai
This will delete the existing database and create a fresh one with all tables.
"""

import os
import sys
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def reset_database():
    """Delete existing database and create a fresh one"""
    try:
        from api.config import sqlite_db_path
        
        # Delete existing database
        if os.path.exists(sqlite_db_path):
            print(f"🗑️  Deleting existing database: {sqlite_db_path}")
            os.remove(sqlite_db_path)
            print("✅ Database deleted")
        else:
            print("ℹ️  No existing database found")
        
        # Initialize fresh database
        from api.db import init_db
        print("🔄 Creating fresh database...")
        
        await init_db()
        
        print("✅ Fresh database created successfully!")
        print(f"📁 Database location: {sqlite_db_path}")
        
        # Verify all tables exist
        from api.utils.db import get_new_db_connection
        
        async with get_new_db_connection() as conn:
            cursor = await conn.cursor()
            
            # Check if ALL important tables exist
            tables_to_check = [
                "users", "organizations", "user_organizations", "pdf_documents", 
                "generated_quizzes", "quiz_questions", "quiz_submissions", "quiz_answers",
                "tasks", "questions", "courses", "cohorts", "milestones",
                "course_tasks", "course_milestones", "course_cohorts",
                "task_completions", "chat_history", "scorecards", "question_scorecards",
                "course_generation_jobs", "task_generation_jobs", "code_drafts",
                "org_api_keys"
            ]
            
            missing_tables = []
            for table in tables_to_check:
                await cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                result = await cursor.fetchone()
                if result:
                    print(f"✅ Table '{table}' exists")
                else:
                    print(f"❌ Table '{table}' missing")
                    missing_tables.append(table)
            
            if missing_tables:
                print(f"\n⚠️  Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                print("\n🎉 All tables exist! Database is ready.")
                return True
        
    except Exception as e:
        print(f"❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔄 Resetting Sensai database...")
    success = asyncio.run(reset_database())
    if success:
        print("\n🚀 Database reset complete! Ready to start backend.")
    else:
        print("\n💥 Database reset failed!")
        sys.exit(1)
