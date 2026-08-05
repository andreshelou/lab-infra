# Uso: reindex_one_index.py

## Objetivo

Ejecutar Remote Reindex para un solo indice y medir cuanto tarda.

Sirve para pruebas puntuales de performance, validacion de `reindex.remote.allowlist` y comparacion rapida de counts.

```text
Origen ES:  http://ptyesnp01:9200
Destino OS: http://ptyesnp01:19200
```

## Dry-run

No escribe nada:

```bash
python3 es2os_scripts/reindex_one_index.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --index dev_index_587
```

## Ejecucion Real

```bash
python3 es2os_scripts/reindex_one_index.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --index dev_index_587 \
  --refresh \
  --execute
```

## Con Throttling

```bash
python3 es2os_scripts/reindex_one_index.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --index dev_index_587 \
  --batch-size 1000 \
  --requests-per-second 500 \
  --refresh \
  --execute
```

## Salida

El script muestra:

```text
Source count before
Target count before
Task ID
Progreso periodico
Elapsed seconds
Elapsed minutes
Source count after
Target count after
Counts match after
Failures
```

Tambien genera un reporte JSON en:

```text
out-one-index-reindex/reports/reindex-one-<index>-<timestamp>.json
```

## Requisitos

OpenSearch debe tener configurado:

```yaml
reindex.remote.allowlist: "ptyesnp01:9200"
```

Si usas IP en `allowlist`, tambien usa IP en `--source`.

## Notas

El indice destino debe existir previamente en OpenSearch con su mapping/settings correcto. Este script no crea indices.
