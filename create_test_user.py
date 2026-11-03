from backend.app.database import SessionLocal
from backend.app.models.user import User

db = SessionLocal()

try:
    user = db.query(User).filter(User.id == 1).first()

    if user:
        print("Test user already exists.")
        print("User ID:", user.id)
    else:
        user = User(
            full_name="Test User",
            email="testuser@example.com",
            hashed_password="temporary-development-password"
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print("Test user created successfully!")
        print("User ID:", user.id)
        print("Email:", user.email)

except Exception as error:
    db.rollback()
    print("Error:", error)

finally:
    db.close()