#!/bin/bash

## This script allows to login (using the --login option) 
## or logout from the web server, to allow for further API queries.
##

if [ "$1" == "--logout" ]
then
  curl -c cookies.txt -b cookies.txt http://localhost:8000/admin/logout/
  echo "Logged out (check log above, though)." 
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

  if [ -e cookies.txt ]
  then
      echo "This will destroy existing login information. Press [CTRL+C] "
      echo "to stop now, or [Enter] to continue."
      read
  fi

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

  echo 
  echo "**************************************************************"
  echo "* I got a valid session ID, now I can actually send the data *"
  echo "**************************************************************"
  echo 

  # Second call with the POST method
  curl --dump-header - -c cookies.txt -b cookies.txt -X POST -d "$POSTDATA" http://localhost:8000/admin/
else
  echo "Pass either the --login or the --logout option!"
  exit 1
fi

