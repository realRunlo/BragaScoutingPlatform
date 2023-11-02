

# Full production environment

resource "azurerm_resource_group" "scouting-rg" {
    name     = "scouting-rg"
    location = "West Europe"
}

module "virtual_machine" {
    source = "../../modules/virtual-machine"
    location = "West Europe"
    rg = "scouting-rg"
}

module "database"{
    source = "../../modules/database"
    location = "West Europe"
    rg = "scouting-rg"
}
