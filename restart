#!/bin/bash

compose_file="/home/jericho/Abet-Discord-bot/docker-compose.yml"

restart() {
        docker compose -f $compose_file down
        docker compose -f $compose_file up -d
}

restart
