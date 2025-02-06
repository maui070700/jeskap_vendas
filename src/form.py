import streamlit as st
from src.google_sheets import insert_values, get_rows, update_rows, get_rows_logista, get_last_row
from streamlit_extras.stylable_container import stylable_container
from datetime import datetime
import pytz
import time
import pandas as pd
import re 

PONTEIRAS = {
    "SEM PONTEIRA": 0,
    "GPX BLACK": 218.65,
    "GP2-R CARBON": 212.30,
    "K4 / K64": 227.97,
    "K67 BLACK / SILVER": 546.54,
    "R35": 163.35,
    "R36": 181.35,
    "R45": 181.66,
    "R46": 202.66,
    "R44": 202.66
}
SISTEMAS = {
    "1x1": 100.80,
    "2x1": 147.30,
    "3x1": 309.08,
    "4x2x1": 322.62,
    "LINK CURTO": 35.29,
    "LINK LONGO": 61.58,
    "RACE": 100.80
}
BONIFICADOS = {
    "Não teve bonificado": 0,
    "Camiseta": 39.50,
    "Boné": 26.90,
    "Camiseta + Boné": 66.40,
    "Agasalho": 90.00
}

def load_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read().splitlines()

def get_current_time():
    sao_paulo_tz = pytz.timezone('America/Sao_Paulo')
    return datetime.now(sao_paulo_tz).strftime('%Y-%m-%d %H:%M:%S')

def convert_to_float(valor):
    if isinstance(valor, str):
        return float(valor.replace(',', '.') if ',' in valor else valor)
    return float(valor)

def calculate_values(valor, desconto, sistema, ponteira, bonificado, frete_valor, frete):
    valor = float(convert_to_float(valor))
    desconto = 0 if desconto == 0 else float(convert_to_float(desconto))
    frete_valor = 0 if frete_valor == 0 else float(convert_to_float(frete_valor))
    sistema_preco = SISTEMAS.get(sistema, 0.0)
    ponteira_preco = PONTEIRAS.get(ponteira, 0.0)
    bonificado_preco = BONIFICADOS.get(bonificado, 0.0)
    custo_producao = ponteira_preco + sistema_preco
    faturamento = round(valor - ((desconto / 100) * valor), 2)
    imposto = round(0.12 * faturamento, 2)
    if frete == 'Cliente':
        faturamento += frete_valor
    return custo_producao, faturamento, imposto

def insert_order_data(sheet_range, values):
    result = insert_values("1DmsYWhRdqEMpDAvxEuMgLliuhgIuw3vmyKMnuff4hjA", sheet_range, "USER_ENTERED", values)
    if isinstance(result, dict):
        st.success("As informações foram lançadas com sucesso")
        time.sleep(2)
        st.rerun()
    else:
        st.error(f"Ocorreu um erro: {result}")

def insert_logista(sheet_range, values):
    result = insert_values("1DmsYWhRdqEMpDAvxEuMgLliuhgIuw3vmyKMnuff4hjA", sheet_range, "USER_ENTERED", values)
    if isinstance(result, dict):
        return 'OK'
    else:
        return result


def form_vendedora():
    name = st.session_state.get("name", "")
    if name == "Raquel":
        vendedora = st.selectbox("Vendedora", ['Fabiana', 'Jessica', 'Mercado Livre', 'Raquel', "Ryan", 'Site', 'Thais - Organico', 'Thais - Trafego pago', 'Zedequias'], index=None, placeholder="Escolha uma opção")
        col1, col2 = st.columns([5, 2])
        with col1:
            data = st.date_input('Data da venda')
        with col2:
            hora = st.time_input('Hora da venda')
            
        return vendedora, data, hora
    elif name == "Thais":
        return st.selectbox("Vendedora", ("Thais - Trafego pago", "Thais - Organico"), index=None, placeholder="Escolha uma opção"), None, None
    elif name == "Jessica":
        return st.selectbox("Vendedora", ("Jessica - Organico", "Jessica"), index=None, placeholder="Escolha uma opção"), None, None
    return st.text_input("Vendedora", value=name, disabled=True), None, None

def form_common_fields():
    valor = st.text_input("Valor",placeholder='0,00')
    frete = st.selectbox("Frete", ["Cliente", "Jeskap"], index=None, placeholder='Escolha uma opção')
    frete_valor = st.text_input("Valor do frete",placeholder='0,00')
    estado = st.selectbox("Estado", load_file('./docs/estado_list.txt'), index=None, placeholder="Escolha uma opção")
    sistema = st.selectbox("Sistema", list(SISTEMAS.keys()), index=None, placeholder="Escolha uma opção")
    ponteira = st.selectbox("Ponteira", list(PONTEIRAS.keys()), index=None, placeholder="Escolha uma opção")
    moto = st.selectbox("Moto", load_file('./docs/moto_list.txt'), index=None, placeholder="Escolha uma opção")
    desconto = st.text_input("Desconto (%)",placeholder='0,00')
    bonificado = st.selectbox("Bonificado", list(BONIFICADOS.keys()), index=None, placeholder="Escolha uma opção")
    origem = st.selectbox('Origem da venda', ['YOUTUBE', 'INSTAGRAM', 'TIK TOK', 'MECÂNICO', 'INDICAÇÃO', "OUTRO"], index=None, placeholder="Escolha uma opção")
    meio_pagamento = st.selectbox("Meio de pagamento", ['PIX', 'CARTÃO DE CRÉDITO', 'BOLETO', 'ENTRADA + CARTÃO', 'ENTRADA + PIX '], index=None, placeholder="Escolha uma opção")
    pedido = st.text_input("Nº do pedido",placeholder=0)
    return valor, frete, frete_valor, estado, sistema, ponteira, moto, desconto, bonificado, origem, meio_pagamento, pedido

def get_ultimo_pedido():
    name = st.session_state.get("name", "")
    ultimo_pedido = get_last_row(name)
    return ultimo_pedido

def render_lancar_pedido():
    with stylable_container(key='with_border', css_styles="""
    {   
        border: 1px solid rgba(250, 250, 250, 0.2);
        width: 40%;
        max-width: 600px;
        border-radius: 1%;
        position: absolute;
        top: 30%;
        left: 130%;
        transform: translate(-50%, -50%); 
        padding-top: 2%;
        padding-bottom: 2%;
        display: flex;
        align-items: center;
        justify-content: center; 
        text-align: center;
    }
"""):
            
            st.write(f"""
Últimos pedidos lançados:\n
{get_ultimo_pedido()}
                    """)
    with st.form(key='pedido', clear_on_submit=True):
        vendedora, data, hora = form_vendedora()
        valor, frete, frete_valor, estado, sistema, ponteira, moto, desconto, bonificado, origem, meio_pagamento, pedido = form_common_fields()

        if st.form_submit_button('Lançar pedido', type="primary"):
            if all([valor, frete, estado, sistema, ponteira, moto, bonificado, origem, meio_pagamento, pedido]):
                if(data):
                    data_hora = f'{data} {hora}'
                else:
                    data_hora = get_current_time()
                custo_producao, faturamento, imposto = calculate_values(valor, desconto, sistema, ponteira, bonificado, frete_valor, frete)
                values = [[data_hora, vendedora, valor, desconto, faturamento, estado, sistema, ponteira, moto, bonificado, BONIFICADOS[bonificado], pedido, custo_producao, origem, frete_valor, frete, imposto, meio_pagamento]]
                insert_order_data("Pedidos!A1:N1", values)
            else:
                st.warning("Por favor, preencha todos os campos.")

def render_lancar_pecas():
    vendedora, data, hora = form_vendedora()
    valor_peca = st.text_input("Valor", placeholder='0,00')
    peca = st.selectbox("Peça/Serviços", load_file('./docs/pecas_avulsas.txt'), index=None, placeholder="Escolha uma opção")
    meio_pagamento_peca = st.selectbox("Meio de pagamento", ['PIX', 'CARTÃO DE CRÉDITO', 'BOLETO', 'ENTRADA + CARTÃO', 'ENTRADA + PIX '], index=None, placeholder="Escolha uma opção")
    pedido_peca = st.text_input("Nº do pedido", placeholder=None)

    if st.form_submit_button('Lançar peça avulsa', type='primary'):
        if all([vendedora, valor_peca, peca, meio_pagamento_peca, pedido_peca]):
            if(data):
                data_hora = f'{data} {hora}'
            else:
                data_hora = get_current_time()
            values = [[data_hora, vendedora, valor_peca, peca, pedido_peca, meio_pagamento_peca]]
            insert_order_data("Peças avulsas!A1:N1", values)
        else:
            st.warning("Por favor, preencha todos os campos.")

def render_alterar_pedido():
    pedido_n = st.text_input('Digite o pedido para alterar')
    if st.button('Buscar'):
        row, row_number = get_rows(pedido_n)
        
        if row:
            st.session_state.update({'pedido_encontrado_alterar': True})     
        else:
            st.error('Pedido não encontrado')      

    if st.session_state.get('pedido_encontrado_alterar'):
        with st.form(key='pedido'):
            row, row_number = get_rows(pedido_n)
            if row:
                vendedora = st.selectbox("Vendedora", ['Fabiana', 'Jessica', 'Mercado Livre', 'Raquel', "Ryan", 'Site', 'Thais - Organico', 'Thais - Trafego pago', 'Zedequias'], index=None, placeholder=row[1])
                valor = st.text_input("Valor",placeholder='0,00', value=float(row[2].replace(',', '.') if ',' in row[2] else row[2]))
                try:
                    frete_placeholder = row[15]
                except:
                    frete_placeholder = 'Escolha uma opção'
                frete = st.selectbox("Frete", ["Cliente", "Jeskap"], index=None, placeholder=frete_placeholder)
                frete_valor = st.text_input("Valor do frete", placeholder='0,00', value=float(row[14].replace(',', '.') if ',' in row[14] else row[14]))
                estado = st.selectbox("Estado", load_file('./docs/estado_list.txt'), index=None, placeholder=row[5])
                sistema = st.selectbox("Sistema", list(SISTEMAS.keys()), index=None, placeholder=row[6])
                ponteira = st.selectbox("Ponteira", list(PONTEIRAS.keys()), index=None, placeholder=row[7])
                moto = st.selectbox("Moto", load_file('./docs/moto_list.txt'), index=None, placeholder=row[8])
                desconto = st.text_input("Desconto (%)",placeholder='0,00', value=float(row[3].replace(',', '.') if ',' in row[3] else row[3]))
                bonificado = st.selectbox("Bonificado", list(BONIFICADOS.keys()), index=None, placeholder=row[9])
                origem = st.selectbox('Origem da venda', ['YOUTUBE', 'INSTAGRAM', 'TIK TOK', 'MECÂNICO', 'INDICAÇÃO', "OUTRO"], index=None, placeholder=row[13])
                try:
                    meio_pagamento_placeholder = row[17]
                except:
                    meio_pagamento_placeholder = 'Escolha uma opção'
                meio_pagamento = st.selectbox("Meio de pagamento", ['PIX', 'CARTÃO DE CRÉDITO', 'BOLETO', 'ENTRADA + CARTÃO', 'ENTRADA + PIX '], index=None, placeholder=meio_pagamento_placeholder)
                pedido = st.number_input("Nº do pedido", min_value=0, value=int(pedido_n), disabled=True)
                
                check = st.checkbox('Alterar para hora atual')

                if st.form_submit_button('Alterar pedido', type="primary"):
                    vendedora = vendedora if vendedora else row[1]
                    valor = valor if valor else row[2]
                    frete = frete if frete else row[15]
                    frete_valor = frete_valor if frete_valor else row[14]
                    estado = estado if estado else row[5]
                    sistema = sistema if sistema else row[6]
                    ponteira = ponteira if ponteira else row[7]
                    moto = moto if moto else row[8]
                    desconto = desconto = 0 if desconto == 0 else (desconto if desconto else row[3])
                    try:
                        meio_pagamento = meio_pagamento if meio_pagamento else row[17]
                    except:
                        meio_pagamento = ''
                    
                    bonificado = bonificado if bonificado else row[9]
                    origem = origem if origem else row[13]
                    pedido = pedido_n


                    if all([valor, frete, estado, sistema, ponteira, moto, bonificado, origem, pedido]):
                        custo_producao, faturamento, imposto = calculate_values(valor, desconto, sistema, ponteira, bonificado, frete_valor, frete)
                        if check:
                            hora = get_current_time()
                        else:
                            hora = row[0]
                        values = [[hora, vendedora, valor, desconto, faturamento, estado, sistema, ponteira, moto, bonificado, BONIFICADOS[bonificado], pedido, custo_producao, origem, frete_valor, frete, imposto, meio_pagamento, 'Alterado']]
                        update_rows(f"Pedidos!A{row_number}:S{row_number}", values)
                        st.success("As informações foram alteradas com sucesso")
                    else:
                        st.warning("Por favor, preencha todos os campos.")

def render_deletar_pedido():
    pedido_n = st.text_input('Digite o pedido para excluir')
    if st.button('Buscar'):
        row, row_number = get_rows(pedido_n)
        
        if row:
            st.session_state.update({'pedido_encontrado_excluir': True})     
        else:
            st.error('Pedido não encontrado')      

    if st.session_state.get('pedido_encontrado_excluir'):
        with st.form(key='pedido'):
            row, row_number = get_rows(pedido_n)
            if row:
                vendedora = st.text_input("Vendedora", value=row[1], disabled=True)
                valor = st.number_input("Valor", format="%.2f", value=float(row[2].replace(',', '.')), disabled=True)
                try:
                    frete_placeholder = row[15]
                except:
                    frete_placeholder = 'Escolha uma opção'
                frete = st.selectbox("Frete", ["Cliente", "Jeskap"], index=None, placeholder=frete_placeholder, disabled=True)
                frete_valor = st.number_input("Valor do frete", format="%.2f", value=float(row[14].replace(',', '.')), disabled=True)
                estado = st.selectbox("Estado", load_file('./docs/estado_list.txt'), index=None, placeholder=row[5], disabled=True)
                sistema = st.selectbox("Sistema", list(SISTEMAS.keys()), index=None, placeholder=row[6], disabled=True)
                ponteira = st.selectbox("Ponteira", list(PONTEIRAS.keys()), index=None, placeholder=row[7], disabled=True)
                moto = st.selectbox("Moto", load_file('./docs/moto_list.txt'), index=None, placeholder=row[8], disabled=True)
                desconto = st.number_input("Desconto (%)", format="%.2f", value=float(row[3].replace(',', '.')), disabled=True)
                bonificado = st.selectbox("Bonificado", list(BONIFICADOS.keys()), index=None, placeholder=row[9], disabled=True)
                origem = st.selectbox('Origem da venda', ['YOUTUBE', 'INSTAGRAM', 'TIK TOK', 'MECÂNICO', 'INDICAÇÃO', "OUTRO"], index=None, placeholder=row[13], disabled=True)
                try:
                    meio_pagamento_placeholder = row[17]
                except:
                    meio_pagamento_placeholder = 'Escolha uma opção'
                meio_pagamento = st.selectbox("Meio de pagamento", ['PIX', 'CARTÃO DE CRÉDITO', 'BOLETO', 'ENTRADA + CARTÃO', 'ENTRADA + PIX '], index=None, placeholder=meio_pagamento_placeholder, disabled=True)
                pedido = st.number_input("Nº do pedido", min_value=0, value=int(pedido_n), disabled=True)

                if st.form_submit_button('Excluir pedido', type="primary"):
                    vendedora = row[1]
                    valor = row[2]
                    frete = row[15]
                    frete_valor = row[14]
                    estado = row[5]
                    sistema = row[6]
                    ponteira = row[7]
                    moto = row[8]
                    desconto = row[3]
                    bonificado = row[9]
                    origem = row[13]
                    faturamento = row[4]
                    custo_producao = row[12]
                    imposto = row[16]
                    try:
                        meio_pagamento = row[17]
                    except:
                        meio_pagamento = ''
                    pedido = pedido_n

                    if all([valor, frete, estado, sistema, ponteira, moto, bonificado, origem, pedido]):
                        values = [[row[0], vendedora, valor, desconto, faturamento, estado, sistema, ponteira, moto, bonificado, BONIFICADOS[bonificado], pedido, custo_producao, origem, frete_valor, frete, imposto, meio_pagamento, 'Excluido']]
                        update_rows(f"Pedidos!A{row_number}:S{row_number}", values)
                        st.success("O pedido foi excluido com sucesso")
                    else:
                        st.warning("Por favor, preencha todos os campos.")
            

def add_item(df, item, quantity):
    new_row = pd.DataFrame([{
        'nome': item,
        'quantidade': quantity
    }])
    df = pd.concat([df, new_row], ignore_index=True)
    return df

def render_lancar_logista():
    if 'dfs' not in st.session_state:
        st.session_state.dfs = {
            'sistema': pd.DataFrame(columns=['nome', 'quantidade']),
            'ponteira': pd.DataFrame(columns=['nome', 'quantidade']),
            'moto': pd.DataFrame(columns=['nome', 'quantidade'])
        }

    dfs = st.session_state.dfs

    vendedora = st.selectbox("Vendedor", ("Mercado Livre", "Site", "Raquel", 'Thais - Organico'), index=None, placeholder="Escolha uma opção", key='vendedora_logista')
    col1, col2 = st.columns([5, 2])
    with col1:
        data = st.date_input('Data da venda')
    with col2:
        hora = st.time_input('Hora da venda')
    cliente = st.text_input('Cliente', key='cliente_logista')
    valor = st.text_input("Valor",placeholder='0,00', key='valor_logista')
    frete = st.selectbox("Frete", ["Cliente", "Jeskap"], index=None, placeholder='Escolha uma opção', key='frete_logista')
    frete_valor = st.text_input("Valor do frete",placeholder='0,00', key='valor_frete_logista')
    estado = st.selectbox("Estado", load_file('./docs/estado_list.txt'), index=None, placeholder="Escolha uma opção", key='estado_logista')

    st.write(
        """<style>
        [data-testid="stHorizontalBlock"] {
            align-items: flex-end;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    for item_type, options in [('sistema', SISTEMAS.keys()), ('ponteira', PONTEIRAS.keys()), ('moto', load_file('./docs/moto_list.txt'))]:
        col1, col2, col3 = st.columns([7, 3, 2])
        with col1:
            item = st.selectbox(f"{item_type.capitalize()}", list(options), index=None, placeholder="Escolha uma opção", key=f"select_{item_type}")
        with col2:
            quantidade = st.number_input(f'Quantidade', min_value=1, step=1, key=f"quantity_{item_type}")
        with col3:
            botao_adicionar = st.button('Adicionar', key=f"add_{item_type}")
        if botao_adicionar:
            if item != None:
                dfs[item_type] = add_item(dfs[item_type], item, quantidade)
                st.query_params.updated=f"{item_type}"

        df = dfs[item_type]
        if not df.empty:
            for i, row in df.iterrows():
                cols = st.columns(len(row)+1)
                for j, (colname, value) in enumerate(row.items()):
                    cols[j].write(value)
                if cols[len(row)].button('Deletar', key=f"delete_{item_type}_{i}"):
                    dfs[item_type] = dfs[item_type][~((dfs[item_type]['nome'] == row['nome']) & (dfs[item_type]['quantidade'] == row['quantidade']))]
                    st.query_params.updated=f"delete_{item_type}_{i}"
                    st.rerun()

    pedido = st.text_input("Nº do pedido",placeholder='0', key='pedido_logista')

    if st.button('Lançar pedido'):
        if all([pedido, cliente, valor, frete, estado]):
            
            valor = convert_to_float(valor)
            frete = convert_to_float(frete_valor)
            
            faturamento = valor
            imposto = round(0.12 * faturamento, 2)
            if frete == 'Cliente':
                faturamento += frete_valor

            sistema_df = dfs['sistema']
            ponteira_df = dfs['ponteira']
            moto_df = dfs['moto']
            final_df = pd.concat([sistema_df.reset_index(drop=True), 
                                ponteira_df.reset_index(drop=True), 
                                moto_df.reset_index(drop=True)], 
                                axis=1, keys=['sistema', 'ponteira', 'moto'])

            final_df.columns = [f'{col[0]} {col[1]}' for col in final_df.columns]
            
            final_df['Custo_producao'] = (
            final_df['sistema nome'].map(SISTEMAS).fillna(0) * final_df['sistema quantidade'].fillna(0)
        ) + (
            final_df['ponteira nome'].map(PONTEIRAS).fillna(0) * final_df['ponteira quantidade'].fillna(0)
        )

            for _, row in final_df.iterrows():
                values = [[
                    pedido,
                    row['sistema nome'] if pd.notna(row['sistema nome']) else '',
                    row['sistema quantidade'] if pd.notna(row['sistema quantidade']) else '',
                    row['ponteira nome'] if pd.notna(row['ponteira nome']) else '',
                    row['ponteira quantidade'] if pd.notna(row['ponteira quantidade']) else '',
                    row['moto nome'] if pd.notna(row['moto nome']) else '',
                    row['moto quantidade'] if pd.notna(row['moto quantidade']) else '',
                    row['Custo_producao'] if pd.notna(row['Custo_producao']) else ''
                ]]
                result = insert_logista(f"Logista-Itens!A1:D1", values)
            if(data):
                    data_hora = f'{data} {hora}'
            else:
                data_hora = get_current_time()

            values = [[data_hora, vendedora, cliente, valor, estado, pedido, frete_valor, frete, faturamento, imposto, final_df['Custo_producao'].sum()]]
            result = insert_logista(f"Logista-Geral!A1:G1", values)
            

            st.session_state.dfs = {
                'sistema': pd.DataFrame(columns=['nome', 'quantidade']),
                'ponteira': pd.DataFrame(columns=['nome', 'quantidade']),
                'moto': pd.DataFrame(columns=['nome', 'quantidade'])
            }

            if result == 'OK':
                st.success("As informações foram lançadas com sucesso")
            else:
                st.error(f"Ocorreu um erro: {result}")
            time.sleep(2)
            st.query_params.clear()
            st.rerun()
        else:
            st.warning('Precisa preencher todos os campos!')


def render_excluir_logista():
    pedido_logista = st.text_input('Digite o pedido para excluir')
    if st.button('Buscar'):
        rows_geral, row_number_geral, rows_itens, row_number_itens = get_rows_logista(pedido_logista)
        
        if rows_geral and rows_itens:
            st.session_state.update({'pedido_logista_encontrado_excluir': True})     
        else:
            st.error('Pedido não encontrado')      

    if st.session_state.get('pedido_logista_encontrado_excluir'):
        with st.form(key='pedido'):
            rows_geral, row_number_geral, rows_itens, row_number_itens = get_rows_logista(pedido_logista)
            if rows_geral and rows_itens:
                vendedora = st.selectbox("Vendedora", ("Mercado Livre", "Site", "Raquel", 'Thais - Organico'), index=None, placeholder=rows_geral[1], key='vendedora_logista')
                cliente = st.text_input('Cliente', key='cliente_logista', placeholder=rows_geral[2], disabled=True)
                valor = st.text_input("Valor", value=rows_geral[3].replace(',', '.'), key='valor_logista', disabled=True)
                frete = st.selectbox("Frete", ["Cliente", "Jeskap"], index=None, placeholder=rows_geral[7], key='frete_logista')
                frete_valor = st.text_input("Valor do frete", value=rows_geral[6].replace(',', '.'), key='valor_frete_logista', disabled=True)
                estado = st.selectbox("Estado", load_file('./docs/estado_list.txt'), index=None, placeholder=rows_geral[4], key='estado_logista', disabled=True)

                df_itens = pd.DataFrame(rows_itens)
                df_itens = df_itens.drop([0, 7], axis=1)

                df_itens.columns = ['SISTEMA', 'SISTEMA QUANTIDADE', 'PONTEIRA', 'PONTEIRA QUANTIDADE', 'MOTO', 'MOTO QUANTIDADE']
                st.dataframe(df_itens)
                pedido = st.number_input("Nº do pedido", min_value=0, value=int(rows_geral[5]), key='pedido_logista', disabled=True)

                if st.form_submit_button('Excluir pedido', type="primary"):
                    update_rows(f"Logista-Geral!L{row_number_geral}:L{row_number_geral}", [['Excluido']])
                    for i in row_number_itens:
                        update_rows(f"Logista-Itens!I{i}:I{i}", [['Excluido']])
                    st.success("O pedido foi excluido com sucesso")
                    
                    

def render_alterar_logista():
    pedido_logista = st.text_input('Digite o pedido para alterar')
    
    if st.button('Buscar'):
        rows_geral, row_number_geral, rows_itens, row_number_itens = get_rows_logista(pedido_logista)
        
        if rows_geral and rows_itens:
            st.session_state.update({'pedido_logista_alterar': True})     
        else:
            st.error('Pedido não encontrado')      

    if st.session_state.get('pedido_logista_alterar'):
        rows_geral, row_number_geral, rows_itens, row_number_itens = get_rows_logista(pedido_logista)
        
        with st.form(key='pedido'):
            vendedora = st.selectbox("Vendedora", ("Mercado Livre", "Site", "Raquel", 'Thais - Organico'), 
                                    index=None, placeholder=rows_geral[1], key='vendedora_logista')
            cliente = st.text_input('Cliente', key='cliente_logista', placeholder=rows_geral[2])
            valor = st.text_input("Valor", value=rows_geral[3].replace(',', '.'), key='valor_logista')
            frete = st.selectbox("Frete", ["Cliente", "Jeskap"], index=None, placeholder=rows_geral[7], key='frete_logista')
            frete_valor = st.text_input("Valor do frete", value=rows_geral[6].replace(',', '.'), key='valor_frete_logista')
            estado = st.selectbox("Estado", load_file('./docs/estado_list.txt'), index=None, placeholder=rows_geral[4], key='estado_logista')

            df_itens = pd.DataFrame(rows_itens)
            df_itens = df_itens.drop([0, 7], axis=1)
            df_itens.columns = ['SISTEMA', 'SISTEMA QUANTIDADE', 'PONTEIRA', 'PONTEIRA QUANTIDADE', 'MOTO', 'MOTO QUANTIDADE']
            st.data_editor(df_itens, num_rows="dynamic")
            
            pedido = st.text_input("Nº do pedido", value=rows_geral[5], key='pedido_logista')
            
            check = st.checkbox('Alterar para hora atual')

            if st.form_submit_button('Alterar pedido', type="primary"):
                vendedora = vendedora if vendedora else rows_geral[1]
                cliente = cliente if cliente else rows_geral[2]
                valor = valor if valor else rows_geral[3]
                frete = frete if frete else rows_geral[7]
                frete_valor = frete_valor if frete_valor else rows_geral[6]
                estado = estado if estado else rows_geral[4]
                pedido = pedido if pedido else rows_geral[5]

                valor = convert_to_float(valor)
                frete_valor = convert_to_float(frete_valor)
                
                faturamento = valor
                if frete == 'Cliente':
                    faturamento += frete_valor
                
                imposto = round(0.12 * faturamento, 2)

                sistema_df = df_itens[['SISTEMA', 'SISTEMA QUANTIDADE']].rename(columns={'SISTEMA': 'nome', 'SISTEMA QUANTIDADE': 'quantidade'})
                ponteira_df = df_itens[['PONTEIRA', 'PONTEIRA QUANTIDADE']].rename(columns={'PONTEIRA': 'nome', 'PONTEIRA QUANTIDADE': 'quantidade'})
                moto_df = df_itens[['MOTO', 'MOTO QUANTIDADE']].rename(columns={'MOTO': 'nome', 'MOTO QUANTIDADE': 'quantidade'})

                final_df = pd.concat([sistema_df, ponteira_df, moto_df], axis=1, keys=['sistema', 'ponteira', 'moto'])
                final_df.columns = [f'{col[0]}_{col[1]}' for col in final_df.columns]
                
                for col in ['sistema_quantidade', 'ponteira_quantidade']:
                    final_df[col] = pd.to_numeric(final_df[col], errors='coerce').fillna(0)

                final_df['Custo_producao'] = (
                    final_df['sistema_nome'].map(lambda x: SISTEMAS.get(x, 0)).fillna(0) * final_df['sistema_quantidade']
                ) + (
                    final_df['ponteira_nome'].map(lambda x: PONTEIRAS.get(x, 0)).fillna(0) * final_df['ponteira_quantidade']
                )
                
                for _, row in final_df.iterrows():
                    values = [[
                        pedido,
                        row['sistema_nome'] if pd.notna(row['sistema_nome']) else '',
                        row['sistema_quantidade'] if pd.notna(row['sistema_quantidade']) else '',
                        row['ponteira_nome'] if pd.notna(row['ponteira_nome']) else '',
                        row['ponteira_quantidade'] if pd.notna(row['ponteira_quantidade']) else '',
                        row['moto_nome'] if pd.notna(row['moto_nome']) else '',
                        row['moto_quantidade'] if pd.notna(row['moto_quantidade']) else '',
                        row['Custo_producao'] if pd.notna(row['Custo_producao']) else '',
                        'Alterado'
                    ]]
                                
                for i, row_values in enumerate(values, start=min(row_number_itens)):
                    if i in row_number_itens:
                        update_rows(f"Logista-Itens!A{i}:I{i}", [row_values])
                    else:
                        insert_logista(f"Logista-Itens!A{i}:I{i}", [row_values])
                
                for i in row_number_itens[len(values):]:
                    update_rows(f"Logista-Itens!I{i}:I{i}", [['Excluido']])

        
                if check:
                    hora = get_current_time()
                else:
                    hora = rows_geral[0]
                values = [[hora, vendedora, cliente, valor, estado, pedido, frete_valor, frete, faturamento, imposto, final_df['Custo_producao'].sum()]]
                update_rows(f"Logista-Geral!A{row_number_geral}:K{row_number_geral}", values)

                st.success("O pedido foi alterado com sucesso")

def render_form():
    options = ["Lançar pedido", "Lançar peças avulsas"]
    if st.session_state.get("name", "") == "Raquel":
        options += ["Alterar pedido", "Excluir pedido", "Lançar pedido logista", "Alterar pedido logista", 'Excluir pedido logista']
    lancamento_opcoes = st.radio("Pedido", options, horizontal=True, label_visibility='hidden')

    if lancamento_opcoes == "Lançar pedido":
        render_lancar_pedido()
    elif lancamento_opcoes == "Lançar peças avulsas":

        with st.form(key='pecas', clear_on_submit=True):
            render_lancar_pecas()
    elif lancamento_opcoes == "Alterar pedido":
        render_alterar_pedido()
    elif lancamento_opcoes == "Excluir pedido":
        render_deletar_pedido()
    elif lancamento_opcoes == "Lançar pedido logista":
        with stylable_container(key='with_border', css_styles="""
            {   
                border: 1px solid rgba(250, 250, 250, 0.2);
                width: 105%;
                border-radius: 1%;
                padding-left: 20px;
                padding-bottom: 2%;
                padding-top: 3%;
            }
                                """):
            render_lancar_logista()
    
    elif lancamento_opcoes == "Excluir pedido logista":
        render_excluir_logista()
        
    elif lancamento_opcoes == 'Alterar pedido logista':
        render_alterar_logista()