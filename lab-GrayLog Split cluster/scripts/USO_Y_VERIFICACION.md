# Uso Y Verificacion De La Herramienta ES -> OS

## 1. Objetivo De Esta Guia

Esta guia describe como usar los scripts Python incluidos en `es2os_scripts/` para preparar una migracion desde Elasticsearch `7.17.29` hacia OpenSearch `2.15.0`.

Los comandos de descubrimiento y generacion son seguros contra Elasticsearch: solo usan `GET`.

Los comandos que podrian escribir en OpenSearch requieren `--execute`. Sin ese flag imprimen lo que harian en modo dry-run.

## 2. Requisitos

Python recomendado:

```bash
python3 --version
```

Version recomendada:

```text
Python 3.9+
```

Instalacion de dependencias:

```bash
python3 -m pip install -r es2os_scripts/requirements.txt
```

Actualmente no hay dependencias externas obligatorias; el archivo `requirements.txt` queda como referencia operativa.

## 3. Archivos Principales

```text
PROPUESTA_MIGRACION_ES_OS_GRAYLOG.md
USO_Y_VERIFICACION.md
es2os_scripts/
  es2os.py
  requirements.txt
  config.example.json
```

## 4. Descubrir Indices

```bash
python3 es2os_scripts/es2os.py discover \
  --source http://ptyesnp01.itspty.dom:9200 \
  --output ./out \
  --exclude-internal
```

Salida esperada:

```text
out/discovery/indices.json
out/reports/summary.json
```

Validar:

```bash
python3 -m json.tool out/discovery/indices.json >/dev/null
python3 -m json.tool out/reports/summary.json >/dev/null
```

## 5. Generar Payloads Para OpenSearch

```bash
python3 es2os_scripts/es2os.py generate-payloads \
  --source http://ptyesnp01.itspty.dom:9200 \
  --target-version 2.15 \
  --output ./out \
  --exclude-internal \
  --aliases-mode separate
```

Salida esperada:

```text
out/payloads/<index>.create.json
out/reports/<index>.report.json
out/aliases/aliases-plan.json
out/reports/summary.json
```

Validar un payload:

```bash
python3 -m json.tool out/payloads/graylog_3411.create.json >/dev/null
```

Revisar que no existan campos prohibidos:

```bash
python3 es2os_scripts/es2os.py scan-payloads --payloads ./out/payloads
```

## 6. Validar Contra OpenSearch De Prueba

Este paso contacta OpenSearch destino. Sin `--execute`, no crea nada.

Dry-run:

```bash
python3 es2os_scripts/es2os.py validate \
  --target http://OPENSEARCH_HOST:9200 \
  --payloads ./out/payloads
```

Validacion real con indices temporales:

```bash
python3 es2os_scripts/es2os.py validate \
  --target http://OPENSEARCH_HOST:9200 \
  --payloads ./out/payloads \
  --execute
```

La validacion real crea indices temporales con prefijo `validate_` y los elimina al finalizar.

## 7. Crear Indices En OpenSearch

Dry-run:

```bash
python3 es2os_scripts/es2os.py create-indices \
  --target http://OPENSEARCH_HOST:9200 \
  --payloads ./out/payloads
```

Ejecucion real:

```bash
python3 es2os_scripts/es2os.py create-indices \
  --target http://OPENSEARCH_HOST:9200 \
  --payloads ./out/payloads \
  --execute
```

## 8. Remote Reindex

Antes de ejecutar Remote Reindex, configurar OpenSearch:

```yaml
reindex.remote.whitelist: "ptyesnp01.itspty.dom:9200"
```

O, segun la distribucion:

```yaml
reindex.remote.allowlist: "ptyesnp01.itspty.dom:9200"
```

Dry-run:

```bash
python3 es2os_scripts/es2os.py remote-reindex \
  --source http://ptyesnp01.itspty.dom:9200 \
  --target http://OPENSEARCH_HOST:9200 \
  --indices ./out/discovery/indices.json
```

Ejecucion real:

```bash
python3 es2os_scripts/es2os.py remote-reindex \
  --source http://ptyesnp01.itspty.dom:9200 \
  --target http://OPENSEARCH_HOST:9200 \
  --indices ./out/discovery/indices.json \
  --execute
```

## 9. Comparar Conteos

```bash
python3 es2os_scripts/es2os.py compare-counts \
  --source http://ptyesnp01.itspty.dom:9200 \
  --target http://OPENSEARCH_HOST:9200 \
  --indices ./out/discovery/indices.json
```

El criterio minimo es:

```text
_count origen == _count destino
```

## 10. Aplicar Aliases

Dry-run:

```bash
python3 es2os_scripts/es2os.py apply-aliases \
  --target http://OPENSEARCH_HOST:9200 \
  --aliases-plan ./out/aliases/aliases-plan.json
```

Ejecucion real:

```bash
python3 es2os_scripts/es2os.py apply-aliases \
  --target http://OPENSEARCH_HOST:9200 \
  --aliases-plan ./out/aliases/aliases-plan.json \
  --execute
```

## 11. Orden De Prueba Recomendado

```text
1. Crear OpenSearch 2.15.0 vacio.
2. Configurar remote reindex allowlist/whitelist.
3. Ejecutar discover.
4. Ejecutar generate-payloads.
5. Revisar summary y reportes.
6. Validar payloads contra OpenSearch de prueba.
7. Crear solo 3 o 4 indices representativos.
8. Ejecutar Remote Reindex solo para esos indices.
9. Comparar conteos.
10. Probar busquedas.
11. Aplicar aliases en prueba.
12. Repetir con todos los indices.
```

Indices sugeridos para prueba inicial:

```text
gl-events_69
gl-system-events_48
qa_index_719
graylog_3411
```

## 12. Cutover A Produccion

```text
1. Mantener Graylog apuntando a Elasticsearch.
2. Crear indices en OpenSearch.
3. Ejecutar Remote Reindex historico.
4. Comparar conteos.
5. Programar ventana de corte.
6. Pausar ingesta o detener Graylog.
7. Ejecutar delta final si corresponde.
8. Aplicar aliases deflector en OpenSearch.
9. Cambiar Graylog a OpenSearch.
10. Arrancar Graylog.
11. Validar busquedas e ingesta.
12. Mantener Elasticsearch disponible para rollback.
```

## 13. Rollback

Si falla despues de redireccionar Graylog:

```text
1. Detener Graylog.
2. Cambiar Graylog nuevamente hacia Elasticsearch.
3. Arrancar Graylog.
4. Validar busquedas.
5. Validar ingesta.
6. Investigar OpenSearch en paralelo.
```

Mantener Elasticsearch intacto al menos 24-72 horas despues del cutover.
