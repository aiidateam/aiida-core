#!/bin/bash
set -e

AIIDA_PATH=/home/kristjan/.aiida # .aiida/config.json
VERDIEXEC=/home/kristjan/opt/anaconda/envs/aiida/bin/verdi
PROFILE_NAME=qs
DEST=/home/kristjan/backup-test
#DEST=dev-aiida:/home/ubuntu/kristjan-tests/backup-test

export AIIDA_PATH

# If DEST includes the remote specifier user@host:/directory, extract both parts.
# if REMOTE_ID is empty, local destination is assumed
if [[ $DEST =~ .*:.* ]]; then
    REMOTE_ID="${DEST%%:*}"
else
    REMOTE_ID=""
fi
DEST_PATH="${DEST#*:}"

# While backup is running, use LIVE_DIR directory and when it succeeds, move & overwrite the FINAL_DIR
LIVE_DIR=tempbackup
FINAL_DIR=lastbackup
if [ -z "$REMOTE_ID" ]; then
    mkdir -p $DEST_PATH/$LIVE_DIR
else
    ssh $REMOTE_ID "mkdir -p $DEST_PATH/$LIVE_DIR"
fi

TMP_DIR=/tmp/$PROFILE_NAME-$(date +"%FT%H%M%S")
mkdir -p $TMP_DIR

# Step 1: first run the storage maintenance version that can safely be performed while aiida is running
# q: should we use --compress?
# q: should we clean_storage as well?
$VERDIEXEC storage maintain --force

# Step 2: dump the PostgreSQL database onto a temporary local file
$VERDIEXEC --profile=$PROFILE_NAME profile dbdump --output_file=$TMP_DIR/db.psql #--stop-if-existing

# Step 3: transfer the PostgreSQL database file
rsync -azh $TMP_DIR/db.psql $DEST/$LIVE_DIR

#### Disk-objectstore
#### Safest if backed up in order: 1) loose files; 2) sqlite database; 3) packed files.

DOS_PATH=$AIIDA_PATH/repository/$PROFILE_NAME/container
DOS_DEST=$DEST/$LIVE_DIR/container

# Step 4: transfer the loose objects of the disk-objectstore
rsync -azh $DOS_PATH/loose $DOS_DEST

# Step 4: dump locally the disk-objectstore Sqlite database
sqlite3 $DOS_PATH/packs.idx ".backup $TMP_DIR/packs.idx"

# Step 5: transfer the Sqlite dump
# transfer the dump backup.db TO THE CORRECT NAME in the backup # DO NOT RUN A FULL REPACK BETWEEN STEP 5 and 6, it might happen that...
# check_no_repack()
rsync -azh $TMP_DIR/packs.idx $DOS_DEST

# step 6: transfer the pack files
# check_no_repack()
rsync -azh $DOS_PATH/packs $DOS_DEST

# step 7: final rsync of the remaining parts of disk-objectstore
rsync -azh $DOS_PATH/config.json $DOS_PATH/duplicates $DOS_PATH/sandbox $DOS_DEST

# Possibly run a dostore verify on top!

# step 8: overwrite the old backup folder
if [ -z "$REMOTE_ID" ]; then
    echo $(date +"%FT%H%M%S") > $DEST_PATH/$LIVE_DIR/COMPLETED_DATE
    if [ -d $DEST_PATH/$FINAL_DIR ]; then mv $DEST_PATH/$FINAL_DIR $DEST_PATH/$FINAL_DIR-old; fi
    mv $DEST_PATH/$LIVE_DIR $DEST_PATH/$FINAL_DIR
    rm -rf $DEST_PATH/$FINAL_DIR-old
else
    ssh $REMOTE_ID "echo $(date +'%FT%H%M%S') > $DEST_PATH/$LIVE_DIR/COMPLETED_DATE"
    ssh $REMOTE_ID "if [ -d $DEST_PATH/$FINAL_DIR ]; then mv $DEST_PATH/$FINAL_DIR $DEST_PATH/$FINAL_DIR-old; fi"
    ssh $REMOTE_ID "mv $DEST_PATH/$LIVE_DIR $DEST_PATH/$FINAL_DIR"
    ssh $REMOTE_ID "rm -rf $DEST_PATH/$FINAL_DIR-old"
fi

echo "Success! Backup completed to $DEST/$FINAL_DIR"
