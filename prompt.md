Eres un desarrollador backend senior especializado en Django y PostgreSQL.

Voy a desarrollar el Sprint 1 de mi proyecto "Control de Gastos y Servicios del Hogar".

## Stack tecnológico
- Backend: Django 5 + Django REST Framework
- Base de datos: PostgreSQL (Supabase en producción)
- Autenticación: JWT con djangorestframework-simplejwt
- Contenedores: Docker + Docker Compose
- Almacenamiento imágenes: Cloudflare R2 (más adelante)
- Emails: Resend (más adelante)
- CI/CD: GitHub Actions → Render

## Modelos de base de datos (ya definidos)
Tengo 6 tablas diseñadas:

1. cliente (id, nombre, correo, password_hash, created_at, updated_at)
2. tipo_servicio (id, nombre)
3. catalogo_servicio (id, tipo_servicio_id FK, nombre, imagen_url)
4. servicio_usuario (id, cliente_id FK, tipo_servicio_id FK, 
   catalogo_servicio_id FK nullable, nombre_servicio nullable, 
   imagen_url nullable, monto_mensual, fecha_vencimiento, 
   activo DEFAULT TRUE, created_at, updated_at)
   CHECK: (catalogo_servicio_id IS NOT NULL AND nombre_servicio IS NULL) 
   OR (catalogo_servicio_id IS NULL AND nombre_servicio IS NOT NULL)
5. historial_pago (id, servicio_usuario_id FK, monto_pagado, 
   fecha_pago nullable, fecha_vencimiento_cubierta, 
   estado DEFAULT 'pendiente' CHECK IN ('pendiente','pagado'), created_at)
6. notificacion (id, cliente_id FK, servicio_usuario_id FK, 
   tipo CHECK IN ('vencimiento_proximo','pago_pendiente'), 
   mensaje, created_at)

## Objetivo del Sprint 1
Implementar la autenticación completa y la estructura base del proyecto.

## Entregables que necesito:

### 1. Estructura de carpetas del proyecto
Muéstrame la estructura completa de directorios y archivos.

### 2. Docker Compose
Archivo docker-compose.yml con:
- Servicio Django (con hot reload)
- Servicio PostgreSQL
- Servicio Redis (para Celery en Sprint 4)
- Variables de entorno desde .env
- Volúmenes persistentes para PostgreSQL

### 3. Configuración Django
- settings.py separado en base/development/production
- Variables de entorno con python-decouple
- CORS configurado para Vue.js en localhost:5173
- DRF configurado con JWT por defecto
- Conexión a PostgreSQL

### 4. Modelos Django
Los 6 modelos exactamente según la estructura de DB definida arriba.
Incluir:
- Meta classes con verbose_name
- __str__ methods
- on_delete=CASCADE donde corresponde
- El CHECK CONSTRAINT de servicio_usuario

### 5. Migraciones y seed data
- Comando para crear y aplicar migraciones
- Fixture o management command para insertar los 8 tipos de servicio:
  Luz, Agua, Internet, Gas, Línea móvil, Suscripción, Alquiler, Otro

### 6. Autenticación JWT
Usando djangorestframework-simplejwt:
- POST /api/auth/register/ → crear cliente + devolver tokens
- POST /api/auth/login/ → validar credenciales + devolver tokens
- POST /api/auth/token/refresh/ → renovar access token
- GET /api/auth/me/ → datos del usuario autenticado
- PUT /api/auth/me/ → actualizar nombre, correo, contraseña

Serializers con validaciones:
- correo único
- contraseña mínimo 8 caracteres
- hash con bcrypt antes de guardar

### 7. Permisos
- Todos los endpoints protegidos requieren JWT válido
- Cada usuario solo puede ver y modificar sus propios datos
- Clase de permiso personalizada IsOwner

### 8. Pruebas con Postman
Colección de Postman o Thunder Client con todos los endpoints
del Sprint 1 listos para probar.

### 9. requirements.txt
Con todas las dependencias necesarias y sus versiones exactas.

## Consideraciones importantes
- Usar modelo Cliente personalizado que extiende AbstractBaseUser
  (no el User de Django por defecto) para usar correo como login
- El campo password_hash en la DB corresponde al password de Django
- Seguir buenas prácticas REST: status codes correctos, 
  mensajes de error claros en español
- Código limpio con comentarios en las partes complejas
- .env.example con todas las variables necesarias

## Lo que NO necesito en este sprint
- Frontend Vue.js (eso lo hago por separado)
- Celery ni tareas programadas
- Subida de imágenes
- Endpoints de servicios, pagos ni notificaciones

Empieza por la estructura de carpetas y el Docker Compose,
luego avanza en el orden listado arriba. 
Explica brevemente cada decisión técnica importante.