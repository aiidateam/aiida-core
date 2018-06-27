# Content

This folder contains an example of an extension of the torquessh-base image,
where we add a very basic script to double a number.
This is meant to be a very lightweight 'code' to test daemon functionality.

# Notes

Inside the docker image, we use a filename including single quotes, double
quotes and spaces in order to test the robustness of AiiDA's escaping routines.
