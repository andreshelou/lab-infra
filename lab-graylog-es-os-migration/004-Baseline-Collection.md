# 004 :: Baseline Collection

## Objective

Collect a complete baseline of the environment before starting the migration from Elasticsearch to OpenSearch.

The baseline will be used later to compare the environment after the migration and verify that all services continue to operate correctly.

---

## Prerequisites

- Elasticsearch cluster operational.
- Graylog cluster operational.
- MongoDB Replica Set operational.
- Test environment created as described in `003-Prepare-Test-Environment.md`.

---

## Procedure

### 4.1 Elasticsearch Baseline

Execute:

```bash
scripts/elasticsearch-collect-baseline.sh http://es01:9200 \
    | tee evidence/pre-migration/elasticsearch-baseline.txt
```

Expected result:

- Validation Summary reports all checks as **OK**.

---

### 4.2 Graylog Baseline

Execute:

```bash
scripts/graylog-collect-baseline.sh \
    | tee evidence/pre-migration/graylog-baseline.txt
```

Expected result:

- Validation Summary reports all checks as **OK**.
- Migration Test Index Set exists.
- Migration Test Stream exists.

---

### 4.3 MongoDB Baseline

Execute:

```bash
scripts/mongodb-collect-baseline.sh \
    | tee evidence/pre-migration/mongodb-baseline.txt
```

Expected result:

- Validation Summary reports all checks as **OK**.
- Replica Set healthy.
- One PRIMARY.
- Two SECONDARY members.

---

## Validation

The baseline collection is considered successful when:

- Elasticsearch baseline completed successfully.
- Graylog baseline completed successfully.
- MongoDB baseline completed successfully.
- Evidence files have been generated.