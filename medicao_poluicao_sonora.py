from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events



import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import math
import time
import datetime as dt
import pytz
import holidays
import geocoder
import folium
from streamlit_folium import folium_static


def tipo_periodo(horario):
    feriados= holidays.Brazil()
    dia = dt.datetime.today().strftime("%Y-%m-%d")
    dia_semana = dt.datetime.today().weekday()

    start_util="07:00:00"
    start_domingoOuFeriado="09:00:00"
    end="22:00:00"

    start_util_dt = dt.datetime.strptime(start_util, '%H:%M:%S')
    start_domingoOuFeriado_dt = dt.datetime.strptime(start_domingoOuFeriado, '%H:%M:%S')
    end_dt = dt.datetime.strptime(end, '%H:%M:%S')
    horario_dt = dt.datetime.strptime(horario, '%H:%M:%S')

    if (dia in feriados['2022-01-01': '2022-12-31']) or (dia_semana==6):
        if (horario_dt<start_domingoOuFeriado_dt) or (horario_dt>end_dt):
            return 'Noturno'
        else:
            return 'Diurno'
    elif (horario_dt<start_util_dt) or (horario_dt>end_dt):
        return 'Noturno'
    else:
        return 'Diurno'


def calculo_media_energia_db(lista):
    energia_total=0
    for numero in lista:
        if ',' in str(numero):
            numero = numero.replace(',','.')

        valor_parcela_energia = 10**(float(numero)/10)
        energia_total+=valor_parcela_energia

    media = energia_total/len(lista)
    medicao_media_db = 10*math.log(media, 10)
    return round(medicao_media_db,1)

def calculo_subtracao_energia_db(NPS_total, NPS_residual):
    valor_parcela_energia_total = 10**(float(NPS_total)/10)
    valor_parcela_energia_residual = 10**(float(NPS_residual)/10)
    energia_total = valor_parcela_energia_total - valor_parcela_energia_residual

    subtracao_db = 10*math.log(energia_total, 10)
    return round(subtracao_db,1)



def medicao_pontos(repetibilidade_medicao, pontos_medicao, texto='tot '):
    medicao_pontos =[]
    lista_repetibilidade = st.columns(repetibilidade_medicao)
    for ponto in range(pontos_medicao):
        valores_por_ponto=[]
        with lista_repetibilidade[ponto]:
            st.write('**Ponto '+str(ponto+1) + '**')
            for ponto_repeticao in range(repetibilidade_medicao):

                valor_medicao = st.text_input(str(ponto+1) +'.'+ str(ponto_repeticao+1)+ ' ' +texto , '0')
                valores_por_ponto.append(valor_medicao)

            medicao_media_db = calculo_media_energia_db(valores_por_ponto)
            medicao_pontos.append(medicao_media_db)
            st.write('Ponto '+str(ponto+1) + ' - média = '+ str(medicao_media_db) + 'dB')

    return medicao_pontos

#Tabelas
limites_NPS = pd.read_csv('limites_NPS.csv')

#VARIAVEIS

#tempo atual
# t = time.localtime()
# current_time = time.strftime("%H:%M:%S", t)
t = dt.datetime.now(tz= pytz.timezone('Brazil/East')).time()#time.localtime()
current_time = str(t).split('.')[0]#time.strftime("%H:%M:%S", str(t))

#st.write(dia)

#localização atual
#g = geocoder.ip('me')
#g_lat_long = g.latlng
#g_lat_long  = [-27.600723, -48.581245]
#st.text(g_lat_long)
loc_button = Button(label="Atualizar Localização")
loc_button.js_on_event("button_click", CustomJS(code="""
    navigator.geolocation.getCurrentPosition(
        (loc) => {
            document.dispatchEvent(new CustomEvent("GET_LOCATION", {detail: {lat: loc.coords.latitude, lon: loc.coords.longitude}}))
        }
    )
    """))
result = streamlit_bokeh_events(
    loc_button,
    events="GET_LOCATION",
    key="get_location",
    refresh_on_update=False,
    override_height=75,
    debounce_time=0)

if ValueError:
    g_lat_long  = [-27.600723, -48.581245]
else:
    g_lat_long  = [result["GET_LOCATION"]['lat'], result["GET_LOCATION"]['lon']]


#repetições de cada ponto de medição
repetibilidade_medicao=3
LR_medido_emissor=0

#MAPA
m = folium.Map(location=g_lat_long, zoom_start=16)#, width=300, height=200)
## add marker for local de medicao
tooltip = "Local de Medicao"
folium.Marker(
    g_lat_long, popup="Local de Medicao", tooltip=tooltip
).add_to(m)


#LAYOUT PAGINA
st.title('Guia de Medição de Poluição Sonora')
#col1, col2 = st.columns(2)
#with col2:
# call to render Folium map in Streamlit
folium_static(m)
periodo_medicao = tipo_periodo(current_time)
st.write('Hora: ', current_time, ', Período: ', periodo_medicao)


#with col1:
with st.expander("1 - Atendimento dos requisitos ambientais"):

    chuva_trovoada = st.checkbox('Tempo sem chuva e trovoadas',value=True)
    veloc_vento = st.checkbox('Velocidade do vento < 5 m/s',value=True)
    temperatura = st.checkbox('Temperatura entre 0ºC e 40ºC',value=True)
    instrumento = st.checkbox('Umidade relativa do ar, velocidade do vento e temperatura de acordo com especificações dos instrumentos de medição',value=True)


    if False in ([chuva_trovoada, veloc_vento, temperatura, instrumento]):
        justificativa = st.text_input('Justificativa', 'Justifique sobre necessidade de fazer medição em condições adversas')

with st.expander("2 - Definição do tempo de medição e integração"):
    st.write('O tempo de medição deve permitir a caracterização sonora do objeto de medição, abrangendo as variações sonoras durante seu funcionamento ou ciclo.')
    tempo_medicao = st.number_input('Tempo de medição em segundos', value=30, step=1)
    st.write('Tempo de medição utilizado', tempo_medicao, 'segundos')

with st.expander("3 - Definição de pontos de medição"):
    pontos_medicao_local = st.number_input('Número de pontos de medição do emissor', value=3, step=1)
    st.write('Nº de pontos de medição do emissor = ', pontos_medicao_local)

    pontos_medicao_residual = st.number_input('Número de pontos de medição do ruído residual', value=1, step=1)
    st.write('Nº de pontos de medição do ruído residual = ', pontos_medicao_residual)

    tipos_medicao = ('Medições em locais externos aos empreendimentos, instalações, eventos e edificações', 
            'Medições em locais externos às fachadas de edificações', 
            'Medições em ambientes internos a edificações')

    option_tipomedicao = st.radio(
        'Tipo de medição',
        tipos_medicao)

    if option_tipomedicao == tipos_medicao[2]:
        mobiliado = st.checkbox('Ambiente com mobília', value=True)
        if mobiliado:
            k=3
        else:
            k=0


with st.expander("4 - Definição do método de medição"):
    metodos = ('Método simplificado', 'Método detalhado')
    tipos_bandas = ('Banda de 1/1 oitava', 'Banda de 1/3 de oitava')

    option_metodomedicao = st.radio(
            'Método de medição',
            metodos)
    if option_metodomedicao == 'Método detalhado':
        st.selectbox('Bandas de frequência: ', tipos_bandas)

with st.expander("5 - Ajuste do sonômetro"):
    st.write('Ajuste o sonômetro com o calibrador sonoro acoplado ao microfone, imediatamente antes de cada série de medições com o valor indicado no certificado de calibração.')
    st.write('O ajuste deve ser realizado no local das medições e isento de interferências sonoras que possam influenciá-lo.')
    st.write('Ao final de cada série de medições, deve ser lido o nível de pressão sonora com o calibrador sonoro ligado e acoplado ao microfone.')
    st.write('**Se a diferença for maior ou inferior ao valor absoluto de 0,5 dB, os resultados devem ser descartados e novas medições realizadas.**')
    ajuste_realizado = st.checkbox('Ajuste do sonômetro realizado e dentro da diferença de 0,5 dB', value=False)

if ajuste_realizado:
    with st.expander("6 - Definição do nível de pressão sonora"):
        st.write(option_metodomedicao)
        if option_metodomedicao == metodos[0]:
            st.write('**Nível de Pressão Sonora Total**')
            medicao_pontos_tot = medicao_pontos(repetibilidade_medicao, pontos_medicao_local)
            media_NPS_total = calculo_media_energia_db(medicao_pontos_tot)
            st.write('Média do NPS Total: **'+ str(media_NPS_total), ' dB**')

            st.write('**Nível de Pressão Sonora Residual**')
            medicao_pontos_res = medicao_pontos(repetibilidade_medicao, pontos_medicao_residual,  texto='res ')
            media_NPS_residual = calculo_media_energia_db(medicao_pontos_res)
            st.write('Média do NPS Residual: **'+ str( media_NPS_residual), ' dB**')

            st.write('**Nível de Pressão Sonora Específico**')
            #st.write(media_NPS_total)
            #st.write(media_NPS_residual)
            componente_medicao_interna = 0
            if option_tipomedicao==tipos_medicao[2]:
                componente_medicao_interna = -k +10
                st.write(componente_medicao_interna)


            if (media_NPS_total-media_NPS_residual)>15:
                st.write('NPS Total - NPS Residual > 15 dB')
                st.write('Lesp = Ltot = ', media_NPS_total)
                LR_medido_emissor = media_NPS_total + componente_medicao_interna

            elif media_NPS_total-media_NPS_residual>=3:
                subtracao_energia_db = calculo_subtracao_energia_db(media_NPS_total, media_NPS_residual)
                st.write('3 dB <= NPS Total - NPS Residual < 15 dB')
                st.write('Lesp = ', subtracao_energia_db)
                LR_medido_emissor = subtracao_energia_db + componente_medicao_interna
            else:
                st.write('NPS total - NPS residual < 3 dB')
                st.write("Não é possível determinar com exatidão o nível de pressão sonora do som específico. \
                Recomenda-se informar no relatório que o nível de pressão sonora do som específico é próximo ao nível de pressão sonora residual.")
                LR_medido_emissor = 0

        


with st.expander("7 - Avaliação sonora em ambientes externos"):


    limites_NPS.set_index(limites_NPS.columns[0], inplace = True)
    tipo_area_medida = st.selectbox('Tipo de área medida', limites_NPS.index, index=1)
    st.write('Período ', periodo_medicao)
    st.write ('NPS para comparação = ', LR_medido_emissor)
    
    st.dataframe(limites_NPS)
    
    #if LR_medido_emissor> limites_NPS.loc[tipo_area_medida, periodo_medicao.lower()]:
    #    st.write ('Medição acima do nível aceitado para tipo de área habitada e período do dia.')
    #    st.write ('Medição acima do nível aceitado para tipo de área habitada e período do dia.')



text_contents = '''This is some text'''
st.download_button('Baixar Relatório', text_contents)
