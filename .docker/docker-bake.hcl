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
  default = ["aiida-core-base", "aiida-core-with-services", "aiida-core-dev"]
}

function "tags" {
  params = [image]
  result = [
    "${REGISTRY}${ORGANIZATION}/${image}"
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
target "aiida-core-dev-meta" {
  tags = tags("aiida-core-dev")
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
    "MAMBA_VERSION" = "1.5.2"
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
target "aiida-core-dev" {
  inherits = ["aiida-core-dev-meta"]
  context = "aiida-core-dev"
  contexts = {
    src = ".."
    aiida-core-with-services = "target:aiida-core-with-services"
  }
  platforms = "${PLATFORMS}"
}
