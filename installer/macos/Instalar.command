#!/bin/bash
# Dois cliques no Finder para instalar o Light Gun Joypad.
cd "$(dirname "$0")"
bash ./install.sh
echo
read -n 1 -s -r -p "Pressione qualquer tecla para fechar..."
