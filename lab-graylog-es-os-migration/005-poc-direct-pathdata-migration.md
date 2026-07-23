# 005 :: Direct `path.data` Migration Test

## Objective

Evaluate whether OpenSearch 2.15.0 can start using the existing
Elasticsearch 7.17.29 `path.data` without restoring snapshots,
reindexing or copying indices.

## Laboratory

- Ubuntu Server 24.04
- Elasticsearch 7.17.29
- OpenSearch 2.15.0
- 3-node cluster
- Graylog stopped
- MongoDB stopped
- VMware snapshots created before the test

## Procedure

1. Stop Graylog.
2. Stop Elasticsearch.
3. Install OpenSearch 2.15.0.
4. Configure OpenSearch with:
   - same cluster name
   - same node names
   - same discovery settings
   - `path.data=/var/lib/elasticsearch`
5. Change ownership of the data directory.
6. Start the three OpenSearch nodes.

## Result

FAILED

OpenSearch was unable to read the persisted cluster state created by
Elasticsearch 7.17.29.

Error:

```text
[data_stream] unknown field [_meta]
```

Stack trace:

```text
org.opensearch.core.xcontent.XContentParseException:
[data_stream] unknown field [_meta]
```

## Conclusion

The direct reuse of the Elasticsearch 7.17.29 data directory is not
supported in this laboratory.

The cluster does not start because OpenSearch 2.15.0 fails while parsing
the persisted cluster metadata.

No production migration should rely on this approach without additional
validation.

## Rollback

The laboratory was restored using VMware snapshots.