# Prepare Ubuntu

## Objetivo

Preparar una instalación base de Ubuntu Server 24.04 para la posterior instalación de MongoDB.

Este procedimiento deja el sistema operativo actualizado, con las herramientas comunes necesarias para el laboratorio y sin errores de servicios.

---

## Requisitos

- Ubuntu Server 24.04 recién instalado.
- Acceso a Internet.
- Usuario con privilegios de `sudo`.

---

## Procedimiento

### 1. Actualizar el sistema

Actualizar el índice de paquetes.

```bash
sudo apt update
```

Actualizar todos los paquetes instalados.

```bash
sudo apt full-upgrade -y
```

Eliminar paquetes que ya no sean necesarios.

```bash
sudo apt autoremove -y
```

---

### 2. Instalar herramientas comunes

Instalar las herramientas que serán utilizadas durante la construcción y administración del laboratorio.

```bash
sudo apt install -y \
    curl \
    wget \
    gnupg \
    ca-certificates \
    lsb-release \
    vim \
    nano \
    jq \
    net-tools
```

---

### 3. Verificar servicios

Comprobar que no existan servicios en estado de error.

```bash
systemctl --failed
```

Resultado esperado:

```text
0 loaded units listed.
```

---

### 4. Verificar actualizaciones pendientes

Comprobar que no existan paquetes pendientes de actualización.

```bash
apt list --upgradable
```

Resultado esperado:

```text
Listing... Done
```

> **Nota**
>
> Durante la construcción de este laboratorio se detectó una actualización pendiente para `snapd`.
>
> Se decidió **no eliminar ni modificar** componentes propios de Ubuntu Server para mantener la instalación lo más cercana posible a una instalación estándar.

---

## Archivos modificados

Ninguno.

---

## Validación

Verificar:

- [ ] Sistema actualizado.
- [ ] Herramientas comunes instaladas.
- [ ] Sin servicios fallando (`systemctl --failed`).
- [ ] Sin paquetes pendientes de actualización (o únicamente componentes del sistema que se decidió mantener).

---

## Resultado esperado

La máquina queda preparada para comenzar la instalación de MongoDB Community Server.

---

## Próximo paso

Continuar con:

```text
002-add-mongodb-repository.md
```