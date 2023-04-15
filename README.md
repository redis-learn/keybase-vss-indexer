# Keybase VSS Indexer

VSS indexer to operate the Redis Knowledge Base 

## Instructions

Use the Dockerfile to create the image:

```
docker build -t keybase-vss:v1 .
```

To launch the image in a container, use the following and specify the Redis database.

```
docker run -d --cap-add sys_resource --env DB_SERVICE=<REDIS_HOST> --env DB_PORT=<REDIS_PORT> --env DB_PWD=<REDIS_PSW> --env KEYBASE_STREAM_BLOCK=<STREAM_TIMEOUT>  --env KEYBASE_VSS_LOG=<LOG_PATH> --name keybase-vss  keybase-vss:v1
```
