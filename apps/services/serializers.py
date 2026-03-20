from rest_framework import serializers

from .models import (
    Ayuda,
    Catalogo_servicio,
    Historial_pago,
    Notificacion,
    Servicio_usuario,
    Tipo_servicio,
)


class Tipo_servicioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tipo_servicio
        fields = ['id', 'nombre']
        read_only_fields = ['id']


class Catalogo_servicioSerializer(serializers.ModelSerializer):
    tipo_servicio_nombre = serializers.CharField(source='tipo_servicio.nombre', read_only=True)

    class Meta:
        model = Catalogo_servicio
        fields = ['id', 'tipo_servicio', 'tipo_servicio_nombre', 'nombre', 'imagen_url']
        read_only_fields = ['id']


class Servicio_usuarioSerializer(serializers.ModelSerializer):
    tipo_servicio_nombre = serializers.CharField(source='tipo_servicio.nombre', read_only=True)
    catalogo_servicio_nombre = serializers.CharField(source='catalogo_servicio.nombre', read_only=True)

    class Meta:
        model = Servicio_usuario
        fields = [
            'id', 'tipo_servicio', 'tipo_servicio_nombre', 
            'catalogo_servicio', 'catalogo_servicio_nombre',
            'nombre_servicio', 'imagen_url', 'monto_mensual', 
            'dia_vencimiento', 'activo', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'activo', 'created_at', 'updated_at']

    def validate_dia_vencimiento(self, value):
        if value < 1 or value > 31:
            raise serializers.ValidationError("El día de vencimiento debe estar entre 1 y 31.")
        return value

    def validate(self, attrs):
        catalogo = attrs.get('catalogo_servicio')
        nombre_servicio = attrs.get('nombre_servicio')
        
        if catalogo and nombre_servicio:
            raise serializers.ValidationError({
                'non_field_errors': ['Solo puede especificarse catalogo_servicio o nombre_servicio, no ambos.']
            })
        if not catalogo and not nombre_servicio:
            raise serializers.ValidationError({
                'non_field_errors': ['Debe especificarse al menos uno: catalogo_servicio o nombre_servicio.']
            })
        return attrs


class Historial_pagoSerializer(serializers.ModelSerializer):
    servicio_usuario_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Historial_pago
        fields = [
            'id', 'servicio_usuario', 'servicio_usuario_nombre',
            'monto_pagado', 'fecha_pago', 'fecha_vencimiento_cubierta',
            'estado', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

    def get_servicio_usuario_nombre(self, obj):
        return obj.servicio_usuario.nombre_servicio or obj.servicio_usuario.catalogo_servicio.nombre


class NotificacionSerializer(serializers.ModelSerializer):
    servicio_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Notificacion
        fields = [
            'id', 'servicio_usuario', 'servicio_nombre',
            'tipo', 'mensaje', 'leida', 'created_at'
        ]
        read_only_fields = ['id', 'tipo', 'mensaje', 'created_at']

    def get_servicio_nombre(self, obj):
        if obj.servicio_usuario:
            return obj.servicio_usuario.nombre_servicio or obj.servicio_usuario.catalogo_servicio.nombre
        return None


class AyudaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ayuda
        fields = ['id', 'pregunta', 'respuesta', 'categoria', 'orden', 'activa']
        read_only_fields = ['id']
