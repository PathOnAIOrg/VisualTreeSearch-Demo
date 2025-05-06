from sqlalchemy import create_engine, text
import traceback
import logging
from typing import Dict, List, Any
import json

from fastapi import APIRouter, HTTPException

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

router = APIRouter()

# Database connection parameters of webarena container
DB_CONFIG = {
    "username": "root",
    "password": "1234567890",
    "database": "magentodb",
    "host": "172.17.0.2",
    "port": 3306
}

def get_db_connection():
    """Create and return a SQLAlchemy database engine"""
    try:
        connection_string = f"mysql+pymysql://{DB_CONFIG['username']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
        logging.info(f"Creating connection with: {connection_string}")
        
        engine = create_engine(
            connection_string,
            connect_args={'connect_timeout': 30},
            echo=False  # Set to True for SQL debugging
        )
        return engine
    except Exception as e:
        logging.error(f"Error creating database engine: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Database connection error: {str(e)}")

@router.get("/status")
async def db_status():
    """Check database connection status"""
    try:
        engine = get_db_connection()
        with engine.connect() as connection:
            version_query = connection.execute(text("SELECT VERSION()"))
            version = version_query.scalar()
            
        return {
            "status": "connected",
            "version": version,
            "config": {
                "host": DB_CONFIG["host"],
                "port": DB_CONFIG["port"],
                "database": DB_CONFIG["database"],
                "username": DB_CONFIG["username"]
            }
        }
    except Exception as e:
        logging.error(f"Database status check failed: {str(e)}")
        return {
            "status": "error",
            "message": str(e),
            "config": {
                "host": DB_CONFIG["host"],
                "port": DB_CONFIG["port"],
                "database": DB_CONFIG["database"],
                "username": DB_CONFIG["username"]
            }
        }

@router.get("/tables")
async def list_tables():
    """List all tables in the database"""
    try:
        engine = get_db_connection()
        tables = []
        
        with engine.connect() as connection:
            result = connection.execute(text("SHOW TABLES"))
            for row in result:
                tables.append(row[0])
        
        return {
            "status": "success",
            "table_count": len(tables),
            "tables": tables
        }
    except Exception as e:
        logging.error(f"Error listing tables: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error listing tables: {str(e)}")

@router.get("/tables/{table_name}/structure")
async def get_table_structure(table_name: str):
    """Get the structure of a specific table"""
    try:
        engine = get_db_connection()
        
        with engine.connect() as connection:
            # Check if table exists
            tables_result = connection.execute(text("SHOW TABLES"))
            tables = [row[0] for row in tables_result]
            
            if table_name not in tables:
                raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")
            
            # Get table structure
            columns_result = connection.execute(text(f"DESCRIBE {table_name}"))
            columns = []
            for row in columns_result:
                columns.append({
                    "field": row[0],
                    "type": row[1],
                    "null": row[2],
                    "key": row[3],
                    "default": row[4],
                    "extra": row[5]
                })
        
        return {
            "status": "success",
            "table": table_name,
            "columns": columns
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting table structure: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error getting table structure: {str(e)}")

@router.get("/query")
async def run_test_query(query: str = "SELECT VERSION()"):
    """Run a test query (read-only for safety)"""
    # Only allow SELECT queries for safety
    if not query.strip().upper().startswith("SELECT"):
        raise HTTPException(status_code=400, detail="Only SELECT queries are allowed")
    
    try:
        engine = get_db_connection()
        
        with engine.connect() as connection:
            result = connection.execute(text(query))
            rows = [dict(row._mapping) for row in result]
        
        return {
            "status": "success",
            "query": query,
            "row_count": len(rows),
            "results": rows
        }
    except Exception as e:
        logging.error(f"Error executing query: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error executing query: {str(e)}")
