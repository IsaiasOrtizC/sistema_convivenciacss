"""Profile Controller: consulta y actualización de los datos públicos del perfil."""

import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Usuario

logger = logging.getLogger(__name__)


def gestion_datos_publicos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
        
    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(Usuario.objects.select_related('rol'), pk=usuario_id_sesion)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        correo = request.POST.get('correo', '').strip()
        try:
            if not all((nombre, apaterno, amaterno, correo)):
                raise ValidationError("Completa todos los datos personales.")
            validate_email(correo)
            if Usuario.objects.filter(usuario_correo__iexact=correo).exclude(
                pk=usuario_perfil.pk
            ).exists():
                raise ValidationError("Ese correo ya está asociado a otra cuenta.")

            usuario_perfil.usuario_nombre = nombre
            usuario_perfil.usuario_apaterno = apaterno
            usuario_perfil.usuario_amaterno = amaterno
            usuario_perfil.usuario_correo = correo
            usuario_perfil.save()
            request.session['usuario_nombre'] = f'{nombre} {apaterno}'
            request.session['usuario_correo'] = correo
            messages.success(request, "Tus datos personales se actualizaron correctamente.")
            return redirect('gestion_datos_publicos')
        except ValidationError as exc:
            messages.error(request, ' '.join(exc.messages))
        except Exception:
            logger.exception("Error actualizando el perfil del usuario %s", usuario_id_sesion)
            messages.error(request, "No fue posible actualizar tus datos personales.")

    context = {
        'perfil': usuario_perfil
    }
    return render(request, 'gestion_casos/gestion_datos_publicos.html', context)
