#!/bin/bash

## This script performs both a GET and a PATCH request on the first 
## dbcomputer entry to change the description, to see if the authentication
## works.
## Note that you have to login first using the loginlogout.sh script.
## It creates a cookies.txt file storing the CSRF Token. 

ENDPOINT="http://localhost:8000/api/v1/dbcomputer/12/"

############################################################################

if [ ! -e cookies.txt ]
then
  echo "WARNING! You are running without cookies, meaning that you are going to "
  echo "         execute the queries unauthenticated. Press [Enter] to continue or"
  echo "         [CTRL+C] to exit now."
  echo "         Run with the loginlogout.sh program to also login first."
  read
else
  #update the csrf token (I need to send it also as X-CSRFToken header)
  CSRF=`cat cookies.txt | grep localhost | grep csrftoken | cut -f 7`
fi

# Try the API call; important to set also the X-CSRFToken header!
if [ "$CSRF" == "" ]
then
  curl --dump-header - -c cookies.txt -b cookies.txt -H "Content-Type: application/json" -X DELETE "$ENDPOINT"
else
  curl --dump-header - -c cookies.txt -b cookies.txt -H "Content-Type: application/json" -H "X-CSRFToken: ${CSRF}" -X DELETE "$ENDPOINT"
fi



