variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "eu-west-2"
}

variable "app_name" {
  description = "Application name prefix used in resource names"
  type        = string
  default     = "fm-mcp-ui"
}

variable "instance_name" {
  description = "Name tag for the EC2 instance"
  type        = string
  default     = "fm-mcp-ui"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ssh_key_name" {
  description = "Existing EC2 key pair name used for SSH access"
  type        = string
}

variable "ssh_allowed_cidr" {
  description = "CIDR allowed to SSH to the instance"
  type        = string
  default     = "0.0.0.0/0"
}

variable "http_allowed_cidr" {
  description = "CIDR allowed to access HTTP (port 80)"
  type        = string
  default     = "0.0.0.0/0"
}

variable "root_volume_size_gb" {
  description = "Root EBS volume size in GiB"
  type        = number
  default     = 16
}

variable "root_volume_type" {
  description = "Root EBS volume type"
  type        = string
  default     = "gp3"
}

variable "initial_container_image" {
  description = "Bootstrap container image deployed by EC2 user data"
  type        = string
  default     = "ghcr.io/github/github-mcp-server:latest"
}

variable "initial_container_port" {
  description = "Internal app container port"
  type        = number
  default     = 8000
}

variable "container_runtime_dir" {
  description = "Runtime directory on EC2 host for env and deployment helpers"
  type        = string
  default     = "/opt/fm-mcp-ui"
}

variable "auto_clear_interval_secs" {
  description = "Upload auto-clear interval passed to app environment"
  type        = number
  default     = 3600
}

variable "tags" {
  description = "Extra tags applied to resources"
  type        = map(string)
  default     = {}
}
