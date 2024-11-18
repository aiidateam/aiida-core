# AiiDA Docker stacks

### Build images locally

To build the images, run the following command: (tested with _docker buildx_ version v0.8.2)

```bash
docker buildx bake -f docker-bake.hcl -f build.json --load
```

The build system will attempt to detect the local architecture and automatically build images for it (tested with amd64 and arm64).

You can also specify a custom platform with `--platform`, for example:

```bash
docker buildx bake -f docker-bake.hcl -f build.json --set *.platform=linux/amd64 --load
```

### Test built images locally

To test the images, run

```bash
TAG=newly-baked python -m pytest -s tests
```

### Trigger a build on ghcr.io and Dockerhub

- Only an open PR to the organization's repository will trigger a build on ghcr.io.
- A push to dockerhub is triggered when making a release on github.
