# Configure Nodes

## Objetivo

Asignar una identidad única a cada nodo del laboratorio mediante la configuración del hostname, la dirección IP y la resolución local de nombres.

Este procedimiento debe realizarse en:

```text
gl01
gl02
gl03
```

---

## Requisitos

- Las tres máquinas virtuales fueron creadas.
- Las tres máquinas arrancan correctamente.
- MongoDB permanece detenido y deshabilitado.

---

## Configuración del laboratorio

| Nodo | Dirección IP |
|------|--------------|
| gl01 | 192.168.122.101 |
| gl02 | 192.168.122.102 |
| gl03 | 192.168.122.103 |

---

## Procedimiento

### Configurar el hostname

En cada nodo, asignar el hostname correspondiente.

En `gl01`:

```bash
sudo hostnamectl set-hostname gl01
```

En `gl02`:

```bash
sudo hostnamectl set-hostname gl02
```

En `gl03`:

```bash
sudo hostnamectl set-hostname gl03
```

---

### Configurar `/etc/hosts`

Editar:

```text
/etc/hosts
```

Dejar el siguiente contenido en los tres nodos:

```text
127.0.0.1 localhost
127.0.1.1 localhost.localdomain

192.168.122.101 gl01
192.168.122.102 gl02
192.168.122.103 gl03
```

---

### Identificar el archivo de Netplan

```bash
ls -l /etc/netplan/
```

Editar el archivo YAML existente dentro de:

```text
/etc/netplan/
```

La configuración debe conservar el nombre real de la interfaz de red presente en cada máquina virtual.

---

### Configurar la dirección IP de `gl01`

Ejemplo:

```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: false
      addresses:
        - 192.168.122.101/24
      routes:
        - to: default
          via: 192.168.122.1
      nameservers:
        addresses:
          - 192.168.122.1
```

---

### Configurar la dirección IP de `gl02`

```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: false
      addresses:
        - 192.168.122.102/24
      routes:
        - to: default
          via: 192.168.122.1
      nameservers:
        addresses:
          - 192.168.122.1
```

---

### Configurar la dirección IP de `gl03`

```yaml
network:
  version: 2
  ethernets:
    enp1s0:
      dhcp4: false
      addresses:
        - 192.168.122.103/24
      routes:
        - to: default
          via: 192.168.122.1
      nameservers:
        addresses:
          - 192.168.122.1
```

> **Nota**
>
> El nombre `enp1s0`, la puerta de enlace y el servidor DNS son ejemplos.
> Deben reemplazarse por los valores reales del laboratorio.

---

### Validar la sintaxis de Netplan

```bash
sudo netplan generate
```

Si no se muestran errores, aplicar la configuración:

```bash
sudo netplan apply
```

---

### Reiniciar cada nodo

```bash
sudo reboot
```

---

## Archivos modificados

```text
/etc/hostname
/etc/hosts
/etc/netplan/<archivo>.yaml
```

El archivo de referencia para `/etc/hosts` debe ubicarse en:

```text
configs/hosts
```

---

## Validación

### Verificar el hostname

```bash
hostnamectl
```

En cada nodo debe mostrarse el hostname correspondiente:

```text
gl01
```

```text
gl02
```

```text
gl03
```

---

### Verificar la dirección IP

```bash
ip -br address
```

Cada nodo debe mostrar su dirección correspondiente:

```text
192.168.122.101
192.168.122.102
192.168.122.103
```

---

### Verificar la resolución de nombres

Desde `gl01`:

```bash
getent hosts gl02
getent hosts gl03
```

Desde `gl02`:

```bash
getent hosts gl01
getent hosts gl03
```

Desde `gl03`:

```bash
getent hosts gl01
getent hosts gl02
```

---

### Verificar conectividad

Desde cada nodo, validar la comunicación con los otros dos.

Ejemplo desde `gl01`:

```bash
ping -c 3 gl02
ping -c 3 gl03
```

---

### Verificar el estado de MongoDB

```bash
systemctl is-enabled mongod
systemctl is-active mongod
```

Resultado esperado:

```text
disabled
inactive
```

---

## Resultado esperado

Cada máquina virtual posee:

- un hostname único;
- una dirección IP fija;
- resolución local para los tres nodos;
- conectividad con los otros nodos.

MongoDB continúa detenido y deshabilitado.

---

## Checklist

- [ ] `gl01` tiene el hostname correcto.
- [ ] `gl02` tiene el hostname correcto.
- [ ] `gl03` tiene el hostname correcto.
- [ ] `gl01` utiliza `192.168.122.101`.
- [ ] `gl02` utiliza `192.168.122.102`.
- [ ] `gl03` utiliza `192.168.122.103`.
- [ ] `/etc/hosts` contiene los tres nodos.
- [ ] Los nombres se resuelven correctamente.
- [ ] Existe conectividad entre los tres nodos.
- [ ] MongoDB permanece deshabilitado.
- [ ] MongoDB permanece inactivo.

---

## Próximo paso

Continuar con:

```text
008-start-mongodb.md
```