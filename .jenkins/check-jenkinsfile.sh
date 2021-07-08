#!/bin/bash

# curl (REST API)
# Assuming "anonymous read access" has been enabled on your Jenkins instance.
JENKINS_URL=http://theossrv6.epfl.ch/jenkins
# JENKINS_CRUMB is needed if your Jenkins master has CRSF protection enabled as it should
JENKINS_CRUMB=`curl "$JENKINS_URL/crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)"`
echo CRUMB: $JENKINS_CRUMB
curl -X POST -H "$JENKINS_CRUMB" -F "jenkinsfile=<Jenkinsfile" $JENKINS_URL/pipeline-model-converter/validate
