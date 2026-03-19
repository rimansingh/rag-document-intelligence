output "backend_url" {
  description = "URL to access the RAG backend"
  value       = "http://localhost:${var.backend_port}"
}

output "prometheus_url" {
  description = "URL to access Prometheus"
  value       = "http://localhost:${var.prometheus_port}"
}

output "grafana_url" {
  description = "URL to access Grafana"
  value       = "http://localhost:${var.grafana_port}"
}

output "backend_health_url" {
  description = "Health check endpoint"
  value       = "http://localhost:${var.backend_port}/health"
}