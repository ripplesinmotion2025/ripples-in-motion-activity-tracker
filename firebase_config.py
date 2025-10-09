import firebase_admin
from firebase_admin import credentials, firestore

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

import os, json
from firebase_admin import credentials, firestore, initialize_app, storage

# Read Firebase credentials from environment variable
firebase_key_json = os.getenv("FIREBASE_KEY")
firebase_key = json.loads(firebase_key_json)

cred = credentials.Certificate(firebase_key)
initialize_app(cred, {
    "storageBucket": "ripples-in-motion-activi-8f311.appspot.com"
})

db = firestore.client()
bucket = storage.bucket()
