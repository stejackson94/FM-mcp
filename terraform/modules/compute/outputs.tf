output "instance_id" {
  description = "EC2 instance ID"
  value       = module.ec2.id
}

output "public_ip" {
  description = "EC2 public IP"
  value       = module.ec2.public_ip
}

output "public_dns" {
  description = "EC2 public DNS"
  value       = module.ec2.public_dns
}

output "security_group_id" {
  description = "Security group ID used by EC2"
  value       = module.security_group.security_group_id
}
