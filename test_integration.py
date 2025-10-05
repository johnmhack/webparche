#!/usr/bin/env python
"""
Script para probar la integración frontend-backend de Torker
"""
import requests
import json
import time

API_BASE_URL = 'http://localhost:8000/api'

def test_registration():
    """Probar registro de nuevo usuario"""
    print("Probando registro...")

    data = {
        "email": "test_frontend@example.com",
        "first_name": "Test",
        "last_name": "Frontend",
        "phone": "+1234567890",
        "password": "test123456"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/auth/register/", json=data)
        print(f"Status: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            print("Registro exitoso!")
            print(f"Usuario: {result['user']['email']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False

def test_login():
    """Probar login"""
    print("\nProbando login...")

    data = {
        "email": "test_frontend@example.com",
        "password": "test123456"
    }

    try:
        response = requests.post(f"{API_BASE_URL}/auth/login/", json=data)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Login exitoso!")
            access_token = result.get('access')
            refresh_token = result.get('refresh')
            print(f"Access Token: {access_token[:50]}...")
            return access_token
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Error de conexión: {e}")
        return None

def test_dashboard(access_token):
    """Probar acceso al dashboard"""
    print("\nProbando dashboard...")

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.get(f"{API_BASE_URL}/dashboard/", headers=headers)
        print(f"Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("Dashboard accesible!")
            print(f"Taller: {result['workshop']['name']}")
            print(f"Estadísticas: {result['stats']}")
            return True
        else:
            print(f"Error: {response.text}")
            return False
    except Exception as e:
        print(f"Error de conexión: {e}")
        return False

def main():
    print("Probando integracion Frontend-Backend de Torker")
    print("=" * 50)

    # Test 1: Registro
    if not test_registration():
        print("\nPrueba de registro fallida")
        return

    time.sleep(1)  # Esperar un poco

    # Test 2: Login
    access_token = test_login()
    if not access_token:
        print("\nPrueba de login fallida")
        return

    time.sleep(1)  # Esperar un poco

    # Test 3: Dashboard
    if not test_dashboard(access_token):
        print("\nPrueba de dashboard fallida")
        return

    print("\n" + "=" * 50)
    print("Todas las pruebas pasaron exitosamente!")
    print("Frontend y Backend integrados correctamente")
    print("\nAhora puedes probar Torker en:")
    print("http://localhost:8000/pages/torker/")

if __name__ == '__main__':
    main()