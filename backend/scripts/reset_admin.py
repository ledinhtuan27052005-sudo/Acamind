"""
Reset admin account: delete all existing admins and create a new one.
Usage: python scripts/reset_admin.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.db.postgres import SessionLocal
from app.models.document import User
from app.core.security import hash_password

NEW_ADMIN_EMAIL = "admin@acamind.com"
NEW_ADMIN_PASSWORD = "admin123"
NEW_ADMIN_NAME = "Admin"

def main():
    db = SessionLocal()
    try:
        # 1. Delete all existing admin accounts
        admins = db.query(User).filter(User.role == "admin").all()
        if admins:
            print(f"Found {len(admins)} admin account(s):")
            for a in admins:
                print(f"  - {a.email} (id={a.id})")
                db.delete(a)
            db.commit()
            print("All old admin accounts deleted.\n")
        else:
            print("No existing admin accounts found.\n")

        # 2. Check if the email already exists (as non-admin)
        existing = db.query(User).filter(User.email == NEW_ADMIN_EMAIL).first()
        if existing:
            print(f"User {NEW_ADMIN_EMAIL} exists with role='{existing.role}'. Promoting to admin...")
            existing.role = "admin"
            existing.hashed_password = hash_password(NEW_ADMIN_PASSWORD)
            existing.full_name = NEW_ADMIN_NAME
            db.commit()
            print(f"Updated existing user to admin: {existing.email}")
        else:
            # 3. Create new admin
            new_admin = User(
                email=NEW_ADMIN_EMAIL,
                hashed_password=hash_password(NEW_ADMIN_PASSWORD),
                full_name=NEW_ADMIN_NAME,
                role="admin",
            )
            db.add(new_admin)
            db.commit()
            print(f"New admin created successfully!")

        print(f"\n{'='*40}")
        print(f"  Email:    {NEW_ADMIN_EMAIL}")
        print(f"  Password: {NEW_ADMIN_PASSWORD}")
        print(f"  Role:     admin")
        print(f"{'='*40}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
