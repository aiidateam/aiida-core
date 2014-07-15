#!/bin/bash

./manage.py sqlclear scaling | ./manage.py dbshell
rm -rf neo4j/data/graph.db

./manage.py syncdb
