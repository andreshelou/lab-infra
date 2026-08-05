# Uso: reindex_window.py

## Objetivo

Ejecutar Remote Reindex para uno o varios indices usando una ventana de tiempo sobre el campo `timestamp`.

Sirve para dividir la migracion en partes:

```text
Historico: timestamp < T0
Delta:     timestamp >= T0 y timestamp < now
```

## Dry-run

```bash
python3 es2os_scripts/reindex_window.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --indices out-ptyesnp01-os215-structure/discovery/indices.json \
  --lt "2026-08-01 00:00:00.000"
```

## Reindex Historico Hasta T0

```bash
python3 es2os_scripts/reindex_window.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --indices out-ptyesnp01-os215-structure/discovery/indices.json \
  --timestamp-field timestamp \
  --lt "2026-08-01 00:00:00.000" \
  --wait \
  --refresh \
  --execute
```

## Reindex De Una Ventana T0-T1

```bash
python3 es2os_scripts/reindex_window.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --indices out-ptyesnp01-os215-structure/discovery/indices.json \
  --gte "2026-08-01 00:00:00.000" \
  --lt "2026-08-02 00:00:00.000" \
  --wait \
  --refresh \
  --execute
```

## Delta Hasta Ahora

`now` se resuelve una sola vez al inicio del script, para que todos los indices usen el mismo corte superior.

```bash
python3 es2os_scripts/reindex_window.py \
  --source http://ptyesnp01:9200 \
  --target http://ptyesnp01:19200 \
  --indices out-ptyesnp01-os215-structure/discovery/indices.json \
  --gte "2026-08-02 00:00:00.000" \
  --lt now \
  --wait \
  --refresh \
  --execute
```

## Opciones Importantes

```text
--gt / --gte / --lt / --lte
--timestamp-field timestamp
--batch-size 1000
--requests-per-second 500
--max-parallel 1
--wait
--refresh
--no-date-policy skip|full|fail
--conflicts abort|proceed
--execute
```

Politica para indices sin campo `timestamp`:

```text
skip: no reindexa el indice
full: reindexa completo
fail: aborta ese indice con error
```

Por defecto usa:

```text
--no-date-policy skip
--conflicts proceed
--max-parallel 1
```

## Reporte

Genera reporte JSON en:

```text
out-window-reindex/reports/window-reindex-<timestamp>.json
```

Incluye por indice:

```text
modo
rango usado
source_count_before / after
target_count_before / after
task_id
duracion
failures
counts_match_after
```

## Notas

Los indices destino deben existir previamente en OpenSearch. Este script no crea indices ni aplica aliases.

Para una ventana sin gaps usar:

```text
Historico: --lt T0
Delta:     --gte T0 --lt now
```
