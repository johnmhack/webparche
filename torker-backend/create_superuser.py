#!/usr/bin/env python
"""
Script para crear superusuario en Torker
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'torker_project.settings')
django.setup()

from workshops.models import User, Workshop

def create_superuser():
    try:
        # Verificar si ya existe
        existing = User.objects.filter(email='admin@torker.com').first()
        if existing:
            print('Usuario ya existe')
            print(f'Email: {existing.email}')
            print(f'Active: {existing.is_active}')
            print(f'Superuser: {existing.is_superuser}')
            return

        # Crear nuevo superusuario
        user = User.objects.create_superuser(
            email='admin@torker.com',
            first_name='Admin',
            last_name='Torker',
            password='admin123'
        )

        # Crear taller
        workshop = Workshop.objects.create(
            owner=user,
            name='Taller Administrador',
            subscription_plan='premium'
        )

        print('Superusuario creado exitosamente!')
        print(f'Email: {user.email}')
        print(f'Password: admin123')
        print(f'Taller: {workshop.name}')
        print('')
        print('URLs importantes:')
        print(f'Admin: http://localhost:8000/admin/')
        print(f'API: http://localhost:8000/api/')

    except Exception as e:
        print(f'Error creando superusuario: {e}')
        sys.exit(1)

if __name__ == '__main__':
    create_superuser()