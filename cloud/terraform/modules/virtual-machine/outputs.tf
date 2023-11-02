output "public_ip" {
  description = "Public IP address of a virtual machine"
  value       = azurerm_linux_virtual_machine.scouting-rg.public_ip_address
}

