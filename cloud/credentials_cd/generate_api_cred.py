import sys
import json


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py username password ")
        sys.exit(1)

    username, password = sys.argv[1], sys.argv[2]

    api_credentials = {
        "username": username,
        "password": password
    }

    # Create a JSON file with the credentials
    with open("api_cred.json", "w") as json_file:
        json.dump(api_credentials, json_file, indent=4)

    print("api_cred.json file created with the api credentials.")
