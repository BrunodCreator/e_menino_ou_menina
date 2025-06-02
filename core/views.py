# core/views.py

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout, get_user_model
import json
from .models import Usuario
from django.contrib.auth.decorators import login_required

@require_http_methods(["GET"])
def login_page(request):
    return render(request, 'login.html')

@require_http_methods(["POST"])
def login_view(request):
    """
    Agora usa o authenticate() do Django, que procura no AUTH_USER_MODEL (Usuario).
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': 'JSON inválido.'}
        }, status=400)

    telefone = data.get('telefone', '').strip()
    senha = data.get('senha', '')

    errors = {}
    if not telefone:
        errors['telefone'] = 'Telefone é obrigatório.'
    if not senha:
        errors['senha'] = 'Senha é obrigatória.'
    # (adicione validações extras de formato, se quiser)

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # AUTENTICAÇÃO via Django:
    user = authenticate(request, username=telefone, password=senha)
    if user is not None:
        if not user.is_active:
            return JsonResponse({
                'success': False,
                'errors': {'non_field_errors': 'Usuário desativado.'}
            }, status=400)

        # Faz login e grava last_login automaticamente:
        login(request, user)

        return JsonResponse({
            'success': True,
            'message': f'Bem‐vindo(a), {user.nome}!',
            'redirect_url': '/apostas/'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': 'Telefone ou senha incorretos.'}
        }, status=400)

@require_http_methods(["POST", "GET"])
def logout_view(request):
    """
    Faz logout do usuário logado e redireciona para a página de login.
    """
    logout(request)
    return JsonResponse({
        'success': True,
        'message': 'Deslogado com sucesso.',
        'redirect_url': '/'
    })

@login_required  # agora esse decorator funciona, pois Usuario é um usuário “oficial”.
def apostas_view(request):
    usuario_logado = request.user  # instância de core.Usuario
    context = {
        'nome_usuario': usuario_logado.nome,
        'telefone_usuario': usuario_logado.get_telefone_formatado(),
    }
    return render(request, 'apostas.html', context)


# Obtém o modelo de usuário configurado em settings.AUTH_USER_MODEL
User = get_user_model()

@require_http_methods(["GET", "POST"])
def cadastro_usuario(request):
    """
    Se GET: renderiza a página de formulário de cadastro.
    Se POST (JSON enviado pelo JavaScript): valida, cria o usuário e devolve JsonResponse.
    """
    if request.method == "GET":
        return render(request, 'cadastro.html')

    # Se chegou aqui, é POST → processa JSON
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': 'JSON inválido.'}
        }, status=400)

    nome          = data.get('nome', '').strip()
    telefone      = data.get('telefone', '').strip()
    chave_pix     = data.get('chave_pix', '').strip()
    senha         = data.get('senha', '')
    confirma_senha= data.get('confirma_senha', '')
    termos_ok     = data.get('termos', False)

    errors = {}

    # Validação de nome
    if not nome:
        errors['nome'] = 'Nome é obrigatório.'
    elif len(nome) < 3:
        errors['nome'] = 'Nome deve ter ao menos 3 caracteres.'

    # Validação de telefone
    if not telefone:
        errors['telefone'] = 'Telefone é obrigatório.'
    elif len(telefone) not in (10, 11) or not telefone.isdigit():
        errors['telefone'] = 'Telefone inválido (somente números, 10 ou 11 dígitos).'
    else:
        if User.objects.filter(telefone=telefone).exists():
            errors['telefone'] = 'Já existe usuário com este telefone.'

    # Validação de chave PIX
    if not chave_pix:
        errors['chave_pix'] = 'Chave PIX é obrigatória.'

    # Validação de senha
    if not senha:
        errors['senha'] = 'Senha é obrigatória.'
    elif len(senha) < 4:
        errors['senha'] = 'Senha deve ter pelo menos 4 caracteres.'

    # Validação de confirmação de senha
    if not confirma_senha:
        errors['confirma_senha'] = 'Confirme a senha.'
    elif senha and confirma_senha != senha:
        errors['confirma_senha'] = 'As senhas não coincidem.'

    # Validação de termos
    if not termos_ok:
        errors['termos'] = 'Você deve aceitar os termos de uso.'

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # Se chegou até aqui, dados válidos → cria o usuário
    try:
        # Usa o create_user do UserManager, que chama set_password()
        user = User.objects.create_user(
            telefone=telefone,
            nome=nome,
            senha=senha,       # o Manager irá chamar set_password(senha) 
            chave_pix=chave_pix
        )
        return JsonResponse({
            'success': True,
            'message': 'Cadastro realizado com sucesso!',
            'redirect_url': '/'  # redireciona para a página de login
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': f'Erro ao criar usuário: {str(e)}'}
        }, status=500)
