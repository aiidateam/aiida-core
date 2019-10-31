Daemon as system service
------------------------

If you would like the AiiDA daemon to run at startup of your linux system,
you can set up a
`systemd service <https://www.freedesktop.org/software/systemd/man/systemd.service.html>`_
for it.

Create a file ``aiida-daemon@.service`` using the template below, replacing
``{{ venv_dir }}``, ``{{ home_dir }}`` and  ``{{ user }}`` by appropriate
values::

  [Unit]
  Description=AiiDA daemon service for profile %I
  After=network.target postgresql.service rabbitmq-server.service

  [Service]
  Type=forking
  ExecStart={{ venv_dir }}/bin/verdi -p %i daemon start
  PIDFile={{ home_dir }}/.aiida/daemon/circus-%i.pid
  # 2s delay to prevent read error on PID file
  ExecStartPost=/bin/sleep 2

  ExecStop={{ venv_dir }}/bin/verdi -p %i daemon stop
  ExecReload={{ venv_dir }}/bin/verdi -p %i daemon restart

  User={{ user }}
  Group={{ user }}
  Restart=on-failure
  # Restart daemon after 1 min if crashes
  RestartSec=60
  StandardOutput=syslog
  StandardError=syslog
  SyslogIdentifier=aiida-daemon-%i

  [Install]
  WantedBy=multi-user.target

Install the service like so::

  sudo cp aiida-daemon@.service /etc/systemd/system/
  sudo systemctl daemon-reload

Start the AiiDA daemon service for a profile ``profile``::

  sudo systemctl start aiida-daemon@profile.service

After this, the AiiDA daemon should start together with your system.
To remove the service again::

  sudo systemctl disable aiida-daemon@profile.service

