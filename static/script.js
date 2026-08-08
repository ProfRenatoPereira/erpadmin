let funcionarios = [];

function formatarMoeda(valor) {
    return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}

window.addEventListener('DOMContentLoaded', async () => {
    await carregarCargosBanco();
    await carregarDadosBanco();
    
    // Vinculação cirúrgica dos botões operacionais da tela
    document.getElementById('btn_add_cargo')?.addEventListener('click', adicionarCargoNovo);
    document.getElementById('btn_contratar')?.addEventListener('click', adicionarFuncionario);
    document.getElementById('btn_salvar')?.addEventListener('click', salvarAlteracoesFuncionario);
    document.getElementById('btn_limpar')?.addEventListener('click', limparCamposTela);
    document.getElementById('btn_balanco')?.addEventListener('click', imprimirBalanco);
    document.getElementById('btn_13')?.addEventListener('click', abrirDecimoTerceiroGeral);
    document.getElementById('btn_print_list')?.addEventListener('click', () => window.print());
    
    // Atualização em tempo real nas mudanças fiscais e temporais
    document.getElementById('mes_referencia')?.addEventListener('change', actualizarDashboard);
    document.getElementById('ano_referencia')?.addEventListener('change', actualizarDashboard);
    document.getElementById('receita_empresa')?.addEventListener('change', actualizarDashboard);
    document.getElementById('limite_func')?.addEventListener('change', actualizarDashboard);
    document.getElementById('btn_tema')?.addEventListener('click', alternarTema);

    // Conservação do tema de acessibilidade preferido do usuário
    if (localStorage.getItem('tema') === 'escuro') {
        document.body.classList.add('dark-mode');
        const botao = document.getElementById('btn_tema');
        if (botao) botao.innerHTML = '☀️ Modo Claro';
    }
});

async function carregarCargosBanco() {
    try {
        const resposta = await fetch('/api/cargos');
        if (!resposta.ok) throw new Error();
        const cargos = await resposta.json();
        const selectCargo = document.getElementById('cargo');
        if (selectCargo) {
            selectCargo.innerHTML = '';
            cargos.forEach(c => {
                const cargoNome = Array.isArray(c) ? c : c;
                const opt = document.createElement('option');
                opt.value = cargoNome; opt.innerText = cargoNome;
                selectCargo.appendChild(opt);
            });
        }
    } catch (error) {
        const selectCargo = document.getElementById('cargo');
        if (selectCargo && selectCargo.children.length === 0) {
            const padroes = ["Diretoria", "Gerência", "Analista", "Operacional"];
            selectCargo.innerHTML = '';
            padroes.forEach(c => {
                const opt = document.createElement('option');
                opt.value = c; opt.innerText = c;
                selectCargo.appendChild(opt);
            });
        }
    }
}
async function carregarDadosBanco() {
    try {
        const resposta = await fetch('/api/funcionarios');
        if (!resposta.ok) throw new Error();
        funcionarios = await resposta.json();
    } catch (error) {
        console.warn("API de funcionários offline. Rodando local.");
    }
    
    // Alimenta dinamicamente o select de funcionários criado na área de ponto
    const selectPontoFunc = document.getElementById('ponto_selecao_funcionario');
    if (selectPontoFunc) {
        selectPontoFunc.innerHTML = '<option value="">-- Escolha um Profissional --</option>';
        funcionarios.forEach(f => {
            const opt = document.createElement('option');
            opt.value = f.id;
            opt.innerText = f.nome;
            selectPontoFunc.appendChild(opt);
        });
    }

    renderizarTabela();
    actualizarDashboard();
}

async function adicionarCargoNovo() {
    const inputCargo = document.getElementById('novo_cargo_input');
    const nomeCargo = inputCargo ? inputCargo.value.trim() : '';
    if (!nomeCargo) { alert('Digite o nome do novo cargo.'); return; }
    try {
        await fetch('/api/cargos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nome_cargo: nomeCargo })
        });
    } catch(e) { console.error("Erro ao salvar cargo na API"); }
    if (inputCargo) inputCargo.value = '';
    await carregarCargosBanco();
}

async function adicionarFuncionario() {
    const pegarValor = (id) => {
        const el = document.getElementById(id);
        return el ? el.value : '';
    };

    const nome = pegarValor('nome').trim();
    if (!nome) { alert('Insira o nome do profissional.'); return; }
    
    const dados = {
        id: pegarValor('func_id_edicao'),
        nome: nome,
        cargo: pegarValor('cargo'),
        salario: parseFloat(pegarValor('salario')) || 0,
        horasComp: parseFloat(pegarValor('horas_comp')) || 220,
        beneficios: parseFloat(pegarValor('beneficios')) || 0,
        heSemana: parseFloat(pegarValor('he_semana')) || 0,
        heSabado: parseFloat(pegarValor('he_sabado')) || 0,
        heDomingo: parseFloat(pegarValor('he_domingo')) || 0,
        planoSaude: parseFloat(pegarValor('plano_saude')) || 0,
        planoOdonto: parseFloat(pegarValor('plano_odontologico')) || 0,
        valeFarmacia: parseFloat(pegarValor('vale_farmacia')) || 0,
        sindicato: parseFloat(pegarValor('sindicato')) || 0,
        valeRefeicao: parseFloat(pegarValor('vale_refeicao')) || 0,
        valeMercado: parseFloat(pegarValor('vale_mercado')) || 0,
        adiantamento: pegarValor('adiantamento'),
        vt: pegarValor('vt_desconto'),
        qtdFilhos: parseInt(pegarValor('qtd_filhos')) || 0,
        mesRef: pegarValor('mes_referencia'),
        anoRef: pegarValor('ano_referencia') || '2026',
        regimeHe: pegarValor('regime_he'),
        turno: pegarValor('turno'),
        horaEntrada: pegarValor('hora_entrada'),
        departamento: pegarValor('departamento'),
        observacoes: pegarValor('observacoes'),
        dataAdmissao: pegarValor('data_admissao')
    };

    try {
        const resposta = await fetch('/api/calcular', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dados)
        });
        if (resposta.ok) {
            limparCamposTela();
            await carregarDadosBanco();
        } else {
            const erro = await resposta.json();
            alert(erro.message || "Erro no cálculo.");
        }
    } catch(e) { console.error("Erro ao enviar funcionário para API"); }
}
function limparCamposTela() {
    const padroes = {
        'func_id_edicao': '', 'nome': '', 'salario': '3500', 'horas_comp': '220',
        'regime_he': 'pagar', 'beneficios': '500', 'qtd_filhos': '0', 'observacoes': '',
        'he_semana': '0', 'he_sabado': '0', 'he_domingo': '0', 'turno': 'diurno',
        'hora_entrada': '08:00', 'adiantamento': 'nao', 'vt_desconto': 'nao',
        'vale_farmacia': '0', 'sindicato': '0', 'plano_saude': '0', 'plano_odontologico': '0',
        'novo_aumento_salarial': '0', 'vale_refeicao': '0', 'vale_mercado': '0'
    };
    Object.keys(padroes).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = padroes[id];
    });
    const btn = document.getElementById('btn_contratar');
    if (btn) btn.innerText = 'Contratar Profissional';
}

function carregarFuncionarioParaEdicao(f) {
    const mapeamento = {
        'func_id_edicao': f.id, 'nome': f.nome, 'cargo': f.cargo, 'salario': f.salario,
        'horas_comp': f.horas_comp, 'regime_he': f.regime_he, 'beneficios': f.beneficios,
        'qtd_filhos': f.qtd_filhos, 'observacoes': f.observacoes || '', 'data_admissao': f.data_admissao,
        'turno': f.turno, 'hora_entrada': f.hora_entrada, 'departamento': f.departamento,
        'vale_farmacia': f.vale_farmacia || 0, 'sindicato': f.sindicato || 0,
        'plano_saude': f.plano_saude || 0, 'plano_odontologico': f.plano_odontologico || 0,
        'vale_refeicao': f.vale_refeicao || 0, 'vale_mercado': f.vale_mercado || 0
    };
    Object.keys(mapeamento).forEach(id => {
        const el = document.getElementById(id);
        if (el) el.value = mapeamento[id];
    });
    const btn = document.getElementById('btn_contratar');
    if (btn) btn.innerText = 'Modo Edição Ativo';
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function salvarAlteracoesFuncionario() {
    const id = document.getElementById('func_id_edicao')?.value;
    if (!id) { alert('Selecione um funcionário clicando no nome dele primeiro.'); return; }
    const valorPromocao = parseFloat(document.getElementById('novo_aumento_salarial')?.value) || 0;
    if (valorPromocao > 0 && document.getElementById('salario')) { 
        document.getElementById('salario').value = valorPromocao; 
    }
    await adicionarFuncionario(); 
}

function actualizarDashboard() {
    const receita = parseFloat(document.getElementById('receita_empresa')?.value) || 0;
    let totalBruto = 0, totalDescontos = 0, totalLiquido = 0, custoTotalCorporativo = 0;
    
    funcionarios.forEach(f => {
        totalBruto += f.salario + (f.total_he_ganho || 0) + (f.insalubridade || 0) + (f.adicional_noturno || 0);
        totalDescontos += (f.total_descontos || 0);
        totalLiquido += (f.liquido || 0);
        custoTotalCorporativo += f.salario + (f.beneficios || 0) + (f.total_he_ganho || 0) + (f.adicional_noturno || 0);
    });
    
    let saldoFinal = receita - custoTotalCorporativo;
    const elTotal = document.getElementById('dash_total_func');
    const elLim = document.getElementById('limite_func');
    if (elTotal && elLim) elTotal.innerText = funcionarios.length + ' / ' + elLim.value;
    
    if (document.getElementById('dash_custo_bruto')) document.getElementById('dash_custo_bruto').innerText = formatarMoeda(totalBruto);
    if (document.getElementById('dash_total_descontos')) document.getElementById('dash_total_descontos').innerText = formatarMoeda(totalDescontos);
    if (document.getElementById('dash_folha_liquida')) document.getElementById('dash_folha_liquida').innerText = formatarMoeda(totalLiquido);
    if (document.getElementById('dash_saldo_empresa')) document.getElementById('dash_saldo_empresa').innerText = formatarMoeda(saldoFinal);
    if (document.getElementById('card_balanco')) document.getElementById('card_balanco').className = saldoFinal < 0 ? 'metric negative' : 'metric';
    
    renderizarGraficosNativos(totalLiquido, totalDescontos);
}
function renderizarGraficosNativos(liquido, descontos) {
    const total = liquido + descontos;
    const pizza = document.getElementById('nativePizza');
    if (pizza) {
        const perc = total > 0 ? ((descontos / total) * 100).toFixed(1) : 0;
        pizza.style.background = `conic-gradient(#dc2626 0% ${perc}%, #16a34a ${perc}% 100%)`;
    }
    const custosCargo = {};
    funcionarios.forEach(f => custosCargo[f.cargo] = (custosCargo[f.cargo] || 0) + f.salario);
    const cargos = Object.keys(custosCargo).sort((a,b) => custosCargo[b] - custosCargo[a]);
    const maxCusto = cargos.length > 0 ? custosCargo[cargos[0]] : 1;
    const containerPareto = document.getElementById('nativePareto');
    if (containerPareto) {
        containerPareto.innerHTML = '';
        cargos.slice(0, 4).forEach(c => {
            const pct = maxCusto > 0 ? (custosCargo[c] / maxCusto) * 100 : 0;
            containerPareto.innerHTML += `<div class="bar-wrapper"><div class="bar-native" style="height: ${pct}%">${pct.toFixed(0)}%</div><div class="bar-label">${c}</div></div>`;
        });
    }
    const containerLinear = document.getElementById('nativeLinear');
    if (containerLinear) {
        containerLinear.innerHTML = '';
        const maxBruto = funcionarios.length > 0 ? Math.max(...funcionarios.map(f => f.salario)) : 1;
        funcionarios.slice(-4).forEach(f => {
            const pct = maxBruto > 0 ? (f.salario / maxBruto) * 100 : 0;
            containerLinear.innerHTML += `<div class="linear-row"><div class="linear-name">${f.nome}</div><div class="linear-bar-bg"><div class="linear-bar-fill" style="width: ${pct}%"></div></div><div class="linear-value" style="color:#1e3a8a">${formatarMoeda(f.salario)}</div></div>`;
        });
    }
}

function renderizarTabela() {
    const corpo = document.getElementById('tabela_corpo');
    if (!corpo) return;
    corpo.innerHTML = '';
    funcionarios.forEach(f => {
        const dataFormatada = f.data_admissao ? f.data_admissao.split('-').reverse().join('/') : '---';
        const turnoRotulo = f.turno === 'noturno' ? '🌙 Noturno' : '☀️ Diurno';
        const jTexto = f.banco_horas > 0 ? f.horas_comp + 'h (+' + f.banco_horas + 'h BH)' : f.horas_comp + 'h';
        const deptoRotulo = f.departamento ? f.departamento : 'Administrativo';
        
        const tr = document.createElement('tr');
        tr.innerHTML = `<td><a id="lnk_${f.id}" href="javascript:void(0)" style="color:var(--primary); text-decoration:underline;"><strong>${f.nome}</strong></a><br><small>Admissão: ${dataFormatada}</small></td>
        <td>${f.cargo}<br><small style="color:#64748b">Dep: ${deptoRotulo}</small></td>
        <td><small>Jornada: ${jTexto}</small><br><strong>${turnoRotulo}</strong></td>
        <td style="color:#16a34a"><strong>${formatarMoeda(f.liquido)}</strong></td>
        <td class="actions-cell" style="display: flex; gap: 6px; align-items: center; justify-content: flex-start; flex-wrap: wrap;">
            <a onclick="abrirContracheque(${f.id})" href="javascript:void(0)" class="btn-link" style="background: #1e3a8a; color: white;" title="Holerite Mensal">📄 Mês</a>
            <a onclick="abrirFerias(${f.id})" href="javascript:void(0)" class="btn-link" style="background: #16a34a; color: white;" title="Recibo de Férias">🌴 Férias</a>
            <a onclick="calcularDecimoTerceiroIndividual(${f.id})" href="javascript:void(0)" class="btn-link" style="background: #0284c7; color: white;" title="13º Individual">🎄 13º</a>
            <button class="btn-delete" style="background:#dc2626; color:white; border:none; padding:4px 8px; font-size:0.75rem; border-radius:4px;" onclick="dispararRescisaoImediata(${f.id}, 'demissao_sem_justa')" title="Dispensa">⚠️ Dispensa</button>
            <button class="btn-delete" style="background:#f97316; color:white; border:none; padding:4px 8px; font-size:0.75rem; border-radius:4px;" onclick="dispararRescisaoImediata(${f.id}, 'pedido_demissao')" title="Pedido">🚪 Pedido</button>
            <button class="btn-delete" style="background:#7f1d1d; color:white; border:none; padding:4px 8px; font-size:0.75rem; border-radius:4px;" onclick="deletarFuncionario(${f.id})" title="Demitir Profissional">❌ Demitir</button>
        </td>`;
        corpo.appendChild(tr);
        document.getElementById(`lnk_${f.id}`)?.addEventListener('click', () => carregarFuncionarioParaEdicao(f));
    });
}
function abrirContracheque(id) {
    const f = funcionarios.find(emp => emp.id === id);
    if (!f) return;
    const proventos = f.salario + (f.total_he_ganho || 0) + (f.insalubridade || 0) + (f.adicional_noturno || 0) + (f.beneficios || 0) + (f.salario_familia || 0);
    const saude = f.plano_saude || 0; const odonto = f.plano_odontologico || 0; const sind = f.sindicato || 0; const farmacia = f.vale_farmacia || 0;
    const vrDesconto = f.vale_refeicao || 0; const vmDesconto = f.vale_mercado || 0;
    
    const adiantVal = parseFloat(f.adiantamento_valor || f.adiantamento || 0);
    const totalDeducoesAtuais = (f.total_descontos || 0);
    const baseFgts = f.salario + (f.total_he_ganho || 0) + (f.adicional_noturno || 0) + (f.insalubridade || 0);
    const fgtsMes = baseFgts * 0.08;
    const obsEmpresa = document.getElementById('observacoes')?.value.trim() || f.observacoes || "Nenhuma observação informada.";
    const janela = window.open('', '_blank', 'width=800,height=900'); if (!janela) return;

    const horasCompFunc = f.horas_comp || 220;
    const valorHoraNormal = f.salario / horasCompFunc;
    const valorHora25 = valorHoraNormal * 1.25;
    const valorHora50 = valorHoraNormal * 1.50;
    const valorHora100 = valorHoraNormal * 2.00;

    let html = "<html><head><title>Holerite Oficial</title><style>" + obterEstiloHolerite() + "</style></head><body><div class='holerite-box'>";
    html += "<div class='header-holerite'><div style='padding: 0 10px; height: 45px; background: #1e3a8a; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.1rem;'>📊TERADMAS📈</div><div style='text-align: left;'><h2 style='margin: 0; font-size: 1.3rem; color: #1e3a8a;'>TERCEIRO ADM</h2><h3 style='margin: 2px 0 0 0; font-size: 0.9rem; color: #64748b;'>ASSOCIADOS</h3></div></div>";
    html += "<h2 style='text-align:center; font-size:1.2rem; margin: 15px 0 5px 0;'>RECIBO DE PAGAMENTO MENSAL</h2><hr>";
    
    html += "<div class='info-colaborador'>";
    html += "<p><strong>Colaborador:</strong> " + f.nome + " | <strong>Cargo:</strong> " + f.cargo + "</p>";
    html += "<p><strong>Mês de Referência:</strong> " + (document.getElementById('mes_referencia')?.value || f.mes_ref || '7') + "/" + (document.getElementById('ano_referencia')?.value || '2026') + " ";
    html += "<span style='margin-left: 20px; background-color: #f1f5f9; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; color: #1e3a8a; border: 1px solid #cbd5e1;'>";
    html += "<strong>Valores/Hora:</strong> Normal=" + formatarMoeda(valorHoraNormal) + ", Extras 50%=" + formatarMoeda(valorHora50) + ", Extras 100%=" + formatarMoeda(valorHora100);
    html += "</span></p>";
    html += "</div>";
    
    html += "<h4 class='section-title proventos-title'>PROVENTOS (CRÉDITOS)</h4>";
    html += "<table class='table-holerite' style='width:100%; border-collapse:collapse;'>";
    html += "<tr style='border-bottom: 1px solid #000; font-weight:bold;'><td>Descrição</td><td style='text-align:center; width:25%;'>Referência / Qtde</td><td class='text-right' style='width:25%;'>Valor</td></tr>";
    
    html += "<tr><td>(+) Salário Base</td><td style='text-align:center;'>" + horasCompFunc.toFixed(2) + " hrs</td><td class='text-right'>" + formatarMoeda(f.salario) + "</td></tr>";
    
    const temHeNova = (f.v_he_25 > 0 || f.v_he_50 > 0 || f.v_he_100 > 0);
    if (temHeNova) {
        if (f.v_he_25 > 0) {
            const qtdeHe25 = f.he_semana || (f.v_he_25 / valorHora25);
            html += "<tr><td>(+) Horas Extras (25%)</td><td style='text-align:center;'>" + qtdeHe25.toFixed(2) + " hrs</td><td class='text-right'>" + formatarMoeda(f.v_he_25) + "</td></tr>";
        }
        if (f.v_he_50 > 0) {
            const qtdeHe50 = f.he_sabado || (f.v_he_50 / valorHora50);
            html += "<tr><td>(+) Horas Extras (50%)</td><td style='text-align:center;'>" + qtdeHe50.toFixed(2) + " hrs</td><td class='text-right'>" + formatarMoeda(f.v_he_50) + "</td></tr>";
        }
        if (f.v_he_100 > 0) {
            const qtdeHe100 = f.he_domingo || (f.v_he_100 / valorHora100);
            html += "<tr><td>(+) Horas Extras (100%)</td><td style='text-align:center;'>" + qtdeHe100.toFixed(2) + " hrs</td><td class='text-right'>" + formatarMoeda(f.v_he_100) + "</td></tr>";
        }
    } else if (f.total_he_ganho > 0) {
        html += "<tr><td>(+) Horas Extras Acumuladas</td><td style='text-align:center;'>-</td><td class='text-right'>" + formatarMoeda(f.total_he_ganho) + "</td></tr>";
    }
    
    if (f.insalubridade > 0) html += "<tr><td>(+) Adicional Insalubridade</td><td style='text-align:center;'>-</td><td class='text-right'>" + formatarMoeda(f.insalubridade) + "</td></tr>";
    if (f.adicional_noturno > 0) html += "<tr><td>(+) Adicional Noturno</td><td style='text-align:center;'>-</td><td class='text-right'>" + formatarMoeda(f.adicional_noturno) + "</td></tr>";
    if (f.beneficios > 0) html += "<tr><td>(+) Auxílios/Benefícios</td><td style='text-align:center;'>-</td><td class='text-right'>" + formatarMoeda(f.beneficios) + "</td></tr>";
    
    html += "<tr class='row-total'><td>TOTAL PROVENTOS:</td><td style='text-align:center;'>-</td><td class='text-right'>" + formatarMoeda(proventos) + "</td></tr></table>";
    
    html += "<h4 class='section-title descontos-title'>DESCONTOS (RETENÇÕES)</h4><table class='table-holerite'>";
    if (f.inss > 0) html += "<tr><td>(-) INSS Progressivo</td><td class='text-right'>" + formatarMoeda(f.inss) + "</td></tr>";
    if (f.irrf > 0) html += "<tr><td>(-) Imposto de Renda (IRRF)</td><td class='text-right'>" + formatarMoeda(f.irrf) + "</td></tr>";
    if (f.vt > 0) html += "<tr><td>(-) Vale Transporte (6%)</td><td class='text-right'>" + formatarMoeda(f.vt) + "</td></tr>";
    if (saude > 0) html += "<tr><td>(-) Plano de Saúde</td><td class='text-right'>" + formatarMoeda(saude) + "</td></tr>";
    if (odonto > 0) html += "<tr><td>(-) Plano Odontológico</td><td class='text-right'>" + formatarMoeda(odonto) + "</td></tr>";
    if (sind > 0) html += "<tr><td>(-) Contribuição Sindical</td><td class='text-right'>" + formatarMoeda(sind) + "</td></tr>";
    if (farmacia > 0) html += "<tr><td>(-) Vale Farmácia</td><td class='text-right'>" + formatarMoeda(farmacia) + "</td></tr>";
    if (vrDesconto > 0) html += "<tr><td>(-) Vale Refeição</td><td class='text-right'>" + formatarMoeda(vrDesconto) + "</td></tr>";
    if (vmDesconto > 0) html += "<tr><td>(-) Vale Mercado</td><td class='text-right'>" + formatarMoeda(vmDesconto) + "</td></tr>";
    if (adiantVal > 0) html += "<tr><td>(-) Adiantamento Quinzenal</td><td class='text-right'>" + formatarMoeda(adiantVal) + "</td></tr>";
    
    html += "<tr class='row-total'><td>TOTAL DESCONTOS:</td><td class='text-right'>" + formatarMoeda(totalDeducoesAtuais) + "</td></tr></table>";
    html += "<div class='liquido-box'><span class='liquido-label'>VALOR LÍQUIDO A RECEBER:</span><span class='liquido-value'>" + formatarMoeda(proventos - totalDeducoesAtuais) + "</span></div>";
    html += "<div style='margin-top:20px; font-size:0.85rem; border:1px solid #000; padding:10px; background:#fafafa;'><strong>FGTS recolhido no mês (Informativo):</strong> " + formatarMoeda(fgtsMes) + "<br><br><strong>Observações de Aula/Empresa:</strong><br><span style='font-style:italic; color:#334155;'>" + obsEmpresa + "</span></div>";
    html += "<div class='assinatura-container'><div class='linha-assinatura'></div><p>Assinatura do Colaborador</p></div></div></body></html>";
    janela.document.write(html); janela.document.close();
}
function imprimirBalanco() {
    const receita = parseFloat(document.getElementById('receita_empresa')?.value) || 0;
    let totalBruto = 0; funcionarios.forEach(f => { totalBruto += (f.salario + (f.total_he_ganho || 0)); });
    const area = document.getElementById('print-area');
    if (area) {
        area.innerHTML = "<div style='padding:40px; font-family:sans-serif; text-align:center;'><div style='padding: 0 10px; height: 45px; background: #1e3a8a; border-radius: 6px; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.1rem; font-family: Arial, sans-serif; margin-bottom:15px;'>📊TERADMAS📈</div><h2>TERCEIRO ADM ASSOCIADOS - BALANÇO DE CAIXA</h2><hr><br><p style='text-align:left;'><strong>Receita Operacional Bruta:</strong> " + formatarMoeda(receita) + "</p><p style='text-align:left;'><strong>Custo de Salários/Reflexos:</strong> " + formatarMoeda(totalBruto) + "</p><br><h3 style='text-align:left;'>Saldo Final de Caixa: " + formatarMoeda(receita - totalBruto) + "</h3></div>";
    }
    document.body.classList.add('imprimindo-balanco'); window.print();
    setTimeout(() => { document.body.classList.remove('imprimindo-balanco'); }, 1000);
}

function dispararRescisaoImediata(id, tipo) {
    const f = funcionarios.find(emp => emp.id === id);
    if (!f) return;
    const msg = tipo === 'demissao_sem_justa' ? 'Calcular DISPENSA SEM JUSTA CAUSA de ' : 'Calcular PEDIDO DE DEMISSÃO de ';
    if (confirm(msg + f.nome + "?")) { emitirRescisaoExecutiva(f, tipo); }
}

function abrirFerias(id) {
    const f = funcionarios.find(emp => emp.id === id);
    if (!f) return;
    const mediaHorasExtras = f.total_he_ganho || 0;
    const base = f.salario + (f.insalubridade || 0) + mediaHorasExtras;
    const terco = base / 3; const totalBruto = base + terco; const totalDescontos = totalBruto * 0.09;
    const janela = window.open('', '_blank', 'width=800,height=900'); if (!janela) return;
    
    let html = "<html><head><title>Recibo de Férias</title><style>" + obterEstiloHolerite() + "</style></head><body><div class='holerite-box'>";
    html += "<div class='header-holerite'><div style='padding: 0 10px; height: 45px; background: #1e3a8a; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.1rem;'>📊TERADMAS📈</div><div style='text-align: left;'><h2 style='margin: 0; font-size: 1.3rem; color: #1e3a8a;'>TERCEIRO ADM</h2><h3 style='margin: 2px 0 0 0; font-size: 0.9rem; color: #64748b;'>ASSOCIADOS</h3></div></div>";
    html += "<h2 style='text-align:center; font-size:1.2rem; margin: 15px 0 5px 0;'>RECIBO DE AVISO E GOZO DE FÉRIAS</h2><hr>";
    html += "<div class='info-colaborador'><p><strong>Colaborador:</strong> " + f.nome + " | <strong>Cargo:</strong> " + f.cargo + "</p></div>";
    html += "<h4 class='section-title proventos-title'>VERBAS REFEITAS (CRÉDITOS)</h4><table class='table-holerite'><tr><td>(+) Valor Base das Férias (Salário + Média H.E.)</td><td class='text-right'>" + formatarMoeda(base) + "</td></tr><tr><td>(+) Terço Constitucional de Férias (1/3)</td><td class='text-right'>" + formatarMoeda(terco) + "</td></tr><tr class='row-total'><td>TOTAL PROVENTOS:</td><td class='text-right'>" + formatarMoeda(totalBruto) + "</td></tr></table>";
    html += "<h4 class='section-title descontos-title'>DEDUÇÕES LEGAIS</h4><table class='table-holerite'><tr><td>(-) Retenções Previdenciárias/Fiscais</td><td class='text-right'>" + formatarMoeda(totalDescontos) + "</td></tr><tr class='row-total'><td>TOTAL DESCONTOS:</td><td class='text-right'>" + formatarMoeda(totalDescontos) + "</td></tr></table>";
    html += "<div class='liquido-box'><span class='liquido-label'>VALOR LÍQUIDO DAS FÉRIAS:</span><span class='liquido-value'>" + formatarMoeda(totalBruto - totalDescontos) + "</span></div>";
    html += "<div class='assinatura-container'><div class='linha-assinatura'></div><p>Assinatura do Colaborador</p></div></div></body></html>";
    janela.document.write(html); janela.document.close();
}
function calcularDecimoTerceiroIndividual(id) {
    fetch(`/api/decimo_individual/${id}`)
        .then(res => res.json())
        .then(dados => {
            if (dados.status === 'erro') { alert(dados.message); return; }
            const janela = window.open('', '_blank', 'width=800,height=900'); if (!janela) return;
            let html = "<html><head><title>13º Individual</title><style>" + obterEstiloHolerite() + "</style></head><body><div class='holerite-box'>";
            html += "<div class='header-holerite'><div style='padding: 0 10px; height: 45px; background: #1e3a8a; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.1rem;'>📊TERADMAS📈</div><div style='text-align: left;'><h2 style='margin: 0; font-size: 1.3rem; color: #1e3a8a;'>TERCEIRO ADM</h2><h3 style='margin: 2px 0 0 0; font-size: 0.9rem; color: #64748b;'>ASSOCIADOS</h3></div></div>";
            html += "<h2 style='text-align:center; font-size:1.2rem; margin: 15px 0 5px 0;'>DEMONSTRATIVO DE 13º SALÁRIO INDIVIDUAL</h2><hr>";
            html += "<div class='info-colaborador'><p><strong>Colaborador:</strong> " + dados.nome + " | <strong>Meses Proporcionais:</strong> " + dados.meses_proporcionais + "/12</p></div>";
            html += "<h4 class='section-title proventos-title'>CRÉDITOS</h4><table class='table-holerite'><tr><td>(+) Gratificação Natalina Bruta (Com Média H.E.)</td><td class='text-right'>" + formatarMoeda(dados.bruto) + "</td></tr><tr class='row-total'><td>TOTAL PROVENTOS:</td><td class='text-right'>" + formatarMoeda(dados.bruto) + "</td></tr></table>";
            html += "<h4 class='section-title descontos-title'>RETENÇÕES</h4><table class='table-holerite'><tr><td>(-) INSS sobre 13º</td><td class='text-right'>" + formatarMoeda(dados.inss) + "</td></tr><tr class='row-total'><td>TOTAL DESCONTOS:</td><td class='text-right'>" + formatarMoeda(dados.inss) + "</td></tr></table>";
            html += "<div class='liquido-box'><span>LÍQUIDO A RECEBER:</span><span class='liquido-value'>" + formatarMoeda(dados.liquido) + "</span></div></div></body></html>";
            janela.document.write(html); janela.document.close();
        }).catch(err => console.error(err));
}

async function emitirRescisaoExecutiva(f, tipo) {
    let liq = f.salario * 1.4; let proventos = f.salario * 1.5; let descontos = f.salario * 0.1;
    try {
        const resposta = await fetch('/api/rescisao', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ salario: f.salario, admissao: f.data_admissao, tipoRescisao: tipo }) });
        const r = await resposta.json(); liq = r.liquido; proventos = r.totalProventos; descontos = proventos - liq;
    } catch(e) {}
    const janela = window.open('', '_blank', 'width=800,height=900'); if (!janela) return;
    let htmlRescisao = "<html><head><title>Rescisão</title><style>" + obterEstiloHolerite() + "</style></head><body><div class='holerite-box'>";
    htmlRescisao += "<div class='header-holerite'><div style='padding: 0 10px; height: 45px; background: #1e3a8a; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.1rem;'>📊TERADMAS📈</div><div style='text-align: left;'><h2 style='margin: 0; font-size: 1.3rem; color: #1e3a8a;'>TERCEIRO ADM</h2><h3 style='margin: 2px 0 0 0; font-size: 0.9rem; color: #64748b;'>ASSOCIADOS</h3></div></div>";
    htmlRescisao += "<h2 style='text-align:center; font-size:1.2rem;'>TERMO DE QUITAÇÃO DE RESCISÃO CONTRATUAL</h2><hr>";
    htmlRescisao += "<div class='info-colaborador'><p><strong>Colaborador:</strong> " + f.nome + "</p><p><strong>Motivo:</strong> " + (tipo === 'pedido_demissao' ? 'Pedido de Demissão' : 'Dispensa sem Justa Causa') + "</p></div>";
    htmlRescisao += "<h4 class='section-title proventos-title'>CRÉDITOS RESCISÓRIOS</h4><table class='table-holerite'><tr><td>(+) Saldo Salarial, Férias e 13º Proporcionais</td><td class='text-right'>" + formatarMoeda(proventos) + "</td></tr><tr class='row-total'><td>TOTAL PROVENTOS:</td><td class='text-right'>" + formatarMoeda(proventos) + "</td></tr></table>";
    htmlRescisao += "<h4 class='section-title descontos-title'>DEDUÇÕES</h4><table class='table-holerite'><tr><td>(-) Deduções e Descontos Legais</td><td class='text-right'>" + formatarMoeda(descontos) + "</td></tr><tr class='row-total'><td>TOTAL DESCONTOS:</td><td class='text-right'>" + formatarMoeda(descontos) + "</td></tr></table>";
    htmlRescisao += "<div class='liquido-box'><span>VALOR LÍQUIDO DA QUITAÇÃO:</span><span class='liquido-value'>" + formatarMoeda(liq) + "</span></div></div></body></html>";
    janela.document.write(htmlRescisao); janela.document.close();
}

function abrirDecimoTerceiroGeral() {
    if (funcionarios.length === 0) { alert("Nenhum funcionário ativo."); return; }
    let totalProventos = 0; funcionarios.forEach(f => { totalProventos += f.salario + (f.total_he_ganho || 0); });
    let totalDescontos = totalProventos * 0.09;
    const janela = window.open('', '_blank', 'width=800,height=900'); if (!janela) return;
    let html13 = "<html><head><title>Folha de 13º</title><style>" + obterEstiloHolerite() + "</style></head><body><div class='holerite-box'>";
    html13 += "<div class='header-holerite'><div style='padding: 0 10px; height: 45px; background: #1e3a8a; border-radius: 6px; display: flex; align-items: center; justify-content: center; font-weight: bold; color: white; font-size: 1.1rem;'>📊TERADMAS📈</div><div style='text-align: left;'><h2 style='margin: 0; font-size: 1.3rem; color: #1e3a8a;'>TERCEIRO ADM</h2><h3 style='margin: 2px 0 0 0; font-size: 0.9rem; color: #64748b;'>ASSOCIADOS</h3></div></div>";
    html13 += "<h2 style='text-align:center; font-size:1.2rem;'>FOLHA DE DÉCIMO TERCEIRO INTEGRAL GERAL</h2><hr>";
    html13 += "<div class='liquido-box'><span>TOTAL LÍQUIDO A PAGAR GLOBAL:</span><span class='liquido-value'>" + formatarMoeda(totalProventos - totalDescontos) + "</span></div></div></body></html>";
    janela.document.write(html13); janela.document.close();
}
async function deletarFuncionario(id) {
    if (!confirm("Tem certeza que deseja remover este registro do sistema?")) return;
    try { await fetch(`/api/funcionarios/${id}`, { method: 'DELETE' }); } catch(e) {}
    await carregarDadosBanco();
}

function obterEstiloHolerite() {
    return `body { font-family: Arial, sans-serif; padding: 20px; background: #fff; color: #000; } .holerite-box { border: 2px solid #000; padding: 20px; max-width: 750px; margin: 0 auto; background: #fff; } .header-holerite { border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 15px; display: flex; align-items: center; justify-content: center; gap: 15px; } hr { border: 0; border-top: 1px solid #000; margin: 10px 0; } .info-colaborador p { margin: 5px 0; font-size: 0.9rem; } .section-title { font-size: 0.95rem; margin: 20px 0 5px 0; font-weight: bold; border-bottom: 1px solid #000; padding-bottom: 2px; } .proventos-title { color: #1e3a8a; } .descontos-title { color: #dc2626; } .table-holerite { width: 100%; border-collapse: collapse; font-size: 0.85rem; margin-bottom: 15px; } .table-holerite td { padding: 5px; border-bottom: 1px solid #eee; } .text-right { text-align: right; font-weight: bold; } .row-total td { font-weight: bold; border-top: 2px solid #000; padding-top: 8px; border-bottom: none; } .liquido-box { border: 2px solid #000; padding: 12px; display: flex; justify-content: space-between; align-items: center; background: #fafafa; margin-top: 20px; font-weight: bold; font-size: 1rem; } .liquido-value { font-size: 1.15rem; color: #16a34a; } .assinatura-container { margin-top: 40px; display: flex; justify-content: space-between; font-size: 0.85rem; } .linha-assinatura { width: 45%; border-top: 1px solid #000; text-align: center; padding-top: 5px; margin-top: 30px; }`;
}

let tamanhoFonteAtual = 16;
function mudarFonte(direcao) {
    tamanhoFonteAtual += direcao;
    if (tamanhoFonteAtual < 12) tamanhoFonteAtual = 12;
    if (tamanhoFonteAtual > 22) tamanhoFonteAtual = 22;
    document.documentElement.style.fontSize = tamanhoFonteAtual + "px";
}

function alternarAltoContraste() {
    document.body.classList.toggle('alto-contraste');
    if (document.body.classList.contains('alto-contraste')) document.body.classList.remove('dark-mode');
}

function alternarTema() {
    const body = document.body; body.classList.toggle('dark-mode');
    const botao = document.getElementById('btn_tema');
    if (body.classList.contains('dark-mode')) {
        if (botao) botao.innerHTML = '☀️ Modo Claro'; localStorage.setItem('tema', 'escuro');
    } else {
        if (botao) botao.innerHTML = '🌙 Modo Escuro'; localStorage.setItem('tema', 'claro');
    }
}
let leitorAtivo = false;
function alternarLeitorAudio() {
    leitorAtivo = !leitorAtivo; const btn = document.getElementById('btn-leitor-audio');
    if (leitorAtivo) {
        if (btn) btn.innerHTML = "🛑 Desativar Leitor"; alert("Leitor ativo. Passe o mouse sobre o texto."); window.speechSynthesis.cancel();
    } else {
        if (btn) btn.innerHTML = "🔊 Ativar Leitor"; window.speechSynthesis.cancel();
    }
}

document.addEventListener('mouseover', (evento) => {
    if (!leitorAtivo) return;
    const tagsParaLer = ['H1', 'H2', 'H3', 'H4', 'LABEL', 'TH', 'TD', 'P', 'SPAN', 'STRONG'];
    if (tagsParaLer.includes(evento.target.tagName) && evento.target.innerText.trim() !== '') {
        window.speechSynthesis.cancel(); 
        const fala = new SpeechSynthesisUtterance(evento.target.innerText);
        fala.lang = 'pt-BR'; fala.rate = 1.25; window.speechSynthesis.speak(fala);
    }
});

function gerarCalendarioPontoAutomatizado() {
    const campoMes = document.getElementById("ponto_mes_referencia");
    if (!campoMes || !campoMes.value) return;
    const [anoStr, mesStr] = campoMes.value.split("-");
    const ano = parseInt(anoStr, 10); const mes = parseInt(mesStr, 10);
    const totalDias = new Date(ano, mes, 0).getDate();
    const corpoTabela = document.getElementById("corpo_ponto_mensal");
    if (!corpoTabela) return; corpoTabela.innerHTML = "";
    const nomesDias = ["Domingo", "Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado"];
    for (let dia = 1; dia <= totalDias; dia++) {
        const dataItem = new Date(ano, mes - 1, dia); const indiceSemana = dataItem.getDay(); const nomeDiaSemana = nomesDias[indiceSemana];
        let horarioSaidaPadrao = "17:00"; let corFundoLinha = "#ffffff";
        if (indiceSemana === 0 || indiceSemana === 6) { corFundoLinha = "#f8fafc"; horarioSaidaPadrao = "08:00"; }
        const elementoTr = document.createElement("tr"); elementoTr.style.background = corFundoLinha; elementoTr.style.borderBottom = "1px solid #e2e8f0"; elementoTr.setAttribute("data-dia-semana-num", indiceSemana);
        elementoTr.innerHTML = `<td style="padding: 10px; font-weight: bold; color: #1e3a8a;">${dia.toString().padStart(2, '0')}</td><td style="padding: 10px; color: #334155;">${nomeDiaSemana}</td><td style="padding: 10px;"><input type="time" class="ponto-entrada-valor" value="08:00" style="padding: 4px; width: 100px; border: 1px solid #cbd5e1; border-radius: 4px;"></td><td style="padding: 10px;"><input type="time" class="ponto-saida-valor" value="${horarioSaidaPadrao}" style="padding: 4px; width: 100px; border: 1px solid #cbd5e1; border-radius: 4px;"></td>`;
        corpoTabela.appendChild(elementoTr);
    }
}

// CORREÇÃO: Nome alterado cirurgicamente de "ejecutar" para "executar" para alinhar com o HTML
function executarCalculoPontoMensal() {
    const linhasTabela = document.querySelectorAll("#corpo_ponto_mensal tr");
    if (linhasTabela.length === 0) { alert("Gere ou selecione um mês válido primeiro."); return; }
    let acumuladoExtras50 = 0; let acumuladoExtras100 = 0;
    linhasTabela.forEach(linha => {
        const diaSemanaNum = parseInt(linha.getAttribute("data-dia-semana-num"), 10);
        const stringEntrada = linha.querySelector(".ponto-entrada-valor").value; const stringSaida = linha.querySelector(".ponto-saida-valor").value;
        if (!stringEntrada || !stringSaida) return;
        const [horaEnt, minEnt] = stringEntrada.split(":").map(Number); const [horaSai, minSai] = stringSaida.split(":").map(Number);
        let minutosEntradaTotal = horaEnt * 60 + minEnt; let minutosSaidaTotal = horaSai * 60 + minSai;
        if (minutosSaidaTotal < minutosEntradaTotal) { minutosSaidaTotal += 24 * 60; }
        let minutesTrabalhadosNoDia = minutosSaidaTotal - minutosEntradaTotal;
        if (minutesTrabalhadosNoDia > 360) { minutesTrabalhadosNoDia -= 60; }
        const horasTrabalhadasNoDia = minutesTrabalhadosNoDia / 60; const limiteJornadaDiaria = 8;
        if (diaSemanaNum === 0 || diaSemanaNum === 6) { if (stringSaida !== "08:00") { acumuladoExtras100 += horasTrabalhadasNoDia; } } 
        else { if (horasTrabalhadasNoDia > limiteJornadaDiaria) { const saldoExtraDoDia = horasTrabalhadasNoDia - limiteJornadaDiaria; if (saldoExtraDoDia <= 2) { acumuladoExtras50 += saldoExtraDoDia; } else { acumuladoExtras50 += 2; acumuladoExtras100 += (saldoExtraDoDia - 2); } } }
    });
    const inputHeSabado = document.getElementById("he_sabado"); const inputHeDomingo = document.getElementById("he_domingo");
    if (inputHeSabado) inputHeSabado.value = acumuladoExtras50.toFixed(2); if (inputHeDomingo) inputHeDomingo.value = acumuladoExtras100.toFixed(2);
    if (typeof actualizarDashboard === "function") { actualizarDashboard(); }
    alert(`Ponto Computado com Sucesso!\n\nHoras Extras 50%: ${acumuladoExtras50.toFixed(2)}h\nHoras Extras 100%: ${acumuladoExtras100.toFixed(2)}h\n\nOs painéis gráficos e inputs foram atualizados.`);
}

function carregarHistoricoDoColaborador() {
    const idSelecionado = document.getElementById("ponto_selecao_funcionario")?.value;
    const blocoVazio = document.getElementById("ponto_historico_vazio");
    const blocoConteudo = document.getElementById("ponto_historico_conteudo");
    if (!idSelecionado) { if (blocoVazio) blocoVazio.style.display = "block"; if (blocoConteudo) blocoConteudo.style.display = "none"; return; }
    const f = funcionarios.find(emp => emp.id == idSelecionado);
    if (!f) return;
    if (blocoVazio) blocoVazio.style.display = "none";
    if (blocoConteudo) {
        blocoConteudo.style.display = "block";
        blocoConteudo.innerHTML = `
            <p style='margin: 4px 0;'><strong>Salário Contratual:</strong> ${formatarMoeda(f.salario)}</p>
            <p style='margin: 4px 0;'><strong>Departamento Fixo:</strong> ${f.departamento || 'Administrativo'}</p>
            <p style='margin: 4px 0;'><strong>Média Acumulada de H.E. (Estudos):</strong> ${formatarMoeda(f.total_he_ganho || 0)}</p>
            <p style='margin: 4px 0;'><strong>Insalubridade Vinculada:</strong> ${formatarMoeda(f.insalubridade || 0)}</p>
            <p style='margin: 4px 0;'><strong>Último Líquido Gerado:</strong> <span style='color:#16a34a; font-weight:bold;'>${formatarMoeda(f.liquido || 0)}</span></p>
            <hr style='border-top:1px solid #cbd5e1; margin:8px 0;'>
            <button type='button' class='btn-link' onclick='abrirContracheque(${f.id})' style='width:100%; text-align:center; display:block; margin-bottom:5px; background:#1e3a8a; color:white; border-radius:4px; padding:6px; cursor:pointer;'>📄 Reemitir Holerite Salvo</button>
            <button type='button' class='btn-link' onclick='abrirFerias(${f.id})' style='width:100%; text-align:center; display:block; background:#16a34a; color:white; border-radius:4px; padding:6px; cursor:pointer;'>🌴 Auditar Projeção de Férias</button>
        `;
    }
}

document.addEventListener("DOMContentLoaded", () => { gerarCalendarioPontoAutomatizado(); });
