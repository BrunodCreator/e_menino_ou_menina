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
import qrcode # Para gerar a imagem do QR Code
import base64
from io import BytesIO

from pixqrcodegen import Payload

from .models import Aposta 

User = get_user_model()

def validate_telefone_format(telefone, required_length=11):
    """
    Valida o formato do telefone brasileiro.
    Aceita 11 dígitos numéricos.
    """
    telefone_clean = re.sub(r'\D', '', telefone) # Remove caracteres não numéricos
    return len(telefone_clean) == required_length


def generate_pix_qrcode_base64(name ,pix_key ,value , city, txtID):
    """
    Gera o QR Code PIX (BR Code) em formato base64 usando a biblioteca pix-python.
    A chave PIX pode ser CPF, CNPJ, telefone, e-mail ou chave aleatória
    """
    value_str = f"{value:.2f}"
    payload = Payload(name, pix_key, value_str, city, txtID)
    brcode = payload.gerarPayload()

    qr_img = qrcode.make(brcode)

    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")

    img_b64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    return brcode, f"data:image/png;base64,{img_b64}"

@require_http_methods(["GET"])
def login_page(request):
    """
    Exibe a página HTML do formulário de login.
    Se o usuário já estiver autenticado, redireciona para a página de apostas.
    """
    if request.user.is_authenticated:
        return redirect('apostas_page')
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
            'redirect_url': '/apostas/' # Redireciona para a página de apostas
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
            user = User.objects.create_user(telefone=telefone, nome=nome, senha=senha, chave_pix=chave_pix)
            
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





# Se o usuário não estiver logado, ele será redirecionado para a LOGIN_URL definida em settings.py.
@login_required
@require_http_methods(["GET"])
def apostas_view(request):
    """
    Renderiza a página de apostas com os dados iniciais do usuário
    """
    # request.user é uma instância do seu modelo de usuário customizado (core.Usuario)
    # quando o usuário está logado.
    usuario_apostas = Aposta.objects.filter(usuario=request.user, status='valida')
    total_apostado = usuario_apostas.aggregate(total=Sum('valor_aposta'))['total'] or Decimal('0.00')
    quantidade_apostas = usuario_apostas.count()
    ultima_aposta = usuario_apostas.first()
    
    # Cria um dicionário 'context' para passar dados para o template HTML.
    context = {
        'usuario': request.user, # Acessa o nome do usuário logado
        'total_apostado': total_apostado, # Chama um método do seu modelo para formatar o telefone
        'quantidade_apostas': quantidade_apostas,
        'ultima_aposta': ultima_aposta,
    }
    # Renderiza o template 'apostas.html', passando o contexto com os dados do usuário.
    return render(request, 'apostas.html', context)



# View para obter os potes e odds (para o frontend buscar as informações)
@login_required
@require_http_methods(["GET"])
def get_dados_usuario_e_odds(request):
    try:
        odds_data = Aposta.objects.calcular_odds()
        total_masculino = Aposta.objects.get_total_pote_masculino()
        total_feminino = Aposta.objects.get_total_pote_feminino()

        usuario_apostas = Aposta.objects.filter(usuario=request.user, status='valida')
        total_apostado = usuario_apostas.aggregate(total=Sum('valor_aposta'))['total'] or Decimal('0.00')
        quantidade_apostas = usuario_apostas.count()
        ultima_aposta = usuario_apostas.order_by('-data_aposta').first()

        ultima_aposta_texto = "-"
        if ultima_aposta:
            sexo_display = "Menino" if ultima_aposta.sexo_escolha == 'M' else "Menina"
            ultima_aposta_texto = f"{sexo_display} - R$ {ultima_aposta.valor_aposta:.2f}".replace('.', ',')

        return JsonResponse({
            'success': True,
            'odd_menino': str(odds_data.get('M', Decimal('1.0'))),
            'odd_menina': str(odds_data.get('F', Decimal('1.0'))),
            'total_pote_masculino': str(total_masculino),
            'total_pote_feminino': str(total_feminino),
            'usuario': {
                'nome': request.user.nome,
                'total_apostado': f"R$ {total_apostado:.2f}".replace('.', ','),
                'quantidade_apostas': quantidade_apostas,
                'ultima_aposta': ultima_aposta_texto,
            }
        })
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro em get_dados_usuario_e_odds: {e}")
        return JsonResponse({'error': f'Erro ao buscar dados: {str(e)}'}, status=500)



@login_required
@require_http_methods(["POST"])
def iniciar_aposta_pix(request):
    """
    Recebe os dados iniciais da aposta, cria uma aposta com status 'pendente'
    e retorna os detalhes do PIX para o frontend.
    """
    try:
        data = json.loads(request.body)
        sexo_escolha = data.get('sexo_escolha')
        valor_aposta = Decimal(str(data.get('valor_aposta', '0.00')))
        
        if not sexo_escolha or sexo_escolha not in ['M', 'F']:
            return JsonResponse({'error': 'Escolha de sexo inválida. Deve ser "M" ou "F".'}, status=400)
        
        if not valor_aposta or valor_aposta < Decimal('0.01'):
            return JsonResponse({'error': 'Valor da aposta inválido. Mínimo de R$0.01.'}, status=400)
        
        txtID = '123'#str(uuid.uuid4()) #Cria um UUID único convertido para string
        
        aposta = Aposta.objects.create(
            usuario=request.user,
            sexo_escolha=sexo_escolha,
            valor_aposta=valor_aposta,
            status='pendente',
        )

        chave_pix_recebedor = "07533960173"
        nome_recebedor = "EMERSON BRUNO DE QUEIROZ"
        cidade_recebedor = "GOIANIA"

        pix_payload, qr_code_base64 = generate_pix_qrcode_base64(
            nome_recebedor, chave_pix_recebedor, valor_aposta, cidade_recebedor, txtID
        )

        return JsonResponse({
            'success': True,
            'message':'Aposta registrada para pagamento',
            'aposta_id': txtID,
            'valor_aposta': str(aposta.valor_aposta),
            'chave_pix': chave_pix_recebedor,
            'pix_payload': pix_payload,
            'qr_code_base64': qr_code_base64
        }, status=200)
    
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erro ao iniciar aposta Pix: {e}")
        return JsonResponse({'error': f'Erro ao iniciar aposta PIX: {str(e)}'}, status=500)


@login_required
@require_http_methods(["POST"])
def confirmar_pagamento_aposta(request):
    """
    Recebe o ID da aposta pendente (sem comprovante de arquivo),
    e atualiza o status da aposta para 'aguardando_validacao'.
    """
    try:
        data = json.loads(request.body) #Agora espera JSON, não FormData
        aposta_id = data.get('aposta_id')

        if not aposta_id:
            return JsonResponse({'error': 'ID da aposta ausente'}, status=400)
        
        aposta = get_object_or_404(Aposta, id=aposta_id, usuario=request.user, status='pendente')

        aposta.status = 'aguardando_validacao'
        aposta.save()

        # Recalcula e retorna os dados atualizados do usuário para o frontend
        # Filtra por apostas com status 'valida' para os cálculos do usuário

        usuario_apostas = Aposta.objects.filter(usuario=request.user, status='valida')
        total_apostado = usuario_apostas.aggregate(total=Sum('valor_aposta'))['total'] or Decimal('0.00')
        quantidade_apostas = usuario_apostas.count()
        ultima_aposta_obj = usuario_apostas.order_by('-data_aposta').first()

        ultima_aposta_texto = "-"
        if ultima_aposta_obj:
            sexo_display = "Menino" if ultima_aposta_obj.sexo_escolha == 'M' else "Menina"
            ultima_aposta_texto = f"{sexo_display} - R$ {ultima_aposta_obj.valor_aposta:.2f}".replace('.', ',')

        return JsonResponse({
            'success': True,
            'message': 'Aposta finalizada! Aguardando validação do pagamento.',
            'usuario_atualizado': {
                'total_apostado': f"R$ {total_apostado:.2f}".replace('.', ','),
                'quantidade_apostas': quantidade_apostas,
                'ultima_aposta': ultima_aposta_texto,
            }
        }, status=200)
    
    except Aposta.DoesNotExist:
        return JsonResponse({'error': 'Aposta pendente não encontrada ou não pertence ao usuário.'}, status=404)
    except Exception as e:
        print(f"Erro ao confirmar pagamento: {e}")
        return JsonResponse({'error': f'Erro ao confirmar pagamento: {str(e)}'}, status=500)

