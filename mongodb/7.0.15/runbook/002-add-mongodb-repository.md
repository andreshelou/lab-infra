# Add MongoDB Repository

## Objetivo

Agregar el repositorio oficial de MongoDB Community Server 7.0 al sistema para permitir la instalación de la versión requerida.

> **Nota**
>
> Este laboratorio utiliza Ubuntu Server 24.04 LTS.
>
> MongoDB 7.0 no publica actualmente un repositorio específico para Ubuntu 24.04, por lo que se utiliza el repositorio oficial correspondiente a Ubuntu 22.04 (`jammy`), práctica habitual para esta combinación de versiones.

---

## Procedimiento

### 1. Importar la clave pública

```bash
curl -fsSL https://pgp.mongodb.com/server-7.0.asc \
 | sudo gpg --dearmor -o /usr/share/keyrings/mongodb-server-7.0.gpg
```

Verificar:

```bash
ls -l /usr/share/keyrings/mongodb-server-7.0.gpg
```

Resultado esperado:

```text
-rw-r--r-- root root ...
```

---

### 2. Crear el repositorio

```bash
echo "deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" \
| sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
```

Verificar:

```bash
cat /etc/apt/sources.list.d/mongodb-org-7.0.list
```

Resultado esperado:

```text
deb [ signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse
```

---

### 3. Actualizar el índice de paquetes

```bash
sudo apt update
```

---

### 4. Verificar el repositorio

```bash
apt-cache policy mongodb-org
```

Resultado esperado:

- El paquete `mongodb-org` aparece disponible.
- La versión **7.0.15** se encuentra entre las versiones publicadas.

---

## Archivos modificados

```text
/usr/share/keyrings/mongodb-server-7.0.gpg

/etc/apt/sources.list.d/mongodb-org-7.0.list
```

---

## Validación

Verificar:

- [ ] Clave GPG instalada.
- [ ] Repositorio agregado.
- [ ] `apt update` sin errores.
- [ ] `mongodb-org` disponible mediante `apt-cache policy`.
- [ ] La versión 7.0.15 aparece disponible.

---

## Próximo paso

Continuar con:

```text
003-install-mongodb.md
```