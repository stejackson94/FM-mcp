output "instance_id" {
  description = "EC2 instance ID"
  value       = module.compute.instance_id
}

output "public_ip" {
  description = "EC2 public IP"
  value       = module.compute.public_ip
}

output "public_dns" {
  description = "EC2 public DNS"
  value       = module.compute.public_dns
}

output "security_group_id" {
  description = "Security group ID used by EC2"
  value       = module.compute.security_group_id
}
