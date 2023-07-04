# docker-bake.hcl
variable "VERSION" {
}

variable "PYTHON_VERSION" {
}

variable "PGSQL_VERSION" {
}

variable "ORGANIZATION" {
  default = "aiidateam"
}

variable "REGISTRY" {
  default = "docker.io/"
}

variable "PLATFORMS" {
  default = ["linux/amd64"]
}

variable "TARGETS" {
  default = ["base", "base-with-services"]
}

function "tags" {
  params = [image]
  result = [
    "${REGISTRY}${ORGANIZATION}/${image}:latest",
    "${REGISTRY}${ORGANIZATION}/${image}:newly-build"
  ]
}

group "default" {
  targets = "${TARGETS}"
}

target "base-meta" {
  tags = tags("base")
}
target "base-with-services-meta" {
  tags = tags("aiida-core")
}

target "base" {
  inherits = ["base-meta"]
  context = "base"
  contexts = {
    src = ".."
  }
  platforms = "${PLATFORMS}"
  args = {
    "PYTHON_VERSION" = "${PYTHON_VERSION}"
  }
}
target "base-with-services" {
  inherits = ["base-with-services-meta"]
  context = "base-with-services"
  contexts = {
    base = "target:base"
  }
  platforms = "${PLATFORMS}"
  args = {
    "PGSQL_VERSION" = "${PGSQL_VERSION}"
  }
}
