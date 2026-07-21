# Start MongoDB

## Objetivo

Habilitar e iniciar el servicio `mongod` en los tres nodos del laboratorio.

En este paso MongoDB comienza a aceptar conexiones, pero el ReplicaSet todavía no se encuentra inicializado.

---

## Requisitos

- Las tres máquinas virtuales fueron configuradas.
- Hostname configurado.
- Red configurada.
- Resolución de nombres validada.
- MongoDB configurado.
- Servicio `mongod` detenido.

---

## Procedimiento

Ejecutar en los tres nodos.

### 1. Habilitar el servicio

```bash
sudo systemctl enable mongod
```

---

### 2. Iniciar el servicio

```bash
sudo systemctl start mongod
```

---

## Nota

Durante la validación realizada en el documento anterior (`004-configure-mongod.md`) se inició MongoDB manualmente utilizando:

```bash
sudo mongod ...
```

Ese arranque creó el archivo:

```text
/var/lib/mongodb/storage.bson
```

con propietario `root`.

Como el servicio `mongod` ejecutado por `systemd` utiliza el usuario `mongodb`, el servicio no puede acceder a ese archivo y finaliza con:

```text
status=14
```

y el siguiente mensaje en el log:

```text
Failed to read metadata from /var/lib/mongodb/storage.bson
```

Para restaurar los permisos ejecutar en los tres nodos:

```bash
sudo chown -R mongodb:mongodb /var/lib/mongodb
sudo chown -R mongodb:mongodb /var/log/mongodb
```

Luego reiniciar el servicio:

```bash
sudo systemctl restart mongod
```

---

## Archivos modificados

Ninguno.

---

## Validación

Estado del servicio:

```bash
systemctl status mongod --no-pager
```

Resultado esperado:

```text
Active: active (running)
```

---

Puerto de escucha:

```bash
ss -ltnp | grep 27017
```

Resultado esperado:

```text
0.0.0.0:27017
```

---

Conectividad desde cada nodo:

```bash
mongosh --host gl01 --quiet --eval 'db.adminCommand({ ping: 1 })'
mongosh --host gl02 --quiet --eval 'db.adminCommand({ ping: 1 })'
mongosh --host gl03 --quiet --eval 'db.adminCommand({ ping: 1 })'
```

Resultado esperado:

```javascript
{ ok: 1 }
```

---

## Resultado esperado

Los tres nodos ejecutan correctamente el servicio MongoDB y escuchan conexiones en el puerto TCP 27017.

En esta etapa el ReplicaSet todavía no fue inicializado, por lo que es normal observar mensajes similares a:

```text
ReadConcernMajorityNotAvailableYet
Collection [local.oplog.rs] not found
```

Estos mensajes desaparecerán una vez creado el ReplicaSet.

---

## Checklist

- [ ] Servicio habilitado.
- [ ] Servicio iniciado.
- [ ] Puerto 27017 en escucha.
- [ ] Responde al comando `ping`.
- [ ] Los tres nodos permanecen independientes.

---

## Próximo paso

Continuar con:

```text
009-initiate-replicaset.md
```