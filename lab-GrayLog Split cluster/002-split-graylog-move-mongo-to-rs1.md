# 011 :: Crear una segunda instancia de MongoDB en el mismo servidor

## Objetivo

Crear una segunda instancia de MongoDB completamente independiente de la original para alojar un nuevo ReplicaSet.

En este laboratorio:

| Instancia | ReplicaSet | Puerto | Función |
|-----------|------------|--------|---------|
| Original  | rs0 | 27017 | Cluster Graylog activo |
| Nueva     | rs1 | 27018 | Graylog histórico |

---

# 1. Crear directorios

```bash
sudo mkdir -p \
    /var/lib/mongodb-rs1 \
    /var/log/mongodb-rs1 \
    /run/mongodb-rs1

sudo chown -R mongodb:mongodb \
    /var/lib/mongodb-rs1 \
    /var/log/mongodb-rs1 \
    /run/mongodb-rs1
```

---

# 2. Crear el archivo de configuración

```bash
sudo nano /etc/mongod-rs1.conf
```

Contenido:

```yaml
storage:
  dbPath: /var/lib/mongodb-rs1

systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb-rs1/mongod.log

net:
  port: 27018
  bindIp: 0.0.0.0

processManagement:
  timeZoneInfo: /usr/share/zoneinfo
  pidFilePath: /run/mongodb-rs1/mongod.pid

replication:
  replSetName: rs1
```

---

# 3. Crear el servicio systemd

```bash
sudo cp \
    /lib/systemd/system/mongod.service \
    /etc/systemd/system/mongod-rs1.service
```

Editar:

```ini
Description=MongoDB Database Server - RS1

ExecStart=/usr/bin/mongod --config /etc/mongod-rs1.conf

RuntimeDirectory=mongodb-rs1
RuntimeDirectoryMode=0755
```

---

# 4. Recargar systemd

```bash
sudo systemctl daemon-reload
```

---

# 5. Iniciar la nueva instancia

```bash
sudo systemctl start mongod-rs1
```

Verificar:

```bash
sudo systemctl status mongod-rs1
```

---

# 6. Confirmar ambos puertos

```bash
sudo ss -lntp | grep -E '27017|27018'
```

Resultado esperado:

```
27017 -> rs0
27018 -> rs1
```

---

# 7. Inicializar el ReplicaSet

```bash
mongosh --port 27018
```

```javascript
rs.initiate({
  _id: "rs1",
  members: [
    {
      _id: 0,
      host: "gl01:27018"
    }
  ]
})
```

Validar:

```javascript
rs.status()
```

Estado esperado:

```
PRIMARY
```

---

# 8. Restaurar la base de Graylog

```bash
mongorestore \
  --uri='mongodb://gl01:27018/graylog?replicaSet=rs1' \
  "$BACKUP_DIR/graylog"
```

---

# 9. Validar la restauración

```bash
mongosh \
  'mongodb://gl01:27018/graylog?replicaSet=rs1' \
  --quiet \
  --eval 'db.getCollectionNames().length'
```

---

## Resultado

El servidor dispone de dos instancias MongoDB independientes.

```
gl01

27017
└── rs0

27018
└── rs1
```

Cada ReplicaSet puede ser utilizado por un cluster Graylog distinto.