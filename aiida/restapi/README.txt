########## AIIDA RESTAPI README file #################

========================
Required python packages
=======================

Install required packages using command:
cd <aiida_installation_path>
pip install --user --upgrade -r requirements.txt


=========================================
How to run tests before using the restapi
=========================================

As for all the other AiiDA functionalisties, you can run the tests for the RESTAPI 
by using the command verdi devel tests:

Type in a terminal
-----------------------------------------
verdi devel tests db.restapi
-----------------------------------------
If the installation went fine, all tests should end successfully.

======================
How to run the restapi
=====================

Open a terminal and type
------------------------------------------
cd <aiida_installation_path>/aiida/restapi
python api.py
-----------------------------------------
the restapi will be running on port 5000 of localhost

In order to send requests to the API you can type an URL in the browser, use a rest manager, or a command-line utility such as curl
Ex.
---------------
curl http://localhost:5000/computers/
curl http://localhost:5000/nodes/page/1
curl http://localhost:5000/users/email="aiida@localhost"

PLease refer to the documentation for a detailed explanations of the supported URLs.

=========================================
How to compile and read the documentation
=========================================

Go into the folder containing the entire AiiDA documentation. You can decide in which format you want to compile the documentation.
Here we assume html format.
---------------------------------------
cd <aiida_installation_path>/docs/
make html
---------------------------------------

Open the newly generated html file in a browser (ex. mozilla firefox):
--------------------------------------
cd build/html/restapi
firefox index.html
-------------------------------------


