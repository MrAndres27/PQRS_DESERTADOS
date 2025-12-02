#!/bin/bash
# Script de gestión Docker - Sistema PQRS

echo "=================================================="
echo "    GESTIÓN DOCKER - Sistema PQRS"
echo "=================================================="
echo ""
echo "1. Iniciar servicios"
echo "2. Detener servicios"
echo "3. Ver logs"
echo "4. Ver estado"
echo "5. Reiniciar"
echo "0. Salir"
echo ""
read -p "Selecciona: " option

case $option in
    1) docker-compose up -d ;;
    2) docker-compose stop ;;
    3) docker-compose logs -f backend ;;
    4) docker-compose ps ;;
    5) docker-compose restart ;;
    0) exit 0 ;;
    *) echo "Opción inválida" ;;
esac

chmod +x docker-manage.sh