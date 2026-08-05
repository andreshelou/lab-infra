# Uso: Limpiar Documentos Sin Borrar Indices

## Objetivo

Borrar la data/documentos del cluster manteniendo intactos:

```text
indices
mappings
settings
aliases
shards/replicas
```

Esto sirve para volver a cero la data durante pruebas sin tener que recrear estructura.

## Cluster Lab

Ejemplo usado en el laboratorio:

```bash
export ES_TARGET="http://localhost:9200"
```

## 1. Detener Ingesta Continua

Si esta corriendo el generador continuo:

```bash
kill $(cat logs/continuous-seed-local.pid)
```

Validar que ya no esta corriendo:

```bash
ps -p $(cat logs/continuous-seed-local.pid) -o pid,command
```

Si no aparece proceso, esta detenido.

## 2. Ver Estado Antes De Borrar

```bash
curl -sS "$ES_TARGET/_cluster/health?pretty"
curl -sS "$ES_TARGET/_cat/indices?v&h=health,index,docs.count&s=index"
curl -sS "$ES_TARGET/_cat/aliases?v&h=alias,index&s=alias"
```

## 3. Borrar Solo Documentos

Este comando borra documentos de las familias Graylog usadas en el lab, pero conserva indices y estructura.

```bash
curl -sS -XPOST "$ES_TARGET/graylog_*,qa_index_*,ppd_index_*,dev_index_*,1_*,gl-events_*,gl-system-events_*,infosec_*,wallet_adapter_api_*/_delete_by_query?conflicts=proceed&refresh=true&wait_for_completion=true&slices=auto" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match_all":{}}}'
```

No borra indices internos como:

```text
.geoip_databases
```

No borra el indice de prueba:

```text
ah-test-0
```

Si tambien queres borrar documentos de `ah-test-0`, ejecutalo explicitamente:

```bash
curl -sS -XPOST "$ES_TARGET/ah-test-0/_delete_by_query?conflicts=proceed&refresh=true&wait_for_completion=true&slices=auto" \
  -H 'Content-Type: application/json' \
  -d '{"query":{"match_all":{}}}'
```

## 4. Verificar Que Quedaron En Cero

```bash
curl -sS "$ES_TARGET/_cat/indices?v&h=health,index,docs.count&s=index"
```

Esperado para indices del lab:

```text
docs.count = 0
health = green
```

Verificar aliases intactos:

```bash
curl -sS "$ES_TARGET/_cat/aliases?v&h=alias,index&s=alias"
```

Aliases esperados:

```text
1_deflector -> 1_446
dev_index_deflector -> dev_index_588
gl-events_deflector -> gl-events_69
gl-system-events_deflector -> gl-system-events_48
graylog_deflector -> graylog_3413
infosec_deflector -> infosec_1
ppd_index_deflector -> ppd_index_1442
qa_index_deflector -> qa_index_720
wallet_adapter_api_deflector -> wallet_adapter_api_1
```

## 5. Validar Mappings Sin Drift

```bash
python3 - <<'PY'
import json, urllib.request, pathlib, sys
base='http://localhost:9200'
diffs=[]; missing=[]
for path in sorted(pathlib.Path('out-poc-current/payloads').glob('*.create.json')):
    index=path.name.removesuffix('.create.json')
    payload=json.loads(path.read_text())
    try:
        actual=json.loads(urllib.request.urlopen(f'{base}/{index}/_mapping', timeout=30).read().decode())[index].get('mappings', {})
    except Exception as e:
        missing.append({'index': index, 'error': str(e)})
        continue
    if actual != payload.get('mappings', {}):
        diffs.append(index)
print(json.dumps({'missing': missing, 'mapping_diffs_vs_payloads': len(diffs), 'diff_indices': diffs}, indent=2))
sys.exit(1 if missing or diffs else 0)
PY
```

Esperado:

```text
mapping_diffs_vs_payloads = 0
missing = []
```

## 6. Reanudar Ingesta Continua

Si queres volver a generar datos continuos:

```bash
nohup python3 es2os_scripts/continuous_seed_local_data.py \
  --target "$ES_TARGET" \
  --indices out-poc-current/discovery/indices.json \
  --docs-per-index 1 \
  --interval-seconds 10 \
  --refresh \
  > logs/continuous-seed-local.log 2>&1 &

print $! > logs/continuous-seed-local.pid
```

Verificar que crece:

```bash
sleep 20
curl -sS "$ES_TARGET/_cat/indices?v&h=health,index,docs.count&s=index"
```

## Notas

`_delete_by_query` elimina documentos, pero puede no reducir inmediatamente `store.size`. Elasticsearch limpia espacio fisico despues mediante merges internos.

No usar este procedimiento contra el Elasticsearch real de produccion salvo que sea una ventana aprobada y se tenga rollback claro.
