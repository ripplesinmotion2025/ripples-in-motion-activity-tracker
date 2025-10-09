import firebase_admin
from firebase_admin import credentials, firestore

# Pyrebase (for Authentication)
firebaseConfig = {
  "apiKey": "AIzaSyBKQZn1VHpID3D8jpjQdSd3usBg7pxeeRA",
  "authDomain": "ripples-in-motion-activi-8f311.firebaseapp.com",
  "projectId": "ripples-in-motion-activi-8f311",
  "storageBucket": "ripples-in-motion-activi-8f311.firebasestorage.app",
  "messagingSenderId": "149110996777",
  "appId": "1:149110996777:web:ddf26759c826ddbb30c138",
  "measurementId": "G-4WHC505DY3",
  "databaseURL": ""
}

#firebase = pyrebase.initialize_app(firebaseConfig)
#pb_auth = firebase.auth()

# Admin SDK for Firestore
cred = credentials.Certificate("serviceAccountKey.json")  # Download from Firebase Console > Service Accounts

# Initialize Firebase App (only once)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
