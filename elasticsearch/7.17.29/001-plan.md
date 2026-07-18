# Elasticsearch 7.17.29 Lab

> Laboratorio reproducible para aprender Elasticsearch 7.17.29 y validar la migración hacia OpenSearch 2.15 sobre Ubuntu Server 24.04 LTS.

---

# Objetivos

Este laboratorio tiene como objetivos:

- Aprender Elasticsearch desde cero.
- Construir un clúster de tres nodos.
- Comprender el funcionamiento interno del motor.
- Aprender las APIs principales.
- Realizar pruebas de fallos.
- Validar la migración Elasticsearch → OpenSearch.

---

# Arquitectura

```
                 +----------------+
                 |     es01       |
                 | Master/Data    |
                 +----------------+
                     /        \
                    /          \
                   /            \
      +----------------+    +----------------+
      |     es02       |    |     es03       |
      | Master/Data    |    | Master/Data    |
      +----------------+    +----------------+
```

Los tres nodos tendrán los roles por defecto de Elasticsearch.

---

# Requisitos

- Ubuntu Server 24.04 LTS
- 3 máquinas virtuales
- 2 GB de RAM por nodo
- Acceso SSH
- Internet para descargar paquetes

---

# Fase 1

## Preparación de Ubuntu

- Instalar Ubuntu Server.
- Actualizar el sistema.
- Instalar herramientas básicas.

Al finalizar esta fase se debe crear el siguiente snapshot:

> **Snapshot 01 - Ubuntu Base**

Este snapshot representa una instalación limpia completamente actualizada.

---

# Fase 2

## Instalación de Elasticsearch

- Agregar el repositorio oficial.
- Instalar Elasticsearch 7.17.29.
- Configurar el heap.
- Configurar elasticsearch.yml.
- Habilitar el servicio.

**No iniciar Elasticsearch todavía.**

Al finalizar esta fase crear:

> **Snapshot 02 - Elasticsearch Base**

Este snapshot será utilizado para clonar rápidamente nuevos nodos.

---

# Fase 3

## Clonado

A partir del snapshot anterior crear tres máquinas.

```
es01
es02
es03
```

Cada una recibirá:

- Hostname
- Dirección IP
- Configuración de cluster

---

# Fase 4

## Construcción del Cluster

Configurar:

- hostname
- /etc/hosts
- elasticsearch.yml

Iniciar Elasticsearch en los tres nodos.

Verificar:

- Cluster Health
- Nodes
- Master
- Shards
- Allocation

Cuando el estado sea **GREEN**, crear:

> **Snapshot 03 - Cluster GREEN**

Este snapshot representa el punto de partida para todos los laboratorios posteriores.