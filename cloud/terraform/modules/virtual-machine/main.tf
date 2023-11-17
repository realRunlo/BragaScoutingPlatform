resource "azurerm_public_ip" "default_ip" {
    name                = "public-ip"
    location            = var.location
    resource_group_name = var.rg
    allocation_method   = "Static"
}

resource "azurerm_virtual_network" "default_network" {
    name                = "network"
    address_space       = ["10.0.0.0/16"] 
    location            = var.location
    resource_group_name = var.rg
}

resource "azurerm_subnet" "default_subnet" {
    name                 = "internal"
    resource_group_name =  var.rg
    virtual_network_name = azurerm_virtual_network.default_network.name
    address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_network_interface" "default_nic" {
    name                = "nic"
    location            = var.location
    resource_group_name = var.rg

    ip_configuration {
        name                          = "internal"
        subnet_id                     = azurerm_subnet.default_subnet.id
        private_ip_address_allocation = "Dynamic"
        public_ip_address_id           = azurerm_public_ip.default_ip.id
    }
}

# Azure virtual machine
resource "azurerm_linux_virtual_machine" "default_vm" {
    name                = "vm"
    location            = var.location
    resource_group_name = var.rg
    size                = var.hardware  
    admin_username      = "adminuser"
    network_interface_ids = [
        azurerm_network_interface.default_nic.id,
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

