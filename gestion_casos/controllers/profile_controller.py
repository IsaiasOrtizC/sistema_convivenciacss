"""Profile Controller: consulta y actualización de los datos públicos del perfil."""

import logging

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from ..models import HistorialUsuario, Usuario
from ..trazabilidad import trazar

logger = logging.getLogger(__name__)


@trazar('CONTROLADOR', 'ProfileController', 'consultando o actualizando datos públicos del perfil')
def gestion_datos_publicos_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(
        Usuario.objects.select_related('rol'),
        pk=usuario_id_sesion,
    )

    if request.method == 'POST':
        nombre = ' '.join(request.POST.get('nombre', '').split())
        apaterno = ' '.join(request.POST.get('apaterno', '').split())
        amaterno = ' '.join(request.POST.get('amaterno', '').split())
        correo = request.POST.get('correo', '').strip().lower()

        try:
            if not all((nombre, apaterno, amaterno, correo)):
                raise ValidationError("Completa todos los datos personales.")

            validate_email(correo)

            if (
                Usuario.objects
                .filter(usuario_correo__iexact=correo)
                .exclude(pk=usuario_perfil.pk)
                .exists()
            ):
                raise ValidationError("Ese correo ya está asociado a otra cuenta.")

            sin_cambios = (
                usuario_perfil.usuario_nombre == nombre
                and usuario_perfil.usuario_apaterno == apaterno
                and usuario_perfil.usuario_amaterno == amaterno
                and (usuario_perfil.usuario_correo or '').lower() == correo
            )
            if sin_cambios:
                messages.info(request, "No se detectaron cambios en tus datos personales.")
                return redirect('gestion_datos_publicos')

            with transaction.atomic():
                usuario_perfil.usuario_nombre = nombre
                usuario_perfil.usuario_apaterno = apaterno
                usuario_perfil.usuario_amaterno = amaterno
                usuario_perfil.usuario_correo = correo
                usuario_perfil.save(
                    update_fields=[
                        'usuario_nombre',
                        'usuario_apaterno',
                        'usuario_amaterno',
                        'usuario_correo',
                    ]
                )

                HistorialUsuario.objects.create(
                    usuario=usuario_perfil,
                    historial_accion="Actualización de perfil",
                    historial_detalle=(
                        f"Actualizó sus datos personales ({nombre} {apaterno} {amaterno} - {correo})."
                    ),
                )

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
        'perfil': usuario_perfil,
    }
    return render(request, 'gestion_casos/gestion_datos_publicos.html', context)