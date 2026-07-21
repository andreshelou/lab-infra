# MongoDB 7.0.15 Replica Set

Instalación de un Replica Set MongoDB 7.0.15 compuesto por tres nodos sobre Ubuntu Server 24.04.

El procedimiento utiliza una máquina virtual inicial como plantilla. MongoDB se instala y configura en esa máquina antes de clonarla para crear los tres miembros del Replica Set.

## Arquitectura

| Host | Servicio | Rol inicial |
|---|---|---|
| gl01 | MongoDB 7.0.15 | PRIMARY |
| gl02 | MongoDB 7.0.15 | SECONDARY |
| gl03 | MongoDB 7.0.15 | SECONDARY |

Nombre del Replica Set:

```text
rs0