# 007 - Validar el cluster

## Objetivo

Verificar que los tres nodos Graylog se encuentren operativos y correctamente conectados a MongoDB y Elasticsearch.

## Requisitos

- Los tres nodos Graylog iniciados.
- MongoDB ReplicaSet operativo.
- Elasticsearch Cluster operativo.

## Procedimiento

### 1. Verificar el estado del servicio

Ejecutar en cada nodo:

```bash
systemctl is-active graylog-server
```

Resultado esperado:

```text
active
```

---

### 2. Verificar la API REST

Ejecutar en cada nodo:

```bash
curl -s http://localhost:9000/api/system/lbstatus
```

Resultado esperado:

```text
ALIVE
```

---

### 3. Verificar conectividad con MongoDB

```bash
grep -i mongodb /var/log/graylog-server/server.log | tail -20
```

No deben aparecer errores de conexión.

---

### 4. Verificar conectividad con Elasticsearch

```bash
grep -i elastic /var/log/graylog-server/server.log | tail -20
```

No deben aparecer errores de conexión.

---

### 5. Verificar errores críticos

```bash
grep -Ei 'ERROR|FATAL|Exception' \
/var/log/graylog-server/server.log | tail -20
```

No deben existir errores relacionados con:

- MongoDB
- Elasticsearch
- Cluster
- Journal

## Resultado esperado

Los tres nodos se encuentran ejecutándose correctamente y conectados al backend de almacenamiento.

## Checklist

- [ ] gl01 activo.
- [ ] gl02 activo.
- [ ] gl03 activo.
- [ ] API responde ALIVE.
- [ ] MongoDB conectado.
- [ ] Elasticsearch conectado.
- [ ] Sin errores críticos.

## Próximo paso

008-access-web-interface.md