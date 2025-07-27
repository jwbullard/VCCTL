#!/usr/bin/env python3
"""
Explore Derby Database Schema

This script connects to the Derby database and explores the cement table schema
to find the correct column names for correlation data.
"""

import os
import jaydebeapi
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def explore_derby_schema():
    """Explore Derby database schema to find correlation columns."""
    
    # Derby database path
    derby_path = "/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/derby_original_database/vcctl_cement"
    derby_jar = "/Users/jwbullard/Library/CloudStorage/OneDrive-TexasA&MUniversity/Documents/Projects/Modeling/VCCTL-THAMES-SPRING/vcctl-gtk/db-derby-10.6.2.1-bin/lib/derby.jar"
    
    try:
        # Connect to Derby database
        logger.info(f"Connecting to Derby database: {derby_path}")
        connection = jaydebeapi.connect(
            "org.apache.derby.jdbc.EmbeddedDriver",
            f"jdbc:derby:{derby_path};create=false",
            {"user": "", "password": ""},
            derby_jar
        )
        logger.info("Successfully connected to Derby database")
        
        cursor = connection.cursor()
        
        # Get all table names
        cursor.execute("SELECT TABLENAME FROM SYS.SYSTABLES WHERE TABLETYPE='T'")
        tables = cursor.fetchall()
        logger.info("Available tables:")
        for table in tables:
            logger.info(f"  - {table[0]}")
        
        # Get cement table schema - use Derby syntax
        logger.info("\nCement table column information:")
        cursor.execute("SELECT * FROM CEMENT FETCH FIRST 1 ROWS ONLY")
        
        # Get column names from metadata
        columns_info = cursor.description
        column_names = [col[0] for col in columns_info]
        for col_name in column_names:
            logger.info(f"  - {col_name}")
        
        # Try to find correlation-related columns
        logger.info("\nSearching for correlation-related columns...")
        correlation_columns = []
        for col_name in column_names:
            col_upper = col_name.upper()
            if any(keyword in col_upper for keyword in ['CORR', 'C3A', 'C4F', 'SIL', 'ALU', 'C3S']):
                correlation_columns.append(col_name)
                logger.info(f"  Found potential correlation column: {col_name}")
        
        if correlation_columns:
            # Sample a few records to see data structure
            logger.info(f"\nSampling data from correlation columns...")
            sample_query = f"SELECT NAME, {', '.join(correlation_columns)} FROM CEMENT FETCH FIRST 3 ROWS ONLY"
            try:
                cursor.execute(sample_query)
                samples = cursor.fetchall()
                for sample in samples:
                    logger.info(f"  Sample: {sample[0]} - {len(sample)-1} correlation columns")
                    for i, col_name in enumerate(correlation_columns):
                        data = sample[i+1]
                        if data is not None:
                            if isinstance(data, bytes):
                                logger.info(f"    {col_name}: {len(data)} bytes")
                            elif isinstance(data, str):
                                logger.info(f"    {col_name}: {len(data)} chars (first 50: {data[:50]}...)")
                            else:
                                logger.info(f"    {col_name}: {type(data)} - {str(data)[:50]}...")
                        else:
                            logger.info(f"    {col_name}: NULL")
            except Exception as e:
                logger.error(f"Error sampling data: {e}")
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM CEMENT")
        count = cursor.fetchone()[0]
        logger.info(f"\nTotal cement records: {count}")
        
        cursor.close()
        connection.close()
        logger.info("Disconnected from Derby database")
        
        return correlation_columns
        
    except Exception as e:
        logger.error(f"Failed to explore Derby schema: {e}")
        raise

if __name__ == "__main__":
    explore_derby_schema()