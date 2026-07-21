# 004 - Generar secretos del cluster

## Objetivo

Generar los secretos que serán compartidos por todos los nodos del cluster Graylog.

Estos valores forman parte de la identidad lógica del cluster y deberán conservarse para futuras reinstalaciones o incorporaciones de nuevos nodos.

## Requisitos

- Graylog Server 6.0.7 instalado.
- Acceso administrativo mediante `sudo`.

## Introducción

Graylog requiere dos valores de configuración antes de poder iniciar correctamente.

### password_secret

Es una cadena aleatoria utilizada internamente por Graylog para proteger información sensible.

Este valor:

- Debe tener al menos 64 caracteres.
- Debe ser exactamente el mismo en todos los nodos del cluster.
- No debe modificarse una vez que el cluster se encuentra en funcionamiento.

### root_password_sha2

Corresponde al hash SHA-256 de la contraseña del usuario administrador (`admin`).

Graylog nunca almacena la contraseña en texto plano.

El valor configurado en `server.conf` corresponde únicamente al hash SHA-256.

## Procedimiento

### 1. Instalar la herramienta `pwgen`

Graylog recomienda utilizar la utilidad `pwgen` para generar el valor de `password_secret`.

Instalar el paquete:

```bash
sudo apt install pwgen
```

Verificar la instalación:

```bash
pwgen -N 1 -s 96
```

Resultado esperado:

Se genera una cadena aleatoria de 16 caracteres.

---

### 2. Generar el `password_secret`

Ejecutar:

```bash
pwgen -N 1 -s 96
```

Ejemplo:

```text
Lx7k8zY...
```

Guardar el valor obtenido en un lugar seguro.

Este mismo valor deberá utilizarse en los tres nodos del cluster.

---

### 3. Definir la contraseña inicial del administrador

Seleccionar la contraseña inicial del usuario:

```text
admin
```

La contraseña nunca deberá almacenarse dentro del repositorio.

---

### 4. Generar el hash SHA-256

Reemplazar `MiPassword` por la contraseña elegida y ejecutar:

```bash
echo -n 'MiPassword' | sha256sum
```

Ejemplo:

```text
e3b0c44298fc1c149afbf4c8996fb924...
```

Guardar únicamente el hash SHA-256 obtenido.

Este mismo valor deberá utilizarse en los tres nodos del cluster.

## Archivos modificados

Ninguno.

Los valores generados serán utilizados posteriormente durante la configuración de Graylog.

## Validación

Verificar que:

- `pwgen` se encuentre instalado.
- El `password_secret` tenga al menos 64 caracteres.
- El hash SHA-256 tenga exactamente 64 caracteres hexadecimales.

## Resultado esperado

Se dispone de los dos secretos necesarios para configurar el cluster Graylog:

- `password_secret`
- `root_password_sha2`

Ambos valores serán compartidos por los tres nodos del cluster.

## Checklist

- [ ] `pwgen` instalado.
- [ ] `password_secret` generado.
- [ ] `password_secret` almacenado de forma segura.
- [ ] Contraseña inicial definida.
- [ ] Hash SHA-256 generado.
- [ ] Hash almacenado de forma segura.

## Próximo paso

Continuar con:

```text
005-configure-graylog.md
```