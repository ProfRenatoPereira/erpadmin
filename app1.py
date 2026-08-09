from flask import Flask, render_template, request, jsonify
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
import os

app = Flask(__name__)

# --- CONEXÃO COM O SUPABASE (POSTGRESQL) ---
URL_SUPABASE = os.environ.get('DATABASE_URL', "postgresql://postgres:SUA_SENHA_AQUI@db.xxxxxx.supabase.co:5432/postgres")

def obter_conexao():
    return psycopg2.connect(URL_SUPABASE)

def iniciar_banco():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id SERIAL PRIMARY KEY, nome TEXT NOT NULL, cargo TEXT, salario REAL, horas_comp REAL, insalubridade REAL,
            beneficios REAL, qtd_filhos INTEGER, observacoes TEXT, data_admissao TEXT, mes_ref TEXT,
            v_he_semana REAL, v_he_sabado REAL, v_he_domingo REAL, total_he_ganho REAL,
            reflexo_13_ferias REAL, salario_familia REAL, inss REAL, irrf REAL, vt REAL,
            adiantamento_valor REAL, total_descontos REAL, liquido REAL,
            banco_horas REAL, turno TEXT, hora_entrada TEXT, adicional_noturno REAL, regime_he TEXT, departamento TEXT,
            plano_saude REAL DEFAULT 0, plano_odontologico REAL DEFAULT 0, sindicato REAL DEFAULT 0, vale_farmacia REAL DEFAULT 0, ano_ref TEXT DEFAULT '2026'
        )
    ''')
    
    # Migração Segura: Adiciona individualmente as novas colunas caso elas já não existam no Supabase
    try:
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS v_he_25 REAL DEFAULT 0;")
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS v_he_50 REAL DEFAULT 0;")
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS v_he_100 REAL DEFAULT 0;")
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS vale_refeicao REAL DEFAULT 0;")
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS vale_market REAL DEFAULT 0;")
        cursor.execute("ALTER TABLE funcionarios ADD COLUMN IF NOT EXISTS vale_mercado REAL DEFAULT 0;")
    except psycopg2.Error:
        pass

    cursor.execute('CREATE TABLE IF NOT EXISTS cargos_custom (id SERIAL PRIMARY KEY, nome_cargo TEXT UNIQUE)')
    cursor.execute("SELECT COUNT(*) FROM cargos_custom")
    if cursor.fetchone()[0] == 0:
        cargos = [("Diretoria",), ("Gerência",), ("Analista",), ("Operacional",)]
        cursor.executemany("INSERT INTO cargos_custom (nome_cargo) VALUES (%s)", cargos)
    conexao.commit()
    cursor.close()
    conexao.close()
def calcular_inss(salario_contribuicao):
    if salario_contribuicao <= 1412: return salario_contribuicao * 0.075
    if salario_contribuicao <= 2666.68: return (salario_contribuicao * 0.09) - 21.18
    if salario_contribuicao <= 4000.03: return (salario_contribuicao * 0.12) - 101.18
    if salario_contribuicao <= 7786.02: return (salario_contribuicao * 0.14) - 181.18
    return 908.86

def calcular_irrf(salario_contribuicao, desconto_inss):
    base = salario_contribuicao - desconto_inss
    if base <= 2259.20: return 0
    if base <= 2826.65: return (base * 0.075) - 169.44
    if base <= 3751.05: return (base * 0.15) - 381.44
    if base <= 4664.68: return (base * 0.225) - 662.77
    return (base * 0.275) - 896.00

iniciar_banco()
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/cargos', methods=['GET', 'POST'])
def gerenciar_cargos():
    conexao = obter_conexao()
    cursor = conexao.cursor()
    if request.method == 'POST':
        dados = request.json
        novo = dados.get('nome_cargo', '').strip()
        if novo:
            try:
                cursor.execute('INSERT INTO cargos_custom (nome_cargo) VALUES (%s)', (novo,))
                conexao.commit()
            except psycopg2.IntegrityError: pass
        cursor.close()
        conexao.close()
        return jsonify({'status': 'sucesso'})
    else:
        cursor.execute('SELECT nome_cargo FROM cargos_custom ORDER BY nome_cargo')
        cargos = [linha[0] for linha in cursor.fetchall()]
        cursor.close()
        conexao.close()
        return jsonify(cargos)

@app.route('/api/funcionarios', methods=['GET'])
def listar_funcionarios():
    conexao = obter_conexao()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM funcionarios ORDER BY id ASC')
    linhas = cursor.fetchall()
    cursor.close()
    conexao.close()
    return jsonify([dict(linha) for linha in linhas])

@app.route('/api/funcionarios/<int:id_func>', methods=['DELETE'])
def demitir_funcionario(id_func):
    conexao = obter_conexao()
    cursor = conexao.cursor()
    cursor.execute('DELETE FROM funcionarios WHERE id = %s', (id_func,))
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'status': 'removido'})
@app.route('/api/calcular', methods=['POST'])
def calcular_e_salvar():
    dados = request.json
    id_func = dados.get('id')
    salario_base = float(dados.get('salario', 0))
    horas_comp = float(dados.get('horasComp', 220)) or 220
    beneficios = float(dados.get('beneficios', 0))
    insalubridade = float(dados.get('insalubridade', 0))
    qtd_filhos = int(dados.get('qtdFilhos', 0))
    nome, cargo = dados.get('nome', '').strip(), dados.get('cargo', '')
    observacoes, data_admissao = dados.get('observacoes', ''), dados.get('dataAdmissao', '')
    mes_ref, ano_ref = dados.get('mesRef', '7'), dados.get('anoRef', '2026')
    turno, hora_entrada = dados.get('turno', 'diurno'), dados.get('horaEntrada', '08:00')
    regime_he, departamento = dados.get('regimeHe', 'pagar'), dados.get('departamento', 'Administrativo')
    he_semana, he_sabado, he_domingo = float(dados.get('heSemana', 0)), float(dados.get('heSabado', 0)), float(dados.get('heDomingo', 0))
    sindicato, plano_saude, plano_odonto, vale_farmacia = float(dados.get('sindicato', 0)), float(dados.get('planoSaude', 0)), float(dados.get('planoOdonto', 0)), float(dados.get('valeFarmacia', 0))
    vale_refeicao, vale_mercado = float(dados.get('valeRefeicao', 0)), float(dados.get('valeMercado', 0))
    aplicar_adiantamento, descontar_vt = dados.get('adiantamento', 'nao') == 'sim', dados.get('vt', 'nao') == 'sim'
    
    if data_admissao and mes_ref and ano_ref:
        try:
            adm_dt = datetime.strptime(data_admissao, "%Y-%m-%d")
            ref_dt = datetime(int(ano_ref), int(mes_ref), 1)
            if ref_dt < datetime(adm_dt.year, adm_dt.month, 1):
                return jsonify({'status': 'erro', 'message': 'Referência anterior à admissão!'}), 400
        except Exception: pass

    valor_hora = salario_base / horas_comp
    adicional_noturno = salario_base * 0.20 if turno == 'noturno' else 0
    v_he_semana, v_he_sabado, v_he_domingo = he_semana * (valor_hora * 1.25), he_sabado * (valor_hora * 1.50), he_domingo * (valor_hora * 2.00)
    
    banco_horas = 0
    if regime_he == 'pagar':
        total_he_ganho = v_he_semana + v_he_sabado + v_he_domingo
        v_he_25 = v_he_semana
        v_he_50 = v_he_sabado
        v_he_100 = v_he_domingo
        reflexo_13_ferias = total_he_ganho * (2.0 / 12.0)
    else:
        banco_horas = he_semana + he_sabado + he_domingo
        total_he_ganho, reflexo_13_ferias, v_he_semana, v_he_sabado, v_he_domingo = 0, 0, 0, 0, 0
        v_he_25, v_he_50, v_he_100 = 0, 0, 0
        
    total_salario_familia = qtd_filhos * 62.04 if (salario_base + adicional_noturno) <= 1819.26 and qtd_filhos > 0 else 0
    salario_contribuicao = salario_base + total_he_ganho + insalubridade + reflexo_13_ferias + adicional_noturno
    inss = calcular_inss(salario_contribuicao)
    irrf = calcular_irrf(salario_contribuicao, inss)
    vt = salario_base * 0.06 if descontar_vt else 0
    
    proventos_totais = salario_base + beneficios + total_he_ganho + insalubridade + reflexo_13_ferias + total_salario_familia + adicional_noturno
    descontos_totais = inss + irrf + vt + sindicato + plano_saude + plano_odonto + vale_farmacia + vale_refeicao + vale_mercado
    valor_adiantamento = (proventos_totais - descontos_totais) * 0.40 if aplicar_adiantamento else 0
    total_descontos_final = descontos_totais + valor_adiantamento
    liquido_final = proventos_totais - total_descontos_final
    
    conexao = obter_conexao()
    cursor = conexao.cursor()
    if id_func:
        cursor.execute('''
            UPDATE funcionarios SET nome=%s, cargo=%s, salario=%s, horas_comp=%s, insalubridade=%s, beneficios=%s, qtd_filhos=%s, 
            observacoes=%s, data_admissao=%s, mes_ref=%s, v_he_semana=%s, v_he_sabado=%s, v_he_domingo=%s, total_he_ganho=%s, 
            reflexo_13_ferias=%s, salario_familia=%s, inss=%s, irrf=%s, vt=%s, adiantamento_valor=%s, total_descontos=%s, liquido=%s,
            banco_horas=%s, turno=%s, hora_entrada=%s, adicional_noturno=%s, regime_he=%s, departamento=%s,
            plano_saude=%s, plano_odontologico=%s, sindicato=%s, vale_farmacia=%s, ano_ref=%s, v_he_25=%s, v_he_50=%s, v_he_100=%s, vale_refeicao=%s, vale_mercado=%s WHERE id=%s
        ''', (nome, cargo, salario_base, horas_comp, insalubridade, beneficios, qtd_filhos, observacoes, data_admissao, mes_ref, 
              v_he_semana, v_he_sabado, v_he_domingo, total_he_ganho, reflexo_13_ferias, total_salario_familia, inss, irrf, vt, 
              valor_adiantamento, total_descontos_final, liquido_final, banco_horas, turno, hora_entrada, adicional_noturno, regime_he, departamento,
              plano_saude, plano_odonto, sindicato, vale_farmacia, ano_ref, v_he_25, v_he_50, v_he_100, vale_refeicao, vale_mercado, id_func))
    else:
        cursor.execute('''
            INSERT INTO funcionarios (nome, cargo, salario, horas_comp, insalubridade, beneficios, qtd_filhos, 
            observacoes, data_admissao, mes_ref, v_he_semana, v_he_sabado, v_he_domingo, total_he_ganho, 
            reflexo_13_ferias, salario_familia, inss, irrf, vt, adiantamento_valor, total_descontos, liquido,
            banco_horas, turno, hora_entrada, adicional_noturno, regime_he, departamento, plano_saude, plano_odontologico, sindicato, vale_farmacia, ano_ref, v_he_25, v_he_50, v_he_100, vale_refeicao, vale_mercado)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (nome, cargo, salario_base, horas_comp, insalubridade, beneficios, qtd_filhos, observacoes, data_admissao, mes_ref, 
              v_he_semana, v_he_sabado, v_he_domingo, total_he_ganho, reflexo_13_ferias, total_salario_familia, inss, irrf, vt, 
              valor_adiantamento, total_descontos_final, liquido_final, banco_horas, turno, hora_entrada, adicional_noturno, regime_he, departamento,
              plano_saude, plano_odonto, sindicato, vale_farmacia, ano_ref, v_he_25, v_he_50, v_he_100, vale_refeicao, vale_mercado))
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'status': 'sucesso'})

@app.route('/api/decimo_individual/<int:id_func>', methods=['GET'])
def calcular_decimo_individual(id_func):
    conexao = obter_conexao()
    cursor = conexao.cursor(cursor_factory=RealDictCursor)
    cursor.execute('SELECT * FROM funcionarios WHERE id = %s', (id_func,))
    f = cursor.fetchone()
    cursor.close()
    conexao.close()
    if not f: return jsonify({'status': 'erro', 'message': 'Registro não localizado'}), 404
    f_dict = dict(f)
    base_calculo = f_dict['salario'] + (f_dict['total_he_ganho'] or 0) + (f_dict['insalubridade'] or 0) + (f_dict['adicional_noturno'] or 0)
    meses_trabalhados = 12
    if f_dict['data_admissao']:
        try:
            dt_adm = datetime.strptime(f_dict['data_admissao'], "%Y-%m-%d")
            if dt_adm.year == 2026:
                meses_trabalhados = 12 - dt_adm.month + 1
                if dt_adm.day > 15: meses_trabalhados -= 1
                if meses_trabalhados < 0: meses_trabalhados = 0
        except: pass
    bruto = (base_calculo / 12.0) * meses_trabalhados
    inss = bruto * 0.075 if bruto <= 1412 else (bruto * 0.09) - 21.18
    return jsonify({'status': 'sucesso', 'nome': f_dict['nome'], 'cargo': f_dict['cargo'], 'meses_proporcionais': meses_trabalhados, 'bruto': bruto, 'inss': inss, 'liquido': bruto - inss})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
