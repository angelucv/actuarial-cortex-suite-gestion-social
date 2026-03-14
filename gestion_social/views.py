import json
import math
import os
from django.shortcuts import render
from django.utils import timezone
from urllib.parse import urlencode
from .models import Solicitud
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from datetime import datetime, timedelta
try:
    import folium
    from folium.plugins import HeatMap
except ImportError:
    folium = None
    HeatMap = None

CORTEX_SITE_URL = "https://actuarial-cortex.pages.dev/"

# Config Plotly: barra de herramientas con botón Descargar imagen
PLOTLY_CONFIG = {'displayModeBar': True, 'modeBarButtonsToAdd': ['toImage'], 'toImageButtonOptions': {'format': 'png', 'filename': 'grafico'}}

# Centroides aproximados (lat, lon) de estados de Venezuela para el mapa
VENEZUELA_ESTADOS_CENTROIDS = {
    'AMAZONAS': (2.5, -66.5), 'ANZOATEGUI': (8.9, -64.2), 'ANZOÁTEGUI': (8.9, -64.2),
    'APURE': (7.0, -69.0), 'ARAGUA': (10.2, -67.3), 'BARINAS': (8.6, -70.2),
    'BOLIVAR': (6.0, -63.5), 'BOLÍVAR': (6.0, -63.5), 'CARABOBO': (10.2, -68.0),
    'COJEDES': (9.3, -68.3), 'DELTA AMACURO': (8.7, -61.0), 'DISTRITO CAPITAL': (10.48, -66.9),
    'FALCON': (11.0, -69.7), 'FALCÓN': (11.0, -69.7), 'GUARICO': (8.7, -66.6), 'GUÁRICO': (8.7, -66.6),
    'LARA': (10.0, -69.5), 'MERIDA': (8.6, -71.1), 'MÉRIDA': (8.6, -71.1),
    'MIRANDA': (10.2, -66.4), 'MONAGAS': (9.4, -63.0), 'NUEVA ESPARTA': (11.0, -63.9),
    'PORTUGUESA': (9.1, -69.1), 'SUCRE': (10.4, -63.2), 'TACHIRA': (7.9, -72.0), 'TÁCHIRA': (7.9, -72.0),
    'TRUJILLO': (9.4, -70.6), 'VARGAS': (10.6, -66.9), 'YARACUY': (10.4, -68.7), 'ZULIA': (10.0, -72.0),
}

def _query_map(request, mapa):
    q = request.GET.copy()
    q['mapa'] = mapa
    return q.urlencode()


# Nombres únicos de estados para el GeoJSON (un polígono por estado)
_ESTADOS_GEOJSON = [
    'AMAZONAS', 'ANZOÁTEGUI', 'APURE', 'ARAGUA', 'BARINAS', 'BOLÍVAR', 'CARABOBO', 'COJEDES',
    'DELTA AMACURO', 'DISTRITO CAPITAL', 'FALCÓN', 'GUÁRICO', 'LARA', 'MÉRIDA', 'MIRANDA',
    'MONAGAS', 'NUEVA ESPARTA', 'PORTUGUESA', 'SUCRE', 'TÁCHIRA', 'TRUJILLO', 'VARGAS', 'YARACUY', 'ZULIA',
]


def _geojson_estados_venezuela():
    """GeoJSON con polígonos aproximados por estado (cuadrados desde centroides) para choropleth."""
    features = []
    for nombre in _ESTADOS_GEOJSON:
        coord_tup = VENEZUELA_ESTADOS_CENTROIDS.get(nombre) or VENEZUELA_ESTADOS_CENTROIDS.get(
            nombre.replace('Á', 'A').replace('Í', 'I').replace('É', 'E').replace('Ó', 'O').replace('Ú', 'U')
        )
        if not coord_tup:
            continue
        lat, lon = coord_tup
        h = 0.38
        coords = [
            [lon - h, lat - h], [lon + h, lat - h], [lon + h, lat + h],
            [lon - h, lat + h], [lon - h, lat - h],
        ]
        features.append({
            'type': 'Feature',
            'id': nombre,
            'properties': {'name': nombre},
            'geometry': {'type': 'Polygon', 'coordinates': [coords]},
        })
    return {'type': 'FeatureCollection', 'features': features}


EMPTY_CONTEXT = {
    'mensaje': "Sin datos. Cargue solicitudes desde el Admin (import CSV/Excel) o ejecute: python manage.py cargar_datos_demo",
    'total_usd': '0.00', 'total_casos': 0, 'casos_criticos': 0,
    'html_gasto': '', 'txt_gasto': '', 'html_status': '', 'txt_status': '',
    'html_prov': '', 'txt_prov': '', 'cortex_site_url': CORTEX_SITE_URL,
    'html_gauge': '', 'html_gauge2': '', 'html_gauge3': '', 'html_bubble': '', 'html_sunburst': '', 'html_funnel': '', 'html_treemap': '',
    'html_resumen_ejecutivo': '', 'html_comparativa': '', 'html_tendencia': '',     'html_mapa_venezuela': '', 'mapa_estados_opciones': [], 'nota_mapa_estados': '', 'mapa_estados_leyenda_pct': False, 'mapa_estados_pct_min': None, 'mapa_estados_pct_max': None,
    'html_hist_casos': '', 'html_hist_monto': '', 'html_hist_criticos': '', 'html_hist_evol': '', 'html_hist_traza': '',
    'html_hist_area': '', 'html_hist_violin': '',
    'alertas': [], 'especialidades_list': [],
    'filtro_fecha_desde': '', 'filtro_fecha_hasta': '', 'filtro_especialidad': '',
}


def dashboard_social(request):
    solicitudes = Solicitud.objects.all().values(
        'id', 'nro_caso', 'monto_usd', 'especialidad', 'estatus', 'proveedor', 'nivel_prioridad',
        'fecha_recepcion', 'actualizado_en', 'mes', 'creado_en', 'estado'
    )
    df = pd.DataFrame(list(solicitudes))
    if df.empty:
        return render(request, 'dashboard.html', EMPTY_CONTEXT)

    # Filtros (GET)
    filtro_fecha_desde = request.GET.get('fecha_desde', '').strip()
    filtro_fecha_hasta = request.GET.get('fecha_hasta', '').strip()
    filtro_especialidad = request.GET.get('especialidad', '').strip()
    if filtro_fecha_desde:
        try:
            fd = pd.to_datetime(filtro_fecha_desde)
            if 'fecha_recepcion' in df.columns and df['fecha_recepcion'].notna().any():
                df['fecha_recepcion'] = pd.to_datetime(df['fecha_recepcion'], errors='coerce')
                df = df[df['fecha_recepcion'].dt.date >= fd.date()]
        except Exception:
            pass
    if filtro_fecha_hasta:
        try:
            fh = pd.to_datetime(filtro_fecha_hasta)
            if 'fecha_recepcion' in df.columns and df['fecha_recepcion'].notna().any():
                if 'fecha_recepcion' not in df.columns or not pd.api.types.is_datetime64_any_dtype(df['fecha_recepcion']):
                    df['fecha_recepcion'] = pd.to_datetime(df['fecha_recepcion'], errors='coerce')
                df = df[df['fecha_recepcion'].dt.date <= fh.date()]
        except Exception:
            pass
    if filtro_especialidad:
        df = df[df['especialidad'].astype(str).str.upper().str.strip() == filtro_especialidad.upper()]

    # Lista de especialidades para el filtro (antes de normalizar por si df queda vacío)
    especialidades_list = sorted(Solicitud.objects.values_list('especialidad', flat=True).distinct())
    especialidades_list = [str(e) for e in especialidades_list if e]

    if df.empty:
        return render(request, 'dashboard.html', {
            **EMPTY_CONTEXT,
            'mensaje': 'No hay registros con los filtros aplicados. Ajuste fechas o especialidad.',
            'especialidades_list': especialidades_list,
            'filtro_fecha_desde': filtro_fecha_desde, 'filtro_fecha_hasta': filtro_fecha_hasta, 'filtro_especialidad': filtro_especialidad,
        })

    df['monto_usd'] = pd.to_numeric(df['monto_usd'], errors='coerce').fillna(0)
    df['especialidad'] = df['especialidad'].fillna('OTROS').astype(str).str.upper().str.strip()
    df['estatus'] = df['estatus'].fillna('SIN ESTATUS').astype(str).str.upper().str.strip()
    df['proveedor'] = df['proveedor'].fillna('NO IDENTIFICADO').astype(str).str.upper().str.strip()
    df = df[df['monto_usd'] > 0]
    config_html = {'full_html': False, 'include_plotlyjs': False, 'config': PLOTLY_CONFIG}

    # Alertas (valor operativo): días sin actualizar (vía epoch para evitar tz-naive vs tz-aware)
    alertas = []
    if 'actualizado_en' in df.columns and df['actualizado_en'].notna().any():
        ts_actualizado = pd.to_datetime(df['actualizado_en'], errors='coerce')

        def _to_epoch(t):
            if t is pd.NaT or pd.isna(t):
                return float('nan')
            try:
                return t.timestamp()
            except Exception:
                return float('nan')

        actualizado_sec = ts_actualizado.map(_to_epoch)
        ahora_sec = timezone.now().timestamp()
        df['dias_sin_actualizar'] = ((ahora_sec - actualizado_sec) / 86400).fillna(0)
    # Alertas: casos pendientes (estatus PENDIENTE)
    if 'estatus' in df.columns:
        df_pend = df[df['estatus'].astype(str).str.upper().str.strip() == 'PENDIENTE']
        if len(df_pend) > 0:
            n_pend = len(df_pend)
            list_pend = [{'nro_caso': str(r.get('nro_caso', '')), 'especialidad': str(r.get('especialidad', '')), 'monto_usd': f"${float(r.get('monto_usd') or 0):,.2f}" if pd.notna(r.get('monto_usd')) else "—", 'estatus': str(r.get('estatus', ''))} for _, r in df_pend.iterrows()]
            alertas.append({'tipo': 'warning', 'texto': f'{n_pend} caso(s) pendientes.', 'link': '/admin/gestion_social/solicitud/?estatus__exact=PENDIENTE', 'casos': list_pend})
    # Alertas: casos pendientes Y críticos (urgentes), estilo vinotinto
    if 'estatus' in df.columns and 'nivel_prioridad' in df.columns:
        df_urg = df[
            (df['estatus'].astype(str).str.upper().str.strip() == 'PENDIENTE') &
            (df['nivel_prioridad'].astype(str).str.upper().str.strip() == 'CRÍTICO')
        ].copy()
        if len(df_urg) > 0:
            n_urg = len(df_urg)
            casos_urgentes_list = []
            for _, r in df_urg.iterrows():
                monto = r.get('monto_usd')
                monto_str = f"${float(monto):,.2f}" if pd.notna(monto) else "—"
                casos_urgentes_list.append({
                    'nro_caso': str(r.get('nro_caso', '')),
                    'especialidad': str(r.get('especialidad', '')),
                    'monto_usd': monto_str,
                    'estatus': str(r.get('estatus', '')),
                })
            alertas.append({
                'tipo': 'urgente',
                'texto': f'{n_urg} caso(s) pendientes y críticos.',
                'link': '/admin/gestion_social/solicitud/?estatus__exact=PENDIENTE&nivel_prioridad__exact=CR%C3%8DTICO',
                'casos': casos_urgentes_list,
            })

    total_gasto = df['monto_usd'].sum()
    total_casos = len(df)
    casos_criticos = len(df[df['nivel_prioridad'] == 'CRÍTICO'])

    # --- Tacómetro: nivel de cierre (solo en pestaña detallada, contenedor fijo) ---
    estatus_cierre = df['estatus'].str.upper().str.contains('APROBADO|PAGADO|CERRADO|COMPLETADO', na=False)
    pct_cierre = (estatus_cierre.sum() / total_casos * 100) if total_casos else 0
    pct_cierre = min(100, round(float(pct_cierre), 0))
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct_cierre,
        number={'suffix': '%', 'font': {'size': 22}},
        title={'text': "Nivel de cierre (estatus cerrados)", 'font': {'size': 13}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickfont': {'size': 10}},
            'bar': {'color': "#38666A"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#38666A",
            'steps': [
                {'range': [0, 33], 'color': 'rgba(220, 53, 69, 0.25)'},
                {'range': [33, 66], 'color': 'rgba(255, 193, 7, 0.35)'},
                {'range': [66, 100], 'color': 'rgba(25, 135, 84, 0.35)'},
            ],
            'threshold': {
                'line': {'color': "#38666A", 'width': 4},
                'thickness': 0.8,
                'value': pct_cierre,
            },
        },
    ))
    fig_gauge.update_layout(
        margin=dict(l=30, r=30, t=45, b=20), paper_bgcolor='rgba(0,0,0,0)',
        height=260, autosize=True,
        font=dict(size=12),
    )
    html_gauge = pio.to_html(fig_gauge, **config_html)

    # --- Segundo tacómetro: % casos críticos sobre total ---
    pct_criticos = (casos_criticos / total_casos * 100) if total_casos else 0
    pct_criticos = min(100, round(float(pct_criticos), 0))
    fig_gauge2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct_criticos,
        number={'suffix': '%', 'font': {'size': 22}},
        title={'text': "Casos críticos (sobre total)", 'font': {'size': 13}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickfont': {'size': 10}},
            'bar': {'color': "#5c4a47"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#5c4a47",
            'steps': [
                {'range': [0, 25], 'color': 'rgba(25, 135, 84, 0.3)'},
                {'range': [25, 50], 'color': 'rgba(255, 193, 7, 0.35)'},
                {'range': [50, 100], 'color': 'rgba(220, 53, 69, 0.25)'},
            ],
            'threshold': {
                'line': {'color': "#5c4a47", 'width': 4},
                'thickness': 0.8,
                'value': pct_criticos,
            },
        },
    ))
    fig_gauge2.update_layout(
        margin=dict(l=30, r=30, t=45, b=20), paper_bgcolor='rgba(0,0,0,0)',
        height=260, autosize=True, font=dict(size=12),
    )
    html_gauge2 = pio.to_html(fig_gauge2, **config_html)

    # --- Tercer tacómetro: concentración del gasto en la top especialidad ---
    df_top_esp = df.groupby('especialidad')['monto_usd'].sum().sort_values(ascending=False)
    top_esp_monto = float(df_top_esp.iloc[0]) if len(df_top_esp) else 0
    pct_top = (top_esp_monto / total_gasto * 100) if total_gasto else 0
    pct_top = min(100, round(float(pct_top), 0))
    fig_gauge3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=pct_top,
        number={'suffix': '%', 'font': {'size': 22}},
        title={'text': "Concentración gasto (top especialidad)", 'font': {'size': 12}},
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickfont': {'size': 10}},
            'bar': {'color': "#2c3e50"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "#2c3e50",
            'steps': [
                {'range': [0, 33], 'color': 'rgba(25, 135, 84, 0.25)'},
                {'range': [33, 66], 'color': 'rgba(255, 193, 7, 0.3)'},
                {'range': [66, 100], 'color': 'rgba(220, 53, 69, 0.2)'},
            ],
            'threshold': {
                'line': {'color': "#2c3e50", 'width': 4},
                'thickness': 0.8,
                'value': pct_top,
            },
        },
    ))
    fig_gauge3.update_layout(
        margin=dict(l=30, r=30, t=45, b=20), paper_bgcolor='rgba(0,0,0,0)',
        height=260, autosize=True, font=dict(size=12),
    )
    html_gauge3 = pio.to_html(fig_gauge3, **config_html)

    # --- Casos vs inversión por especialidad: barras horizontales (estable y legible) ---
    df_bub = df.groupby('especialidad').agg(casos=('nro_caso', 'count'), monto_usd=('monto_usd', 'sum')).reset_index()
    df_bub = df_bub.sort_values('monto_usd', ascending=True).tail(10)
    df_bub['monto_usd'] = df_bub['monto_usd'].astype(float)
    df_bub['texto_barra'] = df_bub.apply(lambda r: "{} casos · ${:,.0f}".format(int(r['casos']), float(r['monto_usd'])), axis=1)
    fig_bubble = px.bar(
        df_bub, y='especialidad', x='monto_usd', orientation='h',
        title='🎈 Casos e inversión por especialidad',
        text='texto_barra', color='monto_usd', color_continuous_scale='Teal',
        hover_data={'casos': True, 'monto_usd': True},
    )
    fig_bubble.update_traces(textposition='outside', textfont=dict(size=10))
    fig_bubble.update_layout(
        xaxis_title='Inversión ($)', yaxis_title='',
        margin=dict(l=10, r=80, t=45, b=20), height=400,
        plot_bgcolor='white', paper_bgcolor='white',
        showlegend=False, yaxis={'categoryorder': 'total ascending'},
    )
    html_bubble = pio.to_html(fig_bubble, **config_html)

    # --- Sunburst: prioridad -> especialidad ---
    df_sun = df.groupby(['nivel_prioridad', 'especialidad']).agg(casos=('nro_caso', 'count')).reset_index()
    df_sun = df_sun.sort_values('casos', ascending=False).head(25)
    fig_sunburst = px.sunburst(df_sun, path=['nivel_prioridad', 'especialidad'], values='casos',
                               title='☀️ Distribución por prioridad y especialidad',
                               color='casos', color_continuous_scale='Blues')
    fig_sunburst.update_layout(margin=dict(l=10, r=10, t=45, b=10), height=400, paper_bgcolor='rgba(0,0,0,0)')
    html_sunburst = pio.to_html(fig_sunburst, **config_html)

    # --- Embudo: por estatus (cantidad de casos) ---
    df_fun = df.groupby('estatus')['nro_caso'].count().reset_index(name='casos')
    df_fun = df_fun.sort_values('casos', ascending=True)
    fig_funnel = px.funnel(df_fun, x='casos', y='estatus', title='📉 Embudo por estatus',
                           color_discrete_sequence=px.colors.qualitative.Set3)
    fig_funnel.update_layout(margin=dict(l=20, r=20, t=45, b=20), height=380, paper_bgcolor='rgba(0,0,0,0)',
                             xaxis_title='Nº de casos', yaxis_title='')
    html_funnel = pio.to_html(fig_funnel, **config_html)

    # --- Treemap: especialidades por monto (área proporcional al valor, plano) ---
    df_tree = df.groupby('especialidad')['monto_usd'].sum().reset_index()
    df_tree = df_tree.sort_values('monto_usd', ascending=False).head(12)
    df_tree['monto_usd'] = df_tree['monto_usd'].astype(float)
    labels = df_tree['especialidad'].tolist()
    values = df_tree['monto_usd'].tolist()
    parents = [""] * len(labels)
    text_list = [f"${v:,.0f}" for v in values]
    v_min, v_max = min(values), max(values)
    fig_treemap = go.Figure(go.Treemap(
        labels=labels,
        parents=parents,
        values=values,
        text=text_list,
        textinfo="label+text",
        branchvalues="total",
        marker=dict(
            colorscale="Tealgrn",
            cmin=v_min,
            cmax=v_max,
            colors=values,
            colorbar=dict(title="Monto ($)"),
        ),
        hovertemplate="%{label}<br>Monto: $%{value:,.0f}<extra></extra>",
    ))
    fig_treemap.update_layout(
        title='🗺️ Inversión por especialidad (área = monto)',
        margin=dict(l=10, r=10, t=45, b=10), height=400, paper_bgcolor='rgba(0,0,0,0)',
    )
    html_treemap = pio.to_html(fig_treemap, **config_html)

    # --- Barras horizontales Top 8 Especialidades (existente) ---
    df_esp = df.groupby('especialidad')['monto_usd'].sum().reset_index()
    df_esp['pct'] = (df_esp['monto_usd'] / total_gasto * 100).round(1)
    df_esp = df_esp.sort_values('monto_usd', ascending=True).tail(8)
    df_esp['label'] = df_esp.apply(lambda x: f"${x['monto_usd']:,.0f} ({x['pct']}%)", axis=1)
    fig_gasto = px.bar(df_esp, x="monto_usd", y="especialidad", orientation='h', text="label",
                       title='💰 Top 8 Especialidades', color="monto_usd", color_continuous_scale='Blues')
    fig_gasto.update_traces(textposition='inside', textfont_color='white')
    fig_gasto.update_layout(
        yaxis_title="", xaxis_title="Inversión ($)", margin=dict(l=10, r=10, t=40, b=10),
        height=400, width=700, autosize=False,
    )
    html_gasto = pio.to_html(fig_gasto, **config_html)
    txt_gasto = f"Líder en gasto: <b>{df_esp.iloc[-1]['especialidad']}</b>"

    # --- Dona Estatus (existente) ---
    df_status = df.groupby('estatus')['monto_usd'].sum().reset_index()
    fig_status = px.pie(df_status, values='monto_usd', names='estatus', title='📂 Estatus de Solicitudes',
                        hole=0.4, color_discrete_sequence=px.colors.qualitative.Pastel)
    fig_status.update_traces(textposition='inside', textinfo='percent+label')
    fig_status.update_layout(
        showlegend=False, margin=dict(l=20, r=20, t=40, b=20),
        height=380, autosize=True,
    )
    html_status = pio.to_html(fig_status, **config_html)
    txt_status = "Distribución del presupuesto por fase del trámite."

    # --- Barras Top 5 Proveedores (existente) ---
    df_prov = df.groupby('proveedor')['monto_usd'].sum().reset_index()
    total_p = df_prov['monto_usd'].sum()
    df_prov['pct'] = (df_prov['monto_usd'] / total_p * 100).round(1)
    df_prov = df_prov.sort_values('monto_usd', ascending=False).head(5)
    df_prov['label'] = df_prov.apply(lambda x: f"${x['monto_usd']:,.0f}<br>({x['pct']}%)", axis=1)
    fig_prov = px.bar(df_prov, x='proveedor', y='monto_usd', title='🏥 Top 5 Proveedores', text='label',
                      color='monto_usd', color_continuous_scale='Teal')
    fig_prov.update_traces(textposition='outside', cliponaxis=False)
    fig_prov.update_layout(
        xaxis_title="", yaxis_title="Pagado ($)", margin=dict(l=20, r=20, t=60, b=50),
        height=380, autosize=True,
    )
    html_prov = pio.to_html(fig_prov, **config_html)
    top_p = df_prov.iloc[0]['proveedor']
    txt_prov = f"El proveedor principal es <b>{top_p}</b>."

    # --- Resumen ejecutivo: tendencia de gasto por mes ---
    # Período: priorizar fecha_recepcion (variada en demo), luego creado_en, luego mes
    if 'fecha_recepcion' in df.columns and df['fecha_recepcion'].notna().any():
        period_fecha = pd.to_datetime(df['fecha_recepcion'], errors='coerce').dt.to_period('M').astype(str)
        period_fecha = period_fecha.replace('NaT', '')
    else:
        period_fecha = pd.Series([''] * len(df), index=df.index)
    period_creado = pd.to_datetime(df['creado_en'], errors='coerce').dt.to_period('M').astype(str).replace('NaT', '')
    df['_periodo'] = period_fecha.where(period_fecha.astype(str).str.len() > 0, period_creado)
    if (df['_periodo'] == '').all() and 'mes' in df.columns:
        df['_periodo'] = df['mes'].fillna('').astype(str)
    if (df['_periodo'] == '').all():
        df['_periodo'] = 'Total'
    df_mes = df.groupby('_periodo', as_index=False)['monto_usd'].sum().rename(columns={'_periodo': 'periodo'})
    df_mes = df_mes[df_mes['periodo'] != ''].sort_values('periodo').tail(12)
    if df_mes.empty:
        df_mes = pd.DataFrame([{'periodo': 'Actual', 'monto_usd': total_gasto}])
    fig_tendencia = px.line(df_mes, x='periodo', y='monto_usd', title='📈 Tendencia de ejecución por período',
                            markers=True, labels={'monto_usd': 'Monto ($)', 'periodo': 'Período'})
    fig_tendencia.update_layout(margin=dict(l=20, r=20, t=40, b=40), height=320, paper_bgcolor='rgba(0,0,0,0)')
    html_tendencia = pio.to_html(fig_tendencia, **config_html)

    # --- Comparativa: período actual vs anterior ---
    if len(df_mes) >= 2:
        ultimos = df_mes.tail(2).reset_index(drop=True)
        periodos = ultimos['periodo'].astype(str).tolist()
        montos = ultimos['monto_usd'].astype(float).tolist()
        fig_comp = go.Figure(data=[go.Bar(x=periodos, y=montos, marker_color=['#5c4a47', '#38666A'], text=[f'${m:,.0f}' for m in montos], textposition='outside')])
    else:
        fig_comp = go.Figure(data=[go.Bar(x=['Total'], y=[float(total_gasto)], marker_color='#38666A', text=f'${total_gasto:,.0f}', textposition='outside')])
    fig_comp.update_layout(title='📊 Comparativa últimos períodos', xaxis_title='Período', yaxis_title='Monto ($)', margin=dict(l=20, r=20, t=40, b=40), height=300, paper_bgcolor='rgba(0,0,0,0)')
    html_comparativa = pio.to_html(fig_comp, **config_html)

    # --- Visión histórica: series temporales por período (mes) y traza por caso ---
    html_hist_casos = html_hist_monto = html_hist_criticos = html_hist_evol = html_hist_traza = ""
    html_hist_area = html_hist_violin = ""
    if '_periodo' in df.columns and (df['_periodo'].astype(str).str.strip() != '').any():
        df_hist = df[df['_periodo'].astype(str).str.strip() != ''].copy()
        # Orden cronológico: periodo tipo YYYY-MM ordena bien como string
        por_mes = df_hist.groupby('_periodo', as_index=False).agg(
            casos=('nro_caso', 'count'),
            monto_usd=('monto_usd', 'sum'),
        ).rename(columns={'_periodo': 'periodo'})
        por_mes = por_mes[por_mes['periodo'].astype(str).str.len() >= 6].sort_values('periodo').tail(24)
        por_mes_crit = df_hist[df_hist['nivel_prioridad'].astype(str).str.upper() == 'CRÍTICO'].groupby('_periodo', as_index=False).agg(
            casos_criticos=('nro_caso', 'count'),
        ).rename(columns={'_periodo': 'periodo'})
        try:
            # Traza de cada caso: un punto por caso (período vs monto), hover con nro_caso y detalles
            traza_df = df_hist[['_periodo', 'monto_usd', 'nro_caso', 'especialidad', 'estatus']].copy()
            traza_df = traza_df.rename(columns={'_periodo': 'periodo'})
            traza_df['monto_usd'] = traza_df['monto_usd'].astype(float)
            if len(traza_df) > 0:
                fig_traza = px.scatter(
                    traza_df, x='periodo', y='monto_usd',
                    hover_data={'nro_caso': True, 'especialidad': True, 'estatus': True, 'monto_usd': ':.2f'},
                    title='📌 Traza de cada caso: evolución en el tiempo (cada punto = un caso)',
                    labels={'periodo': 'Período', 'monto_usd': 'Monto ($)'},
                )
                fig_traza.update_traces(marker=dict(size=8, opacity=0.7, line=dict(width=0.5, color='#2c3e50')))
                fig_traza.update_layout(margin=dict(l=20, r=20, t=50, b=80), height=380, paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45, showlegend=False)
                html_hist_traza = pio.to_html(fig_traza, **config_html)
            # Casos por período: barras verticales (forma distinta, vistoso)
            fig_hist_casos = go.Figure(data=[
                go.Bar(
                    x=por_mes['periodo'], y=por_mes['casos'],
                    name='Casos', marker_color='#1a5276', marker_line_color='#0e3d52',
                    marker_line_width=1, text=por_mes['casos'], textposition='outside',
                )
            ])
            fig_hist_casos.update_layout(
                title='📅 Cantidad de casos por período',
                xaxis_title='Período', yaxis_title='Casos',
                margin=dict(l=20, r=20, t=45, b=60), height=320, paper_bgcolor='rgba(0,0,0,0)',
                xaxis_tickangle=-45, showlegend=False,
                plot_bgcolor='rgba(248,249,250,0.8)', bargap=0.25,
            )
            html_hist_casos = pio.to_html(fig_hist_casos, **config_html)

            # Monto por período: área rellena (forma distinta)
            fig_hist_monto = go.Figure(data=[
                go.Scatter(
                    x=por_mes['periodo'], y=por_mes['monto_usd'],
                    fill='tozeroy', mode='lines',
                    line=dict(color='#d35400', width=2.5),
                    fillcolor='rgba(211,84,0,0.35)', name='Monto ($)',
                )
            ])
            fig_hist_monto.update_layout(
                title='📅 Monto ejecutado por período',
                xaxis_title='Período', yaxis_title='Monto ($)',
                margin=dict(l=20, r=20, t=45, b=60), height=320, paper_bgcolor='rgba(0,0,0,0)',
                xaxis_tickangle=-45, showlegend=False,
                plot_bgcolor='rgba(255,250,240,0.6)',
            )
            html_hist_monto = pio.to_html(fig_hist_monto, **config_html)

            por_mes_merge = por_mes.merge(por_mes_crit, on='periodo', how='left') if not por_mes_crit.empty else por_mes.assign(casos_criticos=0)
            por_mes_merge['casos_criticos'] = por_mes_merge.get('casos_criticos', pd.Series(0, index=por_mes_merge.index)).fillna(0).astype(int)
            if not por_mes_merge.empty:
                fig_hist_criticos = px.bar(por_mes_merge, x='periodo', y='casos_criticos', title='📅 Casos críticos por período',
                                           labels={'casos_criticos': 'Casos críticos', 'periodo': 'Período'})
                fig_hist_criticos.update_traces(marker_color='#c0392b')
                fig_hist_criticos.update_layout(margin=dict(l=20, r=20, t=40, b=60), height=320, paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45)
                html_hist_criticos = pio.to_html(fig_hist_criticos, **config_html)

            # Evolución acumulada: una serie como área, otra como línea gruesa (forma distinta)
            por_mes_evol = por_mes.copy()
            por_mes_evol['acumulado_casos'] = por_mes_evol['casos'].cumsum()
            por_mes_evol['acumulado_monto'] = por_mes_evol['monto_usd'].cumsum()
            fig_evol = go.Figure()
            fig_evol.add_trace(go.Scatter(
                x=por_mes_evol['periodo'], y=por_mes_evol['acumulado_casos'],
                name='Casos (acum.)', fill='tozeroy', mode='lines',
                line=dict(color='#2874a6', width=2), fillcolor='rgba(40,116,166,0.25)',
            ))
            fig_evol.add_trace(go.Scatter(
                x=por_mes_evol['periodo'], y=por_mes_evol['acumulado_monto'],
                name='Monto acum. ($)', mode='lines+markers', yaxis='y2',
                line=dict(color='#922b21', width=3, dash='dot'),
                marker=dict(symbol='diamond', size=8),
            ))
            fig_evol.update_layout(
                title='📅 Evolución acumulada: casos y monto',
                margin=dict(l=20, r=20, t=45, b=60), height=340, paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45,
                yaxis=dict(title='Casos acumulados', gridcolor='rgba(0,0,0,0.06)'),
                yaxis2=dict(title='Monto acum. ($)', overlaying='y', side='right', gridcolor='rgba(0,0,0,0.04)'),
                legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1),
                plot_bgcolor='rgba(248,249,250,0.5)',
            )
            html_hist_evol = pio.to_html(fig_evol, **config_html)

            # Gráfico de área: casos por período (área rellena, picos y valles visibles)
            if not por_mes.empty:
                fig_area = px.area(
                    por_mes, x='periodo', y='casos',
                    title='📊 Casos por período (área)',
                    labels={'periodo': 'Período', 'casos': 'Casos'},
                )
                fig_area.update_traces(fill='tozeroy', line=dict(color='#38666A', width=2))
                fig_area.update_layout(margin=dict(l=20, r=20, t=40, b=60), height=320, paper_bgcolor='rgba(0,0,0,0)', xaxis_tickangle=-45)
                html_hist_area = pio.to_html(fig_area, **config_html)

        except Exception:
            pass

    # Violin por especialidad (para pestaña Visión detallada; usa todos los datos filtrados)
    if not df.empty and 'especialidad' in df.columns and 'monto_usd' in df.columns:
        try:
            violin_df = df[['especialidad', 'monto_usd']].copy()
            violin_df['monto_usd'] = violin_df['monto_usd'].astype(float)
            violin_df = violin_df[violin_df['monto_usd'].notna() & (violin_df['monto_usd'] > 0)]
            if len(violin_df) >= 5:
                fig_violin = px.violin(
                    violin_df, x='especialidad', y='monto_usd',
                    title='🎻 Distribución del monto por especialidad (Violin)',
                    labels={'especialidad': 'Especialidad', 'monto_usd': 'Monto ($)'},
                    box=False,
                    points=False,
                )
                fig_violin.update_traces(
                    line_color='#38666A',
                    line_width=1.5,
                    fillcolor='rgba(56,102,106,0.6)',
                    meanline_visible=True,
                    spanmode='soft',
                    scalegroup='all',
                    scalemode='width',
                )
                fig_violin.update_layout(
                    margin=dict(l=20, r=20, t=45, b=100),
                    height=400,
                    paper_bgcolor='rgba(0,0,0,0)',
                    xaxis_tickangle=-35,
                    showlegend=False,
                )
                html_hist_violin = pio.to_html(fig_violin, **config_html)
        except Exception:
            pass

    # --- Mapa interactivo Venezuela (Folium/Leaflet): zoom, arrastre, clic en marcadores ---
    df_estado = df.copy()
    df_estado['estado'] = df_estado.get('estado', pd.Series([None] * len(df_estado))).fillna('NO ESPECIFICADO').astype(str).str.strip().str.upper()
    df_estado.loc[df_estado['estado'] == '', 'estado'] = 'NO ESPECIFICADO'
    por_estado = df_estado.groupby('estado').agg(casos=('nro_caso', 'count'), monto_usd=('monto_usd', 'sum')).reset_index()

    vista_mapa = request.GET.get('mapa', 'circulos').lower()
    if vista_mapa not in ('circulos', 'pins', 'heatmap', 'estados'):
        vista_mapa = 'circulos'
    html_mapa_venezuela = ""
    try:
        if folium is not None:
            m = folium.Map(location=[8, -66], zoom_start=5, tiles='OpenStreetMap', control_scale=True)
            max_casos = por_estado['casos'].max() if len(por_estado) else 1
            popups_data = []
            for _, row in por_estado.iterrows():
                estado_nom = str(row['estado']).strip().upper()
                if estado_nom in ('NAN', ''):
                    estado_nom = 'NO ESPECIFICADO'
                coord = VENEZUELA_ESTADOS_CENTROIDS.get(estado_nom) or VENEZUELA_ESTADOS_CENTROIDS.get(estado_nom.replace('Á', 'A').replace('Í', 'I').replace('É', 'E').replace('Ó', 'O').replace('Ú', 'U')) or (10.48, -66.9)
                casos = int(row['casos'])
                monto = float(row['monto_usd'])
                popup_html = f"<div style='min-width:140px;'><b>{estado_nom}</b><br>Casos: <b>{casos}</b><br>Monto: <b>${monto:,.0f}</b></div>"
                tooltip_text = f"{estado_nom} — {casos} casos · ${monto:,.0f}"
                popups_data.append((coord[0], coord[1], estado_nom, casos, monto, popup_html, tooltip_text))

            if vista_mapa == 'estados':
                estado_to_casos = dict(zip(por_estado['estado'].str.strip().str.upper(), por_estado['casos'].astype(int)))
                estado_to_monto = dict(zip(por_estado['estado'].str.strip().str.upper(), por_estado['monto_usd'].astype(float)))
                max_c = max(estado_to_casos.values()) if estado_to_casos else 1

                def _norm(s):
                    return (s or '').replace('Á', 'A').replace('Í', 'I').replace('É', 'E').replace('Ó', 'O').replace('Ú', 'U')

                geojson_folium_path = os.path.join(os.path.dirname(__file__), 'static', 'geojson', 'venezuela_estados.geojson')
                if os.path.exists(geojson_folium_path):
                    try:
                        with open(geojson_folium_path, 'r', encoding='utf-8') as fh:
                            base_geojson = json.load(fh)
                    except Exception:
                        base_geojson = _geojson_estados_venezuela()
                else:
                    base_geojson = _geojson_estados_venezuela()
                for f in base_geojson['features']:
                    name = (f.get('properties') or {}).get('name') or ''
                    casos = estado_to_casos.get(name) or estado_to_casos.get(_norm(name)) or 0
                    monto = estado_to_monto.get(name) or estado_to_monto.get(_norm(name)) or 0
                    f['properties']['casos'] = int(casos)
                    f['properties']['monto'] = f'${monto:,.0f}'

                def style_fn(feature):
                    casos = (feature.get('properties') or {}).get('casos') or 0
                    if max_c and casos > 0:
                        r = min(1.0, casos / max_c)
                        if r >= 0.6:
                            color = '#c0392b'
                        elif r >= 0.3:
                            color = '#e67e22'
                        elif r >= 0.1:
                            color = '#f1c40f'
                        else:
                            color = '#7f8c8d'
                    else:
                        color = '#bdc3c7'
                    return {'fillColor': color, 'color': '#2c3e50', 'weight': 1.2, 'fillOpacity': 0.75}

                def highlight_fn(feature):
                    return {'weight': 2.5, 'fillOpacity': 0.9}

                g = folium.GeoJson(
                    base_geojson,
                    style_function=style_fn,
                    highlight_function=highlight_fn,
                    tooltip=folium.GeoJsonTooltip(
                        fields=['name', 'casos', 'monto'],
                        aliases=['Estado', 'Casos', 'Monto'],
                        localize=True,
                    ),
                )
                g.add_to(m)
            elif vista_mapa == 'heatmap' and HeatMap is not None:
                heatmap_data = [[c[0], c[1], c[3]] for c in popups_data]
                HeatMap(heatmap_data, min_opacity=0.35, max_zoom=12, radius=35, blur=25,
                       gradient={0.2: 'blue', 0.4: 'lime', 0.6: 'yellow', 0.8: 'orange', 1.0: 'red'}).add_to(m)
            elif vista_mapa == 'pins':
                for c in popups_data:
                    color = 'red' if c[3] >= (max_casos * 0.5) else 'orange' if c[3] >= (max_casos * 0.25) else 'blue'
                    folium.Marker(
                        location=[c[0], c[1]],
                        popup=folium.Popup(c[5], max_width=220),
                        tooltip=c[6],
                        icon=folium.Icon(color=color, icon='info-sign'),
                    ).add_to(m)
            else:
                for c in popups_data:
                    coord, estado_nom, casos, monto, popup_html, tooltip_text = (c[0], c[1]), c[2], c[3], c[4], c[5], c[6]
                    radio = max(8, min(25, 6 + (casos / max(1, max_casos)) * 18))
                    color = '#c0392b' if casos >= (max_casos * 0.5) else '#e74c3c' if casos >= (max_casos * 0.25) else '#e67e22' if casos > 0 else '#95a5a6'
                    folium.CircleMarker(
                        location=[coord[0], coord[1]],
                        radius=radio,
                        popup=folium.Popup(popup_html, max_width=220),
                        tooltip=tooltip_text,
                        color='#2c3e50',
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.75,
                        weight=1.5,
                    ).add_to(m)
            m.get_root().width = '100%'
            m.get_root().height = '550px'
            html_mapa_venezuela = m._repr_html_()
    except Exception:
        pass
    if not html_mapa_venezuela:
        # Tabla de datos por estado (sin mensajes operativos)
        filas = []
        for _, row in por_estado.iterrows():
            estado_nom = str(row['estado']).strip().upper() or 'NO ESPECIFICADO'
            casos = int(row['casos'])
            monto = float(row['monto_usd'])
            filas.append(f"<tr><td>{estado_nom}</td><td>{casos}</td><td>${monto:,.0f}</td></tr>")
        html_mapa_venezuela = (
            "<div style='padding:1rem;background:#f8f9fa;border-radius:8px;'>"
            "<p class='mb-3'><strong>🗺️ Casos por estado</strong></p>"
            "<table class='table table-bordered table-sm'><thead><tr><th>Estado</th><th>Casos</th><th>Monto</th></tr></thead><tbody>"
            + "".join(filas) + "</tbody></table></div>"
        )

    # --- Mapa por estados: solo pydeck (polígonos reales, paleta ejecutiva) ---
    mapa_estados_opciones = []
    estado_to_casos = {}
    estado_to_monto = {}
    base_geojson_estados = None
    _norm_plotly = lambda s: (s or '').replace('Á', 'A').replace('Í', 'I').replace('É', 'E').replace('Ó', 'O').replace('Ú', 'U')

    if not por_estado.empty:
        estado_to_casos = dict(zip(por_estado['estado'].str.strip().str.upper(), por_estado['casos'].astype(int)))
        estado_to_monto = dict(zip(por_estado['estado'].str.strip().str.upper(), por_estado['monto_usd'].astype(float)))
        geojson_file = os.path.join(os.path.dirname(__file__), 'static', 'geojson', 'venezuela_estados.geojson')
        if os.path.exists(geojson_file):
            try:
                with open(geojson_file, 'r', encoding='utf-8') as f:
                    base_geojson_estados = json.load(f)
            except Exception:
                base_geojson_estados = None
        else:
            base_geojson_estados = None

    def _add_opcion(oid, nombre, html, mensaje=None):
        mapa_estados_opciones.append({'id': oid, 'nombre': nombre, 'html': html or '', 'mensaje': mensaje})

    mapa_estados_leyenda_pct = False
    mapa_estados_pct_min = None
    mapa_estados_pct_max = None
    try:
        import pydeck as pdk
        if base_geojson_estados and estado_to_casos:
            geojson_pydeck = json.loads(json.dumps(base_geojson_estados))
            total_casos_mapa = sum(estado_to_casos.values()) or 1
            pcts_list = []
            for feat in geojson_pydeck.get('features', []):
                p = dict(feat.get('properties') or {})
                name = (p.get('name') or p.get('NAME') or '').strip().upper()
                if not name:
                    continue
                casos = int(estado_to_casos.get(name) or estado_to_casos.get(_norm_plotly(name)) or 0)
                monto = float(estado_to_monto.get(name) or estado_to_monto.get(_norm_plotly(name)) or 0)
                pct = (casos / total_casos_mapa * 100) if total_casos_mapa else 0
                p['name'] = name
                p['casos'] = casos
                p['pct'] = round(pct, 1)
                p['monto'] = round(monto, 0)
                pcts_list.append(pct)
                feat['properties'] = p
            min_pct = min(pcts_list) if pcts_list else 0
            max_pct = max(pcts_list) if pcts_list else 0
            rango_pct = (max_pct - min_pct) or 1
            for feat in geojson_pydeck.get('features', []):
                p = feat.get('properties') or {}
                if 'pct' not in p:
                    continue
                pct = p['pct']
                pct_norm = (pct - min_pct) / rango_pct
                pct_norm = max(0, min(1.0, pct_norm))
                p['pct_norm_curved'] = (pct_norm ** 0.35) if pct_norm >= 0 else 0
                feat['properties'] = p
            mapa_estados_pct_min = round(min_pct, 1)
            mapa_estados_pct_max = round(max_pct, 1)
            # Color por % del total: escala entre mínimo y máximo observados (mejor contraste)
            layer_estados = pdk.Layer(
                'GeoJsonLayer',
                geojson_pydeck,
                get_fill_color='[5 + 235 * (1 - properties.pct_norm_curved), 35 + 213 * (1 - properties.pct_norm_curved), 75 + 180 * (1 - properties.pct_norm_curved)]',
                get_line_color=[30, 50, 80],
                line_width_min_pixels=1.2,
                pickable=True,
                auto_highlight=True,
            )
            view = pdk.ViewState(latitude=8, longitude=-66, zoom=4.2, pitch=0)
            tooltip = {
                'html': '<b>{name}</b><br>Casos: {casos} ({pct}%)<br>Monto: {monto}',
                'style': {'backgroundColor': '#1a365d', 'color': 'white', 'fontSize': '13px'},
            }
            deck = pdk.Deck(
                layers=[layer_estados],
                initial_view_state=view,
                map_style='road',
                tooltip=tooltip,
            )
            _add_opcion('pydeck', 'pydeck', deck.to_html(as_string=True))
            mapa_estados_leyenda_pct = True
        else:
            _add_opcion('pydeck', 'pydeck', None, 'Polígonos reales: ejecute python manage.py descargar_geojson_venezuela')
    except ImportError:
        _add_opcion('pydeck', 'pydeck', None, 'Instale: pip install pydeck')
    except Exception as e:
        _add_opcion('pydeck', 'pydeck', None, str(e)[:80])

    context = {
        'total_usd': f"{total_gasto:,.2f}",
        'total_casos': total_casos,
        'casos_criticos': casos_criticos,
        'html_gasto': html_gasto, 'txt_gasto': txt_gasto,
        'html_status': html_status, 'txt_status': txt_status,
        'html_prov': html_prov, 'txt_prov': txt_prov,
        'html_gauge': html_gauge, 'html_gauge2': html_gauge2, 'html_gauge3': html_gauge3, 'html_bubble': html_bubble,
        'html_sunburst': html_sunburst, 'html_funnel': html_funnel, 'html_treemap': html_treemap,
        'html_tendencia': html_tendencia, 'html_comparativa': html_comparativa,
        'html_mapa_venezuela': html_mapa_venezuela,
        'html_hist_casos': html_hist_casos,
        'html_hist_monto': html_hist_monto,
        'html_hist_criticos': html_hist_criticos,
        'html_hist_evol': html_hist_evol,
        'html_hist_traza': html_hist_traza,
        'html_hist_area': html_hist_area,
        'html_hist_violin': html_hist_violin,
        'mapa_estados_opciones': mapa_estados_opciones,
        'nota_mapa_estados': 'La zona en reclamación no se representa en este mapa por no disponer de los polígonos exactos para incluirla.',
        'mapa_estados_leyenda_pct': mapa_estados_leyenda_pct,
        'mapa_estados_pct_min': mapa_estados_pct_min,
        'mapa_estados_pct_max': mapa_estados_pct_max,
        'vista_mapa': vista_mapa,
        'query_mapa_circulos': _query_map(request, 'circulos'),
        'query_mapa_pins': _query_map(request, 'pins'),
        'query_mapa_heatmap': _query_map(request, 'heatmap'),
        'query_mapa_estados': _query_map(request, 'estados'),
        'alertas': alertas, 'especialidades_list': especialidades_list,
        'filtro_fecha_desde': filtro_fecha_desde, 'filtro_fecha_hasta': filtro_fecha_hasta, 'filtro_especialidad': filtro_especialidad,
        'cortex_site_url': CORTEX_SITE_URL,
    }
    return render(request, 'dashboard.html', context)
