variable "groq_api_key" {
  description = "Groq API key for LLM access"
  type        = string
  sensitive   = true
}

variable "supabase_url" {
  description = "Supabase project URL"
  type        = string
}

variable "supabase_key" {
  description = "Supabase anon key"
  type        = string
  sensitive   = true
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "local"
}

variable "backend_port" {
  description = "Port to expose the backend on"
  type        = number
  default     = 8000
}

variable "prometheus_port" {
  description = "Port to expose Prometheus on"
  type        = number
  default     = 9090
}

variable "grafana_port" {
  description = "Port to expose Grafana on"
  type        = number
  default     = 3000
}