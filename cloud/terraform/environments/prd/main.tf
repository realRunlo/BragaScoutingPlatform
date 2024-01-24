

# Full production environment

resource "azurerm_resource_group" "scouting-rg" {
    name     = "scouting-rg"
    location = "West Europe"
}

module "postgreSQL"{
    source = "../../modules/postgreSQL"
    location = "West Europe"
    rg = azurerm_resource_group.scouting-rg.name
    server_name = "braga-scout-server"
    hardware = "B_Standard_B1ms" # 1vCore , 2GB ram 
    storage_size = 32768  # 32 gb
    database_name = "scouting"
    admin_user = "adminScouter"
    admin_password = ""
}

module "virtual_machine" {
    source = "../../modules/virtual-machine"
    location = "West Europe"
    rg = azurerm_resource_group.scouting-rg.name
    hardware = "Standard_B1ms" #1 vCpus, 2 Ram 
    public_key = "~/.ssh/vm1.pub"
}

