output "chromadb_endpoint" {
  value = aws_instance.raggie-chromadb.private_ip
}

output "ecs_service_load_balancer_dns_name" {
  value = aws_lb.raggie_alb.dns_name
}