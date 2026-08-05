# Uso: reset_target_index.py

## Objetivo

Volver a cero un indice destino en OpenSearch para repetir pruebas de reindex.

El script borra el indice destino y lo recrea desde el payload limpio generado por `generate-payloads`.

No toca Elasticsearch origen.

## Dry-run

```bash
python3 es2os_scripts/reset_target_index.py \
  --target http://ptyesnp01:19200 \
  --index dev_index_587 \
  --payloads out-ptyesnp01-os215-structure/payloads
```

Muestra:

```text
cluster destino
indice
count actual
aliases actuales
payload usado
acciones que ejecutaria
```

## Reset De Indice Sin Alias

```bash
python3 es2os_scripts/reset_target_index.py \
  --target http://ptyesnp01:19200 \
  --index dev_index_587 \
  --payloads out-ptyesnp01-os215-structure/payloads \
  --refresh \
  --execute
```

## Reset De Indice Con Alias

Si el indice tiene alias, el script bloquea por defecto.

Para resetear y restaurar los mismos aliases:

```bash
python3 es2os_scripts/reset_target_index.py \
  --target http://ptyesnp01:19200 \
  --index graylog_3413 \
  --payloads out-ptyesnp01-os215-structure/payloads \
  --preserve-aliases \
  --force \
  --refresh \
  --execute
```

Esto hace:

```text
1. Lee aliases actuales del indice.
2. Borra el indice.
3. Crea el indice desde <index>.create.json.
4. Reaplica los aliases capturados.
5. Verifica count = 0.
6. Verifica mapping contra payload.
```

## Reporte

Genera reporte JSON en:

```text
out-reset-index/reports/reset-<index>-<timestamp>.json
```

## Protecciones

El script:

```text
usa dry-run por defecto
bloquea indices con alias salvo --force --preserve-aliases
bloquea escritura al cluster ES real protegido conocido
requiere que exista el payload <index>.create.json
```

## Advertencia

No resetear indices que esten siendo usados por Graylog en produccion. Para pruebas con aliases ya aplicados, usar siempre `--preserve-aliases --force` y validar inmediatamente despues.
