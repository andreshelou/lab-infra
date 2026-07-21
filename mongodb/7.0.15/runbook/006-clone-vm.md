# Clone Virtual Machines

## Objetivo

Crear los tres nodos del laboratorio a partir de la máquina virtual base preparada con MongoDB 7.0.15.

---

## Requisitos

- Máquina virtual base preparada.
- MongoDB 7.0.15 instalado.
- Configuración de MongoDB validada.
- Servicio `mongod` detenido y deshabilitado.
- Snapshot interno creado con la máquina virtual apagada.

---

## Procedimiento

Con la máquina virtual base apagada, crear dos clones completos.

Los nombres utilizados en este laboratorio son:

```text
gl01
gl02
gl03
```

La máquina virtual original se conserva como:

```text
gl01
```

Crear los siguientes clones:

```text
gl02
gl03
```

Iniciar cada máquina virtual individualmente para verificar que el sistema operativo arranca correctamente.

Una vez validado el arranque, apagar nuevamente las tres máquinas.

En este punto no se modifica todavía:

- `/etc/hostname`
- `/etc/hosts`
- la configuración de red
- `/etc/mongod.conf`
- el estado del servicio `mongod`

---

## Archivos modificados

Ninguno dentro del sistema operativo.

---

## Validación

Verificar que existen las tres máquinas virtuales:

```text
gl01
gl02
gl03
```

Verificar que las tres pueden iniciar correctamente.

Después de la validación, confirmar que las tres quedaron apagadas.

---

## Resultado esperado

El laboratorio dispone de tres máquinas virtuales idénticas:

```text
gl01
gl02
gl03
```

Las tres máquinas arrancan correctamente y permanecen apagadas al finalizar el procedimiento.

---

## Checklist

- [ ] El snapshot de la máquina base fue creado.
- [ ] Existe la máquina virtual `gl01`.
- [ ] Se creó el clon `gl02`.
- [ ] Se creó el clon `gl03`.
- [ ] Las tres máquinas arrancaron correctamente.
- [ ] Las tres máquinas quedaron apagadas.

---

## Próximo paso

Continuar con:

```text
007-configure-node.md
```