# Laboratory Topology

## Objective

This document describes the laboratory used to validate the migration from Elasticsearch 7.17.29 to OpenSearch 2.15.x.

The goal of the laboratory is to reproduce, as closely as possible, the production environment while remaining simple enough to rebuild from scratch.

---

# Infrastructure

The laboratory is composed of three independent clusters.

| Component | Nodes |
|----------|------:|
| MongoDB Replica Set | 3 |
| Elasticsearch Cluster | 3 |
| Graylog Cluster | 3 |

All servers run Ubuntu Server 24.04 LTS.

---

# Software Versions

| Component | Version |
|----------|----------|
| Ubuntu Server | 24.04 LTS |
| MongoDB | 7.0.15 |
| Graylog | 6.0.7-1 |
| Elasticsearch | 7.17.29 |
| OpenSearch | 2.15.x (Target) |

---

# Cluster Topology

## MongoDB

| Host | Role |
|------|------|
| gl01 | PRIMARY / Graylog |
| gl02 | SECONDARY / Graylog |
| gl03 | SECONDARY / Graylog |

Replica Set

```
rs0
```

---

## Elasticsearch

| Host | Role |
|------|------|
| es01 | Master + Data |
| es02 | Master + Data |
| es03 | Master + Data |

Cluster Health

```
GREEN
```

---

## Graylog

| Host | Role |
|------|------|
| gl01 | Graylog Server |
| gl02 | Graylog Server |
| gl03 | Graylog Server |

Load Balancer

```
Not used
```

---

# Log Flow

The laboratory receives Syslog messages over UDP.

```
Linux Host
     │
     │ UDP 1514
     ▼
 Graylog Input
     │
     ▼
 Journal
     │
     ▼
 Elasticsearch
```

After the migration, only the backend changes.

```
Linux Host
     │
     ▼
 Graylog
     │
     ▼
 Journal
     │
     ▼
 OpenSearch
```

No changes are required on the log sources.

---

# Validation Data

The laboratory continuously generates Syslog messages.

The generated logs are used to validate:

- Continuous ingestion
- Searches
- Streams
- Index Sets
- Dashboard updates
- Index rotation
- Data preservation after migration

---

# Migration Scope

Only the search backend is migrated.

The following components remain unchanged:

- Ubuntu
- MongoDB
- Graylog configuration
- Inputs
- Streams
- Dashboards
- Users
- Pipelines

Only Elasticsearch is replaced by OpenSearch.

---

# Success Criteria

The migration is considered successful if:

- OpenSearch cluster reaches GREEN state.
- Graylog starts successfully.
- Log ingestion resumes.
- Existing data remains searchable.
- New indices are created successfully.
- Streams continue routing messages correctly.
- Dashboards continue displaying data.