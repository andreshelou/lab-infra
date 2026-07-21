# 006 - Iniciar Graylog

## Objetivo

Iniciar el servicio Graylog en los tres nodos del cluster.

## Requisitos

- Configuración finalizada.
- MongoDB operativo.
- Elasticsearch operativo.

## Procedimiento

### Habilitar el servicio

```bash
sudo systemctl enable graylog-server
```

### Iniciar el servicio

```bash
sudo systemctl start graylog-server
```

### Verificar el estado

```bash
systemctl status graylog-server
```

Resultado esperado:

```text
Active: active (running)
```

---

### Revisar el log

```bash
sudo journalctl -u graylog-server -f
```

Esperar hasta observar que Graylog finalice su proceso de inicialización.

Interrumpir la visualización con:

```text
Ctrl+C
```

## Archivos modificados

Ninguno.

## Validación

```bash
systemctl is-active graylog-server
```

Resultado esperado:

```text
active
```

## Resultado esperado

Graylog se encuentra ejecutándose correctamente.

El acceso web y la validación del cluster se realizarán en el siguiente procedimiento.

## Checklist

- [ ] Servicio habilitado.
- [ ] Servicio iniciado.
- [ ] Estado `active`.
- [ ] Sin errores críticos en el log.

## Próximo paso

```text
007-validate-cluster.md
```