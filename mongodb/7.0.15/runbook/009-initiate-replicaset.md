# Initiate ReplicaSet

## Objetivo

Inicializar el ReplicaSet `rs0` y registrar los tres nodos que formarán parte del clúster MongoDB.

---

## Requisitos

- Los tres nodos ejecutan MongoDB correctamente.
- El servicio `mongod` se encuentra iniciado en:
  - gl01
  - gl02
  - gl03
- Existe conectividad TCP entre los tres nodos.

---

## Procedimiento

Conectarse al nodo **gl01**.

```bash
mongosh
```

---

Verificar que el ReplicaSet todavía no existe.

```javascript
rs.status()
```

Resultado esperado:

```text
MongoServerError[NotYetInitialized]: no replset config has been received
```

---

Inicializar el ReplicaSet.

```javascript
rs.initiate({
    _id: "rs0",
    members: [
        { _id: 0, host: "gl01:27017" },
        { _id: 1, host: "gl02:27017" },
        { _id: 2, host: "gl03:27017" }
    ]
})
```

Resultado esperado:

```javascript
{ ok: 1 }
```

---

## Archivos modificados

Ninguno.

La configuración del ReplicaSet queda almacenada en la base de datos interna de MongoDB.

---

## Validación

Intentar ejecutar nuevamente:

```javascript
rs.initiate()
```

Resultado esperado:

```text
MongoServerError[AlreadyInitialized]: already initialized
```

---

## Resultado esperado

El ReplicaSet queda creado correctamente y comienza el proceso automático de elección del nodo PRIMARY.

Durante algunos segundos los nodos pueden cambiar de estado mientras convergen.

---

## Checklist

- [ ] ReplicaSet inicializado.
- [ ] Configuración aceptada.
- [ ] No aparecen errores durante la creación.

---

## Próximo paso

Continuar con:

```text
010-validate-replicaset.md
```