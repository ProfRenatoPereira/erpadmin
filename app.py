import os
import sqlite3
import datetime
import math
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from whitenoise import WhiteNoise

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

# DIRECIONAMENTO DO BANCO: 
# Se houver DATABASE_URL (Supabase no Render), ele mapeia as tabelas usando o psycopg2.
# Caso contrário, mantém o arquivo local padrão intacto.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

DATABASE = 'database.db'
CATALOGO_MAQUINAS = {
    'cnc_romi': {'nome': 'Centro de Usinagem CNC ROMI 5X', 'pot': 22.0, 'cons': 15.4, 'vel': '8000', 'avan': '20000', 'comp': 1000, 'diam': 500, 'mnt': 1000, 'preco': 620000.0, 'dep': 5166.66, 'venda': 124000.0, 'operador': 'Carlos Souza (Técnico CNC)', 'custo_op': 0.45, 'salario': 3100.0, 'adic': 930.0, 'vida': 120},
    'prensa_100t': {'nome': 'Prensa Hidráulica Industrial 100T', 'pot': 15.0, 'cons': 10.5, 'vel': '60', 'avan': '1200', 'comp': 800, 'diam': 800, 'mnt': 1500, 'preco': 220000.0, 'dep': 1833.33, 'venda': 44000.0, 'operador': 'Marcos Lima (Meio Oficial)', 'custo_op': 0.22, 'salario': 1850.0, 'adic': 282.40, 'vida': 120},
    'forno_tempera': {'nome': 'Forno de Têmpera Contínua', 'pot': 45.0, 'cons': 38.0, 'vel': '1200°C', 'avan': 'Automático', 'comp': 1500, 'diam': 600, 'mnt': 800, 'preco': 180000.0, 'dep': 1500.0, 'venda': 36000.0, 'operador': 'Aline Dias (Tratadora Térmica)', 'custo_op': 0.40, 'salario': 2900.0, 'adic': 564.80, 'vida': 120},
    'forno_revenimento': {'nome': 'Forno de Revenimento Industrial', 'pot': 30.0, 'cons': 24.0, 'vel': '700°C', 'avan': 'Estático', 'comp': 1200, 'diam': 600, 'mnt': 800, 'preco': 120000.0, 'dep': 1000.0, 'venda': 24000.0, 'operador': 'Pedro Alves (Operador Forno)', 'custo_op': 0.35, 'salario': 2400.0, 'adic': 282.40, 'vida': 120},
    'solda_mig_tig': {'nome': 'Estação de Solda MIG/TIG Industrial', 'pot': 7.5, 'cons': 5.2, 'vel': 'N/A', 'avan': 'Manual', 'comp': 500, 'diam': 0, 'mnt': 300, 'preco': 15000.0, 'dep': 125.0, 'venda': 3000.0, 'operador': 'Bruno Silva (Soldador TIG)', 'custo_op': 0.38, 'salario': 2600.0, 'adic': 564.80, 'vida': 120},
    'compressor_parafuso': {'nome': 'Compressor de Ar de Parafuso', 'pot': 11.0, 'cons': 8.8, 'vel': '10 bar', 'avan': 'Contínuo', 'comp': 600, 'diam': 400, 'mnt': 600, 'preco': 35000.0, 'dep': 291.66, 'venda': 7000.0, 'operador': 'Posto de Apoio / Indireto', 'custo_op': 0.0, 'salario': 0.0, 'adic': 0.0, 'vida': 120},
    'jato_areia': {'nome': 'Jato de Areia Pressurizado', 'pot': 5.5, 'cons': 4.1, 'vel': 'N/A', 'avan': 'Manual', 'comp': 800, 'diam': 600, 'mnt': 400, 'preco': 28000.0, 'dep': 233.33, 'venda': 5600.0, 'operador': 'Auxiliar de Jateamento', 'custo_op': 0.20, 'salario': 1512.0, 'adic': 282.40, 'vida': 120}
}
CATALOGO_MATERIAIS = {
    'tub_mec': {'cod': 'TUB-MEC-ST52', 'nome': 'Tubo Mecânico de Alta Resistência ST52', 'preco': 45.50, 'dim': 'Ø 3 pol x 2000mm', 'vol': 150.0},
    'tar_aco': {'cod': 'TAR-ACO-4140', 'nome': 'Tarugo Redondo Aço Liga SAE 4140', 'preco': 28.90, 'dim': 'Ø 2 pol x 1000mm', 'vol': 300.0},
    'bar_lat': {'cod': 'BAR-LAT-CLA', 'nome': 'Barra de Latão de Fácil Usinagem CLA', 'preco': 55.20, 'dim': 'Ø 1 pol x 3000mm', 'vol': 80.0},
    'chapa_a36': {'cod': 'CHA-ACO-A36', 'nome': 'Chapa de Aço Carbono ASTM A36 3mm', 'preco': 18.50, 'dim': '1000x2000mm', 'vol': 200.0},
    'gas_mig': {'cod': 'INS-GAS-MIG', 'nome': 'Cilindro Mistura Gás Solda Argônio/CO2', 'preco': 120.00, 'dim': 'Cilindro 50L', 'vol': 15.0}
}

def get_db_connection():
    # Sistema Híbrido: Se estiver rodando no Render com o link do Supabase configurado,
    # ele usa as credenciais da nuvem convertendo para o formato compatível do psycopg2.
    # Caso contrário, mantém o arquivo SQLite local intacto.
    url_banco = os.environ.get('DATABASE_URL')
    if url_banco:
        if url_banco.startswith("postgres://"):
            url_banco = url_banco.replace("postgres://", "postgresql://", 1)
        import psycopg2
        import psycopg2.extras
        conn = psycopg2.connect(url_banco)
        conn.cursor_factory = psycopg2.extras.DictCursor
        return conn
    else:
        conn = sqlite3.connect(DATABASE)
        conn.row_factory = sqlite3.Row
        return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Identifica se é PostgreSQL (Supabase) para usar a sintaxe correta de autoincremento
    is_postgres = not hasattr(conn, 'row_factory')
    pk_auto = "SERIAL PRIMARY KEY" if is_postgres else "INTEGER PRIMARY KEY AUTOINCREMENT"
    text_type = "TEXT"
    real_type = "REAL"
    ts_default = "TIMESTAMP DEFAULT CURRENT_TIMESTAMP"

    cursor.execute(f'CREATE TABLE IF NOT EXISTS usuarios (id {pk_auto}, usuario {text_type} UNIQUE NOT NULL, senha {text_type} NOT NULL, aprovado INTEGER DEFAULT 0)')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS investimentos_imobiliarios (id {pk_auto}, turma_nome {text_type} NOT NULL, cidade_regiao {text_type} NOT NULL, bairro_imovel {text_type} NOT NULL, area_imovel {real_type} NOT NULL, taxa_selic {real_type} NOT NULL, valor_imovel_estimado {real_type} NOT NULL, aluguel_regional {real_type} NOT NULL, perc_acionistas {real_type} NOT NULL, capital_inicial_negocio {real_type} DEFAULT 0.0)')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS maquinas (id {pk_auto}, nome_equipamento {text_type} NOT NULL, potencia {real_type} NOT NULL, consumo_eletrico {real_type} NOT NULL, velocidade {text_type}, avanco {text_type}, comprimento_max {real_type}, diametro_max {real_type}, frequencia_manutencao INTEGER NOT NULL, horas_trabalhadas INTEGER DEFAULT 0, preco_compra {real_type} NOT NULL, depreciacao_mensal {real_type} NOT NULL, valor_venda_final {real_type} NOT NULL, custo_minuto_maquina {real_type} NOT NULL, operador_nome {text_type} DEFAULT \'Posto Vago - Aguardando MOD\', custo_minuto_operador {real_type} DEFAULT 0.0, salario_base {real_type} DEFAULT 0.0, valor_adicionais {real_type} DEFAULT 0.0, turno_trabalho {text_type} DEFAULT \'Diurno\', dia_semana {text_type} DEFAULT \'Regular\', vida_util_meses INTEGER DEFAULT 120)')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS materiais (id {pk_auto}, codigo_material {text_type} UNIQUE NOT NULL, nome_material {text_type} NOT NULL, preco_unidade {real_type} NOT NULL, dimensoes {text_type}, volume_disponivel {real_type} NOT NULL)')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS requisicoes_compras (id {pk_auto}, equipamento_tipo {text_type} NOT NULL, especificacao_desejada {text_type} NOT NULL, quantidade INTEGER DEFAULT 1, status {text_type} DEFAULT \'Pendente em Cotação\', preco_cotado {real_type} DEFAULT 0, potencia_cotada {real_type} DEFAULT 0, depreciacao_sugerida {real_type} DEFAULT 0, vida_util_sugerida INTEGER DEFAULT 120, data_requisicao {ts_default})')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS produtos (id {pk_auto}, codigo_produto {text_type} UNIQUE NOT NULL, nome_produto {text_type} NOT NULL, custo_total_fabricacao {real_type} DEFAULT 0)')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS estrutura_produto (id {pk_auto}, produto_id INTEGER NOT NULL, maquina_id INTEGER, material_id INTEGER, tempo_processo_min {real_type} DEFAULT 0, quantidade_material {real_type} DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS formacao_precos (id {pk_auto}, produto_id INTEGER UNIQUE NOT NULL, imposto_municipal {real_type} DEFAULT 0, imposto_estadual {real_type} DEFAULT 0, imposto_federal {real_type} DEFAULT 0, margem_lucro {real_type} DEFAULT 0, preco_venda_final {real_type} DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS estoque_produtos (id {pk_auto}, produto_id INTEGER UNIQUE NOT NULL, quantidade_disponivel {real_type} DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS pedidos_vendas (id {pk_auto}, produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, desconto_percentual {real_type} DEFAULT 0, observacoes {text_type}, data_pedido {ts_default}, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute(f'CREATE TABLE IF NOT EXISTS ordens_processo (id {pk_auto}, pedido_id INTEGER NOT NULL, numero_operacao {text_type} NOT NULL, maquina_name {text_type} NOT NULL, codigo_produto {text_type} NOT NULL, nome_produto {text_type} NOT NULL, data_entrada {text_type} NOT NULL, tempo_estimado_min {real_type} NOT NULL, data_saida {text_type} NOT NULL, operador_nome {text_type} DEFAULT \'Pendente\', status {text_type} DEFAULT \'Na Fila\', custo_operacao {real_type} DEFAULT 0.0, FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id))')
    conn.commit()
    
    # Adaptação para leitura de contagem tanto no SQLite quanto no PostgreSQL
    cursor.execute('SELECT COUNT(*) AS total FROM investimentos_imobiliarios')
    row = cursor.fetchone()
    total_registros = row[0] if isinstance(row, tuple) else row['total']

    if total_registros == 0:
        # Se for PostgreSQL substitui os marcadores '?' por '%s' dinamicamente
        param = "%s" if is_postgres else "?"
        
        cursor.execute(f'''
            INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio)
            VALUES ('Metalúrgica Modelo S/A - Cenário Base', 'Curitiba CIC', 'CIC (Distrito Industrial)', 450.00, 11.39, 3825000.00, 13500.00, 25.0, 500000.00)
        ''')
        
        for k, m in CATALOGO_MAQUINAS.items():
            if k in ['cnc_romi', 'prensa_100t', 'forno_tempera']:
                minutos_mes = 44 * 4.33 * 60
                c_mm = (m['dep'] / minutos_mes) + ((m['pot'] * 0.75) / 60) + (13500.00 / minutos_mes)
                cursor.execute(f'''
                    INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana, vida_util_meses)
                    VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, 0, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, 'Diurno', 'Regular', {param})
                ''', (m['nome'], m['pot'], m['cons'], m['vel'], m['avan'], m['comp'], m['diam'], m['mnt'], m['preco'], m['dep'], m['venda'], c_mm, m['operador'], m['custo_op'], m['salario'], m['adic'], m['vida']))
                
        for mat in CATALOGO_MATERIAIS.values():
            cursor.execute(f"INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES ({param}, {param}, {param}, {param}, {param})", (mat['cod'], mat['nome'], mat['preco'], mat['dim'], mat['vol']))
            
        cursor.execute(f"INSERT INTO produtos (codigo_produto, nome_produto, custo_total_fabricacao) VALUES ('PROD-EIXO-CNC', 'Eixo de Transmissão Usinado', 115.40)")
        cursor.execute(f"INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES (1, 1, 2, 12.0, 1.5)")
        cursor.execute(f"INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (1, 5.0, 18.0, 9.25, 35.0, 245.50)")
        cursor.execute(f"INSERT INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES (1, 25.0)")
        conn.commit()
    conn.close()

# Executa a inicialização de tabelas e injeção do cenário
def calcular_caixa_disponivel(conn):
    # Trata de forma unificada o formato das tuplas retornadas no SQLite e no PostgreSQL
    def valor_campo(row, chave, indice=0):
        if row is None: return 0.0
        return float(row[chave] if hasattr(row, 'keys') or isinstance(row, dict) else row[indice])

    cursor = conn.cursor()

    cursor.execute('SELECT capital_inicial_negocio, aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ult_imovel = cursor.fetchone()
    if not ult_imovel: 
        return 0.0, 0.0
    
    capital_inicial = valor_campo(ult_imovel, 'capital_inicial_negocio', 0)
    aluguel_fixo = valor_campo(ult_imovel, 'aluguel_regional', 1)
    
    cursor.execute('SELECT COALESCE(SUM(preco_compra), 0) FROM maquinas')
    investido_maquinas = valor_campo(cursor.fetchone(), 0, 0)

    cursor.execute('SELECT COALESCE(SUM(preco_unidade * volume_disponivel), 0) FROM materiais')
    comprado_materials = valor_campo(cursor.fetchone(), 0, 0)

    cursor.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    faturamento = valor_campo(cursor.fetchone(), 0, 0)

    cursor.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    folha_rh = valor_campo(cursor.fetchone(), 0, 0)
    
    caixa_atual = capital_inicial - investido_maquinas - comprado_materials + faturamento - folha_rh - aluguel_fixo
    return caixa_atual, capital_inicial

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login_validar', methods=['POST'])
def login_validar():
    user_input = request.form.get('username')
    pass_input = request.form.get('password')
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM usuarios WHERE usuario = {param}', (user_input,))
    user = cursor.fetchone()
    conn.close()
    
    if user and check_password_hash(user['senha'], pass_input):
        session['logado'] = True
        session['usuario_equipe'] = user_input
        flash('Credenciais validadas com sucesso!', 'success')
        return redirect(url_for('estrutura'))
    else:
        flash('Usuário ou senha inválidos!', 'danger')
        return redirect(url_for('index'))

@app.route('/inicializar_simulador', methods=['POST'])
def inicializar_simulador():
    if not session.get('logado'): return redirect(url_for('index'))
    nome_empresa = request.form.get('nome_empresa', 'Empresa Simulada S/A')
    try: capital_inicial = float(request.form.get('capital_inicial', 0))
    except ValueError: capital_inicial = 0.0
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ordens_processo')
    cursor.execute('DELETE FROM pedidos_vendas')
    cursor.execute('DELETE FROM estoque_produtos')
    cursor.execute('DELETE FROM formacao_precos')
    cursor.execute('DELETE FROM estrutura_produto')
    cursor.execute('DELETE FROM produtos')
    cursor.execute('DELETE FROM materiais')
    cursor.execute('DELETE FROM maquinas')
    cursor.execute('DELETE FROM investimentos_imobiliarios')
    cursor.execute('DELETE FROM requisicoes_compras')
    conn.commit()
    conn.close()
    
    init_db()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio)
        VALUES ({param}, 'Não Definido', 'Não Definido', 0.0, 11.39, 0.0, 0.0, 0.0, {param})
    ''', (nome_empresa, capital_inicial))
    conn.commit()
    conn.close()
    flash(f'Empresa {nome_empresa} inicializada com sucesso!', 'success')
    return redirect(url_for('estrutura'))
@app.route('/professor_painel_secreto')
def professor_painel():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, usuario FROM usuarios')
    todas_equipes = cursor.fetchall()
    conn.close()
    return render_template('professor.html', usuarios=todas_equipes)

@app.route('/professor/resetar', methods=['POST'])
def professor_resetar():
    user_aluno = request.form.get('username')
    nova_senha = request.form.get('nova_senha')
    novo_hash = generate_password_hash(nova_senha)
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'UPDATE usuarios SET senha = {param} WHERE usuario = {param}', (novo_hash, user_aluno))
    conn.commit()
    conn.close()
    flash(f"Mecanismo de Pânico: Senha de '{user_aluno}' alterada para '{nova_senha}'!", 'success')
    return redirect(url_for('professor_painel'))

@app.route('/professor/cadastrar', methods=['POST'])
def professor_cadastrar():
    novo_user = request.form.get('novo_user').strip().lower().replace(" ", "")
    senha_inicial = request.form.get('senha_inicial')
    hash_senha = generate_password_hash(senha_inicial)
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    try:
        cursor.execute(f'INSERT INTO usuarios (usuario, senha) VALUES ({param}, {param})', (novo_user, hash_senha))
        conn.commit()
        flash(f"Equipe '{novo_user}' criada com sucesso!", 'success')
    except:
        flash("Erro: Esse nome de equipe já existe!", 'danger')
    conn.close()
    return redirect(url_for('professor_painel'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/estrutura')
def estrutura():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM investimentos_imobiliarios')
    registros = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('estrutura.html', taxa_atual=11.39, registros=registros, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_estrutura', methods=['POST'])
def salvar_estrutura():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute('SELECT capital_inicial_negocio FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ultimo_registro = cursor.fetchone()
    capital_fixado = float(ultimo_registro['capital_inicial_negocio'] if ultimo_registro else 0.0)
    
    cursor.execute(f'''
        INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio) 
        VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param})
    ''', (request.form.get('turma_nome', 'Grupo Geral'), request.form.get('cidade_regiao', 'Curitiba'), request.form.get('bairro_imovel', 'Centro'), float(request.form.get('area_imovel') or 0), float(request.form.get('taxa_selic') or 11.39), float(request.form.get('valor_imovel_estimado') or 0), float(request.form.get('aluguel_regional') or 0), float(request.form.get('perc_acionistas') or 0), capital_fixado))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/alterar_estrutura/<int:id>', methods=['POST'])
def alterar_estrutura(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT capital_inicial_negocio FROM investimentos_imobiliarios WHERE id={param}', (id,))
    ultimo_registro = cursor.fetchone()
    capital_fixado = float(ultimo_registro['capital_inicial_negocio'] if ultimo_registro else 0.0)
    
    cursor.execute(f'''
        UPDATE investimentos_imobiliarios SET turma_nome={param}, cidade_regiao={param}, bairro_imovel={param}, area_imovel={param}, taxa_selic={param}, valor_imovel_estimado={param}, aluguel_regional={param}, perc_acionistas={param}, capital_inicial_negocio={param} WHERE id={param}
    ''', (request.form.get('turma_nome', 'Grupo Geral'), request.form.get('cidade_regiao', 'Curitiba'), request.form.get('bairro_imovel', 'Centro'), float(request.form.get('area_imovel') or 0), float(request.form.get('taxa_selic') or 11.39), float(request.form.get('valor_imovel_estimado') or 0), float(request.form.get('aluguel_regional') or 0), float(request.form.get('perc_acionistas') or 0), capital_fixado, id))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/deletar_estrutura/<int:id>', methods=['POST'])
def deletar_estrutura(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM investimentos_imobiliarios WHERE id={param}', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('estrutura'))

@app.route('/maquinas')
def maquinas():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM maquinas')
    m_dados = cursor.fetchall()
    
    cursor.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ult = cursor.fetchone()
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    
    # Tratamento unificado de campos para SQLite e PostgreSQL
    if ult:
        base = float(ult['aluguel_regional'] if hasattr(ult, 'keys') or isinstance(ult, dict) else ult[0])
    else:
        base = 0.0
        
    minutos_padrao_mes = 44 * 4.33 * 60
    return render_template('maquinas.html', maquinas=m_dados, custo_minuto_estrutural=base/minutos_padrao_mes if base > 0 else 0, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_maquina', methods=['POST'])
def salvar_maquina():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana, vida_util_meses) 
        VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param})
    ''', (
        request.form.get('nome_equipamento', 'Equipamento'), float(request.form.get('potencia') or 0), float(request.form.get('consumo_eletrico') or 0),
        request.form.get('velocidade', 'N/A'), request.form.get('avanco', 'N/A'), float(request.form.get('comprimento_max') or 0),
        float(request.form.get('diametro_max') or 0), int(request.form.get('frequencia_manutencao') or 500), int(request.form.get('horas_trabalhadas') or 0),
        float(request.form.get('preco_compra') or 0), float(request.form.get('depreciacao_mensal') or 0), float(request.form.get('valor_venda_final') or 0),
        float(request.form.get('custo_minuto_maquina') or 0), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador') or 0.0),
        float(request.form.get('salario_base') or 0.0), float(request.form.get('valor_adicionais') or 0.0), request.form.get('turno', 'Diurno'),
        request.form.get('dia_semana', 'Regular'), int(request.form.get('vida_util_meses') or 120)
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/alterar_maquina/<int:id>', methods=['POST'])
def alterar_maquina(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'''
        UPDATE maquinas SET nome_equipamento={param}, potencia={param}, consumo_eletrico={param}, velocidade={param}, avanco={param}, comprimento_max={param}, diametro_max={param}, frequencia_manutencao={param}, horas_trabalhadas={param}, preco_compra={param}, depreciacao_mensal={param}, valor_venda_final={param}, custo_minuto_maquina={param}, operador_nome={param}, custo_minuto_operador={param}, salario_base={param}, valor_adicionais={param}, turno_trabalho={param}, dia_semana={param}, vida_util_meses={param} WHERE id={param}
    ''', (request.form.get('nome_equipamento', 'Equipamento'), float(request.form.get('potencia') or 0), float(request.form.get('consumo_eletrico') or 0), request.form.get('velocidade', 'N/A'), request.form.get('avanco', 'N/A'), float(request.form.get('comprimento_max') or 0), float(request.form.get('diametro_max') or 0), int(request.form.get('frequencia_manutencao') or 500), int(request.form.get('horas_trabalhadas') or 0), float(request.form.get('preco_compra') or 0), float(request.form.get('depreciacao_mensal') or 0), float(request.form.get('valor_venda_final') or 0), float(request.form.get('custo_minuto_maquina') or 0), request.form.get('operador_nome', 'Posto Vago - Aguardando MOD'), float(request.form.get('custo_minuto_operador') or 0.0), float(request.form.get('salario_base') or 0.0), float(request.form.get('valor_adicionais') or 0.0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), int(request.form.get('vida_util_meses') or 120), id))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/deletar_maquina/<int:id>', methods=['POST'])
def deletar_maquina(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM maquinas WHERE id={param}', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('maquinas'))

@app.route('/rh')
def rh():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    colaboradores = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('rh.html', colaboradores=colaboradores, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_colaborador', methods=['POST'])
def salvar_colaborador():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM maquinas WHERE operador_nome = 'Posto Vago - Aguardando MOD' LIMIT 1")
    posto_vago = cursor.fetchone()
    
    if posto_vago:
        vago_id = posto_vago[0] if isinstance(posto_vago, tuple) else posto_vago['id']
        cursor.execute(f'UPDATE maquinas SET operador_nome={param}, salario_base={param}, valor_adicionais={param}, turno_trabalho={param}, dia_semana={param}, custo_minuto_operador={param} WHERE id={param}', (request.form.get('nome_completo', 'Colaborador'), float(request.form.get('salario_base') or 0), float(request.form.get('valor_adicionais') or 0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular'), float(request.form.get('custo_minuto_operador') or 0), vago_id))
        conn.commit()
        flash('MOD Alocado com sucesso!', 'success')
    else:
        cursor.execute(f"INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana) VALUES ('Posto de Apoio / Indireto', 0, 0, 'N/A', 'N/A', 0, 0, 9999, 0, 0, 0, 0, 0, {param}, {param}, {param}, {param}, {param}, {param})", (request.form.get('nome_completo', 'Colaborador'), float(request.form.get('custo_minuto_operador') or 0), float(request.form.get('salario_base') or 0), float(request.form.get('valor_adicionais') or 0), request.form.get('turno', 'Diurno'), request.form.get('dia_semana', 'Regular')))
        conn.commit()
        flash('Mão de Obra Indireta alocada.', 'success')
    conn.close()
    return redirect(url_for('rh'))

@app.route('/imprimir_holerite/<int:id>/<string:tipo>')
def imprimir_holerite(id, tipo):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM maquinas WHERE id = {param}', (id,))
    col = cursor.fetchone()
    conn.close()
    
    if not col or col['operador_nome'] == 'Posto Vago - Aguardando MOD': return "Colaborador não localizado."
    salario_base = float(col['salario_base'] or 0.0)
    adicionais = float(col['valor_adicionais'] or 0.0)
    horas_extras_acumuladas = 1250.00 if col['dia_semana'] != 'Regular' else 0.0
    titulo_recibo = "RECIBO DE PAGAMENTO MENSAL"
    provento_principal_nome = "Salário Base Nominal"
    provento_principal_valor = salario_base
    if tipo == "ferias":
        titulo_recibo = "RECIBO DE PAGAMENTO DE FÉRIAS (CLT)"
        provento_principal_nome = "Férias Integrais"
        provento_principal_valor = salario_base + (salario_base / 3)
    elif tipo == "decimo":
        titulo_recibo = "RECIBO DE DÉCIMO TERCEIRO SALÁRIO"
        provento_principal_nome = "13º Salário Integral"
        provento_principal_valor = salario_base
    total_proventos = provento_principal_valor + adicionais + horas_extras_acumuladas
    inss = total_proventos * 0.075 if total_proventos <= 1518.00 else ((total_proventos * 0.09) - 22.77 if total_proventos <= 2793.88 else ((total_proventos * 0.12) - 106.59 if total_proventos <= 4190.83 else ((total_proventos * 0.14) - 190.40 if total_proventos <= 8157.41 else 951.64)))
    base_irrf = total_proventos - inss
    irrf = 0.0 if base_irrf <= 2259.20 else ((base_irrf * 0.075) - 169.44 if base_irrf <= 2826.65 else ((base_irrf * 0.15) - 381.44 if base_irrf <= 3751.05 else ((base_irrf * 0.225) - 662.77 if base_irrf <= 4664.68 else (base_irrf * 0.275) - 896.00)))
    vale_transporte = salario_base * 0.06 if col['turno_trabalho'] == 'Diurno' else 0.0
    total_descontos = inss + irrf + vale_transporte
    valor_liquido = total_proventos - total_descontos
    dados_holerite = {"tipo_recibo": titulo_recibo, "nome": col['operador_nome'], "cargo": f"CBO {col['id']} - Ativo", "principal_nome": provento_principal_nome, "principal_valor": provento_principal_valor, "adicionais": adicionais, "horas_extras": horas_extras_acumuladas, "total_proventos": total_proventos, "inss": inss, "irrf": irrf, "vt": vale_transporte, "total_descontos": total_descontos, "liquido": valor_liquido}
    return render_template('holerite.html', h=dados_holerite)

@app.route('/orcamentos')
def orcamentos():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas')
    maqs = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('orcamentos.html', maquinas=maqs, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_orcamento_calculado', methods=['POST'])
def salvar_orcamento_calculado():
    if not session.get('logado'): return redirect(url_for('index'))
    tipo = request.form.get('tipo_produto')
    nome_item = request.form.get('nome_item')
    lote = int(request.form.get('lote') or 1)
    preco_final = float(request.form.get('preco_final_calculado') or 0.0)
    sku = f"ORC-{tipo.upper()}-{int(preco_final)%1000}"
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    try:
        cursor.execute(f'INSERT INTO produtos (codigo_produto, nome_produto) VALUES ({param}, {param})', (sku, nome_item))
        cursor.execute(f'SELECT id FROM produtos WHERE codigo_produto = {param}', (sku,))
        prod_id = cursor.fetchone()
        p_id = prod_id if isinstance(prod_id, (int, float)) else (prod_id[0] if isinstance(prod_id, tuple) else prod_id['id'])
        
        cursor.execute(f'INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES ({param}, {param}, {param}, {param}, {param}, {param})', (p_id, float(request.form.get('iss') or 5), float(request.form.get('icms') or 18), float(request.form.get('federal') or 9.25), float(request.form.get('margem') or 25), preco_final / lote))
        cursor.execute(f'INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES ({param}, {param}, 0, \'SOB ENCOMENDA - Fila PCP\')', (p_id, lote))
        conn.commit()
        flash('Orçamento integrado à carteira de demandas comerciais!', 'success')
    except:
        flash('Erro no processamento comercial.', 'danger')
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/requisicoes')
def requisicoes():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM requisicoes_compras ORDER BY id DESC')
    reqs = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('requisicoes.html', requisicoes=reqs, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/compras')
def compras():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM requisicoes_compras WHERE status LIKE 'Cotado%' ORDER BY id DESC")
    cotadas = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('compras.html', requisicoes_cotadas=cotadas, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_requisicao', methods=['POST'])
def salvar_requisicao():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO requisicoes_compras (equipamento_tipo, especificacao_desejada, quantity) VALUES ({param}, {param}, {param})', (request.form.get('equipamento_tipo', 'Equipamento'), request.form.get('especificacao_desejada', 'N/A'), int(request.form.get('quantidade') or 1)))
    conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/cotar_internet/<int:id>', methods=['POST'])
def cotar_internet(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM requisicoes_compras WHERE id = {param}', (id,))
    req = cursor.fetchone()
    
    if req:
        tipo = req['equipamento_tipo'].lower()
        esp = req['especificacao_desejada'].lower()
        preco, pot, dep = 45000.0, 5.5, 375.0
        if 'torno' in tipo or 'cnc' in tipo or 'centro' in tipo: preco, pot, dep = (620000.0, 35.0, 5100.0) if '5 eixos' in esp else (290000.0, 18.0, 2400.0)
        elif 'forno' in tipo: preco, pot, dep = (180000.0, 45.0, 1500.0)
        elif 'prensa' in tipo: preco, pot, dep = (220000.0, 22.0, 1800.0)
        elif 'solda' in tipo: preco, pot, dep = (15000.0, 7.5, 125.0)
        elif 'material' in tipo or 'insumo' in tipo: preco, pot, dep = (2500.0 if 'tubo' in esp else 850.0), 0.0, 0.0
        
        cursor.execute(f'UPDATE requisicoes_compras SET preco_cotado={param}, potencia_cotada={param}, depreciacao_sugerida={param}, status=\'Cotado - Aguardando Confirmação\' WHERE id={param}', (preco, pot, dep, id))
        conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/efetivar_compra/<int:id>', methods=['POST'])
def efetivar_compra(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM requisicoes_compras WHERE id = {param}', (id,))
    req = cursor.fetchone()
    
    cursor.execute('SELECT aluguel_regional FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    ult_imovel = cursor.fetchone()
    aluguel_mensal = float(ult_imovel['aluguel_regional'] if ult_imovel else 0.0)
    
    minutos_operacionais = 44 * 4.33 * 60
    custo_aluguel_minuto = aluguel_mensal / minutos_operacionais
    
    if req:
        preco = float(request.form.get('preco_final') or 0.0)
        pot = float(request.form.get('potencia_final') or 0.0)
        dep = float(request.form.get('depreciacao_final') or 0.0)
        vida = int(request.form.get('vida_util_meses') or 120)
        if "Máquina" in req['equipamento_tipo'] or "Ativo" in req['equipamento_tipo']:
            c_mm = (dep / minutos_operacionais) + ((pot * 0.75) / 60) + custo_aluguel_minuto
            cursor.execute(f'INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, horas_trabalhadas, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, vida_util_meses) VALUES ({param}, {param}, {param}, \'3000\', \'15000\', 1000, 500, 1000, 0, {param}, {param}, {param}, {param}, \'Posto Vago - Aguardando MOD\', 0.0, {param})', (f"{req['especificacao_desejada']}", pot, pot * 0.7, preco, dep, preco * 0.2, c_mm, vida))
        else:
            sku_gerado = f"SKU-{req['id']}"
            if is_postgres:
                cursor.execute(f"INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (%s, %s, %s, 'Lote', %s) ON CONFLICT (codigo_material) DO UPDATE SET volume_disponivel = materiais.volume_disponivel + EXCLUDED.volume_disponivel", (sku_gerado, req['especificacao_desejada'], preco/float(req['quantidade']), float(req['quantidade'])))
            else:
                cursor.execute(f"INSERT OR REPLACE INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (?, ?, ?, 'Lote', ?)", (sku_gerado, req['especificacao_desejada'], preco/float(req['quantidade']), float(req['quantidade'])))
        cursor.execute(f"UPDATE requisicoes_compras SET status = 'Comprado e Ativado' WHERE id = {param}", (id,))
        conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/deletar_requisicao/<int:id>', methods=['POST'])
def deletar_requisicao(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM requisicoes_compras WHERE id={param}', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('requisicoes'))

@app.route('/inventario')
@app.route('/materiais')
def materiais():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM materiais')
    mats = cursor.fetchall()
    
    cursor.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(ep.quantidade_disponivel, 0) AS quantidade_disponivel FROM produtos p LEFT JOIN estoque_produtos ep ON p.id = ep.produto_id')
    itens_acabados = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('materiais.html', materiais=mats, estoque_itens=itens_acabados, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_material', methods=['POST'])
def salvar_material():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    try:
        cursor.execute(f'INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES ({param}, {param}, {param}, {param}, {param})', (request.form.get('codigo_material', 'SKU').strip(), request.form.get('nome_material', 'Insumo').strip(), float(request.form.get('preco_unidade') or 0), request.form.get('dimensoes', 'N/A'), float(request.form.get('volume_disponivel') or 0)))
        conn.commit()
        conn.close()
    except:
        conn.close()
        return "Erro: SKU duplicado!"
    return redirect(url_for('materiais'))

@app.route('/alterar_material/<int:id>', methods=['POST'])
def alterar_material(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'UPDATE materiais SET codigo_material={param}, nome_material={param}, preco_unidade={param}, dimensoes={param}, volume_disponivel={param} WHERE id={param}', (request.form.get('codigo_material', 'SKU').strip(), request.form.get('nome_material', 'Insumo').strip(), float(request.form.get('preco_unidade') or 0), request.form.get('dimensoes', 'N/A'), float(request.form.get('volume_disponivel') or 0), id))
    conn.commit()
    conn.close()
    return redirect(url_for('materiais'))

@app.route('/deletar_material/<int:id>', methods=['POST'])
def deletar_material(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM materiais WHERE id={param}', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('materiais'))

@app.route('/engenharia')
def engenharia():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM produtos')
    prods = cursor.fetchall()
    
    cursor.execute('SELECT id, nome_equipamento, custo_minuto_maquina FROM maquinas')
    maqs = cursor.fetchall()
    
    cursor.execute('SELECT id, nome_material, preco_unidade FROM materiais')
    mats = cursor.fetchall()
    
    cursor.execute('SELECT ep.*, p.nome_produto, p.codigo_produto, m.nome_equipamento, mat.nome_material FROM estrutura_produto ep JOIN produtos p ON ep.produto_id = p.id LEFT JOIN maquinas m ON ep.maquina_id = m.id LEFT JOIN materiais mat ON ep.material_id = mat.id')
    comps = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('engenharia.html', produtos=prods, maquinas=maqs, materiais=mats, composicoes=comps, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_produto', methods=['POST'])
def salvar_produto():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    try:
        cursor.execute(f'INSERT INTO produtos (codigo_produto, nome_produto) VALUES ({param}, {param})', (request.form.get('codigo_produto', 'PROD').strip(), request.form.get('nome_produto', 'Acabado').strip()))
        conn.commit()
    except:
        conn.close()
        return "Erro: Produto duplicado."
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/vincular_estrutura', methods=['POST'])
def vincular_estrutura():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    maquina_id = request.form.get('maquina_id')
    material_id = request.form.get('material_id')
    m_id = int(maquina_id) if maquina_id and maquina_id.isdigit() else None
    mat_id = int(material_id) if material_id and material_id.isdigit() else None
    
    cursor = conn.cursor()
    cursor.execute(f'INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES ({param}, {param}, {param}, {param}, {param})', (int(request.form.get('produto_id') or 0), m_id, mat_id, float(request.form.get('tempo_processo_min') or 0), float(request.form.get('quantidade_material') or 0)))
    conn.commit()
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/deletar_item_estrutura/<int:id>', methods=['POST'])
def deletar_item_estrutura(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM estrutura_produto WHERE id={param}', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('engenharia'))

@app.route('/precificacao')
def precificacao():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT p.id, p.codigo_produto, p.nome_produto, COALESCE(SUM(ep.tempo_processo_min * mq.custo_minuto_maquina), 0) + COALESCE(SUM(ep.quantidade_material * mt.preco_unidade), 0) AS custo_fabricacao FROM produtos p LEFT JOIN estrutura_produto ep ON p.id = ep.produto_id LEFT JOIN maquinas mq ON ep.maquina_id = mq.id LEFT JOIN materiais mt ON ep.material_id = mt.id GROUP BY p.id, p.codigo_produto, p.nome_produto')
    prods = cursor.fetchall()
    
    cursor.execute('SELECT fp.*, p.codigo_produto, p.nome_produto FROM formacao_precos fp JOIN produtos p ON fp.produto_id = p.id')
    salvos = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('precificacao.html', produtos=prods, precos_salvos=salvos, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/salvar_preco', methods=['POST'])
def salvar_preco():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    p_id = int(request.form.get('produto_id') or 0)
    i_mun = float(request.form.get('imposto_municipal') or 0)
    i_est = float(request.form.get('imposto_estadual') or 0)
    i_fed = float(request.form.get('imposto_federal') or 0)
    margem = float(request.form.get('margem_lucro') or 0)
    p_final = float(request.form.get('preco_venda_final') or 0)
    
    cursor = conn.cursor()
    if is_postgres:
        cursor.execute(f'INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (produto_id) DO UPDATE SET imposto_municipal=EXCLUDED.imposto_municipal, imposto_estadual=EXCLUDED.imposto_estadual, imposto_federal=EXCLUDED.imposto_federal, margem_lucro=EXCLUDED.margem_lucro, preco_venda_final=EXCLUDED.preco_venda_final', (p_id, i_mun, i_est, i_fed, margem, p_final))
    else:
        cursor.execute(f'INSERT OR REPLACE INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (?, ?, ?, ?, ?, ?)', (p_id, i_mun, i_est, i_fed, margem, p_final))
    conn.commit()
    conn.close()
    return redirect(url_for('precificacao'))

@app.route('/vendas')
def vendas():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT p.id, p.codigo_produto, p.nome_produto, fp.preco_venda_final, COALESCE(e.quantidade_disponivel, 0) AS estoque_atual FROM produtos p JOIN formacao_precos fp ON p.id = fp.produto_id LEFT JOIN estoque_produtos e ON p.id = e.produto_id')
    prods = cursor.fetchall()
    
    cursor.execute('SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id ORDER BY pv.id DESC')
    peds = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('vendas.html', produtos=prods, pedidos=peds, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/estoque')
def estoque():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT p.id AS produto_id, p.codigo_produto, p.nome_produto, COALESCE(ep.quantidade_disponivel, 0) AS quantidade_disponivel FROM produtos p LEFT JOIN estoque_produtos ep ON p.id = ep.produto_id')
    itens = cursor.fetchall()
    
    cursor.execute("SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.observacoes LIKE '%SOB ENCOMENDA%'")
    peds = cursor.fetchall()
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('estoque.html', estoque_itens=itens, pedidos=peds, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/lancar_venda', methods=['POST'])
def lancar_venda():
    if not session.get('logado'): return redirect(url_for('index'))
    prod_id = int(request.form.get('produto_id') or 0)
    qtd = int(request.form.get('quantidade') or 1)
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT quantidade_disponivel FROM estoque_produtos WHERE produto_id = {param}', (prod_id,))
    est = cursor.fetchone()
    
    if est:
        estoque_atual = float(est['quantidade_disponivel'] if hasattr(est, 'keys') or isinstance(est, dict) else est[0])
    else:
        estoque_atual = 0.0
        
    if estoque_atual >= qtd:
        cursor.execute(f'UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel - {param} WHERE produto_id = {param}', (qtd, prod_id))
        cursor.execute(f'INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES ({param}, {param}, 0, \'Pronta Entrega - Faturado\')', (prod_id, qtd))
    else:
        # CORREÇÃO: Alterado 'quantity' para 'quantidade' para bater com o esquema do banco de dados
        cursor.execute(f'INSERT INTO pedidos_vendas (produto_id, quantidade, desconto_percentual, observacoes) VALUES ({param}, {param}, 0, \'SOB ENCOMENDA - Fila PCP\')', (prod_id, qtd))
        
    conn.commit()
    conn.close()
    return redirect(url_for('vendas'))

@app.route('/deletar_venda/<int:id>', methods=['POST'])
def deletar_venda(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM pedidos_vendas WHERE id={param}', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('vendas'))
@app.route('/pcp')
def pcp():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens_processo ORDER BY pedido_id ASC, id ASC')
    ords = cursor.fetchall()
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    return render_template('pcp.html', ordens=ords, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/solicitar_producao_pcp/<int:pedido_id>', methods=['POST'])
def solicitar_producao_pcp(pedido_id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT id FROM ordens_processo WHERE pedido_id = {param}', (pedido_id,))
    existe = cursor.fetchone()
    
    if not existe:
        cursor.execute(f'SELECT pv.*, p.codigo_produto, p.nome_produto FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id WHERE pv.id = {param}', (pedido_id,))
        ped = cursor.fetchone()
        
        if ped:
            p_id = int(ped['produto_id'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped)
            p_qtd = int(ped['quantidade'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped)
            p_cod = ped['codigo_produto'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped
            p_nome = ped['nome_produto'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped
            
            cursor.execute(f'SELECT ep.*, m.nome_equipamento, m.custo_minuto_maquina, m.operador_nome FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id WHERE ep.produto_id = {param} ORDER BY ep.id ASC', (p_id,))
            rots = cursor.fetchall()
            
            ponteiro_tempo = datetime.datetime.now()
            tempo_setup_fixo = 15
            for idx, r in enumerate(rots):
                tempo_lote_min = (float(r['tempo_processo_min'] or 0) * p_qtd) + tempo_setup_fixo
                custo_total_operacao = tempo_lote_min * float(r['custo_minuto_maquina'] or 0.15)
                status_inicial = "Na Fila [GARGALO OPERACIONAL]" if tempo_lote_min > 480 else "Na Fila"
                entrada_str = ponteiro_tempo.strftime("%d/%m/%Y %H:%M")
                ponteiro_tempo = ponteiro_tempo + datetime.timedelta(minutes=tempo_lote_min)
                saida_str = ponteiro_tempo.strftime("%d/%m/%Y %H:%M")
                
                cursor.execute(f'INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_name, codigo_produto, nome_produto, data_entrada, tempo_estimado_min, data_saida, status, custo_operacao, operador_nome) VALUES ({param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param}, {param})', (pedido_id, f"OP {(idx+1)*10}", r['nome_equipamento'] or 'Bancada Manual', p_cod, p_nome, entrada_str, tempo_lote_min, saida_str, status_inicial, custo_total_operacao, r['operador_nome'] or 'Pendente'))
            conn.commit()
        flash('Ordem de Produção transmitida com sucesso para o painel do PCP!', 'success')
    conn.close()
    return redirect(url_for('estoque'))

@app.route('/abastecer_estoque_pcp', methods=['POST'])
def abastecer_estoque_pcp():
    if not session.get('logado'): return redirect(url_for('index'))
    prod_id = int(request.form.get('produto_id') or 0)
    pedido_id = int(request.form.get('pedido_id') or 0)
    qtd = float(request.form.get('quantidade_abastecer') or 0)
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT COUNT(*) FROM ordens_processo WHERE pedido_id = {param}', (pedido_id,))
    row_ext = cursor.fetchone()
    ops_existentes = int(row_ext[0] if isinstance(row_ext, tuple) else row_ext)
    
    cursor.execute(f'SELECT COUNT(*) FROM ordens_processo WHERE pedido_id = {param} AND status NOT LIKE \'Finalizado%\'', (pedido_id,))
    row_pend = cursor.fetchone()
    ops_pendentes = int(row_pend[0] if isinstance(row_pend, tuple) else row_pend)
    
    if ops_existentes == 0 or ops_pendentes > 0:
        conn.close()
        flash('Bloqueio de Qualidade: O Almoxarifado não pode receber este lote! Existem operações pendentes no PCP.', 'danger')
        return redirect(url_for('estoque'))
        
    cursor.execute(f'SELECT * FROM estoque_produtos WHERE produto_id = {param}', (prod_id,))
    est = cursor.fetchone()
    
    if not est: 
        cursor.execute(f'INSERT INTO estoque_produtos (produto_id, quantidade_disponivel) VALUES ({param}, {param})', (prod_id, qtd))
    else: 
        cursor.execute(f'UPDATE estoque_produtos SET quantidade_disponivel = quantidade_disponivel + {param} WHERE produto_id = {param}', (qtd, prod_id))
        
    cursor.execute(f'UPDATE ordens_processo SET status = \'Finalizado e Armazenado\' WHERE pedido_id = {param}', (pedido_id,))
    conn.commit()
    conn.close()
    flash('Recebimento efetuado e integrado com sucesso ao estoque disponível.', 'success')
    return redirect(url_for('estoque'))

@app.route('/dar_baixa_op/<int:id>', methods=['POST'])
def dar_baixa_op(id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'UPDATE ordens_processo SET operador_nome = {param}, status = "Finalizado" WHERE id = {param}', (request.form.get('operador_nome', 'Operador'), id))
    conn.commit()
    conn.close()
    return redirect(url_for('pcp'))
@app.route('/imprimir_nf/<int:pedido_id>')
def imprimir_nf(pedido_id):
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    is_postgres = not hasattr(conn, 'row_factory')
    param = "%s" if is_postgres else "?"
    
    cursor = conn.cursor()
    cursor.execute(f'SELECT pv.*, p.codigo_produto, p.nome_produto, fp.preco_venda_final, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id WHERE pv.id = {param}', (pedido_id,))
    ped = cursor.fetchone()
    conn.close()
    
    if not ped: return "Nota Fiscal não encontrada."
    
    p_qtd = int(ped['quantidade'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped[2])
    p_desc = float(ped['desconto_percentual'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped[3])
    pf_venda = float(ped['preco_venda_final'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped[6])
    i_mun = float(ped['imposto_municipal'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped[7])
    i_est = float(ped['imposto_estadual'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped[8])
    i_fed = float(ped['imposto_federal'] if hasattr(ped, 'keys') or isinstance(ped, dict) else ped[9])
    
    sub = pf_venda * p_qtd
    v_desc = sub * (p_desc / 100.0)
    liq = sub - v_desc
    v_mun_calc = liq * (i_mun / 100.0)
    v_est_calc = liq * (i_est / 100.0)
    v_fed_calc = liq * (i_fed / 100.0)
    return render_template('nota_fiscal.html', p=ped, subtotal=sub, v_desconto=v_desc, total_liquido=liq, v_municipal=v_mun_calc, v_estadual=v_est_calc, v_federal=v_fed_calc, total_impostos=v_mun_calc+v_est_calc+v_fed_calc)

@app.route('/financeiro')
def financeiro():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    
    def valor_campo(row, indice=0):
        if row is None: return 0.0
        if hasattr(row, 'keys') or isinstance(row, dict):
            return float(row[list(row.keys())[0]])
        return float(row[indice])

    cursor = conn.cursor()

    cursor.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    faturamento_bruto = valor_campo(cursor.fetchone())

    cursor.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    despesa_pessoal_bruta = valor_campo(cursor.fetchone())

    cursor.execute('SELECT COALESCE(SUM((fp.preco_venda_final * pv.quantidade) * ((fp.imposto_municipal + fp.imposto_estadual + fp.imposto_federal) / 100.0)), 0) FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    impostos_vendas = valor_campo(cursor.fetchone())
    
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    total_encargos = impostos_vendas + (despesa_pessoal_bruta * 0.20)
    return render_template('financeiro.html', faturamento=faturamento_bruto, custo_pessoal=despesa_pessoal_bruta, impostos=total_encargos, saldo_liquido=caixa, caixa_disponivel=caixa, capital_inicial=total)

@app.route('/pagar_dividendos', methods=['POST'])
def pagar_dividendos():
    if not session.get('logado'): return redirect(url_for('index'))
    percentual = float(request.form.get('percentual_lucro') or 25.0)
    flash(f'Distribuição de {percentual}% dos dividendos processada!', 'success')
    return redirect(url_for('financeiro'))

@app.route('/roi')
def roi():
    if not session.get('logado'): return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COALESCE(SUM(fp.preco_venda_final * pv.quantidade), 0) AS receita_bruta, COALESCE(SUM(pv.quantidade), 0) AS total_pecas FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    v_dados = cursor.fetchone()
    
    cursor.execute('SELECT COALESCE(SUM(valor_imovel_estimado + capital_inicial_negocio), 0) AS capital_total, COALESCE(SUM(aluguel_regional), 0) AS aluguel FROM investimentos_imobiliarios')
    invs = cursor.fetchone()
    
    cursor.execute("SELECT COALESCE(SUM(salario_base + valor_adicionais), 0) FROM maquinas WHERE operador_nome != 'Posto Vago - Aguardando MOD' AND operador_nome != ''")
    row_pes = cursor.fetchone()
    
    despesa_pessoal = float(row_pes[0] if isinstance(row_pes, tuple) else row_pes)
    caixa, total = calcular_caixa_disponivel(conn)
    conn.close()
    
    rec = float(v_dados['receita_bruta'] if hasattr(v_dados, 'keys') or isinstance(v_dados, dict) else v_dados[0])
    pecas = float(v_dados['total_pecas'] if hasattr(v_dados, 'keys') or isinstance(v_dados, dict) else v_dados[1])
    cap = float(invs['capital_total'] if hasattr(invs, 'keys') or isinstance(invs, dict) else invs[0])
    aluguel = float(invs['aluguel'] if hasattr(invs, 'keys') or isinstance(invs, dict) else invs[1])
    
    sobra = rec - despesa_pessoal - aluguel
    payback_meses = (cap / sobra) if sobra > 0 else 0.0
    return render_template('roi.html', receita=rec, total_pecas=pecas, capital=cap, payback_real=payback_meses, lucro_acionistas=rec*0.25, caixa_disponivel=caixa, capital_inicial=total)

if __name__ == '__main__':
    app.run(debug=True)

