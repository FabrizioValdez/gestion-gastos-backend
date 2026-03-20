from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from apps.clientes.models import Cliente


class ClienteSerializer(serializers.ModelSerializer):
    """Serializer para mostrar datos del cliente."""

    class Meta:
        model = Cliente
        fields = ['id', 'nombre', 'correo', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer para registro de nuevos clientes."""
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = Cliente
        fields = ['nombre', 'correo', 'password', 'password_confirm']

    def validate_correo(self, value):
        if Cliente.objects.filter(correo=value.lower()).exists():
            raise serializers.ValidationError('Ya existe un cliente con este correo.')
        return value.lower()

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Las contraseñas no coinciden.'})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        cliente = Cliente(
            nombre=validated_data['nombre'],
            correo=validated_data['correo']
        )
        cliente.set_password(password)
        cliente.save()
        return cliente


class LoginSerializer(serializers.Serializer):
    """Serializer para inicio de sesión."""
    correo = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        correo = attrs.get('correo').lower()
        password = attrs.get('password')

        if correo and password:
            try:
                cliente = Cliente.objects.get(correo=correo)
            except Cliente.DoesNotExist:
                raise serializers.ValidationError('Credenciales inválidas.') from None

            if not cliente.check_password(password):
                raise serializers.ValidationError('Credenciales inválidas.')

            if not cliente.is_active:
                raise serializers.ValidationError('Usuario inactivo.')

            attrs['cliente'] = cliente
        else:
            raise serializers.ValidationError('Debe proporcionar correo y contraseña.')

        return attrs


class UpdateClienteSerializer(serializers.ModelSerializer):
    """Serializer para actualizar datos del cliente."""
    password = serializers.CharField(write_only=True, required=False, validators=[validate_password])
    password_actual = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Cliente
        fields = ['nombre', 'correo', 'password', 'password_actual']

    def validate_correo(self, value):
        if Cliente.objects.exclude(pk=self.instance.pk).filter(correo=value.lower()).exists():
            raise serializers.ValidationError('Ya existe otro cliente con este correo.')
        return value.lower()

    def validate(self, attrs):
        password = attrs.get('password')
        password_actual = attrs.get('password_actual')

        if password:
            if not password_actual:
                raise serializers.ValidationError({'password_actual': 'Debe proporcionar la contraseña actual.'})
            if not self.instance.check_password(password_actual):
                raise serializers.ValidationError({'password_actual': 'La contraseña actual es incorrecta.'})

        return attrs

    def update(self, instance, validated_data):
        validated_data.pop('password_actual', None)
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
