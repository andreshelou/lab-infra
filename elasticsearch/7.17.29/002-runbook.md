# Runbook

> Este documento contiene únicamente los pasos de ejecución del laboratorio.

---

# Fase 1 - Ubuntu

Actualizar el sistema.

```bash
sudo apt update
sudo apt full-upgrade -y
sudo reboot
```

Instalar utilidades.

```bash
sudo apt install -y \
    curl \
    wget \
    jq \
    vim \
    htop \
    unzip \
    zip \
    net-tools
```

Verificar instalación.

```bash
hostnamectl

ip a

ip route

cat /etc/os-release

lsb_release -a
```

---

## SNAPSHOT

**Crear Snapshot 01**

```
Ubuntu Base
```

---

# Fase 2 - Elasticsearch

Agregar la clave GPG.

```bash
wget -qO - https://artifacts.elastic.co/GPG-KEY-elasticsearch \
| sudo gpg --dearmor \
-o /usr/share/keyrings/elasticsearch-keyring.gpg
```

Agregar el repositorio.

```bash
echo \
"deb [signed-by=/usr/share/keyrings/elasticsearch-keyring.gpg] https://artifacts.elastic.co/packages/7.x/apt stable main" \
| sudo tee /etc/apt/sources.list.d/elastic-7.x.list
```

Actualizar repositorios.

```bash
sudo apt update
```

Instalar Elasticsearch.

```bash
sudo apt install elasticsearch=7.17.29
```

Verificar instalación.

```bash
dpkg -l | grep elasticsearch

id elasticsearch

/usr/share/elasticsearch/jdk/bin/java --version
```

Crear directorios para el laboratorio.

```bash
mkdir -p ~/lab-infra/elasticsearch/7.17.29/configs
```

Copiar archivos de configuración.

```bash
sudo cp configs/jvm.options \
    /etc/elasticsearch/jvm.options.d/lab.options
```

```bash
sudo cp configs/elasticsearch.yml \
    /etc/elasticsearch/elasticsearch.yml
```

Habilitar el servicio.

```bash
sudo systemctl enable elasticsearch
```

**No iniciar Elasticsearch todavía.**

---

## SNAPSHOT

**Crear Snapshot 02**

```
Elasticsearch Base
```

---

# Fase 3 - Clonado

Clonar la máquina tres veces.

```
es01
es02
es03
```

---

# Fase 4 - Personalización

En cada nodo modificar únicamente los parámetros específicos.

Editar:

```
configs/elasticsearch.yml
```

Modificar:

```yaml
node.name:

es01
es02
es03
```

Editar:

```
configs/hosts
```

Contenido.

```text
192.168.1.101 es01
192.168.1.102 es02
192.168.1.103 es03
```

Copiar la configuración.

```bash
sudo cp configs/elasticsearch.yml \
    /etc/elasticsearch/elasticsearch.yml
```

```bash
sudo cp configs/hosts \
    /etc/hosts
```

Hostname.

```bash
sudo hostnamectl set-hostname es01
```

(Repetir cambiando es02 y es03 según corresponda.)

---

# Fase 5 - Arranque

Iniciar Elasticsearch.

```bash
sudo systemctl start elasticsearch
```

Verificar servicio.

```bash
systemctl status elasticsearch
```

Verificar nodo.

```bash
curl localhost:9200
```

Verificar cluster.

```bash
curl localhost:9200/_cluster/health?pretty
```

```bash
curl localhost:9200/_cat/nodes?v
```

```bash
curl localhost:9200/_cat/master?v
```

```bash
curl localhost:9200/_cat/shards?v
```

```bash
curl localhost:9200/_cat/allocation?v
```

Esperar estado:

```
GREEN
```

---

## SNAPSHOT

**Crear Snapshot 03**

```
Cluster GREEN
```

---

# Próximos laboratorios

- APIs
- CRUD
- Bulk
- Search
- Mapping
- Templates
- Aliases
- Shards
- Replicas
- Recovery
- Failover
- Migración Elasticsearch → OpenSearch