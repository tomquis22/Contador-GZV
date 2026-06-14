import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Contador GZV", layout="wide")

jugadores_lista = ["Mico", "Tomy", "Joaco", "Mate", "Enzo", "Juli", "Fabo", "Kitin", "Mati", "Mayco", "Nick", "Gutierrez", "Emi", "Sanchez"]

if 'pantalla' not in st.session_state:
    st.session_state['pantalla'] = 'seleccion'
if 'rival' not in st.session_state:
    st.session_state['rival'] = ''
if 'jugadores_activos' not in st.session_state:
    st.session_state['jugadores_activos'] = []
if 'puntos' not in st.session_state:
    st.session_state['puntos'] = {j: {'Remates': 0, 'Bloqueos': 0, 'Saques': 0, 'Errores': 0, 'Saques Fallados': 0} for j in jugadores_lista}
if 'puntos_rival' not in st.session_state:
    st.session_state['puntos_rival'] = {'Remates': 0, 'Bloqueos': 0, 'Saques': 0, 'Errores': 0}
if 'historial' not in st.session_state:
    st.session_state['historial'] = []
if 'historial_partido' not in st.session_state:
    st.session_state['historial_partido'] = [] # Aquí guardaremos cada set

def sumar_punto(jugador, accion):
    st.session_state['puntos'][jugador][accion] += 1
    st.session_state['historial'].append({'tipo': 'jugador', 'nombre': jugador, 'accion': accion})

def sumar_punto_rival(accion):
    st.session_state['puntos_rival'][accion] += 1
    st.session_state['historial'].append({'tipo': 'rival', 'accion': accion})

def deshacer_ultima_accion():
    if len(st.session_state['historial']) > 0:
        ultima = st.session_state['historial'].pop()
        
        if ultima['tipo'] == 'jugador':
            jugador = ultima['nombre']
            accion = ultima['accion']
            if st.session_state['puntos'][jugador][accion] > 0:
                st.session_state['puntos'][jugador][accion] -= 1
                
        elif ultima['tipo'] == 'rival':
            accion = ultima['accion']
            if st.session_state['puntos_rival'][accion] > 0:
                st.session_state['puntos_rival'][accion] -= 1

def generar_excel():
    todos_los_sets = st.session_state['historial_partido'] + [
        {'GZV': st.session_state['puntos'].copy(), 'Rival': st.session_state['puntos_rival'].copy()}
    ]
    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        for i, set_data in enumerate(todos_los_sets):
            df_gzv = pd.DataFrame(set_data['GZV']).T
            df_rival = pd.DataFrame([set_data['Rival']], index=[st.session_state['rival'] or 'Rival'])
            
            df_final = pd.concat([df_gzv, df_rival])
            df_final.to_excel(writer, sheet_name=f'Set {i+1}')
            
    return output.getvalue()

def iniciar_partido():
    st.session_state['pantalla'] = 'tablero'

@st.dialog("Fin del Partido / Set")
def popup_fin_set(ganador, score_ganador, score_perdedor):
    if 'fase_descarga' not in st.session_state:
        st.session_state['fase_descarga'] = False

    if not st.session_state['fase_descarga']:
        st.write(f"### ¡Ganador: **{ganador}**!")
        st.write(f"Marcador: **{score_ganador} - {score_perdedor}**")
        
        if st.button("Error (Deshacer)", use_container_width=True):
            deshacer_ultima_accion()
            st.rerun()

        if st.button("Siguiente Set", type="primary", use_container_width=True):
            st.session_state['historial_partido'].append({
                'GZV': st.session_state['puntos'].copy(),
                'Rival': st.session_state['puntos_rival'].copy()
            })

            st.session_state['puntos'] = {j: {'Remates': 0, 'Bloqueos': 0, 'Saques': 0, 'Errores': 0, 'Saques Fallados': 0} for j in jugadores_lista}
            st.session_state['puntos_rival'] = {'Remates': 0, 'Bloqueos': 0, 'Saques': 0, 'Errores': 0}
            st.session_state['historial'] = []
            st.session_state['ver_stats_fin'] = False
            st.rerun()

        if st.button("Terminar Partido", use_container_width=True):
            st.session_state['fase_descarga'] = True
            st.rerun()
            
    else:
        st.write("### ¿Descargar excel del partido?")
        st.write("El archivo incluirá las estadísticas de todos los sets jugados.")
        
        excel_data = generar_excel()
        st.download_button(
            label="Descargar Excel",
            data=excel_data,
            file_name=f"Estadisticas_GZV_vs_{st.session_state['rival'] or 'Rival'}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        if st.button("Finalizar y volver al inicio", type="primary", use_container_width=True):
            st.session_state.clear()
            st.rerun()

if st.session_state['pantalla'] == 'seleccion':
    st.title("🏐 Estadísticas GZV")
    
    st.session_state['rival'] = st.text_input("Equipo Rival:")
    st.session_state['jugadores_activos'] = st.multiselect("Seleccionar Jugadores", jugadores_lista)
    
    if st.button("Comenzar Set", type="primary"):
        iniciar_partido()
        st.rerun()

elif st.session_state['pantalla'] == 'tablero':
    rival_nombre = st.session_state['rival'] if st.session_state['rival'] != '' else 'Rival'
    st.title(f"GZV vs {rival_nombre}")

    total_gzv = sum(
        stats['Remates'] + stats['Bloqueos'] + stats['Saques'] 
        for stats in st.session_state['puntos'].values()
    ) + st.session_state['puntos_rival']['Errores']

    total_rival = (
        st.session_state['puntos_rival']['Remates'] + 
        st.session_state['puntos_rival']['Bloqueos'] + 
        st.session_state['puntos_rival']['Saques']
    ) + sum(
        stats['Errores'] + stats['Saques Fallados'] 
        for stats in st.session_state['puntos'].values()
    )

    if total_gzv >= 25 and (total_gzv - total_rival) >= 2:
        popup_fin_set("GZV", total_gzv, total_rival)
        
    elif total_rival >= 25 and (total_rival - total_gzv) >= 2:
        popup_fin_set(rival_nombre, total_rival, total_gzv)

    marcador_col1, marcador_col2, marcador_col3 = st.columns([1, 2, 1])
    with marcador_col2:
        st.markdown(f"<h1 style='text-align: center; font-size: 70px; margin-bottom: 0px;'>{total_gzv} - {total_rival}</h1>", unsafe_allow_html=True)
    
    with marcador_col3:
        st.write("")
        st.write("")
        if len(st.session_state['historial']) > 0:
            if st.button("Deshacer", type="secondary"):
                deshacer_ultima_accion()
                st.rerun()

    st.divider()

    cols_header = st.columns([2, 1, 1, 1, 1, 1])
    cols_header[0].write("**Jugador**")
    cols_header[1].write("**Remates**")
    cols_header[2].write("**Bloqueos**")
    cols_header[3].write("**Saques**")
    cols_header[4].write("**Errores**")
    cols_header[5].write("**Saques Fallados**")

    st.divider()

    for jugador in st.session_state['jugadores_activos']:
        cols = st.columns([2, 1, 1, 1, 1, 1])
        stats = st.session_state['puntos'][jugador]
        
        cols[0].write(f"**{jugador}**")
        
        if cols[1].button(f"{stats['Remates']}", key=f"R_{jugador}"):
            sumar_punto(jugador, 'Remates')
            st.rerun()
            
        if cols[2].button(f"{stats['Bloqueos']}", key=f"B_{jugador}"):
            sumar_punto(jugador, 'Bloqueos')
            st.rerun()
            
        if cols[3].button(f"{stats['Saques']}", key=f"S_{jugador}"):
            sumar_punto(jugador, 'Saques')
            st.rerun()
            
        if cols[4].button(f"{stats['Errores']}", key=f"E_{jugador}"):
            sumar_punto(jugador, 'Errores')
            st.rerun()

        if cols[5].button(f"{stats['Saques Fallados']}", key=f"F_{jugador}"):
            sumar_punto(jugador, 'Saques Fallados')
            st.rerun()

    st.divider()

    cols_header_rival = st.columns([2, 1, 1, 1, 1, 1])
    cols_header_rival[0].write("")
    cols_header_rival[1].write("**Remates**")
    cols_header_rival[2].write("**Bloqueos**")
    cols_header_rival[3].write("**Saques**")
    cols_header_rival[4].write("**Errores**")

    rival = st.session_state['rival'] if st.session_state['rival'] != '' else 'Rival'
    
    cols_rival = st.columns([2, 1, 1, 1, 1, 1])
    cols_rival[0].write(f"**{rival}**")
    
    stats_rival = st.session_state['puntos_rival']

    if cols_rival[1].button(f"{stats_rival['Remates']}", key="rival_remates"):
        sumar_punto_rival('Remates')
        st.rerun()

    if cols_rival[2].button(f"{stats_rival['Bloqueos']}", key="rival_bloqueos"):
        sumar_punto_rival('Bloqueos')
        st.rerun()

    if cols_rival[3].button(f"{stats_rival['Saques']}", key="rival_saques"):
        sumar_punto_rival('Saques')
        st.rerun()

    if cols_rival[4].button(f"{stats_rival['Errores']}", key="rival_errores"):
        sumar_punto_rival('Errores')
        st.rerun()