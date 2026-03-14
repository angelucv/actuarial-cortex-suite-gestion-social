import unicodedata


def normalizar(texto):
    if not texto:
        return ""
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto)) if unicodedata.category(c) != 'Mn').upper()


def calcular_prioridad(solicitud):
    puntaje = 0
    especialidad = normalizar(solicitud.especialidad)
    descripcion = normalizar(solicitud.descripcion_caso)
    try:
        monto = float(solicitud.monto_usd)
    except (TypeError, ValueError):
        monto = 0.0
    texto = especialidad + " " + descripcion
    criticas = ['ONCOLOGIA', 'CANCER', 'CARDIOLOGIA', 'INFARTO', 'NEUROLOGIA', 'CEREBRAL', 'UCI', 'QUIRURGICA', 'CARDIOVASCULAR', 'TUMOR']
    medias = ['TRAUMATOLOGIA', 'FRACTURA', 'NEFROLOGIA', 'DIALISIS', 'CIRUGIA', 'GASTRO', 'NEUMONOLOGIA']
    if any(p in texto for p in criticas):
        puntaje += 50
    elif any(p in texto for p in medias):
        puntaje += 30
    else:
        puntaje += 10
    if monto > 10000:
        puntaje += 40
    elif monto > 3000:
        puntaje += 30
    elif monto > 500:
        puntaje += 20
    try:
        if int(str(solicitud.nro_caso)[:4]) < 2026:
            puntaje += 5
    except (ValueError, TypeError):
        pass
    if puntaje >= 60:
        return puntaje, "CRÍTICO"
    elif puntaje >= 30:
        return puntaje, "MEDIO"
    return puntaje, "BAJO"
