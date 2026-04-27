provider "aws" {
  region = var.aws_region
}

module "compute" {
  source = "./modules/compute"

  aws_region               = var.aws_region
  app_name                 = var.app_name
  instance_name            = var.instance_name
  instance_type            = var.instance_type
  ssh_key_name             = var.ssh_key_name
  http_allowed_cidr        = var.http_allowed_cidr
  ssh_allowed_cidr         = var.ssh_allowed_cidr
  root_volume_size_gb      = var.root_volume_size_gb
  root_volume_type         = var.root_volume_type
  initial_container_image  = var.initial_container_image
  initial_container_port   = var.initial_container_port
  container_runtime_dir    = var.container_runtime_dir
  auto_clear_interval_secs = var.auto_clear_interval_secs
  tags                     = var.tags
}
