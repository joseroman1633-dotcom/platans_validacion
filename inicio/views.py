import random
import json


from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from django.db.models import Count
from django.http import JsonResponse
from django.core.serializers.json import DjangoJSONEncoder

from .forms import RegistroForm, ParticipantePublicoForm
from .models import PerfilUsuario, ParticipantePublico
from validacion.models import (
    ImagenValidacion,
    PruebaImagenRespuesta,
    SesionPrueba,
    SesionPruebaPublica,
    PruebaImagenRespuestaPublica,
)


def home(request):
    return render(request, "inicio/home.html")


def about(request):
    return render(request, "inicio/acerca.html")


def prueba(request):
    return render(request, "inicio/prueba.html")


def salir(request):
    logout(request)
    return redirect("home")


@login_required
def home2(request):
    return render(request, "inicio/home2.html")


@staff_member_required
def admin_info(request):
    return render(request, "admin/info.html")


@login_required
def iniciar_prueba(request):
    if "prueba_ids" not in request.session:
        imagenes_ids = list(
            ImagenValidacion.objects.filter(activa=True).values_list("id", flat=True)
        )

        if not imagenes_ids:
            return render(
                request,
                "inicio/iniciar_prueba.html",
                {"sin_imagenes": True},
            )

        random.shuffle(imagenes_ids)
        prueba_ids = imagenes_ids[:10]

        sesion = SesionPrueba.objects.create(usuario=request.user)

        request.session["prueba_ids"] = prueba_ids
        request.session["prueba_index"] = 0
        request.session["sesion_prueba_id"] = sesion.id

    prueba_ids = request.session.get("prueba_ids", [])
    prueba_index = request.session.get("prueba_index", 0)
    sesion_id = request.session.get("sesion_prueba_id")

    if not sesion_id:
        return redirect("iniciar_prueba")

    sesion = get_object_or_404(SesionPrueba, id=sesion_id, usuario=request.user)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "responder":
            imagen_id = request.POST.get("imagen_id")
            respuesta = request.POST.get("respuesta")

            if imagen_id and respuesta:
                imagen = get_object_or_404(ImagenValidacion, id=imagen_id)
                es_correcta = imagen.tipo_origen == respuesta

                PruebaImagenRespuesta.objects.create(
                    sesion=sesion,
                    usuario=request.user,
                    imagen=imagen,
                    respuesta=respuesta,
                    es_correcta=es_correcta,
                )

                respuesta_usuario_label = "IA" if respuesta == "IA" else "NO IA"
                respuesta_correcta_label = (
                "IA" if imagen.tipo_origen == "IA" else "NO IA"
            )

                request.session["feedback_data"] = {
                    "imagen_id": imagen.id,
                    "respuesta_usuario": respuesta_usuario_label,
                    "respuesta_correcta": respuesta_correcta_label,
                    "es_correcta": es_correcta,
                    "numero_actual": prueba_index + 1,
                    "total": len(prueba_ids),
                }

                request.session["prueba_index"] = prueba_index + 1
                return redirect("iniciar_prueba")

        elif accion == "finalizar":
            destinatario = request.POST.get("destinatario")

            if destinatario in ["DR_JORGE", "LUCIANO"]:
                sesion.destinatario = destinatario
                sesion.finalizada = True
                sesion.fecha_fin = timezone.now()
                sesion.save()

                total = sesion.respuestas.count()
                correctas = sesion.respuestas.filter(es_correcta=True).count()
                incorrectas = total - correctas

                request.session.pop("prueba_ids", None)
                request.session.pop("prueba_index", None)
                request.session.pop("sesion_prueba_id", None)
                request.session.pop("feedback_data", None)

                return render(
                    request,
                    "inicio/iniciar_prueba.html",
                    {
                        "prueba_terminada": True,
                        "total": total,
                        "correctas": correctas,
                        "incorrectas": incorrectas,
                        "destinatario": destinatario,
                    },
                )

    feedback_data = request.session.pop("feedback_data", None)
    if feedback_data:
        imagen = get_object_or_404(ImagenValidacion, id=feedback_data["imagen_id"])
        return render(
            request,
            "inicio/iniciar_prueba.html",
            {
                "mostrar_feedback": True,
                "imagen": imagen,
                "respuesta_usuario": feedback_data["respuesta_usuario"],
                "respuesta_correcta": feedback_data["respuesta_correcta"],
                "es_correcta": feedback_data["es_correcta"],
                "numero_actual": feedback_data["numero_actual"],
                "total": feedback_data["total"],
            },
        )

    prueba_index = request.session.get("prueba_index", 0)

    if prueba_index >= len(prueba_ids):
        total = sesion.respuestas.count()
        correctas = sesion.respuestas.filter(es_correcta=True).count()
        incorrectas = total - correctas

        return render(
            request,
            "inicio/iniciar_prueba.html",
            {
                "seleccionar_destinatario": True,
                "total": total,
                "correctas": correctas,
                "incorrectas": incorrectas,
            },
        )

    imagen_actual = get_object_or_404(ImagenValidacion, id=prueba_ids[prueba_index])

    return render(
        request,
        "inicio/iniciar_prueba.html",
        {
            "imagen": imagen_actual,
            "numero_actual": prueba_index + 1,
            "total": len(prueba_ids),
        },
    )


def iniciar_prueba_publica(request):
    if request.user.is_authenticated:
        return redirect("iniciar_prueba")

    if "prueba_publica_ids" not in request.session:
        imagenes_ids = list(
            ImagenValidacion.objects.filter(activa=True).values_list("id", flat=True)
        )

        if not imagenes_ids:
            return render(
                request,
                "inicio/iniciar_prueba_publica.html",
                {"sin_imagenes": True},
            )

        random.shuffle(imagenes_ids)
        prueba_ids = imagenes_ids[:10]

        sesion = SesionPruebaPublica.objects.create()

        request.session["prueba_publica_ids"] = prueba_ids
        request.session["prueba_publica_index"] = 0
        request.session["sesion_prueba_publica_id"] = sesion.id

    prueba_ids = request.session.get("prueba_publica_ids", [])
    prueba_index = request.session.get("prueba_publica_index", 0)
    sesion_id = request.session.get("sesion_prueba_publica_id")

    if not sesion_id:
        return redirect("iniciar_prueba_publica")

    sesion = get_object_or_404(SesionPruebaPublica, id=sesion_id)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "responder":
            imagen_id = request.POST.get("imagen_id")
            respuesta = request.POST.get("respuesta")

            if imagen_id and respuesta:
                imagen = get_object_or_404(ImagenValidacion, id=imagen_id)
                es_correcta = imagen.tipo_origen == respuesta

                PruebaImagenRespuestaPublica.objects.create(
                    sesion=sesion,
                    imagen=imagen,
                    respuesta=respuesta,
                    es_correcta=es_correcta,
                )

                respuesta_usuario_label = "IA" if respuesta == "IA" else "NO IA"
                respuesta_correcta_label = (
                "IA" if imagen.tipo_origen == "IA" else "NO IA"
                )

                request.session["feedback_data_publica"] = {
                    "imagen_id": imagen.id,
                    "respuesta_usuario": respuesta_usuario_label,
                    "respuesta_correcta": respuesta_correcta_label,
                    "es_correcta": es_correcta,
                    "numero_actual": prueba_index + 1,
                    "total": len(prueba_ids),
                }

                request.session["prueba_publica_index"] = prueba_index + 1
                return redirect("iniciar_prueba_publica")

        elif accion == "finalizar":
            form_participante = ParticipantePublicoForm(request.POST)
            destinatario = request.POST.get("destinatario")

            if form_participante.is_valid() and destinatario in ["DR_JORGE", "LUCIANO"]:
                participante = form_participante.save()

                sesion.participante = participante
                sesion.destinatario = destinatario
                sesion.finalizada = True
                sesion.fecha_fin = timezone.now()
                sesion.save()

                sesion.respuestas.update(participante=participante)

                total = sesion.respuestas.count()
                correctas = sesion.respuestas.filter(es_correcta=True).count()
                incorrectas = total - correctas

                request.session.pop("prueba_publica_ids", None)
                request.session.pop("prueba_publica_index", None)
                request.session.pop("sesion_prueba_publica_id", None)
                request.session.pop("feedback_data_publica", None)

                return render(
                    request,
                    "inicio/iniciar_prueba_publica.html",
                    {
                        "prueba_terminada": True,
                        "total": total,
                        "correctas": correctas,
                        "incorrectas": incorrectas,
                        "destinatario": destinatario,
                        "participante": participante,
                    },
                )

        elif accion == "reiniciar":
            request.session.pop("prueba_publica_ids", None)
            request.session.pop("prueba_publica_index", None)
            request.session.pop("sesion_prueba_publica_id", None)
            request.session.pop("feedback_data_publica", None)
            return redirect("iniciar_prueba_publica")

    feedback_data = request.session.pop("feedback_data_publica", None)
    if feedback_data:
        imagen = get_object_or_404(ImagenValidacion, id=feedback_data["imagen_id"])
        return render(
            request,
            "inicio/iniciar_prueba_publica.html",
            {
                "mostrar_feedback": True,
                "imagen": imagen,
                "respuesta_usuario": feedback_data["respuesta_usuario"],
                "respuesta_correcta": feedback_data["respuesta_correcta"],
                "es_correcta": feedback_data["es_correcta"],
                "numero_actual": feedback_data["numero_actual"],
                "total": feedback_data["total"],
            },
        )

    prueba_index = request.session.get("prueba_publica_index", 0)

    if prueba_index >= len(prueba_ids):
        total = sesion.respuestas.count()
        correctas = sesion.respuestas.filter(es_correcta=True).count()
        incorrectas = total - correctas

        return render(
            request,
            "inicio/iniciar_prueba_publica.html",
            {
                "seleccionar_destinatario": True,
                "total": total,
                "correctas": correctas,
                "incorrectas": incorrectas,
                "form_participante": ParticipantePublicoForm(),
            },
        )

    imagen_actual = get_object_or_404(ImagenValidacion, id=prueba_ids[prueba_index])

    return render(
        request,
        "inicio/iniciar_prueba_publica.html",
        {
            "imagen": imagen_actual,
            "numero_actual": prueba_index + 1,
            "total": len(prueba_ids),
        },
    )


def register(request):
    if request.method == "POST":
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)

            if user.is_staff or user.is_superuser:
                return redirect("/admin/")

            return redirect("home2")
    else:
        form = RegistroForm()

    return render(request, "registration/register.html", {"form": form})


def _aplicar_filtros_internos(request):
    filtro_fecha = request.GET.get("fecha", "").strip()
    edad_min = request.GET.get("edad_min", "").strip()
    edad_max = request.GET.get("edad_max", "").strip()
    sexo = request.GET.get("sexo", "").strip()

    respuestas_qs = PruebaImagenRespuesta.objects.select_related(
        "usuario",
        "usuario__perfil",
    ).all()

    sesiones_qs = SesionPrueba.objects.select_related(
        "usuario",
        "usuario__perfil",
    ).all()

    if filtro_fecha:
        respuestas_qs = respuestas_qs.filter(fecha_respuesta__date=filtro_fecha)
        sesiones_qs = sesiones_qs.filter(fecha_inicio__date=filtro_fecha)

    if edad_min:
        respuestas_qs = respuestas_qs.filter(usuario__perfil__edad__gte=edad_min)
        sesiones_qs = sesiones_qs.filter(usuario__perfil__edad__gte=edad_min)

    if edad_max:
        respuestas_qs = respuestas_qs.filter(usuario__perfil__edad__lte=edad_max)
        sesiones_qs = sesiones_qs.filter(usuario__perfil__edad__lte=edad_max)

    if sexo:
        respuestas_qs = respuestas_qs.filter(usuario__perfil__sexo=sexo)
        sesiones_qs = sesiones_qs.filter(usuario__perfil__sexo=sexo)

    return respuestas_qs, sesiones_qs, filtro_fecha, edad_min, edad_max, sexo


def _aplicar_filtros_publicos(request):
    filtro_fecha = request.GET.get("fecha", "").strip()
    edad_min = request.GET.get("edad_min", "").strip()
    edad_max = request.GET.get("edad_max", "").strip()
    sexo = request.GET.get("sexo", "").strip()

    respuestas_qs = PruebaImagenRespuestaPublica.objects.select_related(
        "participante"
    ).all()

    sesiones_qs = SesionPruebaPublica.objects.select_related(
        "participante"
    ).all()

    if filtro_fecha:
        respuestas_qs = respuestas_qs.filter(fecha_respuesta__date=filtro_fecha)
        sesiones_qs = sesiones_qs.filter(fecha_inicio__date=filtro_fecha)

    if edad_min:
        respuestas_qs = respuestas_qs.filter(participante__edad__gte=edad_min)
        sesiones_qs = sesiones_qs.filter(participante__edad__gte=edad_min)

    if edad_max:
        respuestas_qs = respuestas_qs.filter(participante__edad__lte=edad_max)
        sesiones_qs = sesiones_qs.filter(participante__edad__lte=edad_max)

    if sexo:
        respuestas_qs = respuestas_qs.filter(participante__sexo=sexo)
        sesiones_qs = sesiones_qs.filter(participante__sexo=sexo)

    return respuestas_qs, sesiones_qs, filtro_fecha, edad_min, edad_max, sexo


def _construir_dashboard_interno(respuestas_qs, sesiones_qs):
    correctas = respuestas_qs.filter(es_correcta=True).count()
    incorrectas = respuestas_qs.filter(es_correcta=False).count()
    total_respuestas = correctas + incorrectas
    total_sesiones = sesiones_qs.count()
    total_usuarios = respuestas_qs.values("usuario").distinct().count()
    precision = round((correctas / total_respuestas) * 100, 2) if total_respuestas else 0

    respuestas_por_tipo_raw = list(
        respuestas_qs.values("respuesta").annotate(total=Count("id"))
    )

    conteo_tipo = {"IA": 0, "NO_IA": 0}
    for item in respuestas_por_tipo_raw:
        if item["respuesta"] == "IA":
            conteo_tipo["IA"] += item["total"]
        else:
            conteo_tipo["NO_IA"] += item["total"]

    respuestas_por_tipo = [
    {"respuesta": "IA", "total": conteo_tipo["IA"]},
    {"respuesta": "NO IA", "total": conteo_tipo["NO_IA"]},
]

    sesiones_por_destinatario = list(
        sesiones_qs
        .exclude(destinatario__isnull=True)
        .exclude(destinatario__exact="")
        .values("destinatario")
        .annotate(total=Count("id"))
        .order_by("destinatario")
    )

    sesiones_por_destinatario = [
        {
            "destinatario": "Dr. Jorge" if item["destinatario"] == "DR_JORGE" else "Luciano",
            "total": item["total"],
        }
        for item in sesiones_por_destinatario
    ]

    respuestas_por_usuario = list(
        respuestas_qs
        .values("usuario__username")
        .annotate(total=Count("id"))
        .order_by("usuario__username")
    )

    respuestas_por_genero_raw = list(
        respuestas_qs.values("usuario__perfil__sexo").annotate(total=Count("id"))
    )

    mapa_genero = {
        "H": "Hombre",
        "M": "Mujer",
        "P": "Prefiero mantenerlo privado",
    }

    respuestas_por_genero = [
        {
            "sexo": mapa_genero.get(item["usuario__perfil__sexo"], "Sin dato"),
            "total": item["total"],
        }
        for item in respuestas_por_genero_raw
    ]

    return {
        "correctas": correctas,
        "incorrectas": incorrectas,
        "total_respuestas": total_respuestas,
        "total_sesiones": total_sesiones,
        "total_personas": total_usuarios,
        "precision": precision,
        "respuestas_por_tipo": respuestas_por_tipo,
        "sesiones_por_destinatario": sesiones_por_destinatario,
        "respuestas_por_usuario": respuestas_por_usuario,
        "respuestas_por_genero": respuestas_por_genero,
    }


def _construir_dashboard_publico(respuestas_qs, sesiones_qs):
    correctas = respuestas_qs.filter(es_correcta=True).count()
    incorrectas = respuestas_qs.filter(es_correcta=False).count()
    total_respuestas = correctas + incorrectas
    total_sesiones = sesiones_qs.count()
    total_participantes = respuestas_qs.values("participante").distinct().count()
    precision = round((correctas / total_respuestas) * 100, 2) if total_respuestas else 0

    respuestas_por_tipo_raw = list(
        respuestas_qs.values("respuesta").annotate(total=Count("id"))
    )

    conteo_tipo = {"IA": 0, "NO_IA": 0}
    for item in respuestas_por_tipo_raw:
        if item["respuesta"] == "IA":
            conteo_tipo["IA"] += item["total"]
        else:
            conteo_tipo["NO_IA"] += item["total"]

    respuestas_por_tipo = [
    {"respuesta": "IA", "total": conteo_tipo["IA"]},
    {"respuesta": "NO IA", "total": conteo_tipo["NO_IA"]},
]

    sesiones_por_destinatario = list(
        sesiones_qs
        .exclude(destinatario__isnull=True)
        .exclude(destinatario__exact="")
        .values("destinatario")
        .annotate(total=Count("id"))
        .order_by("destinatario")
    )

    sesiones_por_destinatario = [
        {
            "destinatario": "Dr. Jorge" if item["destinatario"] == "DR_JORGE" else "Luciano",
            "total": item["total"],
        }
        for item in sesiones_por_destinatario
    ]

    respuestas_por_usuario_raw = list(
        respuestas_qs
        .values("participante__nombre")
        .annotate(total=Count("id"))
        .order_by("participante__nombre")
    )

    respuestas_por_usuario = [
        {
            "usuario__username": item["participante__nombre"] or "Sin nombre",
            "total": item["total"],
        }
        for item in respuestas_por_usuario_raw
    ]

    respuestas_por_genero_raw = list(
        respuestas_qs.values("participante__sexo").annotate(total=Count("id"))
    )

    mapa_genero = {
        "H": "Hombre",
        "M": "Mujer",
        "P": "Prefiero mantenerlo privado",
    }

    respuestas_por_genero = [
        {
            "sexo": mapa_genero.get(item["participante__sexo"], "Sin dato"),
            "total": item["total"],
        }
        for item in respuestas_por_genero_raw
    ]

    return {
        "correctas": correctas,
        "incorrectas": incorrectas,
        "total_respuestas": total_respuestas,
        "total_sesiones": total_sesiones,
        "total_personas": total_participantes,
        "precision": precision,
        "respuestas_por_tipo": respuestas_por_tipo,
        "sesiones_por_destinatario": sesiones_por_destinatario,
        "respuestas_por_usuario": respuestas_por_usuario,
        "respuestas_por_genero": respuestas_por_genero,
    }


@staff_member_required
def admin_graficas(request):
    respuestas_qs, sesiones_qs, filtro_fecha, edad_min, edad_max, sexo = _aplicar_filtros_internos(request)
    dashboard = _construir_dashboard_interno(respuestas_qs, sesiones_qs)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(dashboard)

    context = {
        "titulo_graficas": "Panel de Gráficas Internas",
        "filtro_fecha": filtro_fecha,
        "edad_min": edad_min,
        "edad_max": edad_max,
        "sexo": sexo,
        "sexo_opciones": [
            ("H", "Hombre"),
            ("M", "Mujer"),
            ("P", "Prefiero mantenerlo privado"),
        ],
        "dashboard_json": json.dumps(dashboard, cls=DjangoJSONEncoder),
    }

    return render(request, "admin/graficas.html", context)


@staff_member_required
def admin_graficas_publicas(request):
    respuestas_qs, sesiones_qs, filtro_fecha, edad_min, edad_max, sexo = _aplicar_filtros_publicos(request)
    dashboard = _construir_dashboard_publico(respuestas_qs, sesiones_qs)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(dashboard)

    context = {
        "titulo_graficas": "Panel de Gráficas Públicas",
        "filtro_fecha": filtro_fecha,
        "edad_min": edad_min,
        "edad_max": edad_max,
        "sexo": sexo,
        "sexo_opciones": [
            ("H", "Hombre"),
            ("M", "Mujer"),
            ("P", "Prefiero mantenerlo privado"),
        ],
        "dashboard_json": json.dumps(dashboard, cls=DjangoJSONEncoder),
    }

    return render(request, "admin/graficas_publicas.html", context)


def graficas_publicas(request):
    respuestas_qs, sesiones_qs, filtro_fecha, edad_min, edad_max, sexo = _aplicar_filtros_publicos(request)
    dashboard = _construir_dashboard_publico(respuestas_qs, sesiones_qs)

    if request.headers.get("x-requested-with") == "XMLHttpRequest":
        return JsonResponse(dashboard)

    context = {
        "titulo_graficas": "Panel de Gráficas Públicas",
        "filtro_fecha": filtro_fecha,
        "edad_min": edad_min,
        "edad_max": edad_max,
        "sexo": sexo,
        "sexo_opciones": [
            ("H", "Hombre"),
            ("M", "Mujer"),
            ("P", "Prefiero mantenerlo privado"),
        ],
        "dashboard_json": json.dumps(dashboard, cls=DjangoJSONEncoder),
    }

    return render(request, "inicio/graficas_publicas.html", context)