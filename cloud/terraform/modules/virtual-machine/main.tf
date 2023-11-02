resource "azurerm_public_ip" "scouting-rg" {
    name                = "public-ip"
    location            = var.location
    resource_group_name = var.rg
    allocation_method   = "Static"
}

resource "azurerm_virtual_network" "scouting-rg" {
    name                = "network"
    address_space       = ["10.0.0.0/16"] 
    location            = var.location
    resource_group_name = var.rg
}

resource "azurerm_subnet" "scouting-rg" {
    name                 = "internal"
    resource_group_name =  var.rg
    virtual_network_name = azurerm_virtual_network.scouting-rg.name
    address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_network_interface" "scouting-rg" {
    name                = "nic"
    location            = var.location
    resource_group_name = var.rg

    ip_configuration {
        name                          = "internal"
        subnet_id                     = azurerm_subnet.scouting-rg.id
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id           = azurerm_public_ip.scouting-rg.id
    }
}

# Azure virtual machine
resource "azurerm_linux_virtual_machine" "scouting-rg" {
    name                = "vm"
    location            = var.location
    resource_group_name = var.rg
    size                = var.hardware  #1 vCpus, 2 Ram => $15.11/month ||  # Type of machine - B2s: 2 vCpus, 4 RAM, => $30.37/month
    admin_username      = "adminuser"
    network_interface_ids = [
        azurerm_network_interface.scouting-rg.id,
    ]   

    admin_ssh_key {
        username   = "adminuser"
        public_key = file(var.public_key) 
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

