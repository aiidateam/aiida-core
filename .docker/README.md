# AiiDA docker stacks

### Build images locally

To build the images, run `doit build` (tested with *docker buildx* version v0.8.2).

The build system will attempt to detect the local architecture and automatically build images for it (tested with amd64 and arm64).
All commands `build`, `tests`, and `up` will use the locally detected platform and use a version tag based on the state of the local git repository.
However, you can also specify a custom platform or version with the `--platform` and `--version` parameters, example: `doit build --arch=amd64 --version=my-version`.

You can specify target stacks to build with `--target`, example: `doit build --target base --target base`.
