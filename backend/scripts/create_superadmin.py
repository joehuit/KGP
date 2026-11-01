"""CLI utility to safely bootstrap or create the initial Superadmin user for KGP LIST."""

import argparse
import getpass
import os
import re
import sys
from pathlib import Path

# Ensure backend root is on Python sys.path
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import AdminRole, get_password_hash
from app.db.session import SessionLocal
from app.models.admin_user import AdminUser


def validate_email(email: str) -> str:
    """Validate and normalize email address."""
    cleaned = (email or "").strip().lower()
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", cleaned):
        raise ValueError(f"Invalid email format: '{email}'")
    return cleaned


def validate_password_strength(password: str) -> None:
    """Enforce minimum password security requirements."""
    if not password or len(password) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if not any(c.isupper() for c in password):
        raise ValueError("Password must contain at least one uppercase letter (A-Z).")
    if not any(c.islower() for c in password):
        raise ValueError("Password must contain at least one lowercase letter (a-z).")
    if not any(c.isdigit() for c in password):
        raise ValueError("Password must contain at least one digit (0-9).")


def create_or_update_superadmin(
    email: str,
    full_name: str,
    password: str,
    db: Session | None = None,
) -> AdminUser:
    """Create or update a Superadmin account with secure bcrypt hashing."""
    validate_password_strength(password)
    clean_email = validate_email(email)
    clean_name = full_name.strip()
    if not clean_name:
        raise ValueError("Full name cannot be empty.")

    def _execute(session: Session) -> AdminUser:
        existing = session.scalar(select(AdminUser).where(AdminUser.email == clean_email))
        hashed_pw = get_password_hash(password)

        if existing:
            existing.full_name = clean_name
            existing.hashed_password = hashed_pw
            existing.role = AdminRole.SUPERADMIN.value
            existing.is_active = True
            session.commit()
            session.refresh(existing)
            return existing
        else:
            new_superadmin = AdminUser(
                email=clean_email,
                full_name=clean_name,
                hashed_password=hashed_pw,
                role=AdminRole.SUPERADMIN.value,
                is_active=True,
            )
            session.add(new_superadmin)
            session.commit()
            session.refresh(new_superadmin)
            return new_superadmin

    if db is not None:
        return _execute(db)
    else:
        with SessionLocal() as session:
            return _execute(session)


def main():
    parser = argparse.ArgumentParser(
        description="Safely provision or bootstrap the initial Superadmin user for KGP LIST administration."
    )
    parser.add_argument("--email", help="Superadmin email address")
    parser.add_argument("--name", help="Superadmin full name")
    parser.add_argument(
        "--password-env",
        help="Name of environment variable containing the password (for automated/headless deployment)",
    )

    args = parser.parse_args()

    # 1. Resolve email
    email = args.email
    while not email:
        try:
            raw_email = input("Superadmin Email: ").strip()
            email = validate_email(raw_email)
        except ValueError as e:
            print(f"[!] Error: {e}")
            email = None

    # 2. Resolve Full Name
    full_name = args.name
    while not full_name or not full_name.strip():
        full_name = input("Superadmin Full Name: ").strip()
        if not full_name:
            print("[!] Full name cannot be empty.")

    # 3. Resolve Password securely
    password = None
    if args.password_env:
        password = os.environ.get(args.password_env)
        if not password:
            print(f"[!] Error: Environment variable '{args.password_env}' is not set or empty.")
            sys.exit(1)
        try:
            validate_password_strength(password)
        except ValueError as e:
            print(f"[!] Error in environment password: {e}")
            sys.exit(1)
    else:
        # Interactive hidden password prompt
        while not password:
            pw1 = getpass.getpass("Superadmin Password: ")
            pw2 = getpass.getpass("Confirm Password: ")
            if pw1 != pw2:
                print("[!] Passwords do not match. Please try again.")
                continue
            try:
                validate_password_strength(pw1)
                password = pw1
            except ValueError as e:
                print(f"[!] Weak password: {e}")
                password = None

    try:
        user = create_or_update_superadmin(
            email=email,
            full_name=full_name,
            password=password,
        )
        print(f"[✓] Superadmin account successfully configured: {user.email}")
        print(f"[✓] Role: {user.role} | Active: {user.is_active}")
        print("[✓] You can now log into the Admin Dashboard at http://localhost:8000/admin/")
    except Exception as exc:
        print(f"[!] Failed to provision Superadmin: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
