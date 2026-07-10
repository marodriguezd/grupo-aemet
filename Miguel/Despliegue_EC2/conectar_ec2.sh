#!/bin/bash
# -*- coding: utf-8 -*-

echo "========================================"
echo "    Conexión Fácil al EC2 - AWS"
echo "========================================"

# Ruta a la clave que hemos encontrado en la carpeta de Tamara
CLAVE_PEM="../Tamara/datos_climaticos.pem"

# 1. SSH exige que los archivos .pem tengan permisos muy restrictivos
echo "[1] Ajustando permisos de la clave .pem (chmod 400)..."
chmod 400 $CLAVE_PEM

# 2. Configura aquí la IP pública de tu EC2 cuando la sepas
# (Como no la encontré en el código, déjala aquí apuntada)
IP_EC2="PON_AQUI_LA_IP_PUBLICA_DEL_EC2"
IP_EC2="18.198.208.67"
USUARIO="ec2-user" # La máquina está en Amazon Linux 2023

if [ "$IP_EC2" == "PON_AQUI_LA_IP_PUBLICA_DEL_EC2" ]; then
    echo ""
    echo "⚠️  ¡Aviso! Necesitas editar este archivo y poner la IP de tu EC2 en la variable IP_EC2."
    echo "De momento el comando que se ejecutará sería:"
    echo "ssh -i $CLAVE_PEM $USUARIO@<tu-ip>"
else
    echo "[2] Iniciando conexión SSH con el EC2..."
    ssh -i $CLAVE_PEM $USUARIO@$IP_EC2
fi
