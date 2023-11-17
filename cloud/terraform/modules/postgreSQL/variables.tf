
variable "rg"{
    type = string
    default = ""
}

variable "location"{
    type = string
    default = ""
}

variable "server_name" {
    type = string
    default = ""
}

variable "database_name" {
    type = string
    default = ""
}

variable "hardware"{
    type = string
    default = ""
}

variable "storage_size"{
    type = number #mb
    default= 32768
}
variable "admin_user"{
    type = string
    default = ""
}

variable "admin_password"{
    type = string
    default = ""
}
