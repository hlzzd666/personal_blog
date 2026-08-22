import getpass

from backend.app.core.passwords import hash_password


def main() -> None:
    password = getpass.getpass("Admin password: ")
    confirmation = getpass.getpass("Confirm admin password: ")
    if password != confirmation:
        raise SystemExit("Passwords do not match")
    if not password:
        raise SystemExit("Password must not be empty")
    print(hash_password(password))


if __name__ == "__main__":
    main()
