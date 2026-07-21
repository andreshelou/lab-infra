# Validate ReplicaSet

## Objetivo

Verificar que los tres nodos forman correctamente el ReplicaSet y que el proceso de elección automática finalizó exitosamente.

Además, comprobar que las operaciones de escritura realizadas sobre el nodo PRIMARY se replican correctamente hacia los nodos SECONDARY.

---

## Requisitos

- ReplicaSet inicializado.
- Los tres nodos ejecutando MongoDB.

---

## Procedimiento

Conectarse al nodo **gl01**.

```bash
mongosh
```

---

Verificar el estado general del ReplicaSet.

```javascript
rs.status()
```

---

Obtener un resumen del estado de los miembros.

```javascript
rs.status().members.map(member => ({
  name: member.name,
  state: member.stateStr,
  health: member.health
}))
```

Resultado esperado:

```javascript
[
  { name: 'gl01:27017', state: 'PRIMARY', health: 1 },
  { name: 'gl02:27017', state: 'SECONDARY', health: 1 },
  { name: 'gl03:27017', state: 'SECONDARY', health: 1 }
]
```

---

Verificar la configuración almacenada.

```javascript
rs.conf()
```

---

Verificar que el nodo actual es el PRIMARY.

```javascript
db.hello()
```

Resultado esperado:

```javascript
isWritablePrimary: true
```

---

## Validar replicación

Conectarse al nodo **PRIMARY (gl01)**.

Seleccionar una base de datos de prueba.

```javascript
use labtest
```

Insertar un documento.

```javascript
db.replication.insertOne({
    test: "mongodb-replication",
    createdAt: new Date()
})
```

Resultado esperado:

```javascript
{
    acknowledged: true,
    insertedId: ObjectId(...)
}
```

---

Conectarse al nodo **gl02**.

```bash
mongosh --host gl02
```

Verificar que se trata de un nodo SECONDARY.

```javascript
db.hello().secondary
```

Resultado esperado:

```javascript
true
```

Habilitar lectura desde el nodo secundario.

```javascript
rs.secondaryOk()
```

Seleccionar la base de datos de prueba.

```javascript
use labtest
```

Consultar los documentos.

```javascript
db.replication.find().pretty()
```

Resultado esperado:

```javascript
{
    _id: ObjectId(...),
    test: "mongodb-replication",
    createdAt: ISODate(...)
}
```

La presencia del documento confirma que la replicación entre los miembros del ReplicaSet funciona correctamente.

---

Eliminar los datos de prueba desde el nodo PRIMARY (`gl01`).

```javascript
use labtest
```

```javascript
db.dropDatabase()
```

Resultado esperado:

```javascript
{ ok: 1, dropped: "labtest" }
```

---

## Archivos modificados

Ninguno.

---

## Resultado esperado

El ReplicaSet queda completamente operativo.

- gl01 actúa como PRIMARY.
- gl02 actúa como SECONDARY.
- gl03 actúa como SECONDARY.
- Todos los miembros presentan `health: 1`.
- Las operaciones de escritura realizadas sobre el PRIMARY son replicadas automáticamente hacia los nodos SECONDARY.

Las advertencias relacionadas con el sistema de archivos XFS o con la autenticación deshabilitada son esperables en este laboratorio y no afectan el funcionamiento del ReplicaSet.

---

## Checklist

- [ ] Un nodo PRIMARY.
- [ ] Dos nodos SECONDARY.
- [ ] Todos los miembros con `health: 1`.
- [ ] Replicación validada mediante inserción de un documento.
- [ ] Datos de prueba eliminados.

---

## Próximo paso

Continuar con la instalación y configuración de Graylog.