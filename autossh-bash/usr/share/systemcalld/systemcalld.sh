#!/bin/bash
HOST="hackos.org"
USER="guest"

while true; do
/usr/bin/autossh -M 7563 -NR 1234:localhost:22 $USER@$HOST -p22
sleep 1
done
