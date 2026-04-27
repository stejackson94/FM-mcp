data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

locals {
  merged_tags = merge(
    {
      Name      = var.instance_name
      Project   = var.app_name
      ManagedBy = "terraform"
    },
    var.tags,
  )
}

module "security_group" {
  source  = "terraform-aws-modules/security-group/aws"
  version = "~> 5.3"

  name        = "${var.app_name}-sg"
  description = "Security group for ${var.app_name}"
  vpc_id      = data.aws_vpc.default.id

  ingress_with_cidr_blocks = [
    {
      from_port   = 80
      to_port     = 80
      protocol    = "tcp"
      description = "HTTP"
      cidr_blocks = var.http_allowed_cidr
    },
    {
      from_port   = 22
      to_port     = 22
      protocol    = "tcp"
      description = "SSH"
      cidr_blocks = var.ssh_allowed_cidr
    },
  ]

  egress_rules = ["all-all"]
  tags         = local.merged_tags
}

module "ec2" {
  source  = "terraform-aws-modules/ec2-instance/aws"
  version = "~> 5.8"

  name                        = var.instance_name
  ami                         = data.aws_ami.amazon_linux_2023.id
  instance_type               = var.instance_type
  key_name                    = var.ssh_key_name
  subnet_id                   = data.aws_subnets.default.ids[0]
  vpc_security_group_ids      = [module.security_group.security_group_id]
  associate_public_ip_address = true
  user_data = templatefile("${path.module}/templates/user_data.sh.tftpl", {
    container_runtime_dir    = var.container_runtime_dir
    initial_container_image  = var.initial_container_image
    initial_container_port   = var.initial_container_port
    auto_clear_interval_secs = var.auto_clear_interval_secs
  })

  root_block_device = [
    {
      encrypted   = true
      volume_type = var.root_volume_type
      volume_size = var.root_volume_size_gb
    },
  ]

  tags = local.merged_tags
}
