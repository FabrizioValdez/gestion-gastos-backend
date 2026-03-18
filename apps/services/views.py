from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum, Count
from datetime import datetime as dt
from django.db.models.functions import TruncMonth
from django.utils import timezone
from django.http import HttpResponse
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from apps.clientes.permissions import IsOwner
from .models import Tipo_servicio, Catalogo_servicio, Servicio_usuario, Historial_pago, Notificacion, Ayuda
from .serializers import (
    Tipo_servicioSerializer,
    Catalogo_servicioSerializer,
    Servicio_usuarioSerializer,
    Historial_pagoSerializer,
    NotificacionSerializer,
    AyudaSerializer
)
from .tasks import generar_notificaciones_vencimiento, generar_notificaciones_pago_pendiente


class HealthCheckView(APIView):
    """Endpoint de verificación de estado de la API."""
    permission_classes = []

    def get(self, request):
        return Response({
            'status': 'ok',
            'message': 'API de Gestión de Gastos y Servicios del Hogar'
        }, status=status.HTTP_200_OK)


class Tipo_servicioViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para tipos de servicio."""
    queryset = Tipo_servicio.objects.all()
    serializer_class = Tipo_servicioSerializer
    permission_classes = [IsAuthenticated]


class Catalogo_servicioViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet de solo lectura para catálogo de servicios."""
    queryset = Catalogo_servicio.objects.all()
    serializer_class = Catalogo_servicioSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Catalogo_servicio.objects.all()
        tipo_id = self.request.query_params.get('tipo_servicio')
        if tipo_id:
            queryset = queryset.filter(tipo_servicio_id=tipo_id)
        return queryset


class Servicio_usuarioViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar servicios del usuario."""
    serializer_class = Servicio_usuarioSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Servicio_usuario.objects.filter(cliente=self.request.user)

    def perform_create(self, serializer):
        serializer.save(cliente=self.request.user)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.activo = False
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'])
    def resumen(self, request):
        """Resumen de gastos mensuales del usuario."""
        servicios = self.get_queryset().filter(activo=True)
        total_mensual = servicios.aggregate(total=Sum('monto_mensual'))['total'] or 0
        
        return Response({
            'total_mensual': float(total_mensual),
            'servicios_activos': servicios.count()
        })

    @action(detail=False, methods=['get'])
    def por_tipo(self, request):
        """Gastos agrupados por tipo de servicio."""
        servicios = self.get_queryset().filter(activo=True)
        por_tipo = servicios.values(
            'tipo_servicio__id',
            'tipo_servicio__nombre'
        ).annotate(
            total=Sum('monto_mensual'),
            cantidad=Count('id')
        ).order_by('-total')
        
        return Response([{
            'tipo_id': item['tipo_servicio__id'],
            'tipo_nombre': item['tipo_servicio__nombre'],
            'total': float(item['total']),
            'cantidad': item['cantidad']
        } for item in por_tipo])

    @action(detail=False, methods=['get'])
    def graficos(self, request):
        """Datos para gráficos de gastos."""
        pagos = Historial_pago.objects.filter(
            servicio_usuario__cliente=self.request.user,
            estado='pagado'
        )
        
        por_mes = pagos.annotate(
            mes=TruncMonth('fecha_pago')
        ).values('mes').annotate(
            total=Sum('monto_pagado')
        ).order_by('mes')[:12]
        
        por_tipo = pagos.values(
            'servicio_usuario__tipo_servicio__nombre'
        ).annotate(
            total=Sum('monto_pagado')
        ).order_by('-total')[:6]
        
        return Response({
            'gastos_por_mes': [{
                'mes': item['mes'].strftime('%Y-%m') if item['mes'] else None,
                'total': float(item['total'])
            } for item in por_mes if item['mes']],
            'gastos_por_tipo': [{
                'tipo': item['servicio_usuario__tipo_servicio__nombre'],
                'total': float(item['total'])
            } for item in por_tipo]
        })

    @action(detail=False, methods=['get'])
    def deudas(self, request):
        """Obtener servicios vencidos (deudas) - aquellos cuyo día de vencimiento ya pasó este mes."""
        import calendar
        from datetime import date
        
        fecha_hoy = date.today()
        dia_actual = fecha_hoy.day
        anio_actual = fecha_hoy.year
        mes_actual = fecha_hoy.month
        
        resultados = []
        servicios = self.get_queryset().filter(activo=True, cliente=request.user)
        
        for servicio in servicios:
            dia_venc = servicio.dia_vencimiento
            ultimo_dia_mes = calendar.monthrange(anio_actual, mes_actual)[1]
            dia_ajustado = min(dia_venc, ultimo_dia_mes)
            
            if dia_actual < dia_ajustado:
                continue
            
            fecha_venc_inicio = date(anio_actual, mes_actual, 1)
            fecha_venc_fin = date(anio_actual, mes_actual, ultimo_dia_mes)
            
            pago_este_mes = Historial_pago.objects.filter(
                servicio_usuario=servicio,
                estado='pagado',
                fecha_vencimiento_cubierta__gte=fecha_venc_inicio,
                fecha_vencimiento_cubierta__lte=fecha_venc_fin
            ).exists()
            
            if pago_este_mes:
                continue
            
            nombre = servicio.nombre_servicio or servicio.catalogo_servicio.nombre if servicio.catalogo_servicio else servicio.nombre_servicio
            
            resultados.append({
                'id': servicio.id,
                'nombre': nombre,
                'tipo_servicio': servicio.tipo_servicio.nombre,
                'monto': float(servicio.monto_mensual),
                'dia_vencimiento': dia_venc,
                'dias_vencido': dia_actual - dia_ajustado
            })
        
        return Response(resultados)

    @action(detail=True, methods=['post'])
    def pagar_deuda(self, request, pk=None):
        """Marcar una deuda como pagada."""
        import calendar
        from datetime import date
        
        servicio = self.get_object()
        
        fecha_pago = request.data.get('fecha_pago')
        monto_pagado = request.data.get('monto_pagado')
        
        if not fecha_pago:
            return Response(
                {'error': 'La fecha de pago es requerida'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            fecha_pago_dt = dt.strptime(fecha_pago, '%Y-%m-%d')
        except ValueError:
            return Response(
                {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        dia_venc = servicio.dia_vencimiento
        anio_venc = fecha_pago_dt.year
        mes_venc = fecha_pago_dt.month
        
        # El vencimiento cubierto es el mes/año del pago, no el mes anterior
        # Si pagas el 18/03 y vences el 15, cubres el vencimiento de marzo
        ultimo_dia_mes = calendar.monthrange(anio_venc, mes_venc)[1]
        dia_ajustado = min(dia_venc, ultimo_dia_mes)
        fecha_vencimiento_cubierta = date(anio_venc, mes_venc, dia_ajustado)
        
        monto = float(monto_pagado) if monto_pagado else float(servicio.monto_mensual)
        
        Historial_pago.objects.create(
            servicio_usuario=servicio,
            monto_pagado=monto,
            fecha_pago=fecha_pago_dt,
            fecha_vencimiento_cubierta=fecha_vencimiento_cubierta,
            estado='pagado'
        )
        
        return Response({
            'mensaje': 'Pago registrado correctamente',
            'fecha_vencimiento_cubierta': fecha_vencimiento_cubierta,
            'monto_pagado': monto
        })


class Historial_pagoViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar historial de pagos."""
    serializer_class = Historial_pagoSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        queryset = Historial_pago.objects.filter(
            servicio_usuario__cliente=self.request.user
        )
        
        estado = self.request.query_params.get('estado')
        if estado:
            queryset = queryset.filter(estado=estado)
        
        anio = self.request.query_params.get('anio')
        if anio:
            queryset = queryset.filter(fecha_pago__year=anio)
        
        mes = self.request.query_params.get('mes')
        if mes:
            queryset = queryset.filter(fecha_pago__month=mes)
        
        return queryset.order_by('-fecha_pago', '-created_at')

    def perform_create(self, serializer):
        servicio = serializer.validated_data['servicio_usuario']
        if servicio.cliente != self.request.user:
            raise PermissionError('No tienes acceso a este servicio')
        
        if serializer.validated_data.get('estado') == 'pagado':
            serializer.save(fecha_pago=dt.now())
        else:
            serializer.save()

    @action(detail=False, methods=['get'], url_path='servicio/(?P<servicio_id>[^/.]+)')
    def por_servicio(self, request, servicio_id=None):
        """Obtener pagos de un servicio específico."""
        try:
            servicio = Servicio_usuario.objects.get(
                id=servicio_id, 
                cliente=request.user
            )
            pagos = Historial_pago.objects.filter(servicio_usuario=servicio)
            serializer = self.get_serializer(pagos, many=True)
            return Response(serializer.data)
        except Servicio_usuario.DoesNotExist:
            return Response(
                {'error': 'Servicio no encontrado'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'], url_path='reporte-pdf/(?P<anio>[0-9]+)/(?P<mes>[0-9]+)')
    def reporte_pdf(self, request, anio=None, mes=None):
        """Generar reporte PDF de pagos para un mes específico."""
        try:
            anio = int(anio)
            mes = int(mes)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Año y mes inválidos'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if mes < 1 or mes > 12:
            return Response(
                {'error': 'El mes debe estar entre 1 y 12'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pagos = Historial_pago.objects.filter(
            servicio_usuario__cliente=request.user,
            fecha_pago__year=anio,
            fecha_pago__month=mes,
            estado='pagado'
        ).select_related('servicio_usuario').order_by('fecha_pago')
        
        if not pagos.exists():
            return Response(
                {'error': 'No hay pagos registrados para este período'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        nombre_mes = [
            '', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
            'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
        ][mes]
        
        response = HttpResponse(content_type='application/pdf')
        filename = f'Reporte_Gastos_{nombre_mes}_{anio}.pdf'
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=20,
            alignment=1
        )
        
        elements = []
        
        elements.append(Paragraph('REPORTE DE GASTOS MENSUALES', title_style))
        elements.append(Paragraph(f'Usuario: {request.user.correo}', subtitle_style))
        elements.append(Paragraph(f'Período: {nombre_mes} {anio}', subtitle_style))
        elements.append(Paragraph(f'Fecha de generación: {timezone.now().strftime("%d/%m/%Y %H:%M")}', styles['Normal']))
        elements.append(Spacer(1, 30))
        
        data = [['#', 'Servicio', 'Fecha de Pago', 'Monto']]
        
        total = 0
        for i, pago in enumerate(pagos, 1):
            nombre_servicio = pago.servicio_usuario.nombre_servicio or \
                             pago.servicio_usuario.catalogo_servicio.nombre if pago.servicio_usuario.catalogo_servicio \
                             else pago.servicio_usuario.nombre_servicio or 'Sin nombre'
            fecha_pago = pago.fecha_pago.strftime('%d/%m/%Y') if pago.fecha_pago else '-'
            monto = float(pago.monto_pagado)
            total += monto
            data.append([
                str(i),
                nombre_servicio[:30],
                fecha_pago,
                f'S/ {monto:.2f}'
            ])
        
        data.append(['', '', 'TOTAL:', f'S/ {total:.2f}'])
        
        table = Table(data, colWidths=[0.5*inch, 2.5*inch, 1.5*inch, 1.2*inch])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4F46E5')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -2), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -2), 1, colors.HexColor('#E5E7EB')),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F3F4F6')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#4F46E5')),
        ]))
        
        elements.append(table)
        elements.append(Spacer(1, 30))
        
        total_pagos = len(pagos)
        elements.append(Paragraph(f'Total de pagos: {total_pagos}', styles['Normal']))
        
        doc.build(elements)
        
        return response


class NotificacionViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar notificaciones."""
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return Notificacion.objects.filter(cliente=self.request.user)

    @action(detail=False, methods=['get'])
    def pendientes(self, request):
        """Obtener notificaciones no leídas."""
        notificaciones = self.get_queryset().filter(leida=False)
        serializer = self.get_serializer(notificaciones, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def marcar_leida(self, request, pk=None):
        """Marcar notificación como leída."""
        notificacion = self.get_object()
        notificacion.leida = True
        notificacion.save()
        serializer = self.get_serializer(notificacion)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.leida = request.data.get('leida', instance.leida)
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class AyudaViewSet(viewsets.ModelViewSet):
    """ViewSet para gestionar ayuda/FAQ."""
    serializer_class = AyudaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Ayuda.objects.filter(activa=True)
        categoria = self.request.query_params.get('categoria')
        if categoria:
            queryset = queryset.filter(categoria=categoria)
        return queryset

    @action(detail=False, methods=['post'])
    def generar_notificaciones(self, request):
        """Endpoint manual para generar notificaciones (para pruebas)."""
        resultado1 = generar_notificaciones_vencimiento()
        resultado2 = generar_notificaciones_pago_pendiente()
        return Response({
            'mensaje': 'Notificaciones generadas',
            'vencimiento': resultado1,
            'pago_pendiente': resultado2
        })
