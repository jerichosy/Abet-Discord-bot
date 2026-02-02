#!/bin/bash

while true
do
        docker compose logs --follow -t
        echo "Detached from logs. Re-attaching in 5 seconds..."
        echo "Press Ctrl+C to cancel."
        sleep 5
done
