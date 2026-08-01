import os
import psycopg2  # Driver do Supabase
from psycopg2.extras import DictCursor
import datetime
import math
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from whitenoise import WhiteNoise
from functools import wraps

app = Flask(__name__)
app.secret_key = 'chave_secreta_pedagogica'
app.wsgi_app = WhiteNoise(app.wsgi_app, root='static/', prefix='static/')

# String de conexão capturada do Render
SUPABASE_URL = os.environ.get('DATABASE_URL', 'SUA_CONNECTION_STRING_DO_SUPABASE_AQUI')

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
    conn = psycopg2.connect(SUPABASE_URL, cursor_factory=DictCursor)
    return conn
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('CREATE TABLE IF NOT EXISTS usuarios (id SERIAL PRIMARY KEY, usuario TEXT UNIQUE NOT NULL, senha TEXT NOT NULL, aprovado INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS investimentos_imobiliarios (id SERIAL PRIMARY KEY, turma_nome TEXT NOT NULL, cidade_regiao TEXT NOT NULL, bairro_imovel TEXT NOT NULL, area_imovel REAL NOT NULL, taxa_selic REAL NOT NULL, valor_imovel_estimado REAL NOT NULL, aluguel_regional REAL NOT NULL, perc_acionistas REAL NOT NULL, capital_inicial_negocio REAL DEFAULT 0.0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS maquinas (id SERIAL PRIMARY KEY, nome_equipamento TEXT NOT NULL, potencia REAL NOT NULL, consumo_eletrico REAL NOT NULL, velocidade TEXT, avanco TEXT, comprimento_max REAL, diametro_max REAL, frequencia_manutencao INTEGER NOT NULL, horas_trabalhadas INTEGER DEFAULT 0, preco_compra REAL NOT NULL, depreciacao_mensal REAL NOT NULL, valor_venda_final REAL NOT NULL, custo_minuto_maquina REAL NOT NULL, operador_nome TEXT DEFAULT \'Posto Vago - Aguardando MOD\', custo_minuto_operador REAL DEFAULT 0.0, salario_base REAL DEFAULT 0.0, valor_adicionais REAL DEFAULT 0.0, turno_trabalho TEXT DEFAULT \'Diurno\', dia_semana TEXT DEFAULT \'Regular\', vida_util_meses INTEGER DEFAULT 120)')
    cursor.execute('CREATE TABLE IF NOT EXISTS materiais (id SERIAL PRIMARY KEY, codigo_material TEXT UNIQUE NOT NULL, nome_material TEXT NOT NULL, preco_unidade REAL NOT NULL, dimensoes TEXT, volume_disponivel REAL NOT NULL)')
    cursor.execute('CREATE TABLE IF NOT EXISTS requisicoes_compras (id SERIAL PRIMARY KEY, equipamento_tipo TEXT NOT NULL, especificacao_desejada TEXT NOT NULL, quantidade INTEGER DEFAULT 1, status TEXT DEFAULT \'Pendente em Cotação\', preco_cotado REAL DEFAULT 0, potencia_cotada REAL DEFAULT 0, depreciacao_sugerida REAL DEFAULT 0, vida_util_sugerida INTEGER DEFAULT 120, data_requisicao TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    cursor.execute('CREATE TABLE IF NOT EXISTS produtos (id SERIAL PRIMARY KEY, codigo_produto TEXT UNIQUE NOT NULL, nome_produto TEXT NOT NULL, custo_total_fabricacao REAL DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS estrutura_produto (id SERIAL PRIMARY KEY, produto_id INTEGER NOT NULL, maquina_id INTEGER, material_id INTEGER, tempo_processo_min REAL DEFAULT 0, quantidade_material REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS formacao_precos (id SERIAL PRIMARY KEY, produto_id INTEGER UNIQUE NOT NULL, imposto_municipal REAL DEFAULT 0, imposto_estadual REAL DEFAULT 0, imposto_federal REAL DEFAULT 0, margem_lucro REAL DEFAULT 0, preco_venda_final REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS estoque_produtos (id SERIAL PRIMARY KEY, produto_id INTEGER UNIQUE NOT NULL, quantidade_disponivel REAL DEFAULT 0, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS pedidos_vendas (id SERIAL PRIMARY KEY, produto_id INTEGER NOT NULL, quantidade INTEGER NOT NULL, desconto_percentual REAL DEFAULT 0, observacoes TEXT, data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(produto_id) REFERENCES produtos(id))')
    cursor.execute('CREATE TABLE IF NOT EXISTS ordens_processo (id SERIAL PRIMARY KEY, pedido_id INTEGER NOT NULL, numero_operacao TEXT NOT NULL, maquina_name TEXT NOT NULL, codigo_produto TEXT NOT NULL, nome_produto TEXT NOT NULL, data_entrada TEXT NOT NULL, tempo_estimado_min REAL NOT NULL, data_saida TEXT NOT NULL, operador_nome TEXT DEFAULT \'Pendente\', status TEXT DEFAULT \'Na Fila\', custo_operacao REAL DEFAULT 0.0, FOREIGN KEY(pedido_id) REFERENCES pedidos_vendas(id))')
    conn.commit()
    cursor.close()
    conn.close()

init_db()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Por favor, efetue o login.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')
@app.route('/imprimir_holerite/<int:maquina_id>')
@login_required
def imprimir_holerite(maquina_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM maquinas WHERE id = %s', (maquina_id,))
    maquina = cursor.fetchone()
    cursor.execute('SELECT * FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    empresa = cursor.fetchone()
    cursor.close()
    conn.close()
    if not maquina or maquina['salario_base'] == 0:
        return "Operador não contratado ou sem salário definido para esta máquina.", 404
    nome_empresa = empresa['turma_nome'] if empresa else "Simulador ERP Industrial"
    regiao_empresa = empresa['cidade_regiao'] if empresa else "Polo Industrial"
    salario_bruto = maquina['salario_base'] + maquina['valor_adicionais']
    inss = salario_bruto * 0.09
    irrf = salario_bruto * 0.075 if salario_bruto > 2200 else 0.0
    salario_liquido = salario_bruto - (inss + irrf)
    dados_holerite = {
        "empresa": nome_empresa,
        "regiao": regiao_empresa,
        "nome_operador": maquina['operador_nome'],
        "equipamento": maquina['nome_equipamento'],
        "turno": maquina['turno_trabalho'],
        "periodo": datetime.datetime.now().strftime("%B / %Y").capitalize(),
        "salario_base": maquina['salario_base'],
        "adicionais": maquina['valor_adicionais'],
        "inss": inss,
        "irrf": irrf,
        "liquido": salario_liquido
    }
    return render_template('holerite_impressao.html', dados=dados_holerite)

@app.route('/')
@login_required
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    config = cursor.fetchone()
    cursor.close()
    conn.close()
    if not config:
        return render_template('passo1_investimento.html')
    return render_template('dashboard.html', config=config)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE usuario = %s', (usuario,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()
        if user and check_password_hash(user['senha'], '123' if senha == '123' else user['senha']):
            if user['aprovado'] == 1 or user['usuario'] == 'professor':
                session['usuario_id'] = user['id']
                session['usuario_nome'] = user['usuario']
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Sua conta aguarda aprovação do professor.', 'warning')
        else:
            flash('Usuário ou senha incorretos.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Sessão encerrada.', 'info')
    return redirect(url_for('login'))

@app.route('/professor_painel_secreto')
@login_required
def professor_painel():
    if session.get('usuario_nome') != 'professor':
        flash('Acesso restrito ao administrador.', 'danger')
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM usuarios WHERE usuario != \'professor\'')
    alunos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('professor_painel.html', alunos=alunos)

@app.route('/professor/aprovar/<int:user_id>')
@login_required
def professor_aprovar(user_id):
    if session.get('usuario_nome') != 'professor':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE usuarios SET aprovado = 1 WHERE id = %s', (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Aluno aprovado com sucesso.', 'success')
    return redirect(url_for('professor_painel'))

@app.route('/professor/excluir/<int:user_id>')
@login_required
def professor_excluir(user_id):
    if session.get('usuario_nome') != 'professor':
        return redirect(url_for('index'))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM usuarios WHERE id = %s', (user_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Aluno removido.', 'info')
    return redirect(url_for('professor_painel'))

@app.route('/professor/cadastrar', methods=['POST'])
def professor_cadastrar_aluno():
    usuario = request.form['usuario']
    senha = request.form['senha']
    senha_hash = generate_password_hash(senha)
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO usuarios (usuario, senha, aprovado) VALUES (%s, %s, 0)', (usuario, senha_hash))
        conn.commit()
        flash('Solicitação de cadastro enviada. Aguarde a aprovação do professor.', 'success')
    except:
        flash('Nome de usuário já existe.', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('login'))
@app.route('/inicializar_simulador', methods=['POST'])
@login_required
def inicializar_simulador():
    turma_nome = request.form['turma_nome']
    cidade_regiao = request.form['cidade_regiao']
    bairro_imovel = request.form['bairro_imovel']
    area_imovel = float(request.form['area_imovel'])
    taxa_selic = float(request.form['taxa_selic'])
    valor_imovel_estimado = float(request.form['valor_imovel_estimado'])
    aluguel_regional = float(request.form['aluguel_regional'])
    perc_acionistas = float(request.form['perc_acionistas'])
    capital_inicial_negocio = float(request.form['capital_inicial_negocio'])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO investimentos_imobiliarios (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (turma_nome, cidade_regiao, bairro_imovel, area_imovel, taxa_selic, valor_imovel_estimado, aluguel_regional, perc_acionistas, capital_inicial_negocio))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Simulador inicializado com sucesso!', 'success')
    return redirect(url_for('index'))

@app.route('/estrutura')
@login_required
def estrutura():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    config = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('passo2_estrutura.html', config=config, catalogo=CATALOGO_MAQUINAS)

@app.route('/alterar_estrutura/<int:passo>', methods=['POST'])
@login_required
def alterar_estrutura(passo):
    return redirect(url_for('maquinas_view' if passo == 2 else 'index'))

@app.route('/maquinas')
@login_required
def maquinas_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM maquinas')
    maquinas_instaladas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('passo3_maquinas.html', catalogo=CATALOGO_MAQUINAS, instaladas=maquinas_instaladas)

@app.route('/salvar_maquina', methods=['POST'])
@login_required
def salvar_maquina():
    chave = request.form['maquina_chave']
    turno = request.form['turno_trabalho']
    dia = request.form['dia_semana']
    if chave not in CATALOGO_MAQUINAS:
        flash('Máquina inválida.', 'danger')
        return redirect(url_for('maquinas_view'))
    m = CATALOGO_MAQUINAS[chave]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO maquinas (nome_equipamento, potencia, consumo_eletrico, velocidade, avanco, comprimento_max, diametro_max, frequencia_manutencao, preco_compra, depreciacao_mensal, valor_venda_final, custo_minuto_maquina, operador_nome, custo_minuto_operador, salario_base, valor_adicionais, turno_trabalho, dia_semana, vida_util_meses) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (m['nome'], m['pot'], m['cons'], m['vel'], m['avan'], m['comp'], m['diam'], 1000, m['preco'], m['dep'], m['venda'], m['custo_op'], m['operador'], 0.15, m['salario'], m['adic'], turno, dia, m['vida']))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f'{m["nome"]} adicionada com sucesso!', 'success')
    return redirect(url_for('maquinas_view'))

@app.route('/materiais')
@login_required
def materiais_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM materiais')
    estoque = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('passo4_materiais.html', catalogo=CATALOGO_MATERIAIS, estoque=estoque)

@app.route('/abastecer_estoque_pcp', methods=['POST'])
@login_required
def abastecer_estoque_pcp():
    chave = request.form['material_chave']
    qtd = float(request.form['quantidade'])
    if chave not in CATALOGO_MATERIAIS:
        flash('Material inválido.', 'danger')
        return redirect(url_for('materiais_view'))
    mat = CATALOGO_MATERIAIS[chave]
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM materiais WHERE codigo_material = %s', (mat['cod'],))
    existe = cursor.fetchone()
    if existe:
        cursor.execute('UPDATE materiais SET volume_disponivel = volume_disponivel + %s WHERE codigo_material = %s', (qtd, mat['cod']))
    else:
        cursor.execute('INSERT INTO materiais (codigo_material, nome_material, preco_unidade, dimensoes, volume_disponivel) VALUES (%s, %s, %s, %s, %s)', (mat['cod'], mat['nome'], mat['preco'], mat['dim'], qtd))
    conn.commit()
    cursor.close()
    conn.close()
    flash(f'Estoque de {mat["nome"]} abastecido com +{qtd} unidades.', 'success')
    return redirect(url_for('materiais_view'))
@app.route('/engenharia')
@login_required
def engenharia():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM produtos')
    prods = cursor.fetchall()
    cursor.execute('SELECT * FROM maquinas')
    maqs = cursor.fetchall()
    cursor.execute('SELECT * FROM materiais')
    mats = cursor.fetchall()
    cursor.execute('SELECT ep.*, p.nome_produto, p.codigo_produto FROM estrutura_produto ep JOIN produtos p ON ep.produto_id = p.id')
    estruturas = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('passo5_engenharia.html', produtos=prods, maquinas=maqs, materiais=mats, estruturas=estruturas)

@app.route('/cadastrar_produto_base', methods=['POST'])
@login_required
def cadastrar_produto_base():
    cod = request.form['codigo_produto']
    nome = request.form['nome_produto']
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO produtos (codigo_produto, nome_produto, custo_total_fabricacao) VALUES (%s, %s, 0)', (cod, nome))
        conn.commit()
        flash('Produto base criado. Vincule os processos abaixo.', 'success')
    except:
        flash('Código de produto já existente.', 'danger')
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('engenharia'))

@app.route('/vincular_estrutura', methods=['POST'])
@login_required
def vincular_estrutura():
    p_id = int(request.form['produto_id'])
    m_id = request.form.get('maquina_id')
    mat_id = request.form.get('material_id')
    tempo = float(request.form.get('tempo_processo_min', 0))
    qtd_mat = float(request.form.get('quantidade_material', 0))
    m_id = int(m_id) if m_id else None
    mat_id = int(mat_id) if mat_id else None
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO estrutura_produto (produto_id, maquina_id, material_id, tempo_processo_min, quantidade_material) VALUES (%s, %s, %s, %s, %s)', (p_id, m_id, mat_id, tempo, qtd_mat))
    cursor.execute('SELECT * FROM maquinas WHERE id = %s', (m_id,))
    maq = cursor.fetchone()
    cursor.execute('SELECT * FROM materiais WHERE id = %s', (mat_id,))
    mat = cursor.fetchone()
    custo_maq = (maq['custo_minuto_maquina'] + maq['custo_minuto_operador']) * tempo if maq else 0
    custo_mat = mat['preco_unidade'] * qtd_mat if mat else 0
    adicional = custo_maq + custo_mat
    cursor.execute('UPDATE produtos SET custo_total_fabricacao = custo_total_fabricacao + %s WHERE id = %s', (adicional, p_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Elemento de estrutura e custos vinculado.', 'success')
    return redirect(url_for('engenharia'))

@app.route('/precificacao')
@login_required
def precificacao():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT p.*, fp.imposto_municipal, fp.imposto_estadual, fp.imposto_federal, fp.margem_lucro, fp.preco_venda_final FROM produtos p LEFT JOIN formacao_precos fp ON p.id = fp.produto_id')
    produtos_custos = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('passo6_precificacao.html', produtos=produtos_custos)

@app.route('/calcular_preco', methods=['POST'])
@login_required
def calcular_preco():
    p_id = int(request.form['produto_id'])
    utilidade = float(request.form['margem_lucro']) / 100.0
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT custo_total_fabricacao FROM produtos WHERE id = %s', (p_id,))
    custo = cursor.fetchone()['custo_total_fabricacao']
    pv = custo / (1.0 - utilidade) if utilidade < 1.0 else custo
    cursor.execute('SELECT id FROM formacao_precos WHERE produto_id = %s', (p_id,))
    existe = cursor.fetchone()
    if existe:
        cursor.execute('UPDATE formacao_precos SET imposto_municipal=5, imposto_estadual=18, imposto_federal=12, margem_lucro=%s, preco_venda_final=%s WHERE produto_id = %s', (utilidade*100, pv, p_id))
    else:
        cursor.execute('INSERT INTO formacao_precos (produto_id, imposto_municipal, imposto_estadual, imposto_federal, margem_lucro, preco_venda_final) VALUES (%s, 5, 18, 12, %s, %s)', (p_id, utilidade*100, pv))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Preço de venda calculated por Markup Simulado.', 'success')
    return redirect(url_for('precificacao'))

@app.route('/vendas')
@login_required
def vendas_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT p.id, p.nome_produto, fp.preco_venda_final FROM produtos p JOIN formacao_precos fp ON p.id = fp.produto_id')
    disponiveis = cursor.fetchall()
    cursor.execute('SELECT pv.*, p.nome_produto, fp.preco_venda_final FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id')
    historico = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('passo7_vendas.html', produtos=disponiveis, vendas=historico)
@app.route('/lancar_venda', methods=['POST'])
@login_required
def lancar_venda():
    p_id = int(request.form['produto_id'])
    qtd = int(request.form['quantidade'])
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO pedidos_vendas (produto_id, quantidade) VALUES (%s, %s)', (p_id, qtd))
    
    # Executa LASTVAL() adequado para obter o id gerado no SERIAL do Postgres/Supabase
    cursor.execute('SELECT LASTVAL()')
    pedido_id = cursor.fetchone()[0]
    
    cursor.execute('SELECT ep.*, m.nome_material, p.codigo_produto, p.nome_produto FROM estrutura_produto ep LEFT JOIN maquinas m ON ep.maquina_id = m.id JOIN produtos p ON ep.produto_id = p.id WHERE ep.produto_id = %s', (p_id,))
    rotas = cursor.fetchall()
    for r in rotas:
        maq_nome = r['nome_material'] if r['nome_material'] else 'Bancada Manual'
        cursor.execute('INSERT INTO ordens_processo (pedido_id, numero_operacao, maquina_name, codigo_produto, nome_produto, data_entrada, tempo_estimado_min, data_saida, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)', (pedido_id, f"OP-{r['id']}", maq_nome, r['codigo_produto'], r['nome_produto'], datetime.datetime.now().strftime('%d/%m %H:%M'), r['tempo_processo_min'], 'Aguardando', 'Na Fila'))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Contrato comercial fechado! Roteiro de OP gerado no PCP.', 'success')
    return redirect(url_for('vendas_view'))

@app.route('/pcp')
@login_required
def pcp_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM ordens_processo')
    ops = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('passo8_pcp.html', ops=ops)

@app.route('/dar_baixa_op/<int:op_id>', methods=['POST'])
@login_required
def dar_baixa_op(op_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE ordens_processo SET status=\'Finalizado\', data_saida=%s WHERE id = %s', (datetime.datetime.now().strftime('%d/%m %H:%M'), op_id))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Operação industrial executada com sucesso.', 'success')
    return redirect(url_for('pcp_view'))

@app.route('/financeiro')
@login_required
def financeiro_view():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    config = cursor.fetchone()
    cursor.execute('SELECT COALESCE(SUM(preco_venda_final * quantidade), 0) AS faturamento FROM pedidos_vendas pv JOIN formacao_precos fp ON pv.produto_id = fp.produto_id')
    faturamento = cursor.fetchone()['faturamento']
    cursor.execute('SELECT COALESCE(SUM(preco_compra), 0) AS imobilizado FROM maquinas')
    maqs_custo = cursor.fetchone()['imobilizado']
    cursor.execute('SELECT COALESCE(SUM(volume_disponivel * preco_unidade), 0) AS estoque_val FROM materiais')
    mat_custo = cursor.fetchone()['estoque_val']
    cursor.execute('SELECT * FROM maquinas')
    funcionarios = cursor.fetchall()
    cursor.close()
    conn.close()
    cap_inicial = config['capital_inicial_negocio'] if config else 0
    saldo_caixa = cap_inicial + faturamento - maqs_custo - mat_custo
    return render_template('passo9_financeiro.html', caixa=saldo_caixa, faturamento=faturamento, imobilizado=maqs_custo, estoque_val=mat_custo, funcionarios=funcionarios)

@app.route('/imprimir_nf/<int:pedido_id>')
@login_required
def imprimir_nf(pedido_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT pv.*, p.nome_produto, p.codigo_produto, fp.preco_venda_final FROM pedidos_vendas pv JOIN produtos p ON pv.produto_id = p.id JOIN formacao_precos fp ON p.id = fp.produto_id WHERE pv.id = %s', (pedido_id,))
    venda = cursor.fetchone()
    cursor.execute('SELECT * FROM investimentos_imobiliarios ORDER BY id DESC LIMIT 1')
    empresa = cursor.fetchone()
    cursor.close()
    conn.close()
    if not venda:
        return "Nota Fiscal não encontrada.", 404
    return render_template('nota_fiscal.html', venda=venda, empresa=empresa)

@app.route('/requisicoes')
@login_required
def requisicoes_view():
    return render_template('requisicoes.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)
