# Monitor de Indexación Elasticsearch / OpenSearch

## Objetivo

`monitor_indexing.py` permite observar en tiempo real el caudal de indexación de un cluster Elasticsearch u OpenSearch utilizando la API REST `_stats/indexing`.

El script calcula la diferencia entre dos muestras consecutivas del contador acumulado de operaciones de indexación (`index_total`) y presenta:

- Operaciones indexadas por intervalo.
- Operaciones por segundo.
- Operaciones por minuto.
- Historial de las últimas N muestras.
- Gráfico tipo *sparkline* en la terminal.

Es especialmente útil durante migraciones para verificar el momento exacto en que la ingesta deja de escribirse en Elasticsearch y comienza a escribirse en OpenSearch.

---

# Requisitos

Python 3

No requiere dependencias externas.

---

# Sintaxis

```bash
./monitor_indexing.py --url URL [opciones]
```

---

# Parámetros

| Parámetro | Obligatorio | Descripción | Valor por defecto |
|-----------|-------------|-------------|-------------------|
| `--url` | Sí | URL del cluster Elasticsearch/OpenSearch | - |
| `--label` | No | Nombre mostrado en pantalla | `CLUSTER` |
| `--index` | No | Índice o patrón de índices a consultar | `_all` |
| `--interval` | No | Segundos entre muestras | `60` |
| `--samples` | No | Cantidad de muestras visibles | `30` |
| `--timeout` | No | Timeout HTTP | `5` |

---

# Ejemplos

## Elasticsearch

```bash
./monitor_indexing.py \
    --url http://es01:9200 \
    --label ES
```

---

## OpenSearch

```bash
./monitor_indexing.py \
    --url http://es01:19200 \
    --label OS
```

---

## Consultar únicamente índices Graylog

```bash
./monitor_indexing.py \
    --url http://es01:19200 \
    --label OS \
    --index "graylog_*"
```

---

## Muestreo cada 5 segundos

Ideal para pruebas de laboratorio.

```bash
./monitor_indexing.py \
    --url http://es01:19200 \
    --label OS \
    --interval 5
```

---

## Conservar las últimas 60 muestras

```bash
./monitor_indexing.py \
    --url http://es01:19200 \
    --samples 60
```

---

## Timeout personalizado

```bash
./monitor_indexing.py \
    --url http://es01:19200 \
    --timeout 10
```

---

# Uso recomendado durante la migración

Abrir dos paneles de **tmux**.

Panel izquierdo:

```bash
./monitor_indexing.py \
    --url http://es01:9200 \
    --label Elasticsearch
```

Panel derecho:

```bash
./monitor_indexing.py \
    --url http://es01:19200 \
    --label OpenSearch
```

Durante la migración deberá observarse un comportamiento similar al siguiente.

Antes del cambio:

```
Elasticsearch    ███████████████

OpenSearch
```

Después del cambio:

```
Elasticsearch

OpenSearch      ███████████████
```

Esto permite verificar visualmente el momento exacto en que la ingesta deja de escribirse en Elasticsearch y comienza a hacerlo en OpenSearch.

---

# Información obtenida

El script consulta:

```
GET /<indice>/_stats/indexing
```

y utiliza el contador:

```
_all.primaries.indexing.index_total
```

El valor mostrado representa operaciones de indexación realizadas durante cada intervalo de muestreo.

No representa necesariamente el crecimiento neto de documentos, ya que actualizaciones o reintentos también incrementan dicho contador.

---

# Finalización

Para detener el monitor:

```
Ctrl + C
```