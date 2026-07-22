# Elasticsearch 7.17.29 → OpenSearch 2.15.x Migration Laboratory

## Overview

This repository documents the complete validation process for migrating an existing Elasticsearch 7.17.29 cluster used by Graylog 6.0.7 to OpenSearch 2.15.x.

The objective is to validate the migration procedure in a laboratory environment before executing the same operation in production.

The laboratory reproduces the software versions and cluster topology used in the production environment as closely as possible.

---

## Goals

- Validate the migration from Elasticsearch 7.17.29 to OpenSearch 2.15.x.
- Verify that Graylog continues operating without data loss.
- Produce a repeatable migration procedure.
- Produce a repeatable rollback procedure.
- Measure the execution time of the migration.
- Validate the complete procedure before executing it in production.

---

## Laboratory Components

| Component | Version |
|-----------|----------|
| Ubuntu Server | 24.04 LTS |
| MongoDB | 7.0.15 |
| Graylog | 6.0.7-1 |
| Elasticsearch | 7.17.29 |
| OpenSearch | 2.15.x |

---

## Repository Structure

This repository is organized according to the migration workflow.

| Document | Description |
|----------|-------------|
| 001-Overview | Repository overview |
| 002-Lab-Topology | Laboratory topology |
| 003-Test-Readiness | Prepare the laboratory before migration |
| 004-Pre-Migration | Baseline and pre-migration validation |
| 005-Migration | Elasticsearch to OpenSearch migration |
| 006-Post-Migration | Validation after migration |
| 007-Rollback | Rollback procedure |
| 008-Lessons-Learned | Notes and observations |

---

## Migration Strategy

The migration follows the Full Cluster Restart approach.

The migration consists of:

1. Preparing the laboratory.
2. Validating the Elasticsearch cluster.
3. Preparing Graylog.
4. Migrating Elasticsearch to OpenSearch.
5. Validating OpenSearch.
6. Validating Graylog.
7. Executing rollback if required.

---

## Validation Philosophy

Every procedure documented in this repository has been executed in the laboratory.

Only validated procedures are documented.

No theoretical procedures are included.

---

## Current Status

| Phase | Status |
|---------|--------|
| Laboratory deployment | Completed |
| Graylog deployment | Completed |
| Log ingestion | Completed |
| Migration validation | In Progress |
| Production execution | Pending |