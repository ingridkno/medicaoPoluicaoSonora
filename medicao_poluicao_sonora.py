#https://ingridkno-medicaopoluicaosonora-medicao-poluicao-sonora-w0qrps.streamlit.app/
from bokeh.models.widgets import Button
from bokeh.models import CustomJS
from streamlit_bokeh_events import streamlit_bokeh_events

import streamlit as st
st.set_page_config(layout="wide")
import pandas as pd
import json

from io import BytesIO
from pyxlsb import open_workbook as open_xlsb
import xlsxwriter

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

    if (dia in feriados['2023-01-01': '2023-12-31']) or (dia_semana==6):
        
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

def horario():
    return dt.datetime.now(tz= pytz.timezone('Brazil/East'))

def medicao_pontos(repetibilidade_medicao, pontos_medicao, texto='tot '):
    medicao_pontos =[]
    medicao_pontos_media=[]
    valores_por_ponto=[]
    horario_por_ponto=[]
    lista_repetibilidade = st.columns(repetibilidade_medicao)
    for ponto in range(pontos_medicao):

        with lista_repetibilidade[ponto]:
            st.write('**Ponto '+str(ponto+1) + '**')
            for ponto_repeticao in range(repetibilidade_medicao):

                valor_medicao = st.text_input(str(ponto+1) +'.'+ str(ponto_repeticao+1)+ ' ' +texto , '0')
                t_medicao='-'
                if valor_medicao!="0":
                    t_medicao=horario()

                horario_por_ponto.append(t_medicao)
                valores_por_ponto.append(valor_medicao)

            medicao_media_db = calculo_media_energia_db(valores_por_ponto)
            
            medicao_pontos_media.append(medicao_media_db)
            st.write('Ponto '+str(ponto+1) + ' - média = '+ str(medicao_media_db) + 'dB')



    return medicao_pontos_media, valores_por_ponto, horario_por_ponto


def preenche_medicoes(valores_por_ponto, medicao_pontos, pontos_medicao, repetibilidade, tipo_ponto_index):
    inicio_rep=0
    for n_pontos in range(pontos_medicao):
    #st.write(valores_por_ponto_tot)
        relatorio.loc['Medicao '+tipo_ponto_index+' - Ponto '+str(n_pontos+1), colunas[3:(3+repetibilidade)]] = (valores_por_ponto[inicio_rep:inicio_rep+repetibilidade])
        relatorio.loc['Medicao '+tipo_ponto_index+' - Ponto '+str(n_pontos+1), colunas[3+repetibilidade]] = medicao_pontos[n_pontos]
        inicio_rep+=repetibilidade


#def convert_df(df):
#   return df.to_csv(index=False).encode('utf-8')

def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter', options={'remove_timezone': True})
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']
    format1 = workbook.add_format({'num_format': '0.00'}) 
    worksheet.set_column('A:A', None, format1)  
    writer.save()
    processed_data = output.getvalue()
    return processed_data

#Tabelas
limites_NPS = pd.read_csv('limites_NPS.csv')

#VARIAVEIS

#tempo atual
data_hoje = horario()
t = data_hoje.time()#time.localtime()
#st.write(t)
current_time = str(t).split('.')[0]#time.strftime("%H:%M:%S", str(t))

#st.write(dia)

#localização atual
#g = geocoder.ip('me')
#g_lat_long = g.latlng

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

  
try:
    g_lat_long  = [result["GET_LOCATION"]['lat'], result["GET_LOCATION"]['lon']]
except:
    g_lat_long  = [-27.60719459363507, -48.46709599461304]

#st.write(g_lat_long)



#repetições de cada ponto de medição
#repetibilidade_medicao=3
LR_medido_emissor=0

#MAPA
m = folium.Map(location=g_lat_long, zoom_start=16)#, width=300, height=200)
## add marker for local de medicao
tooltip = "Local de Medicao"
#folium.TileLayer('stamenterrain').add_to(m)
folium.Marker(
    g_lat_long, popup="Local de Medicao", tooltip=tooltip
).add_to(m)


#LAYOUT PAGINA
st.title('Guia de Medição Sonora')
st.subheader('Conforme NBR 10.151/2019')
st.write('_Desenvolvido por Ingrid Knochenhauer_')

#col1, col2 = st.columns(2)
#with col2:
# call to render Folium map in Streamlit
folium_static(m)
periodo_medicao = tipo_periodo(current_time)

data_hoje_string = str(data_hoje).split()[0]
st.write('Hora: ', current_time, ', Data: ', data_hoje_string)
st.write('Período ', periodo_medicao)


#with col1:
with st.expander("0 - Informações sobre local de medição"):
    info_local = st.text_input('Informações', placeholder='Observações sobre local de medição')
    
    
with st.expander("1 - Atendimento dos requisitos ambientais"):
    t_01 = horario()
    chuva_trovoada = st.checkbox('Tempo sem chuva e trovoadas',value=True)
    veloc_vento = st.checkbox('Velocidade do vento < 5 m/s',value=True)
    temperatura = st.checkbox('Temperatura entre 0ºC e 40ºC',value=True)
    instrumento = st.checkbox('Umidade relativa do ar, velocidade do vento e temperatura de acordo com especificações dos instrumentos de medição',value=True)


    if False in ([chuva_trovoada, veloc_vento, temperatura, instrumento]):
        justificativa_ambiental = st.text_input('Justificativa', placeholder='Justifique sobre necessidade de fazer medição em condições adversas')
        t_01 = horario()
    else:
        justificativa_ambiental='Requisitos ambientais não foram intereferentes na medição'

with st.expander("2 - Definição do tempo de medição e integração"):
    st.write('O tempo de medição deve permitir a caracterização sonora do objeto de medição, abrangendo as variações sonoras durante seu funcionamento ou ciclo.')
    tempo_medicao = st.number_input('Tempo de medição em segundos', value=30, step=1)
    st.write('Tempo de medição utilizado', tempo_medicao, 'segundos')

with st.expander("3 - Definição de pontos de medição"):
    pontos_medicao_local = st.number_input('Número de pontos de medição do emissor', value=3, step=1)
    st.write('Nº de pontos de medição do emissor = ', pontos_medicao_local)

    pontos_medicao_residual = st.number_input('Número de pontos de medição do ruído residual', value=1, step=1)
    st.write('Nº de pontos de medição do ruído residual = ', pontos_medicao_residual)

    repetibilidade_medicao=st.number_input('Número de repetições para cada ponto de medição', value=3, step=1)
    st.write('Nº de repetições de medição = ', repetibilidade_medicao)

    tipos_medicao = ('Medições em locais externos aos empreendimentos, instalações, eventos e edificações', 
            'Medições em locais externos às fachadas de edificações', 
            'Medições em ambientes internos a edificações')

    option_tipomedicao = st.radio(
        'Tipo de medição',
        tipos_medicao)

    justificativa_tpmedicao=''

    if option_tipomedicao == tipos_medicao[2]:
        checagem_mobilia = 'Ambiente com mobília'
        mobiliado = st.checkbox(checagem_mobilia, value=True)

        com_ou_sem=''
        if mobiliado:
            k=0
                        
        else:
            k=3
            com_ou_sem='sem'
     
        justificativa_tpmedicao= checagem_mobilia.replace('com', com_ou_sem)+ ', k= ' + str(k)


with st.expander("4 - Definição do método de medição"):
    metodos = ('Método simplificado', 'Método detalhado')
    tipos_bandas = ('Banda de 1/1 oitava', 'Banda de 1/3 de oitava')
    bandas_freq=''

    option_metodomedicao = st.radio(
            'Método de medição',
            metodos)
    if option_metodomedicao == 'Método detalhado':
        bandas_freq = st.selectbox('Bandas de frequência: ', tipos_bandas)

with st.expander("5 - Ajuste do sonômetro"):
    st.write('Ajuste o sonômetro com o calibrador sonoro acoplado ao microfone, imediatamente antes de cada série de medições com o valor indicado no certificado de calibração.')
    st.write('O ajuste deve ser realizado no local das medições e isento de interferências sonoras que possam influenciá-lo.')
    st.write('Ao final de cada série de medições, deve ser lido o nível de pressão sonora com o calibrador sonoro ligado e acoplado ao microfone.')
    st.write('**Se a diferença for maior ou inferior ao valor absoluto de 0,5 dB, os resultados devem ser descartados e novas medições realizadas.**')
    
    mensagem_ajuste_true = 'Ajuste do sonômetro realizado e dentro da diferença de 0,5 dB'
    ajuste_realizado = st.checkbox(mensagem_ajuste_true, value=False)

if ajuste_realizado:
    with st.expander("6 - Definição do nível de pressão sonora"):
        st.write(option_metodomedicao)
        if option_metodomedicao == metodos[0]:
            st.write('**Nível de Pressão Sonora Total**')
            medicao_pontos_tot, valores_por_ponto_tot, horario_por_ponto_tot = medicao_pontos(repetibilidade_medicao, pontos_medicao_local)
            #st.write(horario_por_ponto_tot)
            media_NPS_total = calculo_media_energia_db(medicao_pontos_tot)
            st.write('Média do NPS Total: **'+ str(media_NPS_total), ' dB**')

            st.write('**Nível de Pressão Sonora Residual**')
            medicao_pontos_res, valores_por_ponto_res, horario_por_ponto_res = medicao_pontos(repetibilidade_medicao, pontos_medicao_residual,  texto='res ')
            media_NPS_residual = calculo_media_energia_db(medicao_pontos_res)
            st.write('Média do NPS Residual: **'+ str( media_NPS_residual), ' dB**')

            st.write('**Nível de Pressão Sonora Específico**')
            #st.write(media_NPS_total)
            #st.write(media_NPS_residual)
            componente_medicao_interna = 0
            mensagem_medicao_interna=''
            if option_tipomedicao==tipos_medicao[2]:
                mensagem_medicao_interna= 'Medicao corrigida para ambientes internos'
                componente_medicao_interna = -k +10

                st.write(componente_medicao_interna)


             
            if (media_NPS_total-media_NPS_residual)>15:
                Lesp= media_NPS_total
                mensagem_calculo_especifico = 'NPS Total - NPS Residual > 15 dB'
                Lesp_msg = '**Lesp = Ltot = '+ str(Lesp)+'**'
                st.write(mensagem_calculo_especifico)
                st.write(Lesp_msg)
                #st.write('NPS Total - NPS Residual > 15 dB')
                #st.write('Lesp = Ltot = ', media_NPS_total)
                LR_medido_emissor = media_NPS_total + componente_medicao_interna

            elif media_NPS_total-media_NPS_residual>=3:
                subtracao_energia_db = calculo_subtracao_energia_db(media_NPS_total, media_NPS_residual)
                Lesp= subtracao_energia_db
                mensagem_calculo_especifico = '3 dB <= NPS Total - NPS Residual < 15 dB '
                Lesp_msg = '**Lesp = '+ str(Lesp)+'**'
                st.write(mensagem_calculo_especifico)
                st.write(Lesp_msg)

                #st.write('3 dB <= NPS Total - NPS Residual < 15 dB')
                #st.write('Lesp = ', subtracao_energia_db)
                LR_medido_emissor = subtracao_energia_db + componente_medicao_interna
            else:
                mensagem_calculo_especifico = 'NPS total - NPS residual < 3 dB '
                Lesp_msg ="**Não é possível determinar com exatidão** o nível de pressão sonora do som específico. \
                 \nRecomenda-se informar no relatório que o nível de pressão sonora do som específico é próximo ao nível de pressão sonora residual."
                Lesp= Lesp_msg 
                st.write(mensagem_calculo_especifico)
                st.write(Lesp_msg)
                #st.write('NPS total - NPS residual < 3 dB')
                #st.write("Não é possível determinar com exatidão o nível de pressão sonora do som específico. \
                #Recomenda-se informar no relatório que o nível de pressão sonora do som específico é próximo ao nível de pressão sonora residual.")
                LR_medido_emissor = 0

        


with st.expander("7 - Avaliação sonora em ambientes externos"):


    limites_NPS.set_index(limites_NPS.columns[0], inplace = True)
    tipo_area_medida = st.selectbox('Tipo de área medida', limites_NPS.index, index=1)
    periodo_procurado = 'Período '+ periodo_medicao.lower()
    st.write(periodo_procurado)
    st.write ('NPS para comparação = ', LR_medido_emissor)
    
    st.dataframe(limites_NPS)

        
    NPS_aceitavel = limites_NPS.loc[tipo_area_medida, periodo_procurado]
    if LR_medido_emissor> NPS_aceitavel :
        msg_nps_comparacao = "**NPS medido** ("+str(LR_medido_emissor)+" dB) > " + str(NPS_aceitavel) + " dB"
        msg_dentro_norma = 'Medição **acima do nível aceitado** para '+periodo_procurado.lower()+' em '+tipo_area_medida.lower()+ '.'

    else:
        msg_nps_comparacao ="**NPS medido** ("+str(LR_medido_emissor)+" dB) <= " + str(NPS_aceitavel) + " dB"
        msg_dentro_norma = 'Medição **dentro do nível aceitado** para '+periodo_procurado.lower()+' em '+tipo_area_medida.lower()+ '.'

    st.write( msg_nps_comparacao )
    st.write ( msg_dentro_norma )



text_contents = '''This is some text'''


n_colunas_medicao = max(pontos_medicao_local, pontos_medicao_residual)
colunas_medicao = ['Medicao NPS '+ str(x) for x in range(1, n_colunas_medicao+1)]
horario_medicao = ['Horario NPS '+ str(x) for x in range(1, n_colunas_medicao+1)]

colunas = ['Relatorio','Justificativa', 'Horario'] +(colunas_medicao +['NPS resultante']+ horario_medicao)
relatorio = pd.DataFrame(columns=colunas)


#PREENCHENDO O DATAFRAME RELATORIO

relatorio.loc['Informacoes Local de Medicao', colunas[0]]=info_local
relatorio.loc['Localizacao', colunas[0]]=g_lat_long
relatorio.loc['Requisitos Ambientais', colunas[1:3]]=[justificativa_ambiental, t_01]
relatorio.loc['Tempo de medicao (s)', colunas[0]] = tempo_medicao
relatorio.loc['N pontos medicao - emissor', colunas[0]] = pontos_medicao_local
relatorio.loc['N pontos medicao - ruido residual', colunas[0]] = pontos_medicao_residual
relatorio.loc['Tipo medicao', colunas[0:2]] = [option_tipomedicao, justificativa_tpmedicao]
relatorio.loc['Metodo de medicao', colunas[0:2]] = [option_metodomedicao, bandas_freq]

if ajuste_realizado:
    relatorio.loc['Ajuste do sonometro', colunas[0]] = mensagem_ajuste_true



preenche_medicoes(valores_por_ponto_tot, medicao_pontos_tot, pontos_medicao_local, repetibilidade_medicao, "Emissor")
preenche_medicoes(valores_por_ponto_res, medicao_pontos_res, pontos_medicao_residual, repetibilidade_medicao, "Ruido Residual")

relatorio.loc['Calculo L especifico', colunas[0]] = mensagem_calculo_especifico
relatorio.loc['Calculo L especifico', colunas[3+repetibilidade_medicao]] = Lesp
relatorio.loc['Lr', colunas[0:2]] = [LR_medido_emissor, mensagem_medicao_interna]
relatorio.loc['Tipo area medida', colunas[0]] = tipo_area_medida
relatorio.loc['Periodo medido', colunas[0]] = periodo_medicao
relatorio.loc['Classificacao da emissao do ruido', colunas[0:2]] = [msg_dentro_norma,msg_nps_comparacao]


#st.write(medicao_pontos_tot)


#st.write(type(relatorio.columns))
#relatorio.columns= relatorio.columns.tolist()+(colunas_medicao +['NPS resultante']+ horario_medicao)
st.dataframe(relatorio)

relatorio = relatorio.astype(str)
df_xlsx = to_excel(relatorio.reset_index())



st.download_button(label='📥 Baixar Relatório',
                                data=df_xlsx ,
                                file_name= 'relatorio_medicao_'+data_hoje_string+'.xlsx')


