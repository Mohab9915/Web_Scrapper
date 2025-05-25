"""
Script to generate SQL statements for setting up the database schema.
"""
import os

# Read all SQL migration files in order
migration_files = sorted([f for f in os.listdir("backend/migrations") if f.endswith(".sql")])

combined_sql = ""
for file_name in migration_files:
    with open(os.path.join("backend/migrations", file_name), "r") as f:
        combined_sql += f.read() + "\n-- End of migration file: " + file_name + "\n\n"

# Split the combined SQL into individual statements
sql_statements = combined_sql.split(';')

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
print("1. Go to https://supabase.com/dashboard/project/slkzwhpfeauezoojlvou/sql/new") # NOTE: Replace with your actual Supabase project URL if different
print("2. Copy the contents of supabase_setup.sql")
print("3. Paste into the SQL editor")
print("4. Click 'Run' to execute the SQL statements")
print("5. Check that the tables and functions were created successfully")
