import streamlit as st
from dotenv import load_dotenv
import os
import openai  # Certifique-se de importar a biblioteca openai
from utils_openai import retorna_resposta_modelo
from utils_files import *

# Carrega as variáveis do arquivo .env (apenas para desenvolvimento)
load_dotenv()
ENV_TYPE = os.getenv("ENV_TYPE", "dev").lower()

# Carregar a chave da API dependendo do ambiente
if ENV_TYPE == "prod":
    # Em produção, esperamos que a chave da API esteja configurada como uma variável de ambiente
    API_KEY = os.getenv("OPENAI_API_KEY_PROD")
else:
    # Em desenvolvimento, use as variáveis do .env
    API_KEY = os.getenv("OPENAI_API_KEY")

# Verificação de Depuração
if API_KEY is None or API_KEY == "":
    st.error(
        "A chave da API não foi carregada. Verifique o arquivo .env ou as variáveis de ambiente.")
else:
    st.info("Chave da API carregada com sucesso.")

# Defina a chave da API diretamente na biblioteca `openai`
openai.api_key = API_KEY

# INICIALIZAÇÃO ==================================================


def inicializacao():
    if not 'mensagens' in st.session_state:
        st.session_state.mensagens = []
    if not 'conversa_atual' in st.session_state:
        st.session_state.conversa_atual = ''
    if not 'modelo' in st.session_state:
        st.session_state.modelo = 'gpt-3.5-turbo'
    if not 'api_key' in st.session_state:
        # Usando a chave carregada do arquivo .env ou variável de ambiente
        st.session_state.api_key = API_KEY

# TABS ==================================================


def tab_conversas(tab):
    tab.button('➕ Nova conversa',
               on_click=seleciona_conversa,
               args=('', ),
               use_container_width=True)
    tab.markdown('')
    conversas = listar_conversas()
    for nome_arquivo in conversas:
        nome_mensagem = desconverte_nome_mensagem(nome_arquivo).capitalize()
        if len(nome_mensagem) == 30:
            nome_mensagem += '...'
        tab.button(nome_mensagem,
                   on_click=seleciona_conversa,
                   args=(nome_arquivo, ),
                   disabled=nome_arquivo == st.session_state['conversa_atual'],
                   use_container_width=True)


def seleciona_conversa(nome_arquivo):
    if nome_arquivo == '':
        st.session_state['mensagens'] = []
    else:
        mensagem = ler_mensagem_por_nome_arquivo(nome_arquivo)
        st.session_state['mensagens'] = mensagem
    st.session_state['conversa_atual'] = nome_arquivo


def tab_configuracoes(tab):
    modelo_escolhido = tab.selectbox('Selecione o modelo',
                                     ['gpt-3.5-turbo', 'gpt-4'])
    st.session_state['modelo'] = modelo_escolhido

    # Removendo a entrada da chave de API do código
    tab.success('Chave de API configurada automaticamente.')

# PÁGINA PRINCIPAL ==================================================


def pagina_principal():
    mensagens = ler_mensagens(st.session_state['mensagens'])

    st.header('🤖 Politx GPT', divider=True)

    for mensagem in mensagens:
        chat = st.chat_message(mensagem['role'])
        chat.markdown(mensagem['content'])

    prompt = st.chat_input('Fale com o chat')
    if prompt:
        if st.session_state['api_key'] == '':
            st.error('Adicione uma chave de API na aba de configurações')
        else:
            nova_mensagem = {'role': 'user',
                             'content': prompt}
            chat = st.chat_message(nova_mensagem['role'])
            chat.markdown(nova_mensagem['content'])
            mensagens.append(nova_mensagem)

            # Definindo a chave explicitamente antes da requisição
            openai.api_key = st.session_state['api_key']

            chat = st.chat_message('assistant')
            placeholder = chat.empty()
            placeholder.markdown("▌")
            resposta_completa = ''
            respostas = retorna_resposta_modelo(mensagens,
                                                st.session_state['api_key'],
                                                modelo=st.session_state['modelo'],
                                                stream=True)
            for resposta in respostas:
                resposta_completa += resposta.choices[0].delta.get(
                    'content', '')
                placeholder.markdown(resposta_completa + "▌")
            placeholder.markdown(resposta_completa)
            nova_mensagem = {'role': 'assistant',
                             'content': resposta_completa}
            mensagens.append(nova_mensagem)

            st.session_state['mensagens'] = mensagens
            salvar_mensagens(mensagens)

# MAIN ==================================================


def main():
    inicializacao()
    pagina_principal()
    tab1, tab2 = st.sidebar.tabs(['Conversas', 'Configurações'])
    tab_conversas(tab1)
    tab_configuracoes(tab2)


if __name__ == '__main__':
    main()
