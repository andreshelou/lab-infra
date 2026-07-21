# Configure MongoDB

## Objetivo

Configurar MongoDB para escuchar conexiones remotas y preparar el servidor para formar parte del ReplicaSet `rs0`.

El servicio permanecerá detenido y deshabilitado al finalizar este procedimiento.

---

## Requisitos

- MongoDB Community Server 7.0.15 instalado.
- Todos los paquetes `mongodb-org-*` fijados en la versión `7.0.15`.
- Servicio `mongod` detenido.
- Servicio `mongod` deshabilitado.

---

## Referencias

Documentación oficial:

- MongoDB Configuration File Options
- MongoDB Replica Set Configuration

---

## Procedimiento

### 1. Crear una copia del archivo original

```bash
sudo cp /etc/mongod.conf /etc/mongod.conf.original
```

---

### 2. Modificar la interfaz de escucha

Editar:

```text
/etc/mongod.conf
```

Cambiar:

```yaml
net:
  port: 27017
  bindIp: 127.0.0.1
```

por:

```yaml
net:
  port: 27017
  bindIp: 0.0.0.0
```

Esta configuración permite que MongoDB acepte conexiones desde otras máquinas del laboratorio.

> **Nota**
>
> MongoDB queda expuesto en todas las interfaces de red.
> Este laboratorio no utiliza autenticación ni TLS, por lo que debe ejecutarse únicamente dentro de una red controlada.

---

### 3. Configurar el ReplicaSet

Reemplazar:

```yaml
#replication:
```

por:

```yaml
replication:
  replSetName: rs0
```

El ReplicaSet todavía no se inicializa en este paso.

---

## Configuración final

```yaml
# mongod.conf

# for documentation of all options, see:
#   http://docs.mongodb.org/manual/reference/configuration-options/

# Where and how to store data.
storage:
  dbPath: /var/lib/mongodb
#  engine:
#  wiredTiger:

# where to write logging data.
systemLog:
  destination: file
  logAppend: true
  path: /var/log/mongodb/mongod.log

# network interfaces
net:
  port: 27017
  bindIp: 0.0.0.0

# how the process runs
processManagement:
  timeZoneInfo: /usr/share/zoneinfo

#security:

#operationProfiling:

replication:
  replSetName: rs0

#sharding:

## Enterprise-Only Options:

#auditLog:
```

---

## Archivos modificados

```text
/etc/mongod.conf
```

Archivo de respaldo creado:

```text
/etc/mongod.conf.original
```

El archivo versionado en el repositorio debe ubicarse en:

```text
configs/mongod.conf
```

---

## Validación

### Comparar la configuración con el archivo original

```bash
diff -u /etc/mongod.conf.original /etc/mongod.conf
```

El resultado debe mostrar únicamente:

```diff
-  bindIp: 127.0.0.1
+  bindIp: 0.0.0.0
```

y:

```diff
-#replication:
+replication:
+  replSetName: rs0
```

---

### Validar la configuración mediante un arranque controlado

```bash
sudo mongod \
  --config /etc/mongod.conf \
  --fork \
  --logpath /tmp/mongod-config-test.log \
  --pidfilepath /tmp/mongod-config-test.pid
```

Resultado esperado:

```text
about to fork child process, waiting until server is ready for connections.
child process started successfully, parent exiting
```

---

### Detener el proceso de prueba

```bash
sudo kill "$(cat /tmp/mongod-config-test.pid)"
```

---

### Verificar el cierre

```bash
sudo tail -n 30 /tmp/mongod-config-test.log
```

El log debe contener:

```text
mongod shutdown complete
```

y:

```text
exitCode: 0
```

---

### Verificar el estado de systemd

```bash
systemctl is-enabled mongod
systemctl is-active mongod
```

Resultado esperado:

```text
disabled
inactive
```

---

## Resultado esperado

MongoDB queda configurado para:

- escuchar en el puerto `27017` sobre todas las interfaces;
- utilizar el ReplicaSet `rs0`;
- permanecer detenido;
- permanecer deshabilitado en systemd;
- no utilizar autenticación;
- no utilizar TLS.

---

## Checklist

- [ ] Se creó `/etc/mongod.conf.original`.
- [ ] `bindIp` quedó configurado como `0.0.0.0`.
- [ ] `replSetName` quedó configurado como `rs0`.
- [ ] MongoDB inició correctamente con la configuración.
- [ ] MongoDB cerró con `exitCode: 0`.
- [ ] El servicio `mongod` permanece deshabilitado.
- [ ] El servicio `mongod` permanece inactivo.

---

## Próximo paso

Continuar con:

```text
005-prepare-template-vm.md
```