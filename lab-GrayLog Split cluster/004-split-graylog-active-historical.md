# Separación de Graylog activo e histórico

## 1. Objetivo

Validar en laboratorio la separación del cluster Graylog original en dos entornos independientes:

### Entorno activo

- Graylog: `gl02` y `gl03`
- MongoDB: ReplicaSet original `rs0` en `gl01`, `gl02` y `gl03`
- Backend: OpenSearch 2.15.0 en:
  - `es01:19200`
  - `es02:19200`
  - `es03:19200`
- Ingesta y frontend publicados por F5 únicamente sobre `gl02` y `gl03`
- OpenSearch contiene los índices, mappings y settings preparados, pero sin documentos históricos

### Entorno histórico

- Graylog: `gl01`
- MongoDB: nuevo ReplicaSet independiente `rs1`, de un solo nodo
- Backend: Elasticsearch histórico en:
  - `es01:9200`
  - `es02:9200`
  - `es03:9200`
- Sin ingesta
- Frontend publicado mediante una VIP y URL independientes
- Conserva la configuración de Graylog existente al momento del corte mediante un backup de MongoDB

---

## 2. Alcance de esta prueba

Este runbook cubre:

1. Preparación del cambio.
2. Corte controlado de la ingesta y el frontend.
3. Backup consistente de la base de datos de Graylog en MongoDB.
4. Migración del cluster activo `gl02`/`gl03` al backend OpenSearch vacío.
5. Reapertura del servicio activo.
6. Creación posterior del entorno histórico en `gl01`.
7. Validaciones y rollback.

La prioridad durante la ventana es recuperar primero la ingesta en `gl02` y `gl03`. La construcción del entorno histórico se realiza después y no forma parte de la ventana crítica.

---

## 3. Consideraciones importantes

### 3.1 Pérdida de mensajes durante el corte

Detener o cerrar la VIP de ingesta impide que nuevos mensajes lleguen a Graylog.

- Los mensajes que ya ingresaron a Graylog quedan protegidos por el journal hasta ser indexados.
- Los emisores TCP pueden reintentar, dependiendo de su configuración.
- Los mensajes enviados por UDP durante el corte pueden perderse.

La prueba debe medir el tiempo efectivo sin VIP y verificar el comportamiento de los emisores.

### 3.2 `password_secret`

El Graylog histórico debe conservar el mismo `password_secret` del cluster original.

No debe generarse uno nuevo porque la información sensible almacenada en la copia de MongoDB fue cifrada usando el secreto original.

### 3.3 MongoDB `rs0`

El ReplicaSet original no se divide ni se modifica durante la ventana crítica.

MongoDB permanece activo en:

```text
gl01:27017
gl02:27017
gl03:27017
```

Aunque el servicio Graylog de `gl01` quede detenido, su instancia MongoDB debe continuar participando en `rs0`.

### 3.4 Backend de `gl01`

Después de cambiar `gl02` y `gl03` a OpenSearch, el Graylog original de `gl01` no debe iniciarse nuevamente apuntando a `rs0` y Elasticsearch.

Primero debe quedar conectado a la nueva copia MongoDB `rs1`. Esto evita que dos clusters Graylog con backends diferentes compartan la misma configuración activa.

---

## 4. Topología inicial

```text
                       F5
                  ingesta + UI
                         |
             +-----------+-----------+
             |           |           |
           gl01        gl02        gl03
        Graylog       Graylog     Graylog
        MongoDB       MongoDB     MongoDB
             \           |           /
              +----------+----------+
                         |
                    MongoDB rs0
                         |
       Elasticsearch es01/es02/es03:9200
```

OpenSearch 2.15.0 ya se encuentra instalado en `es01`, `es02` y `es03`, escuchando en el puerto `19200`, con índices, mappings y settings preparados pero sin documentos.

---

## 5. Topología final

```text
ENTORNO ACTIVO

F5 activo
   |
   +--> gl02 --+
   |           +--> MongoDB rs0: gl01/gl02/gl03
   +--> gl03 --+
               |
               +--> OpenSearch es01/es02/es03:19200


ENTORNO HISTÓRICO

F5 histórico / VIP independiente
   |
   +--> gl01
          |
          +--> MongoDB rs1: gl01:<PUERTO_RS1>
          |
          +--> Elasticsearch es01/es02/es03:9200
```

---

# PARTE I - PREPARACIÓN

## 6. Registrar el estado inicial

Ejecutar y guardar la salida de las validaciones.

### 6.1 Graylog

En `gl01`, `gl02` y `gl03`:

```bash
sudo systemctl status graylog-server --no-pager
sudo grep -E '^(mongodb_uri|elasticsearch_hosts|password_secret|http_bind_address|http_publish_uri)' \
  /etc/graylog/server/server.conf
sudo cat /etc/graylog/server/node-id
```

Confirmar:

- Los tres nodos Graylog están operativos.
- Los tres apuntan a `rs0`.
- Los tres apuntan a Elasticsearch `:9200`.
- Cada nodo tiene un `node-id` distinto.
- El `password_secret` es el mismo en los tres nodos.

### 6.2 MongoDB

Desde un nodo con acceso a `mongosh`:

```bash
mongosh --quiet --eval 'rs.status()'
mongosh --quiet --eval 'rs.conf()'
```

Resultado esperado:

- Un miembro `PRIMARY`.
- Dos miembros `SECONDARY`.
- ReplicaSet: `rs0`.

### 6.3 Elasticsearch histórico

```bash
curl -s http://es01:9200/_cluster/health?pretty
curl -s 'http://es01:9200/_cat/indices?v&s=index'
```

Confirmar:

- Cluster operativo.
- Índices históricos disponibles.
- Búsquedas funcionales desde Graylog antes del cambio.

### 6.4 OpenSearch nuevo

```bash
curl -s http://es01:19200/_cluster/health?pretty
curl -s 'http://es01:19200/_cat/nodes?v'
curl -s 'http://es01:19200/_cat/indices?v&s=index'
```

Confirmar:

- Los tres nodos OpenSearch están levantados.
- El cluster está operativo.
- Los índices esperados existen.
- Los mappings y settings ya fueron validados.
- Los índices no contienen documentos históricos.

> OpenSearch debe quedar levantado y validado antes de iniciar la ventana.

---

## 7. Preparar las configuraciones de `gl02` y `gl03`

Crear una copia de seguridad local:

```bash
sudo cp -a /etc/graylog/server/server.conf \
  /etc/graylog/server/server.conf.pre-opensearch
```

Preparar una copia nueva del archivo:

```bash
sudo cp -a /etc/graylog/server/server.conf \
  /etc/graylog/server/server.conf.opensearch
```

En `server.conf.opensearch`, modificar únicamente el backend:

```properties
elasticsearch_hosts = http://es01:19200,http://es02:19200,http://es03:19200
```

No modificar:

```properties
mongodb_uri
password_secret
root_password_sha2
```

Comparar los archivos:

```bash
sudo diff -u \
  /etc/graylog/server/server.conf \
  /etc/graylog/server/server.conf.opensearch
```

La única diferencia prevista debe ser `elasticsearch_hosts`.

---

## 8. Preparar el backup de MongoDB

Crear un directorio con fecha:

```bash
BACKUP_DIR="/backup/graylog-split-$(date +%Y%m%d-%H%M%S)"
sudo mkdir -p "$BACKUP_DIR"
sudo chown "$(id -un):$(id -gn)" "$BACKUP_DIR"
echo "$BACKUP_DIR"
```

Identificar el PRIMARY:

```bash
mongosh --quiet --eval 'db.hello().primary'
```

Preparar el comando de dump, incluyendo autenticación cuando corresponda:

```bash
mongodump \
  --uri='mongodb://<USUARIO>:<PASSWORD>@gl01:27017,gl02:27017,gl03:27017/graylog?replicaSet=rs0&authSource=admin' \
  --out="$BACKUP_DIR"
```

No ejecutar todavía el dump definitivo. El comando queda preparado para la ventana.

> Como los servicios Graylog estarán detenidos, la base `graylog` no debería recibir cambios durante el dump. Para esta prueba se respalda específicamente la base utilizada por Graylog.

---

## 9. Preparar F5

Dejar definidos los cambios antes de la ventana.

### Pool activo de ingesta

Miembros finales:

```text
gl02
gl03
```

### Pool activo de frontend

Miembros finales:

```text
gl02
gl03
```

### Pool histórico

Se crea después de validar `gl01`:

```text
gl01
```

Durante la ventana, las VIP actuales deben quedar temporalmente cerradas o con todos los miembros deshabilitados.

---

## 10. Criterios de inicio de la ventana

No iniciar el cambio hasta confirmar:

- [ ] Elasticsearch está operativo.
- [ ] OpenSearch está operativo.
- [ ] Los índices vacíos existen en OpenSearch.
- [ ] `rs0` está saludable.
- [ ] Los archivos `server.conf.opensearch` están preparados en `gl02` y `gl03`.
- [ ] El comando de backup fue probado o validado sintácticamente.
- [ ] Existe espacio suficiente para el dump.
- [ ] Los cambios de F5 están preparados.
- [ ] Existe un procedimiento de rollback.
- [ ] Se registró un mensaje de prueba previo al corte.

---

# PARTE II - VENTANA CRÍTICA

## 11. Registrar el inicio

```bash
date -Is
```

Anotar la hora exacta de inicio de la interrupción.

---

## 12. Cerrar las VIP activas

En F5:

1. Detener el tráfico de ingesta.
2. Detener el tráfico del frontend.
3. Verificar que no se abren conexiones nuevas hacia `gl01`, `gl02` o `gl03`.

No modificar todavía la membresía definitiva de los pools. Primero se completa la validación del nuevo backend.

---

## 13. Esperar el drenaje de mensajes

Antes de detener Graylog:

1. Revisar el journal desde la UI o métricas.
2. Confirmar que no queden mensajes pendientes de indexación.
3. Registrar el último mensaje visible en Elasticsearch.

Ejemplo de marca previa al corte:

```bash
logger --server <VIP_INGESTA> --port 1514 --udp \
  "graylog-before-split $(date -Is)"
```

Esperar a que el mensaje sea visible en Elasticsearch.

---

## 14. Detener los tres servicios Graylog

En `gl01`, `gl02` y `gl03`:

```bash
sudo systemctl stop graylog-server
sudo systemctl is-active graylog-server
```

Resultado esperado:

```text
inactive
```

No detener MongoDB.

No detener Elasticsearch.

No detener OpenSearch.

---

## 15. Verificar MongoDB `rs0`

```bash
mongosh --quiet --eval 'rs.status()'
```

Confirmar que continúa existiendo:

- Un `PRIMARY`.
- Dos `SECONDARY`.

---

## 16. Tomar el backup definitivo de MongoDB

Ejecutar el comando preparado:

```bash
mongodump \
  --uri='mongodb://<USUARIO>:<PASSWORD>@gl01:27017,gl02:27017,gl03:27017/graylog?replicaSet=rs0&authSource=admin' \
  --out="$BACKUP_DIR"
```

Guardar también la configuración del ReplicaSet como referencia:

```bash
mongosh --quiet --eval 'rs.conf()' \
  > "$BACKUP_DIR/rs0-config-reference.txt"
```

Verificar el backup:

```bash
find "$BACKUP_DIR" -type f -printf '%p %s bytes\n' | sort
```

No continuar si:

- `mongodump` devuelve error.
- El directorio está vacío.
- No aparece la base `graylog`.

---

## 17. Aplicar la configuración OpenSearch en `gl02` y `gl03`

En ambos nodos:

```bash
sudo cp -a \
  /etc/graylog/server/server.conf.opensearch \
  /etc/graylog/server/server.conf
```

Validar:

```bash
sudo grep -E '^(mongodb_uri|elasticsearch_hosts)' \
  /etc/graylog/server/server.conf
```

Resultado esperado:

- `mongodb_uri` continúa apuntando a `rs0`.
- `elasticsearch_hosts` apunta a `es01`, `es02` y `es03` por `19200`.

`gl01` debe continuar detenido y sin modificaciones por el momento.

---

## 18. Levantar `gl02`

```bash
sudo systemctl start graylog-server
sudo systemctl status graylog-server --no-pager
sudo journalctl -u graylog-server -n 100 --no-pager
```

Validar en los logs:

- Conexión correcta a MongoDB `rs0`.
- Conexión correcta a OpenSearch.
- Ausencia de errores de autenticación.
- Ausencia de errores de mappings.
- Inicio correcto del nodo.

---

## 19. Levantar `gl03`

```bash
sudo systemctl start graylog-server
sudo systemctl status graylog-server --no-pager
sudo journalctl -u graylog-server -n 100 --no-pager
```

Validar los mismos puntos que en `gl02`.

---

## 20. Validar el cluster activo antes de abrir F5

Ingresar directamente a la UI de `gl02` o `gl03`.

Confirmar:

- [ ] Los usuarios existentes continúan disponibles.
- [ ] Los streams continúan visibles.
- [ ] Los index sets continúan visibles.
- [ ] Los inputs conservan su configuración.
- [ ] Los dashboards y búsquedas guardadas continúan disponibles.
- [ ] En `System / Nodes` aparecen `gl02` y `gl03` activos.
- [ ] `gl01` aparece detenido o fuera de línea.
- [ ] Las búsquedas sobre el backend nuevo no muestran documentos históricos.

Verificar OpenSearch:

```bash
curl -s http://es01:19200/_cluster/health?pretty
curl -s 'http://es01:19200/_cat/indices?v&s=index'
```

---

## 21. Probar ingesta directa

Antes de abrir F5, enviar un mensaje directamente a un input de `gl02` o `gl03`.

Ejemplo:

```bash
logger --server gl02 --port 1514 --udp \
  "graylog-opensearch-direct-test $(date -Is)"
```

Confirmar:

- El mensaje aparece en Graylog.
- El documento queda almacenado en OpenSearch.
- El conteo del índice aumenta.
- Elasticsearch histórico no recibe el mensaje.

Buscar en OpenSearch, adaptando el patrón de índices:

```bash
curl -s 'http://es01:19200/graylog_*/_search?q=graylog-opensearch-direct-test&pretty'
```

---

## 22. Abrir F5 sobre `gl02` y `gl03`

### Ingesta

Dejar habilitados únicamente:

```text
gl02
gl03
```

### Frontend activo

Dejar habilitados únicamente:

```text
gl02
gl03
```

`gl01` debe quedar fuera de ambos pools.

---

## 23. Validar el servicio recuperado

Enviar un mensaje a la VIP:

```bash
logger --server <VIP_INGESTA> --port 1514 --udp \
  "graylog-after-split $(date -Is)"
```

Confirmar:

- [ ] El F5 entrega tráfico a `gl02`/`gl03`.
- [ ] El mensaje aparece en la UI activa.
- [ ] El mensaje queda almacenado en OpenSearch.
- [ ] Elasticsearch histórico permanece sin cambios.
- [ ] El frontend activo funciona por F5.
- [ ] Los journals no crecen de manera sostenida.
- [ ] No aparecen errores de indexación.

Registrar la hora de recuperación:

```bash
date -Is
```

La ventana crítica termina en este punto.

---

# PARTE III - CONSTRUCCIÓN DEL ENTORNO HISTÓRICO

## 24. Mantener `gl01` aislado

Hasta completar `rs1`:

- Mantener `graylog-server` detenido en `gl01`.
- Mantener `gl01` fuera de los pools activos de F5.
- Mantener la instancia MongoDB original de `gl01:27017` activa dentro de `rs0`.

Estado esperado:

```text
gl01
  graylog-server: detenido
  mongod rs0: activo

gl02
  graylog-server: activo
  mongod rs0: activo

gl03
  graylog-server: activo
  mongod rs0: activo
```

---

## 25. Crear una segunda instancia MongoDB en `gl01`

Definir valores para laboratorio:

```text
ReplicaSet: rs1
Puerto: <PUERTO_RS1>
dbPath: /var/lib/mongodb-rs1
Log: /var/log/mongodb/mongod-rs1.log
PID: /run/mongodb/mongod-rs1.pid
```

La nueva instancia no debe compartir con `rs0`:

- Puerto.
- `dbPath`.
- Archivo de log.
- Archivo PID.
- Unit de systemd.

Ejemplo conceptual de configuración:

```yaml
storage:
  dbPath: /var/lib/mongodb-rs1

systemLog:
  destination: file
  path: /var/log/mongodb/mongod-rs1.log
  logAppend: true

net:
  bindIp: 0.0.0.0
  port: <PUERTO_RS1>

processManagement:
  pidFilePath: /run/mongodb/mongod-rs1.pid

replication:
  replSetName: rs1
```

Crear directorios y permisos según el usuario de MongoDB.

---

## 26. Inicializar `rs1`

Levantar la nueva instancia y conectar con `mongosh`:

```bash
mongosh --host gl01 --port <PUERTO_RS1>
```

Inicializar el ReplicaSet de un solo miembro:

```javascript
rs.initiate({
  _id: "rs1",
  members: [
    {
      _id: 0,
      host: "gl01:<PUERTO_RS1>"
    }
  ]
})
```

Validar:

```javascript
rs.status()
```

Resultado esperado:

```text
name: PRIMARY
set: rs1
```

---

## 27. Restaurar la base `graylog` en `rs1`

Ejemplo sin autenticación inicial:

```bash
mongorestore \
  --host gl01 \
  --port <PUERTO_RS1> \
  --drop \
  "$BACKUP_DIR/graylog"
```

Adaptar el comando si `rs1` utiliza autenticación.

Validar:

```bash
mongosh --host gl01 --port <PUERTO_RS1> --quiet \
  --eval 'db.getSiblingDB("graylog").getCollectionNames()'
```

Comparar la cantidad de colecciones entre `rs0` y `rs1`.

---

## 28. Configurar el Graylog histórico de `gl01`

Respaldar la configuración actual:

```bash
sudo cp -a /etc/graylog/server/server.conf \
  /etc/graylog/server/server.conf.pre-historical
```

Modificar:

```properties
mongodb_uri = mongodb://gl01:<PUERTO_RS1>/graylog?replicaSet=rs1

elasticsearch_hosts = http://es01:9200,http://es02:9200,http://es03:9200
```

Mantener sin cambios:

```properties
password_secret
root_password_sha2
```

Actualizar, si corresponde:

```properties
http_publish_uri
http_external_uri
```

para usar la nueva URL histórica.

Validar:

```bash
sudo grep -E '^(mongodb_uri|elasticsearch_hosts|http_publish_uri|http_external_uri)' \
  /etc/graylog/server/server.conf
```

---

## 29. Levantar el Graylog histórico

```bash
sudo systemctl start graylog-server
sudo systemctl status graylog-server --no-pager
sudo journalctl -u graylog-server -n 150 --no-pager
```

Validar:

- Conexión a MongoDB `rs1`.
- Conexión a Elasticsearch `:9200`.
- Usuarios y roles originales.
- Streams originales.
- Index sets originales.
- Dashboards originales.
- Búsquedas sobre documentos históricos.

---

## 30. Deshabilitar la ingesta histórica

Antes de publicar la UI histórica:

1. Deshabilitar todos los inputs en `gl01`.
2. Revisar inputs globales restaurados desde MongoDB.
3. Bloquear por firewall los puertos de ingesta en `gl01`.
4. Confirmar que `gl01` no pertenece al pool activo de ingesta.
5. Revisar Sidecars, forwarders y outputs asociados.

La interfaz histórica debe utilizarse únicamente para búsquedas.

---

## 31. Revisar retención de índices históricos

La copia MongoDB conserva las políticas originales de index sets.

Antes de dejar el entorno operativo:

- Revisar rotación.
- Revisar retención.
- Evitar la eliminación automática de índices históricos.
- Confirmar que no se generen índices nuevos en Elasticsearch.
- Mantener un snapshot o punto de retorno de Elasticsearch.

---

## 32. Publicar la VIP histórica

Crear un pool independiente:

```text
gl01
```

Publicar una VIP y URL diferentes a las del cluster activo.

Ejemplo conceptual:

```text
Graylog activo:     https://graylog-lab.example/
Graylog histórico:  https://graylog-history-lab.example/
```

Validar:

- Acceso por la nueva URL.
- Autenticación.
- Búsquedas históricas.
- Ausencia de ingesta.
- Separación completa respecto del frontend activo.

---

# PARTE IV - VALIDACIÓN FINAL

## 33. Checklist del entorno activo

- [ ] `gl02` está activo.
- [ ] `gl03` está activo.
- [ ] `gl01` no participa como servidor Graylog activo.
- [ ] `rs0` conserva sus tres miembros MongoDB.
- [ ] `gl02` y `gl03` apuntan a OpenSearch `:19200`.
- [ ] OpenSearch recibe únicamente mensajes nuevos.
- [ ] Los índices históricos no fueron copiados a OpenSearch.
- [ ] F5 de ingesta apunta sólo a `gl02` y `gl03`.
- [ ] F5 de frontend activo apunta sólo a `gl02` y `gl03`.
- [ ] Los journals permanecen estables.
- [ ] No existen errores sostenidos de indexación.

## 34. Checklist del entorno histórico

- [ ] `gl01` apunta a MongoDB `rs1`.
- [ ] `rs1` tiene un solo miembro y está `PRIMARY`.
- [ ] `gl01` apunta a Elasticsearch `:9200`.
- [ ] Se conservan usuarios, streams, index sets y dashboards.
- [ ] Las búsquedas históricas funcionan.
- [ ] Los inputs están deshabilitados o bloqueados.
- [ ] Las políticas de retención no eliminan históricos.
- [ ] La VIP histórica es independiente.

## 35. Prueba de aislamiento

Realizar una modificación no destructiva en el cluster activo, por ejemplo crear una búsqueda guardada de prueba.

Confirmar que no aparece en el Graylog histórico.

Realizar otra modificación no destructiva en el histórico.

Confirmar que no aparece en el cluster activo.

Esto demuestra que `rs0` y `rs1` son independientes.

---

# PARTE V - ROLLBACK

## 36. Condiciones de rollback durante la ventana

Ejecutar rollback si:

- `gl02` o `gl03` no conectan con OpenSearch.
- Graylog no puede crear o utilizar los índices preparados.
- Aparecen errores de mappings que impiden indexar.
- La ingesta de prueba no funciona.
- No es posible validar el frontend activo.

---

## 37. Procedimiento de rollback

Mantener las VIP cerradas.

En `gl02` y `gl03`:

```bash
sudo systemctl stop graylog-server

sudo cp -a \
  /etc/graylog/server/server.conf.pre-opensearch \
  /etc/graylog/server/server.conf

sudo systemctl start graylog-server
```

Opcionalmente levantar también `gl01` con su configuración original si todavía no fue modificada:

```bash
sudo systemctl start graylog-server
```

Validar:

- Los nodos vuelven a conectar con Elasticsearch `:9200`.
- Las búsquedas históricas funcionan.
- Un mensaje de prueba se indexa en Elasticsearch.

Reabrir las VIP originales.

Registrar:

- Hora del rollback.
- Error observado.
- Logs relevantes.
- Estado final de Graylog, MongoDB, Elasticsearch y OpenSearch.

---

# PARTE VI - REGISTRO DE LA PRUEBA

## 38. Resultados

Completar después de ejecutar el laboratorio.

| Verificación | Resultado | Observaciones |
|---|---|---|
| Backup MongoDB completado | Pendiente | |
| `gl02` conectado a OpenSearch | Pendiente | |
| `gl03` conectado a OpenSearch | Pendiente | |
| Ingesta directa en OpenSearch | Pendiente | |
| Ingesta mediante F5 | Pendiente | |
| Frontend activo mediante F5 | Pendiente | |
| Creación de `rs1` | Pendiente | |
| Restore de MongoDB en `rs1` | Pendiente | |
| Búsquedas históricas en `gl01` | Pendiente | |
| Inputs históricos deshabilitados | Pendiente | |
| Aislamiento entre ambos clusters | Pendiente | |
| Rollback probado | Pendiente | |

## 39. Medición de la ventana

| Evento | Hora |
|---|---|
| Cierre de VIP de ingesta | Pendiente |
| Graylog detenido | Pendiente |
| Backup MongoDB finalizado | Pendiente |
| `gl02` y `gl03` levantados | Pendiente |
| Ingesta directa validada | Pendiente |
| VIP de ingesta reabierta | Pendiente |
| Duración total de la interrupción | Pendiente |

---

## 40. Criterio de aceptación

La prueba se considera satisfactoria cuando:

1. `gl02` y `gl03` reciben e indexan mensajes nuevos en OpenSearch.
2. `rs0` continúa saludable con sus tres miembros.
3. `gl01` consulta los índices históricos de Elasticsearch usando una copia independiente de MongoDB en `rs1`.
4. Los cambios de configuración de un entorno no aparecen en el otro.
5. `gl01` no recibe ingesta.
6. El rollback es conocido y ejecutable.
7. La duración de la ventana es compatible con el objetivo de NONPROD.

---

## Referencias

- Graylog: configuración inicial y parámetros `mongodb_uri` / backend de búsqueda.
- Graylog: despliegue multinodo con MongoDB ReplicaSet.
- MongoDB: creación e inicialización de ReplicaSets.
- MongoDB Database Tools: `mongodump` y `mongorestore`.
