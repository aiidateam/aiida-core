Other Operating Systems
=======================

Gentoo Linux
------------


1) To install RabbitMQ do the following
# emerge -av rabbitmq-server

2) Run RabbitMQ start script at the system boot
# rc-update add rabbitmq

3) Start RabbitMQ 
# /etc/init.d/rabbitmq start

4) Check the status of RabbitMQ server
# /etc/init.d/rabbitmq status
# rabbitmqctl status

5) If you have an error like 
"Argument '-smp enable' not supported."
Remove the mentioned optime from the file /usr/libexec/rabbitmq/rabbitmq-env

