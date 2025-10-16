#!/usr/bin/env python
"""
Script para crear usuario de prueba en Railway
Ejecutar con: python manage.py shell < create_test_user.py
"""

import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from django.contrib.auth.models import User
from workshops.models import Workshop

def create_test_user():
    try:
        # Verificar si ya existe
        if User.objects.filter(email='test@example.com').exists():
            print("Usuario de prueba ya existe")
            return

        # Crear usuario
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='CHANGE_THIS_PASSWORD_IN_PRODUCTION',
            first_name='Usuario',
            last_name='Prueba'
        )

        # Crear taller
        workshop = Workshop.objects.create(
            name='Taller Demo',
            owner=user,
            email='test@example.com',
            phone='+573001234567'
        )

        print("✅ Usuario de prueba creado exitosamente!")
        print(f"📧 Email: test@example.com")
        print(f"🔑 Password: test123")
        print(f"🏪 Taller: Taller Demo")

    except Exception as e:
        print(f"❌ Error creando usuario: {e}")

if __name__ == '__main__':
    create_test_user()