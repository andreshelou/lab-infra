# MongoDB 7.0.15 Replica Set

## Objetivo

Construir un Replica Set MongoDB compuesto por tres nodos utilizando Ubuntu Server 24.04 y MongoDB Community Server 7.0.15.

El resultado será un cluster tolerante a fallos que será utilizado posteriormente por Graylog como base de datos para su configuración y metadatos.

---

## Arquitectura

| Host | Servicio | Rol |
|------|----------|-----|
| gl01 | MongoDB | PRIMARY |
| gl02 | MongoDB | SECONDARY |
| gl03 | MongoDB | SECONDARY |

Replica Set:

```text
rs0
```

Puerto:

```text
27017/tcp
```

---

## Componentes

| Componente | Versión |
|------------|----------|
| Ubuntu Server | 24.04 LTS |
| MongoDB Community | 7.0.15 |

---

## Topología

```text
                +----------------+
                |     gl01       |
                |   MongoDB      |
                |   PRIMARY      |
                +-------+--------+
                        |
        ----------------+----------------
        |                               |
        |                               |
+-------+--------+              +-------+--------+
|     gl02       |              |     gl03       |
|   MongoDB      |              |   MongoDB      |
|  SECONDARY     |              |  SECONDARY     |
+----------------+              +----------------+
```

---

## Estrategia de despliegue

La instalación se realizará en cinco etapas.

### Etapa 1

Preparación de una máquina virtual base con Ubuntu Server 24.04.

---

### Etapa 2

Instalación y configuración de MongoDB 7.0.15.

En esta etapa el Replica Set todavía no será inicializado.

---

### Etapa 3

Creación de un snapshot de la máquina base.

La VM será utilizada como origen para generar los tres nodos del cluster.

---

### Etapa 4

Clonación de la VM.

Se crearán:

```text
gl01
gl02
gl03
```

Cada nodo será personalizado modificando:

- hostname
- dirección IP
- configuración de red
- resolución local de nombres

---

### Etapa 5

Inicialización del Replica Set.

Se verificará:

- elección de PRIMARY
- sincronización de SECONDARY
- estado HEALTHY de los tres miembros

---

## Archivos de configuración

Los archivos utilizados durante la instalación se encuentran en:

```text
configs/
```

Contenido:

```text
mongod.conf
hosts
rs-init.js
```

Los archivos del repositorio representan la configuración final esperada.

Durante el procedimiento cada archivo será editado manualmente en el servidor correspondiente.

---

## Snapshots

Se recomienda crear snapshots en los siguientes puntos.

### Snapshot 01

Sistema operativo completamente preparado.

---

### Snapshot 02

MongoDB instalado y configurado.

Antes de clonar la máquina.

---

### Snapshot 03

Replica Set completamente operativo.

---

## Resultado esperado

```text
gl01
└── MongoDB
    └── PRIMARY

gl02
└── MongoDB
    └── SECONDARY

gl03
└── MongoDB
    └── SECONDARY
```

El Replica Set quedará disponible para la posterior instalación de Graylog.