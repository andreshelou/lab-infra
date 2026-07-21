# Graylog 6.0.7 - Plan de implementación

## Objetivo

Implementar una plataforma Graylog 6.0.7 distribuida sobre tres nodos Ubuntu Server 24.04.

Los nodos Graylog utilizarán el ReplicaSet MongoDB `rs0`, previamente instalado y validado sobre los mismos servidores.

La plataforma utilizará inicialmente Elasticsearch 7.17.29 como backend de búsqueda y almacenamiento de índices.

Al finalizar el procedimiento, los tres nodos Graylog deberán estar operativos, conectados al mismo ReplicaSet de MongoDB y al mismo cluster de Elasticsearch.

## Arquitectura

La plataforma estará compuesta por tres nodos:

| Nodo | Sistema operativo | Graylog | MongoDB |
|---|---|---:|---|
| `gl01` | Ubuntu Server 24.04 | 6.0.7 | 7.0.15 |
| `gl02` | Ubuntu Server 24.04 | 6.0.7 | 7.0.15 |
| `gl03` | Ubuntu Server 24.04 | 6.0.7 | 7.0.15 |

MongoDB se encuentra configurado como un ReplicaSet:

| Nodo | Estado MongoDB |
|---|---|
| `gl01` | PRIMARY |
| `gl02` | SECONDARY |
| `gl03` | SECONDARY |

El ReplicaSet utilizado es:

```text
rs0