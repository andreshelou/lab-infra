# Install MongoDB

## Objetivo

Instalar MongoDB Community Server 7.0.15 y mantener todos los paquetes `mongodb-org-*` fijados en esa versión.

---

## Requisitos

- Ubuntu Server preparado.
- Repositorio oficial de MongoDB 7.0 configurado.
- Clave GPG del repositorio instalada.
- Conectividad a Internet.

---

## Referencias

Documentación oficial:

- https://www.mongodb.com/docs/v7.0/tutorial/install-mongodb-on-ubuntu/

---

## Procedimiento

### 1. Verificar la disponibilidad de la versión

```bash
apt-cache madison mongodb-org
```

La versión `7.0.15` debe aparecer en la lista.

---

### 2. Instalar MongoDB 7.0.15

```bash
sudo apt install -y \
    mongodb-org=7.0.15 \
    mongodb-org-database=7.0.15 \
    mongodb-org-database-tools-extra=7.0.15 \
    mongodb-org-mongos=7.0.15 \
    mongodb-org-server=7.0.15 \
    mongodb-org-shell=7.0.15 \
    mongodb-org-tools=7.0.15
```

> **Nota**
>
> Es necesario fijar explícitamente los metapaquetes
> `mongodb-org-database` y `mongodb-org-database-tools-extra`.
>
> Si solo se fija `mongodb-org=7.0.15`, APT puede seleccionar la versión más
> reciente disponible para esas dependencias.

Los paquetes `mongodb-mongosh` y `mongodb-database-tools` utilizan un esquema de versionado independiente.

---

### 3. Verificar la versión del servidor

```bash
mongod --version
```

Resultado esperado:

```text
db version v7.0.15
```

---

### 4. Verificar los paquetes instalados

```bash
dpkg -l | grep mongodb
```

Todos los paquetes `mongodb-org-*` deben figurar en la versión `7.0.15`.

---

### 5. Proteger los paquetes contra actualizaciones

```bash
sudo apt-mark hold \
    mongodb-org \
    mongodb-org-database \
    mongodb-org-database-tools-extra \
    mongodb-org-mongos \
    mongodb-org-server \
    mongodb-org-shell \
    mongodb-org-tools
```

---

### 6. Verificar los paquetes retenidos

```bash
apt-mark showhold
```

Resultado esperado:

```text
mongodb-org
mongodb-org-database
mongodb-org-database-tools-extra
mongodb-org-mongos
mongodb-org-server
mongodb-org-shell
mongodb-org-tools
```

---

### 7. Verificar el estado inicial del servicio

```bash
systemctl status mongod
```

Resultado esperado:

```text
Active: inactive (dead)
```

```bash
systemctl is-enabled mongod
```

Resultado esperado:

```text
disabled
```

---

## Archivos modificados

- Base de datos de paquetes de APT.
- Estado de paquetes retenidos por `apt-mark`.
- Unidad systemd instalada en:

```text
/usr/lib/systemd/system/mongod.service
```

---

## Validación

- [ ] `mongod` informa la versión `7.0.15`.
- [ ] Todos los paquetes `mongodb-org-*` están en `7.0.15`.
- [ ] Los paquetes aparecen en `apt-mark showhold`.
- [ ] El servicio `mongod` permanece detenido.
- [ ] El servicio `mongod` permanece deshabilitado.

---

## Resultado esperado

MongoDB Community Server 7.0.15 instalado y protegido contra actualizaciones accidentales, sin iniciar todavía el servicio.

---

## Próximo paso

Continuar con:

```text
004-configure-mongod.md
```