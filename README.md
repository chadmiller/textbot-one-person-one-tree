# Textbot module for one-person-one-tree

Inside `src/` are a few files. Two are important. 

## models.py 

This is the database storage for the state machine, and learning what is not set directs the next
step in what we send the user. A field's help param is the text we send the user to promt them for
what to send to fill this.

## entrance.py

This is where the text-message dispatcher inserts text messages. It has methods to list ourselves
in help, and a function that takes messages, updates the database-cum-state-machine, and then
returns a list of messages to give the user
