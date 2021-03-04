"""
Standalone program to test the usage of pyrebase
Pyrebase package helps python interact with Google firebase realtime database
Features:
 - It can upload files to the the storage bucket
 - It can authenticate users with thier email id
 - It can push, pull, and modify data in the realtime database
 - It can create a listener in the real time database and run code when a change is detected
For this project, modification of realtime database and creation of listeners is nessesary

As this is the backend code, authentication for this program to access the firebase database should not be nessesary
This is why a service account should be generated for this program
requirements: pyrebase4 (https://github.com/nhorvath/Pyrebase4)
"""
import time

# Importing pyrebase
import pyrebase
import yaml

# Getting creds from the creds file
with open("creds.yaml") as file:
    creds = yaml.full_load(file)

# Creating the config dictionary using the credentials
config = {
    "apiKey": creds["firebase api key"],
    "authDomain": creds["firebase authentication domain"],
    "databaseURL": creds["firebase database url"],
    "storageBucket": creds["firebase storage bucket url"],
    "serviceAccount": "serviceacc.json",
}

# Creating the firebase object
firebase = pyrebase.initialize_app(config)

# Creating the database object (other objects include storage and authentication)
db = firebase.database()

# Trial code to pull information from the database. Return type is a dictionary of data
# .child canb be used to download only specific information from a certain path
for i in db.get().each():
    print(i.val())

# Trial Code to push information to the database
# .child can be used to push to specific location
data = {"trial": "push to firebase"}
db.push(data)
# Pushing using the push function to the database gives a unique key to the data, which might not be easy to retrieve
# In such cases, update() can be used instead of push

# Creating a listening stream on a specific path
# Function call on listener event:
def stream_handler(message):
    print(message["event"])  # Type of event that occured: get, put, modify, delete
    print(message["path"])  # Path of the event that occured: ".", "/users" etc
    print(message["data"])  # Data that was affected by the event: {"name":"Anish"}


# Creating the streaming object
my_stream = db.stream(stream_handler)
time.sleep(45)

# Closing the stream
my_stream.close()
