# 002 - Agregar el repositorio de Graylog

## Objetivo

Agregar el repositorio oficial de Graylog 6.0 para permitir la instalación del paquete mediante APT.

## Requisitos

- Validación del entorno completada.
- Acceso administrativo mediante `sudo`.
- Conectividad a Internet.

## Procedimiento

### 1. Descargar el paquete del repositorio

Ejecutar:

```bash
wget https://packages.graylog2.org/repo/packages/graylog-6.0-repository_latest.deb
```

---

### 2. Instalar el repositorio

Ejecutar:

```bash
sudo dpkg -i graylog-6.0-repository_latest.deb
```

Resultado esperado:

El repositorio de Graylog queda registrado en el sistema.

---

### 3. Actualizar el índice de paquetes

Ejecutar:

```bash
sudo apt update
```

Resultado esperado:

El repositorio oficial de Graylog aparece entre los repositorios consultados.

No deben producirse errores.

## Archivos modificados

Durante este procedimiento se agregan automáticamente los archivos del repositorio APT correspondientes a Graylog.

## Validación

Verificar que el repositorio haya sido agregado correctamente:

```bash
apt policy graylog-server
```

Resultado esperado:

Debe mostrarse una versión disponible correspondiente a Graylog 6.0.x.

## Resultado esperado

El sistema queda preparado para instalar Graylog desde el repositorio oficial mediante APT.

## Checklist

- [ ] Repositorio descargado.
- [ ] Repositorio instalado.
- [ ] Índice APT actualizado.
- [ ] Paquete `graylog-server` disponible.

## Próximo paso

Continuar con:

```text
003-install-graylog.md
```