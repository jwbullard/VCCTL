from src.app.database.service import DatabaseService
from src.app.services.grading_service import GradingService

db = DatabaseService()
gs = GradingService(db)

# Get a standard grading and check its sieve data
astm_fine = gs.get_by_name("ASTM C-33 Fine Aggregate")
if astm_fine and astm_fine.get_sieve_data():
    sieve_data = astm_fine.get_sieve_data()
    print(f"✅ ASTM Fine has {len(sieve_data)} sieve points")
    print(f"   Sample: {sieve_data[0]} to {sieve_data[-1]}")
else:
    print("❌ ASTM Fine grading missing sieve data")

# Test custom grading with complex data
complex_sieve_data = [
    {"sieve_size": 25.0, "percent_passing": 100.0},
    {"sieve_size": 19.0, "percent_passing": 95.0},
    {"sieve_size": 12.5, "percent_passing": 45.0},
    {"sieve_size": 9.5, "percent_passing": 20.0},
    {"sieve_size": 4.75, "percent_passing": 5.0},
]

custom = gs.save_grading_with_sieve_data(
    "Test Complex Grading",
    "COARSE",
    complex_sieve_data,
    "Complex test for Phase 1 verification",
)

retrieved = gs.get_by_name("Test Complex Grading")
if retrieved:
    data = retrieved.get_sieve_data()
    print(
        f"✅ Complex grading: {len(data)} points, max_diameter={retrieved.max_diameter}"
    )
else:
    print("❌ Complex grading not saved properly")
