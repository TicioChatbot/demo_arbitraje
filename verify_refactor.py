from app import app, db, init_db, Arbiter, Case

with app.app_context():
    # Force init
    init_db()
    
    print("--- Verifying Arbiters ---")
    arbiters = Arbiter.query.order_by(Arbiter.name).all()
    for a in arbiters:
        print(f"ID: {a.id}, Name: {a.name}")
    
    print("\n--- Verifying Case Associations ---")
    case = Case.query.first()
    if case:
        print(f"Case: {case.title}")
        print(f"Original String: {case.arbiter}")
        print(f"Associated Arbiters: {[a.name for a in case.arbiters]}")
    else:
        print("No cases found.")
