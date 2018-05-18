# Inventory system proof of concept

## Servers

This is an elementarty proof of concept API and associated DB for use playing with ideas for the inventory
system proof of concept.

### Get list of servers

`curl -u tim:swordfish123 -i http://localhost:5000/inventory/api/v1/servers`

### Get details of specific server

`curl -u tim:swordfish123 -i http://localhost:5000/inventory/api/v1/server/1`

### Add a new server

`curl -u tim:swordfish123 -i -H "Content-Type: application/json" -X POST -d '{"tag": "CVB444", "sid": "66", "stockid": "77"}' http://localhost:5000/invetory/api/v1/servers`

### Delete a server

`curl -u tim:swordfish123 http://localhost:5000/inventory/api/v1/server/17 -X DELETE`

### Update a server

`curl -utim:swordfish123 -i -H "Content-Type: application/json" -X PUT -d '{"comment": "Fuck me backwards! It worked!"}' http://localhost:5000/inventory/api/v1/server/2`