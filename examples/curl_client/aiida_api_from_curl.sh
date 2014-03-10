#!/bin/bash

## This script allows to login first (using the --login option) 
## and then perform both a GET and a PATCH request on the first 
## dbcomputer entry to change the description, to see if the authentication
## works.
## It creates a cookies.txt file storing the CSRF Token. 
## If you want to "logout", either run with the "--logout" option 
## (this is the correct way), or remove the cookies.txt file (actually,
## in this way you are only losing the session and token data, but you
## are still "logged in" in the server)


ENDPOINT="http://localhost:8000/api/v1/dbcomputer/1/"
NEWDESC="A very long new description text to substitute the previous one and see how this is rendered on the webpage"

if [ "$1" == "--logout" ]
then
  curl -c cookies.txt -b cookies.txt http://localhost:8000/admin/logout/
  echo "Logged out (check log above, though)." 
  echo "Press [Enter] to perform the API queries now, or [CTRL+C] to exit."
  read
elif [ "$1" == "--login" ]
then
  ## IF I AM HERE, I ALSO NEED TO LOGIN (I.E., TO GET SESSIONID AND TOKEN)
  if [ "$2" == "" -o "$3" == "" ]
  then
    echo "Pass also username and password on the command line!"
    exit 1
  fi
  USERNAME="$2"
  PASSWORD="$3"

  # Before removing the cookies, I also perform correctly a logout
  curl -c cookies.txt -b cookies.txt http://localhost:8000/admin/logout/
  if [ -e cookies.txt ]
  then
    rm cookies.txt
  fi

  #First call to get the cookies right; IMPORTANT TO PUT THE SLASH AT THE END!
  curl -c cookies.txt -b cookies.txt http://localhost:8000/admin/

  #get the csrf token
  CSRF=`cat cookies.txt | grep localhost | grep csrftoken | cut -f 7`

  POSTDATA="username=$USERNAME&password=$PASSWORD&csrfmiddlewaretoken=$CSRF&this_is_the_login_form=1&next=/  admin/curl send"

  echo "PRESS ENTER TO GO TO STEP 2 with postdata: $POSTDATA"
  read

  # Second call with the POST method
  curl --dump-header - -c cookies.txt -b cookies.txt -X POST -d "$POSTDATA" http://localhost:8000/admin/

  echo "PRESS ENTER TO GO TO STEP 3 (API GET AND PATCH)"
  read
fi

# This part is done anyway
if [ ! -e cookies.txt ]
then
  echo "WARNING! You are running without cookies, meaning that you are going to "
  echo "         execute the queries unauthenticated. Press [Enter] to continue or"
  echo "         [CTRL+C] to exit now."
  echo "         Run with the "--login USERNAME PASSWORD" option to also login"
  read
else
  #update the csrf token (changes after login)
  CSRF=`cat cookies.txt | grep localhost | grep csrftoken | cut -f 7`
fi

curl --dump-header - -c cookies.txt -b cookies.txt -H "Content-Type: application/json" "$ENDPOINT"
echo
echo
echo "Press enter to do the PATCH request now."
read

# Try the API call; important to set also the X-CSRFToken header!
if [ "$CSRF" == "" ]
then
  curl --dump-header - -c cookies.txt -b cookies.txt -H "Content-Type: application/json" -X PATCH --data '{"description": "'"$NEWDESC"'"}' "$ENDPOINT"
else
  curl --dump-header - -c cookies.txt -b cookies.txt -H "Content-Type: application/json" -H "X-CSRFToken: ${CSRF}" -X PATCH --data '{"description": "'"$NEWDESC"'"}' "$ENDPOINT"
fi



