# Estrategia de migración Graylog + Elasticsearch → OpenSearch (sin Remote Reindex)

## Objetivo

Migrar el backend de Graylog desde Elasticsearch hacia OpenSearch sin mover los datos históricos.

La estrategia aprovecha la retención natural de los índices (10 días) para mantener un entorno histórico temporal mientras toda la información nueva comienza a almacenarse en OpenSearch.

---

# Fase 1 - Preparación

## 1. Preparar OpenSearch

Antes de la ventana de mantenimiento:

- Instalar OpenSearch.
- Configurar el cluster.
- Crear los índices vacíos.
- Replicar templates, mappings, settings y aliases desde Elasticsearch.
- Validar que el backend esté completamente operativo.

---

## 2. Respaldar la configuración

Guardar:

- Configuración de Graylog.
- Configuración de MongoDB.
- Configuración del F5.

---

# Fase 2 - Corte

## 3. Detener la ingesta

Desde el F5:

- Deshabilitar la recepción de logs.
- Esperar a que desaparezcan las conexiones activas.
- Verificar que el Journal de Graylog quede vacío.

---

## 4. Detener Graylog

Apagar los tres nodos de Graylog.

MongoDB y Elasticsearch permanecen operativos.

---

## 5. Respaldar MongoDB

Con Graylog detenido:

- Verificar el estado del ReplicaSet.
- Ejecutar el backup lógico de MongoDB.

Este backup representa exactamente el estado del sistema en el momento del corte.

---

# Fase 3 - Puesta en marcha del nuevo entorno

## 6. Reconfigurar Graylog

Modificar únicamente los nodos:

- GL02
- GL03

para que utilicen OpenSearch como backend.

No modificar MongoDB.

---

## 7. Iniciar el nuevo cluster

Levantar:

- GL02
- GL03

Validar:

- Inicio correcto.
- Acceso Web.
- Búsquedas.
- Streams.
- Pipelines.
- Recepción de logs de prueba.
- Creación y utilización correcta de los índices.

---

## 8. Reanudar la ingesta

Si todas las validaciones son satisfactorias:

- Rehabilitar la ingesta desde el F5.
- Mantener únicamente GL02 y GL03 dentro del pool de balanceo.

A partir de este momento toda la información nueva queda almacenada en OpenSearch.

---

# Fase 4 - Construcción del entorno histórico

Esta etapa ya no forma parte del camino crítico de la migración.

Puede realizarse con tranquilidad una vez validado el nuevo entorno.

---

## 9. Crear una nueva instancia MongoDB

En GL01:

- Crear una nueva instancia de MongoDB.
- Crear un ReplicaSet independiente de un solo nodo.

---

## 10. Restaurar el backup

Importar el backup realizado anteriormente.

Validar:

- Usuarios.
- Streams.
- Dashboards.
- Pipelines.
- Index Sets.
- Configuración general.

---

## 11. Configurar Graylog histórico

Modificar GL01 para que utilice:

- El nuevo ReplicaSet de MongoDB.
- Elasticsearch como backend.

---

## 12. Iniciar Graylog histórico

Levantar GL01.

Validar:

- Inicio correcto.
- Login.
- Búsquedas históricas.
- Dashboards.
- Streams.

---

# Fase 5 - Publicación

## 13. Crear un acceso histórico

Publicar una nueva URL mediante el F5.

El nuevo portal utilizará únicamente GL01 y permitirá consultar exclusivamente la información histórica almacenada en Elasticsearch.

---

# Estado final temporal

## Portal principal

- GL02
- GL03
- OpenSearch

Recibe toda la ingesta nueva.

---

## Portal histórico

- GL01
- MongoDB independiente
- Elasticsearch

Disponible únicamente para consultas históricas.

---

# Estado final definitivo

Una vez vencida la retención de Elasticsearch:

- Apagar el entorno histórico.
- Eliminar Elasticsearch.
- Reincorporar GL01 al cluster principal.
- Configurar GL01 para utilizar OpenSearch.
- Incorporarlo nuevamente al pool del F5.

Finalmente el entorno vuelve a quedar compuesto por:

- GL01
- GL02
- GL03

utilizando un único backend OpenSearch.