# Terraform Deployment (EC2 UI)

This stack provisions a single EC2 host for the FM UI using a modules-first design.

## Layout

- `main.tf`: root wiring to local `compute` module
- `modules/compute`: wraps upstream modules
  - `terraform-aws-modules/security-group/aws`
  - `terraform-aws-modules/ec2-instance/aws`

## Required Input

- `ssh_key_name`: existing EC2 key pair name for SSH access

## Optional Inputs

- `aws_region` (default: `eu-west-2`)
- `instance_type` (default: `t3.micro`)
- `ssh_allowed_cidr` (default: `0.0.0.0/0`, restrict in production)
- `root_volume_size_gb` (default: `16`)

## Local Commands

```bash
cd terraform
terraform init
terraform validate
terraform plan -var='ssh_key_name=<your-key-name>'
terraform apply -var='ssh_key_name=<your-key-name>'
```

## Outputs

- `public_ip`
- `public_dns`
- `instance_id`
- `security_group_id`
