import sys

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import SessionLocal
from app.models.user import User, UserRole
from app.repositories.user_repository import UserRepository


def seed_admin() -> None:
    """Explicitly seeds the initial administrator from configured environment variables."""
    email = settings.FIRST_ADMIN_EMAIL.strip().lower()
    name = settings.FIRST_ADMIN_NAME.strip()
    password = settings.FIRST_ADMIN_PASSWORD

    print(f"[*] Checking for admin account: {email}")
    db = SessionLocal()
    try:
        user_repo = UserRepository(db)
        existing = user_repo.get_by_email(email)
        if existing:
            if existing.role != UserRole.ADMIN:
                existing.role = UserRole.ADMIN
                existing.is_approved = True
                existing.is_active = True
                db.commit()
                print(f"[+] Existing user {email} promoted to admin.")
            else:
                print(f"[i] Admin account {email} already exists.")
            return

        admin_user = User(
            name=name,
            email=email,
            password_hash=get_password_hash(password),
            role=UserRole.ADMIN,
            is_active=True,
            is_approved=True,
        )
        user_repo.create(admin_user)
        db.commit()
        print(f"[+] Administrator {email} created successfully!")
    finally:
        db.close()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "seed-admin":
        seed_admin()
    else:
        print("Usage: uv run python -m app.cli seed-admin")


if __name__ == "__main__":
    main()
