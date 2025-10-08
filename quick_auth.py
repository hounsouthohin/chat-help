from google_auth_oauthlib.flow import InstalledAppFlow
import pickle

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly',
          'https://www.googleapis.com/auth/gmail.send']

# Votre code d'autorisation
CODE = '4/1AVGzR1CWZ4pE1Q1-WLCHeH4obrHAaaXJXQDpgNr2BvCNzB9lpY854DI3zn8'

flow = InstalledAppFlow.from_client_secrets_file(
    'config/gmail_credentials.json', 
    SCOPES
)
flow.redirect_uri = 'urn:ietf:wg:oauth:2.0:oob'

# Échanger le code contre le token
flow.fetch_token(code=CODE)
creds = flow.credentials

# Sauvegarder
with open('config/token.pickle', 'wb') as f:
    pickle.dump(creds, f)

print("✅ Token créé dans config/token.pickle")