# origin-haproxy-router

## Build image
```
docker build --build-arg HAPROXY_VERSION=1.8.25 -t origin-haproxy-router:latest .
docker run --volume ./haproxy:/builder --rm origin-haproxy-router:latest
```
