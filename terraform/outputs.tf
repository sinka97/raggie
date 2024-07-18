output "chromadb_endpoint" {
  value = aws_instance.raggie_chromadb.public_ip
}

output "raggie_endpoint" {
  value = aws_eip.raggie_streamlit_eip.public_ip
}
