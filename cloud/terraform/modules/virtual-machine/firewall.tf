resource "azurerm_network_security_group" "scouting-rg" {
    name                = "vm-nsg"
    location            = var.location 
    resource_group_name = var.rg
    
    # Inbound rules

    # Allow ssh
    security_rule {
	name                       = "SSH-Inbound"
	priority                   = 101
	direction                  = "Inbound"
	access                     = "Allow"
	protocol                   = "Tcp"
	source_port_range          = "*"
	destination_port_range     = "22"
	source_address_prefix      = "*"
	destination_address_prefix = "*"
    }
    
    # Allow https
    security_rule {
	name                       = "HTTPS-Inbound"  
	priority                   = 102
	direction                  = "Inbound"
	access                     = "Allow"
	protocol                   = "Tcp"
	source_port_range          = "*"
	destination_port_range     = "443"
	source_address_prefix      = "*"
	destination_address_prefix = "*"
    }

    # Deny all inbound traffic
    security_rule {
	name                       = "Deny-Inbound"
	priority                   = 200
	direction                  = "Inbound"
	access                     = "Deny"
	protocol                   = "*"
	source_port_range          = "*"
	destination_port_range     = "*"
	source_address_prefix      = "*"
	destination_address_prefix = "*"
    }    

    # Outbound rules


    # Deny all outbound traffic
   # security_rule {
#	name                       = "Deny-Outbound"
#	priority                   = 200
#	direction                  = "Outbound"
#	access                     = "Deny"
#	protocol                   = "*"
#	source_port_range          = "*"
#	destination_port_range     = "*"
#	source_address_prefix      = "*"
#	destination_address_prefix = "*"
 #   }
}


