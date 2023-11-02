
variable "location"{
    type = string
    default = "West Europe"
}

variable "rg"{
    type = string
    default = "scouting-rg"
}

variable "hardware" {
    type = string
    default = "Standard_B1ms" #1 vCpus, 2 Ram => $15.11/month | just in case: B2s: 2 vCpus, 4 RAM, => $30.37/month
}
variable "public_key" {
  type = string
  default = "~/.ssh/vm1.pub"
}
