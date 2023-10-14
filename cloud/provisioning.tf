terraform {
    required_providers {
        azurerm = {
            source  = "hashicorp/azurerm"
            version = "~> 3.75.0"
        }
    }
}

provider "azurerm" {
    features {}
}

resource "azurerm_resource_group" "scouting-rg" {
    name     = "resources"
    location = "France Central"
}

resource "azurerm_public_ip" "scouting-rg" {
    name                = "public-ip"
    location            = azurerm_resource_group.scouting-rg.location
    resource_group_name = azurerm_resource_group.scouting-rg.name
    allocation_method   = "Static"
}

resource "azurerm_virtual_network" "scouting-rg" {
    name                = "network"
    address_space       = ["10.0.0.0/16"]
    location            = azurerm_resource_group.scouting-rg.location
    resource_group_name = azurerm_resource_group.scouting-rg.name
}

resource "azurerm_subnet" "scouting-rg" {
    name                 = "internal"
    resource_group_name  = azurerm_resource_group.scouting-rg.name
    virtual_network_name = azurerm_virtual_network.scouting-rg.name
    address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_network_interface" "scouting-rg" {
    name                = "nic"
    location            = azurerm_resource_group.scouting-rg.location
    resource_group_name = azurerm_resource_group.scouting-rg.name

    ip_configuration {
        name                          = "internal"
        subnet_id                     = azurerm_subnet.scouting-rg.id
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id           = azurerm_public_ip.scouting-rg.id
    }
}

# Azure virtual machine

resource "azurerm_linux_virtual_machine" "scouting-rg" {
    name                = "machine"
    resource_group_name = azurerm_resource_group.scouting-rg.name
    location            = azurerm_resource_group.scouting-rg.location
    size                = "Standard_B2s"   # Type of machine - B2s: 2 vCpus, 4 RAM, => $30.37/month
    admin_username      = "adminuser"
    network_interface_ids = [
        azurerm_network_interface.scouting-rg.id,
    ]

    admin_ssh_key {
        username   = "adminuser"
        public_key = file("~/.ssh/vm1.pub")
    }

    os_disk {
        caching              = "ReadWrite"
        storage_account_type = "Standard_LRS"
    }

    source_image_reference {
        publisher = "Canonical"
        offer     = "0001-com-ubuntu-server-focal"
        sku       = "20_04-lts"
        version   = "latest"
    }
}

# Azure SQL service

resource "azurerm_mssql_server" "scouting-rg" {
    name                         = "scouting-sql-server"
    resource_group_name          = azurerm_resource_group.scouting-rg.name
    location                     = azurerm_resource_group.scouting-rg.location
    version                      = "12.0"
    administrator_login          = "admin-db"
    administrator_login_password = "2020-Rockydb2020pw"
}
# Missing better configs
resource "azurerm_mssql_database" "scouting-rg" {
    name           = "braga-scouting-db"
    server_id      = azurerm_mssql_server.scouting-rg.id
    collation      = "SQL_Latin1_General_CP1_CI_AS"
    license_type   = "LicenseIncluded"
    max_size_gb    = 2

}



