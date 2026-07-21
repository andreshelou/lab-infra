# 005 - Configurar Graylog

## Objetivo

Configurar Graylog Server 6.0.7 para formar parte del cluster.

Al finalizar este procedimiento el archivo `server.conf` deberá contener todos los parámetros necesarios para permitir el inicio del servicio.

## Requisitos

- Graylog Server 6.0.7 instalado.
- Secretos del cluster generados.
- MongoDB ReplicaSet operativo.
- Elasticsearch Cluster operativo.

## Introducción

La configuración principal de Graylog se encuentra en:

```text
/etc/graylog/server/server.conf
```

Este archivo define el comportamiento del servidor, la conexión con MongoDB, la conexión con Elasticsearch y los parámetros propios del nodo.

## Procedimiento

### 1. Realizar una copia de seguridad

```bash
sudo cp /etc/graylog/server/server.conf \
/etc/graylog/server/server.conf.orig
```

---

### 2. Editar la configuración

```bash
sudo vi /etc/graylog/server/server.conf
```

Modificar únicamente los parámetros documentados en este procedimiento.

---

## Parámetros del cluster

### password_secret

Corresponde al secreto generado en el procedimiento anterior.

Ejemplo:

```properties
password_secret=<PASSWORD_SECRET>
```

---

### root_password_sha2

Corresponde al hash SHA-256 generado previamente.

Ejemplo:

```properties
root_password_sha2=<ROOT_PASSWORD_SHA2>
```

---

### http_bind_address

Permite aceptar conexiones HTTP.

```properties
http_bind_address=0.0.0.0:9000
```

---

### http_publish_uri

Dirección publicada por este nodo.

Nodo gl01:

```properties
http_publish_uri=http://gl01:9000/
```

Nodo gl02:

```properties
http_publish_uri=http://gl02:9000/
```

Nodo gl03:

```properties
http_publish_uri=http://gl03:9000/
```

---

### is_leader

Define si el nodo actuará como líder del cluster.

En un cluster Graylog debe existir **un único nodo líder**.

El nodo líder ejecuta tareas administrativas como migraciones, trabajos programados y otras tareas internas del cluster.

Configurar:

Nodo gl01:

```properties
is_leader = true
```

Nodo gl02:

```properties
is_leader = false
```

Nodo gl03:

```properties
is_leader = false
```

---

### mongodb_uri

Cadena de conexión hacia el ReplicaSet.

```properties
mongodb_uri=mongodb://gl01:27017,gl02:27017,gl03:27017/graylog?replicaSet=rs0
```

---

### elasticsearch_hosts

Lista de nodos Elasticsearch.

```properties
elasticsearch_hosts=http://es01:9200,http://es02:9200,http://es03:9200
```

## Archivos modificados

```text
/etc/graylog/server/server.conf
```

## Validación

Verificar la configuración:

```bash
grep -E \
'password_secret|root_password_sha2|http_bind_address|http_publish_uri|is_leader|mongodb_uri|elasticsearch_hosts' \
/etc/graylog/server/server.conf
```

Verificar que todos los parámetros se encuentren presentes y correctamente configurados para el nodo correspondiente.

## Resultado esperado

El archivo `server.conf` contiene la configuración necesaria para permitir el inicio de Graylog.

El servicio aún no ha sido iniciado.

## Checklist

- [ ] Backup realizado.
- [ ] password_secret configurado.
- [ ] root_password_sha2 configurado.
- [ ] http_bind_address configurado.
- [ ] http_publish_uri configurado.
- [ ] is_leader configurado.
- [ ] mongodb_uri configurado.
- [ ] elasticsearch_hosts configurado.

## Próximo paso

Continuar con:

```text
006-start-graylog.md
```