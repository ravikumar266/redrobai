import sys
import os
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

# API scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive.file"
]

def main():
    credentials_path = "credentials.json"
    token_path = "token.json"
    
    flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
    # Get the authorization URL
    auth_url, _ = flow.authorization_url(prompt='consent')
    print("=========================================================")
    print("Here is the authentication URL:")
    print(auth_url)
    print("=========================================================")
    
    code = input("Enter the authorization code: ")
    flow.fetch_token(code=code)
    creds = flow.credentials
    
    with open(token_path, "w") as token:
        token.write(creds.to_json())
    print("Token saved successfully!")

if __name__ == "__main__":
    main()
