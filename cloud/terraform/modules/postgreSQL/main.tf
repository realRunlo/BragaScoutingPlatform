# Postgre sql server
resource "azurerm_postgresql_flexible_server" "default_server" {
  name                   = var.server_name
  resource_group_name    = var.rg
  location               = var.location
  version                = "12"
  administrator_login    = var.admin_user
  administrator_password = var.admin_password 
  storage_mb             = var.storage_size 
  sku_name               = var.hardware
}

# Firewall rules
resource "azurerm_mssql_firewall_rule" "default_rule" {
    name             = "any"
    server_id        = azurerm_postgresql_flexible_server.default_server.id
    start_ip_address = "0.0.0.0"
    end_ip_address   = "255.255.255.255"
}   

resource "azurerm_postgresql_flexible_server_database" "default_database" {
  name      = var.database_name
  server_id = azurerm_postgresql_flexible_server.default_server.id
  collation = "en_US.utf8"
  charset   = "utf8"
}

