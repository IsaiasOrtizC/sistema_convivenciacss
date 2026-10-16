"""Configuracion Controller: ajustes de la cuenta (contraseña y opciones personales)."""

from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.shortcuts import get_object_or_404, redirect, render

from ..models import Usuario


def gestion_configuracion_view(request):
    if 'usuario_id' not in request.session:
        return redirect('login')
        
    usuario_id_sesion = request.session.get('usuario_id')
    usuario_perfil = get_object_or_404(Usuario.objects.select_related('rol'), pk=usuario_id_sesion)

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apaterno = request.POST.get('apaterno', '').strip()
        amaterno = request.POST.get('amaterno', '').strip()
        nueva_contrasena = request.POST.get('contrasena', '')

        try:
            if nombre and apaterno and amaterno:
                usuario_perfil.usuario_nombre = nombre
                usuario_perfil.usuario_apaterno = apaterno
                usuario_perfil.usuario_amaterno = amaterno
                request.session['usuario_nombre'] = f"{nombre} {apaterno}"
            
            if nueva_contrasena:
                usuario_perfil.usuario_contrasena = make_password(nueva_contrasena)
                # RF: ya cambió su contraseña temporal -> deja de estar obligado a hacerlo
                usuario_perfil.usuario_primer_ingreso = False
                request.session['primer_ingreso'] = False

            usuario_perfil.save()
            messages.success(request, "Tus credenciales y datos privados se actualizaron correctamente.")
            return redirect('gestion_configuracion')
        except Exception as e:
            messages.error(request, "Ocurrió un error al intentar actualizar la configuración.")

    context = {
        'perfil': usuario_perfil,
        'debe_cambiar_contrasena': request.session.get('primer_ingreso', False),
    }
    return render(request, 'gestion_casos/gestion_configuracion.html', context)
