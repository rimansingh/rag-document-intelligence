terraform {
  required_version = ">= 1.5.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "~> 3.0"
    }
  }
}

provider "docker" {}

# ── Shared network ────────────────────────────────────────────────────────
# All containers communicate on this network by container name
resource "docker_network" "rag_network" {
  name = "rag-network"
}

# ── Backend image ─────────────────────────────────────────────────────────
resource "docker_image" "backend" {
  name = "rag-backend:latest"

  build {
    context    = "${path.module}/../backend"
    dockerfile = "Dockerfile"
  }

  # Rebuild if any backend source file changes
  triggers = {
    dir_sha = sha1(join("", [
      for f in fileset("${path.module}/../backend/app", "*.py") :
      filesha1("${path.module}/../backend/app/${f}")
    ]))
  }
}

# ── Backend container ─────────────────────────────────────────────────────
resource "docker_container" "backend" {
  name  = "rag-backend"
  image = docker_image.backend.image_id

  networks_advanced {
    name = docker_network.rag_network.name
  }

  ports {
    internal = 8000
    external = var.backend_port
  }

  env = [
    "GROQ_API_KEY=${var.groq_api_key}",
    "SUPABASE_URL=${var.supabase_url}",
    "SUPABASE_KEY=${var.supabase_key}",
    "ENVIRONMENT=${var.environment}",
    "CHROMA_PATH=/app/chroma_db",
  ]

  volumes {
    container_path = "/app/chroma_db"
    host_path      = abspath("${path.module}/../chroma_db")
  }

  healthcheck {
    test         = ["CMD", "python", "-c",
      "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"
    ]
    interval     = "30s"
    timeout      = "10s"
    start_period = "60s"
    retries      = 3
  }

  restart = "unless-stopped"

  # Wait for network before starting
  depends_on = [docker_network.rag_network]
}

# ── Prometheus image ──────────────────────────────────────────────────────
resource "docker_image" "prometheus" {
  name         = "prom/prometheus:latest"
  keep_locally = true
}

# ── Prometheus container ──────────────────────────────────────────────────
resource "docker_container" "prometheus" {
  name  = "rag-prometheus"
  image = docker_image.prometheus.image_id

  networks_advanced {
    name = docker_network.rag_network.name
  }

  ports {
    internal = 9090
    external = var.prometheus_port
  }

  volumes {
    container_path = "/etc/prometheus/prometheus.yml"
    host_path      = abspath("${path.module}/../monitoring/prometheus.yml")
    read_only      = true
  }

  volumes {
    container_path = "/etc/prometheus/alerts.yml"
    host_path      = abspath("${path.module}/../monitoring/alerts.yml")
    read_only      = true
  }

  volumes {
    container_path = "/prometheus"
    host_path      = abspath("${path.module}/../monitoring/prometheus_data")
  }

  restart    = "unless-stopped"
  depends_on = [docker_container.backend]
}

# ── Grafana image ─────────────────────────────────────────────────────────
resource "docker_image" "grafana" {
  name         = "grafana/grafana:latest"
  keep_locally = true
}

# ── Grafana container ─────────────────────────────────────────────────────
resource "docker_container" "grafana" {
  name  = "rag-grafana"
  image = docker_image.grafana.image_id

  networks_advanced {
    name = docker_network.rag_network.name
  }

  ports {
    internal = 3000
    external = var.grafana_port
  }

  env = [
    "GF_SECURITY_ADMIN_USER=admin",
    "GF_SECURITY_ADMIN_PASSWORD=admin",
    "GF_USERS_ALLOW_SIGN_UP=false",
  ]

  restart    = "unless-stopped"
  depends_on = [docker_container.prometheus]
}