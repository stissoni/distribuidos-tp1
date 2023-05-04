## Instrucciones

Pegar el archivo de datos data.zip en client/data/data.zip

Luego ejecutar:

```bash
docker compose -f docker-compose.yaml up -d --build
```

Para detener:

```bash
docker compose -f docker-compose.yaml stop -t 1
docker compose -f docker-compose.yaml down
docker volume prune --force
docker image prune --force
```

Ver logs:
    
```bash
docker logs -f --tail 50 <nombre o id del container>
```

## Correciones

Middleware
Disenio: desacoplar las entidades
No data en memoria
Fixear montreal
El cliente