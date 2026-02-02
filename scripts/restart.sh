#!/bin/bash

restart() {
        docker compose down
        docker compose up -d
}

restart
