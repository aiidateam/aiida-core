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

target "aiida-core-base" {
  tags = tags("aiida-core-base")
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
  tags = tags("aiida-core-with-services")
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
  tags = tags("aiida-core-dev")
  context = "aiida-core-dev"
  contexts = {
    src = ".."
    aiida-core-with-services = "target:aiida-core-with-services"
  }
  platforms = "${PLATFORMS}"
}
