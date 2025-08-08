#!/usr/bin/env python3
"""
Database initialization script for Sensai
"""

import os
import sys
import asyncio

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def init_database():
    """Initialize the database with all required tables"""
    try:
        from api.db import init_db
        print("🔄 Initializing database...")
        
        # This will create all tables
        await init_db()
        
        print("✅ Database initialized successfully!")
        print("📁 Database location: src/db/db.sqlite")
        
        # Test that we can connect and query
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
                print("This might cause errors. Consider deleting the database and reinitializing.")
            else:
                print("\n🎉 All tables exist! Database is ready.")
        
        print("\n🚀 Ready to start backend!")
        
    except Exception as e:
        print(f"❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(init_database())
    if success:
        print("\n🚀 Ready to start backend!")
    else:
        print("\n💥 Database initialization failed!")
        sys.exit(1)
