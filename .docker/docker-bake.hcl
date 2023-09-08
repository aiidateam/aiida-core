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
  default = ["aiida-core-base", "aiida-core-with-services"]
}

function "tags" {
  params = [image]
  result = [
    "${REGISTRY}${ORGANIZATION}/${image}:newly-baked"
  ]
}

group "default" {
  targets = "${TARGETS}"
}

target "aiida-core-base-meta" {
  tags = tags("aiida-core-base")
}
target "aiida-core-with-services-meta" {
  tags = tags("aiida-core-with-services")
}

target "aiida-core-base" {
  inherits = ["aiida-core-base-meta"]
  context = "aiida-core-base"
  contexts = {
    src = ".."
  }
  platforms = "${PLATFORMS}"
  args = {
    "PYTHON_VERSION" = "${PYTHON_VERSION}"
  }
}
target "aiida-core-with-services" {
  inherits = ["aiida-core-with-services-meta"]
  context = "aiida-core-with-services"
  contexts = {
    aiida-core-base = "target:aiida-core-base"
  }
  platforms = "${PLATFORMS}"
  args = {
    "PGSQL_VERSION" = "${PGSQL_VERSION}"
    "RMQ_VERSION" = "${RMQ_VERSION}"
  }
}
