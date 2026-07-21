# server.conf

Los siguientes parámetros fueron modificados respecto de la configuración por defecto.

```properties
password_secret=<PASSWORD_SECRET>

root_password_sha2=<ROOT_PASSWORD_SHA2>

http_bind_address=0.0.0.0:9000

http_publish_uri=http://gl01:9000/

mongodb_uri=mongodb://gl01:27017,gl02:27017,gl03:27017/graylog?replicaSet=rs0

elasticsearch_hosts=http://es01:9200,http://es02:9200,http://es03:9200
```