# Uso: continuous_seed_local_data.py

## Objetivo

Generar ingesta sintetica continua en indices existentes del lab para simular actividad durante pruebas de cambio de arquitectura.

El script escribe documentos con `timestamp` actual y filtra campos contra el mapping existente para evitar drift.

## Ejecucion En Primer Plano

```bash
python3 es2os_scripts/continuous_seed_local_data.py \
  --target http://localhost:9200 \
  --indices out-poc-current/discovery/indices.json \
  --docs-per-index 1 \
  --interval-seconds 10 \
  --refresh
```

Detener con `Ctrl-C`.

## Ejecucion En Background

```bash
nohup python3 es2os_scripts/continuous_seed_local_data.py \
  --target http://localhost:9200 \
  --indices out-poc-current/discovery/indices.json \
  --docs-per-index 1 \
  --interval-seconds 10 \
  --refresh \
  > continuous-seed.log 2>&1 &
```

Guardar el PID:

```bash
jobs -l
```

Detener:

```bash
kill <PID>
```

## Corrida Limitada

Ejecutar 6 ciclos y salir:

```bash
python3 es2os_scripts/continuous_seed_local_data.py \
  --target http://localhost:9200 \
  --indices out-poc-current/discovery/indices.json \
  --docs-per-index 1 \
  --interval-seconds 10 \
  --cycles 6 \
  --refresh
```

## Seguridad

Por defecto solo permite clusters llamados:

```text
lab-es
lab-os
```

Para otro cluster de pruebas:

```bash
--allow-cluster nombre-del-cluster
```

No usar contra produccion.

## Verificacion

```bash
curl -sS 'http://localhost:9200/_cluster/health?pretty'
curl -sS 'http://localhost:9200/_cat/indices?v&h=health,index,docs.count&s=index'
```

Buscar documentos recientes:

```bash
curl -sS -XPOST 'http://localhost:9200/graylog_3413/_search' \
  -H 'Content-Type: application/json' \
  -d '{"size":5,"sort":[{"timestamp":{"order":"desc"}}],"query":{"match":{"source":"continuous-graylog_3413"}}}'
```
