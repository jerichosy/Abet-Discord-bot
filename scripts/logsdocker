#!/bin/bash

root=$(git rev-parse --show-toplevel)
compose_file="${root}/docker-compose.yml"

while true
do
        docker compose -f ${compose_file} logs --follow -t
        echo "Detached from logs. Re-attaching in 5 seconds..."
        echo "Press Ctrl+C to cancel."
        sleep 5
done
