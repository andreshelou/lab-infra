# 003 - Instalar Graylog

## Objetivo

Instalar Graylog Server 6.0.7 utilizando el repositorio oficial previamente configurado.

Al finalizar este procedimiento el paquete `graylog-server` deberá encontrarse instalado en el sistema, sin realizar aún ninguna configuración.

## Requisitos

- Validación del entorno completada.
- Repositorio oficial de Graylog configurado.
- Acceso administrativo mediante `sudo`.

## Procedimiento

### 1. Instalar Graylog Server

Ejecutar:

```bash
sudo apt install graylog-server=6.0.7-1
```

Confirmar la instalación cuando APT lo solicite.

---

### 2. Verificar la versión instalada

Ejecutar:

```bash
dpkg -l | grep graylog
```

Resultado esperado:

```text
ii  graylog-server    6.0.7-1
```

La versión podrá variar únicamente en el número de revisión del paquete.

---

### 3. Verificar la instalación del servicio

Ejecutar:

```bash
systemctl status graylog-server
```

Resultado esperado:

El servicio debe encontrarse instalado.

Es esperable que aún no pueda iniciarse correctamente ya que la configuración todavía no fue realizada.

## Archivos modificados

Los archivos son instalados automáticamente por el paquete.

Entre los principales:

```text
/etc/graylog/server/server.conf

/etc/default/graylog-server

/usr/share/graylog-server/

/var/lib/graylog-server/

/var/log/graylog-server/
```

## Validación

Verificar que el paquete quedó instalado:

```bash
apt policy graylog-server
```

Ejecutar:

```bash
dpkg -l | grep graylog
```

Debe observarse el paquete instalado.

## Resultado esperado

Graylog Server 6.0.7 queda instalado en el sistema.

La configuración aún no ha sido modificada.

El servicio todavía no se encuentra operativo.

## Checklist

- [ ] Graylog instalado.
- [ ] Paquete verificado.
- [ ] Servicio instalado.
- [ ] Directorios creados.

## Próximo paso

Continuar con:

```text
004-generate-secrets.md
```