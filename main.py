"""
main.py
Main program to act as the server backend for the application
Pre-requisites:
 - Pre-trained model pickle file

Flow of the main program:
 -> Listen to incoming messages from firebase
 -> Once a message is recieved, validate the information received
 -> After validation, perform NLP on the received string to derive intent of the string
 -> If playlist link is received, process the link to obtain all songs and thier properties
 -> If song list is received, process each song to obtain song properties
 -> Load pre-trained model and predict tags for each received song
 -> Extract all songs that have the same tag as the derived intent above
 -> Select one random song out of the choices, and return the chosen song ID to firebase in given format
"""
