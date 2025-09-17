from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required # Se os usuários forem autenticados
from django.db import IntegrityError
from django.db.models import Sum, F
import json
from decimal import Decimal
import re # Para validar o formato do telefone
import uuid # Para gerar um TxID único
from pixqrcodegen import Payload
from io import StringIO
import sys

from .models import Palpite 

User = get_user_model()

def validate_telefone_format(telefone, required_length=11):
    """
    Valida o formato do telefone brasileiro.
    Aceita 11 dígitos numéricos.
    """
    telefone_clean = re.sub(r'\D', '', telefone) # Remove caracteres não numéricos
    return len(telefone_clean) == required_length


def generate_pix_payload(name, pix_key, value, city, txtID):
    # Format the value
    value_str = f"{value:.2f}"
    payload = Payload(name, pix_key, value_str, city, txtID)

    # Capture the printed output
    old_stdout = sys.stdout
    buf     = StringIO()
    sys.stdout = buf
    try:
        payload.gerarPayload()      # this prints the BR-Code
    finally:
        sys.stdout = old_stdout     # restore

    # Grab and trim the string
    payload = buf.getvalue().strip()
    return payload

@require_http_methods(["GET"])
def login_page(request):
    """
    Exibe a página HTML do formulário de login.
    Se o usuário já estiver autenticado, redireciona para a página de palpites.
    """
    if request.user.is_authenticated:
        return redirect('palpite_page')
    return render(request, 'login.html')



@require_http_methods(["POST"])
def login_view(request):
    """
    Processa as credenciais de login (telefone e senha).
    Usa o sistema de autenticação do Django para verificar e logar o usuário.
    Espera dados JSON no corpo da requisição.
    """
    try:
        # request.body contém os dados brutos da requisição HTTP (em bytes)
        # json.loads() tenta converter essa string JSON em um dicionário Python
        data = json.loads(request.body)
    except json.JSONDecodeError:
        # Se o request.body não for um JSON válido, retorna um erro 400 (Bad Request)
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': 'Formato de dados inválido (JSON esperado).'}
        }, status=400)

    # Pega o valor associado à chave 'telefone' do dicionário data (que veio do JSON)
    # .get('telefone', '') é uma forma segura de acessar chaves de dicionário:
    # se 'telefone' não existir, ele retorna uma string vazia '' em vez de gerar um erro.
    telefone = data.get('telefone', '').strip()
    senha = data.get('senha', '')

    errors = {} # Dicionário para armazenar erros de validação

    # Validação dos campos obrigatórios
    if not telefone:
        errors['telefone'] = 'Telefone é obrigatório.'
    elif not validate_telefone_format(telefone): # Valida o formato usando a função auxiliar
        errors['telefone'] = 'Formato de telefone inválido. Use DDD+número (11 dígitos).'
    
    if not senha:
        errors['senha'] = 'Senha é obrigatória.'
    
    # Se existirem erros após as validações iniciais, retorna a resposta JSON de erro
    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # AUTENTICAÇÃO via Django:
    # authenticate() verifica as credenciais do usuário. Ele usa o AUTH_USER_MODEL (Usuario)
    # e o USERNAME_FIELD (telefone) para encontrar o usuário e comparar a senha.
    user = authenticate(request, telefone=telefone, password=senha)
    
    if user is not None: # Se as credenciais são válidas e o usuário foi encontrado
        if not user.is_active:
            # Se o usuário existe mas está desativado (is_active = False)
            return JsonResponse({
                'success': False,
                'errors': {'non_field_errors': 'Usuário desativado.'}
            }, status=400)

        # Faz login do usuário na sessão do Django.
        # Isso cria a sessão, marca o usuário como logado e atualiza o last_login.
        login(request, user)

        # Retorna uma resposta JSON de sucesso, com mensagem e URL de redirecionamento
        return JsonResponse({
            'success': True,
            'message': f'Bem-vindo(a), {user.nome}!',
            'redirect_url': '/palpite/' # Redireciona para a página de palpites
        })
    else:
        # Se authenticate() retornou None, significa que as credenciais são inválidas
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': 'Telefone ou senha incorretos.'}
        }, status=400) # Status 400 indica erro na requisição do cliente


@require_POST
def logout_view(request):
    logout(request)
    return redirect('login_page')


@require_http_methods(["GET", "POST"])
def cadastro_usuario(request):
    """
    Lida com o registro de novos usuários.
    - GET: Exibe o formulário de cadastro.
    - POST: Processa os dados do formulário, valida-os e cria o usuário.
    """
    if request.method == "GET":
        # Se a requisição for GET, simplesmente renderiza o template 'cadastro.html'
        # para que o usuário possa preencher o formulário.
        return render(request, 'cadastro.html')

    if request.method == "POST":
        # Pega os dados enviados pelo formulário (via request.POST para FormData)
        nome = request.POST.get('nome', '').strip()
        telefone = request.POST.get('telefone', '').strip()
        chave_pix = request.POST.get('chave_pix', '').strip()
        senha = request.POST.get('senha', '')
        confirma_senha = request.POST.get('confirma_senha', '')
        # Checkboxes enviam 'on' se marcados. Se não marcados, o .get() retornaria None.
        # Comparamos com 'on' para garantir que foi explicitamente marcado.
        termos_ok = request.POST.get('termos') == 'on' 

        errors = {} # Dicionário para armazenar as mensagens de erro

        # Bloco de Validações de Entrada (antes de interagir com o banco)
        if not nome:
            errors['nome'] = 'Nome completo é obrigatório.'
        
        if not telefone:
            errors['telefone'] = 'Telefone é obrigatório.'
        elif not validate_telefone_format(telefone): # Usa a função auxiliar para validar o formato
            errors['telefone'] = 'Formato de telefone inválido. Use DDD+número (11 dígitos).'
        
        if not chave_pix:
            errors['chave_pix'] = 'Chave PIX é obrigatória.'
        
        if not senha:
            errors['senha'] = 'Senha é obrigatória.'
        elif len(senha) < 6: # Adiciona uma validação de comprimento mínimo para a senha
            errors['senha'] = 'Senha deve ter pelo menos 6 caracteres.'
        elif senha != confirma_senha:
            errors['senha'] = 'As senhas não coincidem.'
            errors['confirma_senha'] = 'As senhas não coincidem.' # Feedback mais claro
        
        if not termos_ok:
            errors['termos'] = 'Você deve aceitar os termos de uso para se cadastrar.'

        # Se houver *qualquer* erro de validação até este ponto, retorna-os imediatamente.
        if errors:
            return JsonResponse({'success': False, 'errors': errors}, status=400) # Status 400 para erros de validação

        # Bloco de Criação do Usuário e Validações de Banco de Dados
        try:
            # Validação crucial: Verifica se o telefone já está cadastrado no banco de dados.
            # É feito aqui porque só precisamos do banco de dados para essa verificação.
            if User.objects.filter(telefone=telefone).exists():
                errors['telefone'] = 'Este telefone já está cadastrado.'
                # Se o telefone já existe, retorna o erro sem tentar criar o usuário.
                return JsonResponse({'success': False, 'errors': errors}, status=400)
            
            # Cria o usuário usando o gerenciador customizado (UsuarioManager).
            # O 'senha' aqui é o argumento que seu create_user no Manager espera,
            # e ele internamente chama set_password para hashear.
            user = User.objects.create_user(telefone=telefone, nome=nome, chave_pix=chave_pix, password=senha )
            
            # Se o usuário foi criado com sucesso, retorna uma resposta de sucesso.
            return JsonResponse({
                'success': True,
                'message': 'Cadastro realizado com sucesso! Faça login para continuar.',
                'redirect_url': '/' # Redireciona para a página inicial (que pode ser o login)
            })
        
        # Captura erros específicos que podem ocorrer na interação com o banco de dados.
        except IntegrityError as e:
            # IntegrityError ocorre se há uma violação de restrição do banco (ex: telefone duplicado,
            # embora já tenhamos uma validação antes, essa é uma camada de segurança).
            print(f"IntegrityError ao criar usuário: {str(e)}") # Log para debug no servidor
            return JsonResponse({
                'success': False,
                'errors': {'non_field_errors': 'Ocorreu um erro de dados. Possivelmente telefone já cadastrado.'}
            }, status=400) # Erro 400 porque o cliente enviou dados que violam as regras
        except Exception as e:
            # Captura qualquer outro erro inesperado durante a criação do usuário.
            print(f"Erro inesperado ao criar usuário: {str(e)}") # Log para debug no servidor
            return JsonResponse({
                'success': False,
                'errors': {'non_field_errors': 'Ocorreu um erro interno ao cadastrar. Tente novamente mais tarde.'}
            }, status=500) # Erro 500 para problemas internos do servidor




from decimal import Decimal, ROUND_HALF_UP
# Se o usuário não estiver logado, ele será redirecionado para a LOGIN_URL definida em settings.py.
@login_required
@require_http_methods(["GET"])
def palpites_view(request):
    usuario = request.user

    # Verifica se há palpites encerradas no sistema
    palpite_encerrada_global = Palpite.objects.filter(encerrado=True).last()

    # Verifica se o usuário atual tem algum palpite vencedor
    palpite_usuario = (
        Palpite.objects.filter(usuario=usuario, encerrado=True, status='valida')
    )

    if palpite_encerrada_global:
            
        if palpite_usuario:
            valores_recebidos = palpite_usuario.aggregate(total=Sum('valor_para_pagar'))['total'] or Decimal('0.00')
            valores_palpites = palpite_usuario.aggregate(total=Sum('valor_palpite'))['total'] or Decimal('0.00')
            #valor_enxoval = (valores_palpites * Decimal("0.25")).quantize(Decimal('0.01'))
            quantidade_palpites = palpite_usuario.count()
            odds_data = Palpite.objects.calcular_odds()

            palpite_ganhador = palpite_usuario.filter(valor_para_pagar__gt=0).first()

            percentual = Decimal("0.25")
            valor_enxoval = Decimal("0.00")
            palpites_processados = []

            for palpite in palpite_usuario:
                taxa = (palpite.valor_palpite * percentual).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                contribuicao = taxa  # valor padrão: só a taxa+

                # palpite vencedor
                if palpite.palpite_solidario:
                    contribuicao = taxa + palpite.valor_para_pagar.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    contribuicao = taxa

                valor_enxoval += contribuicao

            if palpite_ganhador:
                if palpite_ganhador.sexo_escolha == "F":
                    resultado_nascimento = "É UMA MENINA!"
                    resultado_odd = odds_data["F"]
                else:
                    resultado_nascimento = "É UM MENINO!"
                    resultado_odd = odds_data["M"]
            else:
                #Se não tem um palpite ganhador, o resultado será o oposto do que o usuário apostou
                primeiro_palpite = palpite_usuario.first()
                if primeiro_palpite:
                    if primeiro_palpite.sexo_escolha == "F":
                        resultado_nascimento = "É UM MENINO!"  # Oposto do que apostou
                        resultado_odd = odds_data["M"]
                        
                    else:
                        resultado_nascimento = "É UMA MENINA!"  # Oposto do que apostou
                        resultado_odd = odds_data["F"]
                else:
                    resultado_nascimento = "RESULTADO INDEFINIDO"
            
            context = {
                'usuario': usuario,
                'palpite_encerrada_global': palpite_encerrada_global,
                'odds_data': resultado_odd,
                'palpite_usuario': palpite_usuario,
                'resultado_nascimento': resultado_nascimento,
                'quantidade_palpites': quantidade_palpites,
                'valor_enxoval': valor_enxoval,
                'valores_palpites': valores_palpites,
                'valores_recebidos': valores_recebidos,
                 
            }
            return render(request, 'palpite.html', context)
        
        context = {
            'usuario': usuario,
            'palpite_encerrada_global': palpite_encerrada_global,
            'palpite_vencedora_usuario': palpite_usuario, 
            
        }
        return render(request, 'palpite.html', context)       

    # Caso contrário, tela normal de palpites
    usuario_palpites = Palpite.objects.filter(usuario=usuario, status='valida')
    total_palpitedo = usuario_palpites.aggregate(total=Sum('valor_palpite'))['total'] or Decimal('0.00')
    quantidade_palpites = usuario_palpites.count()
    ultima_palpite = usuario_palpites.first()


    context = {
        'usuario': usuario,
        'total_palpitedo': total_palpitedo,
        'usuario': usuario,
        'total_palpitedo': total_palpitedo,
        'quantidade_palpites': quantidade_palpites,
        'ultima_palpite': ultima_palpite,
    }
    return render(request, 'palpite.html', context)




# View para obter os potes e odds (para o frontend buscar as informações)
@login_required
@require_http_methods(["GET"])
def get_dados_usuario_e_odds(request):
    try:
        odds_data = Palpite.objects.calcular_odds()
        total_masculino = Palpite.objects.get_total_pote_masculino()
        total_feminino = Palpite.objects.get_total_pote_feminino()

        usuario_palpites = Palpite.objects.filter(usuario=request.user, status='valida')
        total_palpitedo = usuario_palpites.aggregate(total=Sum('valor_palpite'))['total'] or Decimal('0.00')
        quantidade_palpites = usuario_palpites.count()
        ultima_palpite = usuario_palpites.order_by('-data_palpite').first()

        ultima_palpite_texto = "-"
        if ultima_palpite:
            sexo_display = "Menino" if ultima_palpite.sexo_escolha == 'M' else "Menina"
            ultima_palpite_texto = f"{sexo_display} - R$ {ultima_palpite.valor_palpite:.2f}".replace('.', ',')

        return JsonResponse({
            'success': True,
            'odd_menino': str(odds_data.get('M', Decimal('1.0'))),
            'odd_menina': str(odds_data.get('F', Decimal('1.0'))),
            'total_pote_masculino': str(total_masculino),
            'total_pote_feminino': str(total_feminino),
            'usuario': {
                'nome': request.user.nome,
                'total_palpitedo': f"R$ {total_palpitedo:.2f}".replace('.', ','),
                'quantidade_palpites': quantidade_palpites,
                'ultima_palpite': ultima_palpite_texto,
            }
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro em get_dados_usuario_e_odds: {e}")
        return JsonResponse({'error': f'Erro ao buscar dados: {str(e)}'}, status=500)



@login_required
@require_http_methods(["POST"])
def iniciar_palpite_pix(request):
    """
    Recebe os dados iniciais da palpite, cria uma palpite com status 'pendente'
    e retorna os detalhes do PIX para o frontend.
    """
    try:
        data = json.loads(request.body)
        sexo_escolha = data.get('sexo_escolha')
        valor_palpite = Decimal(str(data.get('valor_palpite', '0.00')))
        palpite_solidario = data.get('palpite_solidario', True)
        
        if not sexo_escolha or sexo_escolha not in ['M', 'F']:
            return JsonResponse({'error': 'Escolha de sexo inválida. Deve ser "M" ou "F".'}, status=400)
        
        if not valor_palpite or valor_palpite < Decimal('0.01'):
            return JsonResponse({'error': 'Valor da palpite inválido. Mínimo de R$0.01.'}, status=400)
        
        
        
        palpite = Palpite.objects.create(
            usuario=request.user,
            palpite_solidario = palpite_solidario,
            sexo_escolha=sexo_escolha,
            valor_palpite=valor_palpite,
            status='pendente',
        )

        chave_pix_recebedor = "winchesterjheny@gmail.com"
        nome_recebedor = "HENYFFER LANNA PEREIRA BUENO"
        cidade_recebedor = "GOIANIA"
        

        
        pix_payload = generate_pix_payload(
            nome_recebedor, chave_pix_recebedor, valor_palpite, cidade_recebedor, str(palpite.id)
        )
        print(pix_payload)
        
        return JsonResponse({
            'success': True,
            'message':'palpite registrada para pagamento',
            'palpite_id': str(palpite.id),
            'valor_palpite': str(palpite.valor_palpite),
            'chave_pix': str(chave_pix_recebedor),
            'pix_payload': str(pix_payload)
        }, status=200)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao iniciar palpite Pix: {e}")
        return JsonResponse({'error': f'Erro ao iniciar palpite PIX: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def confirmar_pagamento_palpite(request):
    """
    Recebe o ID da palpite pendente (sem comprovante de arquivo),
    e atualiza o status da palpite para 'aguardando_validacao'.
    """
    try:
        data = json.loads(request.body) #Agora espera JSON, não FormData
        palpite_id = data.get('palpite_id')

        if not palpite_id:
            return JsonResponse({'error': 'ID da palpite ausente'}, status=400)
        palpite = get_object_or_404(Palpite, id=palpite_id, usuario=request.user, status='pendente')
        #print(palpite, palpite_id)#
        palpite.status = 'aguardando_validacao'
        palpite.save()

        # Recalcula e retorna os dados atualizados do usuário para o frontend
        # Filtra por palpites com status 'valida' para os cálculos do usuário

        usuario_palpites = Palpite.objects.filter(usuario=request.user, status='valida')
        total_palpitedo = usuario_palpites.aggregate(total=Sum('valor_palpite'))['total'] or Decimal('0.00')
        quantidade_palpites = usuario_palpites.count()
        ultima_palpite_obj = usuario_palpites.order_by('-data_palpite').first()

        ultima_palpite_texto = "-"
        if ultima_palpite_obj:
            sexo_display = "Menino" if ultima_palpite_obj.sexo_escolha == 'M' else "Menina"
            ultima_palpite_texto = f"{sexo_display} - R$ {ultima_palpite_obj.valor_palpite:.2f}".replace('.', ',')

        return JsonResponse({
            'success': True,
            'message': 'palpite finalizada! Aguardando validação do pagamento.',
            'usuario_atualizado': {
                'total_palpitedo': f"R$ {total_palpitedo:.2f}".replace('.', ','),
                'quantidade_palpites': quantidade_palpites,
                'ultima_palpite': ultima_palpite_texto,
            }
        }, status=200)
    
    except palpite.DoesNotExist:
        return JsonResponse({'error': 'palpite pendente não encontrada ou não pertence ao usuário.'}, status=404)
    except Exception as e:
        print(f"Erro ao confirmar pagamento: {e}")
        return JsonResponse({'error': f'Erro ao confirmar pagamento: {str(e)}'}, status=500)


import logging
from django.contrib import admin, messages
from django.shortcuts import render, redirect, get_list_or_404
from django import forms
from .models import Palpite

class EncerramentoForm(forms.Form):
    OPCOES = (
        ('M', 'Menino'),
        ('F', 'Menina'),
    )
    opcao_correta = forms.ChoiceField(choices=OPCOES, label='Qual foi a opção correta?')
    palpite_ids = forms.CharField(widget=forms.HiddenInput) #IDs das palpites selecionadas

# Configura logger
logger = logging.getLogger(__name__)

def encerrar_palpites_view(request):
    """
    View avançada para encerrar palpites no admin.
    Protegida via admin_site.admin_view.
    """
    try:
        # Recupera IDs via GET ou POST
        if request.method == 'POST':
            form = EncerramentoForm(request.POST)
            if form.is_valid():
                opcao_correta = form.cleaned_data['opcao_correta']
                palpite_ids = [id_ for id_ in form.cleaned_data['palpite_ids'].split(',') if id_.isdigit()]

                # Filtra apenas palpites válidas e ainda não encerradas
                palpites = Palpite.objects.filter(id__in=palpite_ids, status='valida', encerrado=False)
                
                if not palpites.exists():
                    messages.warning(request, "Nenhum palpite válido encontrada para encerrar.")
                    return redirect('admin:core_palpite_changelist')

                # Calcula odds, com fallback seguro
                try:
                    odds = Palpite.objects.calcular_odds()
                    odd_pagamento = odds.get(opcao_correta, Decimal('1.00'))
                except Exception as e:
                    logger.error(f"Erro ao calcular odds: {e}")
                    odds = {}
                    odd_pagamento = Decimal('1.00')

                total_encerradas = 0
                total_vencedoras = 0
                valor_total_pago = Decimal('0.00')

                for palpite in palpites:
                    try:
                        palpite.encerrado = True
                        valor_liquido = palpite.valor_para_pote or Decimal('0.00')

                        if palpite.sexo_escolha == opcao_correta:
                            palpite.valor_para_pagar = valor_liquido * Decimal(odd_pagamento)
                            valor_total_pago += palpite.valor_para_pagar
                            total_vencedoras += 1
                        else:
                            palpite.valor_para_pagar = Decimal('0.00')

                        palpite.save()
                        total_encerradas += 1
                    except Exception as e:
                        logger.error(f"Erro ao processar palpite {palpite.id}: {e}")

                resultado_nome = "👶 Menino" if opcao_correta == 'M' else "👧 Menina"
                msg = f"""
                    🎉 RESULTADO: {resultado_nome}
                    📊 ESTATÍSTICAS:
                    • Total processadas: {total_encerradas}
                    • palpites vencedoras: {total_vencedoras}
                    • palpites perdedoras: {total_encerradas - total_vencedoras}
                    • Valor total pago: R$ {valor_total_pago:.2f}
                    ✅ TODAS AS palpiteS FORAM ENCERRADAS!
                                    """.strip()
                messages.success(request, msg)
                return redirect('admin:core_palpite_changelist')

        else:
            # GET: mostra o formulário do admin
            palpite_ids = request.GET.get('ids', '')
            palpite_ids = [id_ for id_ in palpite_ids.split(',') if id_.isdigit()]
            palpites = Palpite.objects.filter(id__in=palpite_ids, encerrado=False)
            form = EncerramentoForm(initial={'palpite_ids': ','.join(palpite_ids)})

            if not palpites.exists():
                messages.warning(request, "Nenhuma palpite válida encontrada para encerrar.")
                return redirect('admin:core_palpite_changelist')

        context = {
            'form': form,
            'palpites': palpites,
            'total_palpites': palpites.count(),
            'palpites_menino': palpites.filter(sexo_escolha='M').count(),
            'palpites_menina': palpites.filter(sexo_escolha='F').count(),
        }
        return render(request, 'admin/encerrar_palpites.html', context)

    except Exception as e:
        logger.exception(f"Erro inesperado na view de encerramento de palpites: {e}")
        messages.error(request, "Ocorreu um erro inesperado. Veja os logs para mais detalhes.")
        return redirect('admin:core_palpite_changelist')
