# 001 - Validar requisitos previos

## Objetivo

Verificar que la infraestructura se encuentre preparada para instalar Graylog 6.0.7.

Este procedimiento asume que MongoDB ya fue instalado y configurado sobre los nodos `gl01`, `gl02` y `gl03`, y que el cluster Elasticsearch 7.17.29 ya se encuentra operativo sobre los nodos `es01`, `es02` y `es03`.

## Requisitos

- Ubuntu Server 24.04 instalado.
- Acceso administrativo mediante `sudo`.
- Conectividad entre todos los nodos del laboratorio.
- MongoDB ReplicaSet operativo.
- Elasticsearch Cluster operativo.

## Procedimiento

### 1. Verificar el hostname

Ejecutar:

```bash
hostnamectl
```

Resultado esperado (según el nodo):

```text
gl01
```

```text
gl02
```

```text
gl03
```

---

### 2. Verificar resolución de nombres

Ejecutar:

```bash
getent hosts gl01
getent hosts gl02
getent hosts gl03
getent hosts es01
getent hosts es02
getent hosts es03
```

Resultado esperado:

Todos los nodos deben resolverse correctamente.

---

### 3. Verificar conectividad

Desde cada nodo Graylog ejecutar:

```bash
ping -c 2 gl01
ping -c 2 gl02
ping -c 2 gl03

ping -c 2 es01
ping -c 2 es02
ping -c 2 es03
```

Todos los nodos deben responder correctamente.

---

### 4. Verificar MongoDB

Ejecutar:

```bash
sudo systemctl status mongod
```

Resultado esperado:

```text
Active: active (running)
```

---

### 5. Verificar ReplicaSet

Conectarse a MongoDB:

```bash
mongosh
```

Ejecutar:

```javascript
rs.status()
```

Resultado esperado:

- `gl01` → PRIMARY
- `gl02` → SECONDARY
- `gl03` → SECONDARY

---

### 6. Verificar Elasticsearch

Ejecutar:

```bash
curl http://es01:9200/_cluster/health?pretty
```

Resultado esperado:

El cluster debe responder correctamente.

Verificar especialmente:

```json
"status" : "green"
```

---

### 7. Verificar sincronización horaria

Ejecutar:

```bash
timedatectl
```

Resultado esperado:

```text
System clock synchronized: yes
```

---

### 8. Verificar espacio disponible

Ejecutar:

```bash
df -h
```

Verificar especialmente el espacio disponible en:

- `/`
- `/var`
- `/var/lib`

---

### 9. Actualizar índices de paquetes

Ejecutar:

```bash
sudo apt update
```

No deben producirse errores.

## Archivos modificados

Ninguno.

## Validación

La infraestructura se considera preparada cuando:

- Los hostnames son correctos.
- Existe resolución de nombres entre todos los nodos.
- Existe conectividad entre los nodos Graylog y Elasticsearch.
- MongoDB está iniciado.
- El ReplicaSet funciona correctamente.
- Elasticsearch responde correctamente.
- La sincronización horaria está activa.
- Existe espacio suficiente en disco.
- Los repositorios APT se actualizan sin errores.

## Resultado esperado

La infraestructura se encuentra lista para comenzar la instalación de Graylog 6.0.7.

## Checklist

- [ ] Hostnames verificados.
- [ ] Resolución de nombres validada.
- [ ] Conectividad entre nodos validada.
- [ ] MongoDB operativo.
- [ ] ReplicaSet validado.
- [ ] Elasticsearch operativo.
- [ ] Sincronización horaria validada.
- [ ] Espacio disponible verificado.
- [ ] Repositorios APT actualizados.

## Próximo paso

Continuar con:

```text
002-add-graylog-repository.md
```