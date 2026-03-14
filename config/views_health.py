# Vista de salud para monitoreo (ej. comprobaciones de disponibilidad)
from django.http import JsonResponse


def health(request):
    """Responde 200 OK con status para que load balancers o monitoreo comprueben que la app está viva."""
    return JsonResponse({"status": "ok", "service": "gestion-social"}, status=200)
