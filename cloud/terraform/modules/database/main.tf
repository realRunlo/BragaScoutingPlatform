# Microsoft sql server
resource "azurerm_mssql_server" "scouting-rg" {
    name                         = "testbraga-scout-server"
    resource_group_name          = var.rg
    location                     = var.location
    version                      = "12.0"
    administrator_login          = "dbadmin"
    administrator_login_password = "2020-Rockydb2020pw!"
    minimum_tls_version          = "1.2"
		
    public_network_access_enabled = true
}

# Firewall rules
resource "azurerm_mssql_firewall_rule" "scouting-rg" {
    name             = "any"
    server_id        = azurerm_mssql_server.scouting-rg.id
    start_ip_address = "0.0.0.0"
    end_ip_address   = "255.255.255.255"
}   

# Database
resource "azurerm_mssql_database" "scouting-rg" {
    name           = var.database-name
    server_id      = azurerm_mssql_server.scouting-rg.id
    collation      = "LATIN1_GENERAL_100_CI_AS_SC_UTF8"
    min_capacity   = 2
    read_scale     = false
    sku_name       = "GP_S_Gen5_2"
    zone_redundant = true
    auto_pause_delay_in_minutes = 60 # minutes of inactivity before the instance is paused

}
