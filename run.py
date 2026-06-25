from database import create_tables
from app import app

print("Checking database...")

# Create DB if not exists
create_tables()

print("Database ready")

print("Starting Flask project...")

app.run(debug=True)