FROM aiidateam/aiida-prerequisites:0.4.0

# allow for collection of query statistics
# (must also be intialised on each database)
RUN sed -i '/.*initdb -D.*/a echo "shared_preload_libraries='pg_stat_statements'" >> /home/${SYSTEM_USER}/.postgresql/postgresql.conf' /opt/start-postgres.sh
# other options
# pg_stat_statements.max = 10000
# pg_stat_statements.track = all

# Copy AiiDA repository
COPY . aiida-core
