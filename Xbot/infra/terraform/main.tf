terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  description = "AWS region for Xbot deployment"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "staging"
}

resource "aws_s3_bucket" "audit_bucket" {
  bucket = "xbot-audit-${var.environment}"
}

resource "aws_security_group" "eks_nodes" {
  name        = "xbot-eks-nodes-${var.environment}"
  description = "Security group for Xbot EKS nodes"
}

output "audit_bucket_name" {
  value = aws_s3_bucket.audit_bucket.id
}

