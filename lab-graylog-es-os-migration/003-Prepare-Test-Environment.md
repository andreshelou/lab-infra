# Prepare Test Environment

## Document Information

| Item | Value |
|------|-------|
| Status | In Progress |
| Tested | Partially |
| Tested On | Ubuntu 24.04 |
| Elasticsearch | 7.17.29 |
| Graylog | 6.0.7-1 |
| MongoDB | 7.0.15 |

---

# Step 1 - Create and Validate the Test Data Generator

## Objective

Create a continuous Syslog message generator that will be used throughout the migration validation.

The generated messages must be easy to identify in Graylog and must contain enough information to distinguish them from other logs.

---

## Script

The generator is located at:

```text
scripts/test-data/generate-syslog.sh
```

---

## Usage

```bash
./scripts/test-data/generate-syslog.sh <graylog_host> <port>
```

Example:

```bash
./scripts/test-data/generate-syslog.sh gl01 1514
```

The script requires:

- Graylog hostname or IP address
- Syslog UDP port

If the required parameters are not provided, the script displays its usage information and exits with an error.

Help can be displayed with:

```bash
./scripts/test-data/generate-syslog.sh --help
```

---

## Generated Message Format

The script continuously generates messages using the following format:

```text
LAB-MIGRATION sequence=<number> hostname=<host> timestamp=<timestamp>
```

Example:

```text
LAB-MIGRATION sequence=125 hostname=slk timestamp=2026-07-22T18:51:03-03:00
```

---

## Validation Procedure

1. Start the generator.

```bash
./scripts/test-data/generate-syslog.sh <graylog_host> 1514
```

2. Open the Graylog web interface.

3. Go to:

```text
Search
```

4. Select a recent time range, such as:

```text
Last 5 minutes
```

5. Search for:

```text
LAB-MIGRATION
```

---

## Expected Result

- One new message is received every second.
- Messages contain the `LAB-MIGRATION` prefix.
- Sequence numbers increase continuously.
- The source hostname is visible.
- The timestamp is correct.
- Messages are searchable from Graylog.

---

## Validation Result

| Validation | Status |
|------------|--------|
| Script starts successfully | Completed |
| Required parameters are validated | Completed |
| Syslog messages are sent over UDP | Completed |
| Messages are received by Graylog | Completed |
| Messages are searchable | Completed |
| Sequence numbers increase | Completed |
| Timestamp is correct | Completed |

---

## Status

Step validated successfully.