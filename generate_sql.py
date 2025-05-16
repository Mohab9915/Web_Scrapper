"""
Script to generate SQL statements for setting up the database schema.
"""
import os

# Read the SQL migration file
with open("backend/migrations/01_initial_schema.sql", "r") as f:
    sql_migration = f.read()

# Split the SQL into individual statements
sql_statements = sql_migration.split(';')

# Generate a file with the SQL statements
with open("supabase_setup.sql", "w") as f:
    for statement in sql_statements:
        # Skip empty statements
        if not statement.strip():
            continue
            
        # Add semicolon back
        statement = statement.strip() + ';'
        
        f.write(statement + "\n\n")

print("SQL statements generated in supabase_setup.sql")
print("Please copy and paste these statements into the Supabase SQL editor.")
print("Instructions:")
print("1. Go to https://supabase.com/dashboard/project/slkzwhpfeauezoojlvou/sql/new")
print("2. Copy the contents of supabase_setup.sql")
print("3. Paste into the SQL editor")
print("4. Click 'Run' to execute the SQL statements")
print("5. Check that the tables and functions were created successfully")
