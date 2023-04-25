# docker-bake.hcl
variable "VERSION" {
}

variable "PYTHON_VERSION" {
}

variable "PGSQL_VERSION" {
}

variable "BASE_IMAGE" {
  default = "jupyter/minimal-notebook:python-${PYTHON_VERSION}" 
}

variable "ORGANIZATION" {
  default = "aiidateam"
}

variable "REGISTRY" {
  default = "docker.io/"
}

variable "PLATFORMS" {
  default = ["linux/amd64", "linux/arm64"]
}

variable "TARGETS" {
  default = ["base", "base-with-services"]
}

function "tags" {
  params = [image]
  result = [
    "${REGISTRY}${ORGANIZATION}/${image}:${VERSION}",
    "${REGISTRY}${ORGANIZATION}/${image}:python-${PYTHON_VERSION}",
    "${REGISTRY}${ORGANIZATION}/${image}:postgresql-${PGSQL_VERSION}",
  ]
}

group "default" {
  targets = "${TARGETS}"
}

target "base-meta" {
  tags = tags("base")
}
target "base-with-services-meta" {
  tags = tags("base-with-services")
}

target "base" {
  inherits = ["base-meta"]
  context = "stack/base"
  platforms = "${PLATFORMS}"
  args = {
    "BASE" = "${BASE_IMAGE}"
  }
}
target "base-with-services" {
  inherits = ["base-with-services-meta"]
  context = "stack/base-with-services"
  contexts = {
    base = "target:base"
  }
  platforms = "${PLATFORMS}"
  args = {
    "PGSQL_VERSION" = "${PGSQL_VERSION}"
  }
}