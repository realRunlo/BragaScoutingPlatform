import sys
import json


if __name__ == "__main__":
    if len(sys.argv) != 5:
        print("Usage: python script.py host user password database")
        sys.exit(1)

    host, user, password, database = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

    db_credentials = {
        "host": host,
        "user": user,
        "password": password,
        "database": database
    }

    # Create a JSON file with the credentials
    with open("db_cred.json", "w") as json_file:
        json.dump(db_credentials, json_file, indent=4)

    print("db_cred.json file created with the database credentials.")