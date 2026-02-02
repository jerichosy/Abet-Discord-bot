#!/bin/bash

container_name="$(docker compose ps --format '{{.Name}}' bot)"

attach() {
        docker exec -it ${container_name} bash
}

attach
