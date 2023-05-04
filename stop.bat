docker compose -f docker-compose.yaml stop -t 1
docker compose -f docker-compose.yaml down
docker volume prune --force
docker image prune --force