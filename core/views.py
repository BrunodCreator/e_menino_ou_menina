from django.shortcuts import render
import json
import re # Certifique-se de que re está importado
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout # Importe login e logout
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth.decorators import login_required # Para proteger views
from .models import Usuario

# --- Funções Auxiliares ---

def validate_telefone(telefone):
    """
    Valida formato do telefone brasileiro.
    Aceita 10 ou 11 dígitos.
    """
    # Remove caracteres não numéricos
    telefone_clean = re.sub(r'\D', '', telefone)
    # Verifica se tem 10 ou 11 dígitos
    return len(telefone_clean) in [10, 11]

def authenticate_by_phone(request, telefone, senha):
    """
    Autentica usuário usando o modelo Usuario customizado.
    """
    try:
        # Importe Usuario aqui para evitar circular import se models.py importar views
        from .models import Usuario

        # Buscar usuário pelo telefone
        try:
            usuario = Usuario.objects.get(telefone=telefone)
            print(f"Usuário encontrado: {usuario.nome}") # Debug

            # Verificar se está ativo
            if not usuario.ativo:
                print(f'Usuário inativo: {telefone}')
                return None

            # Verificar a senha usando o método do modelo (check_senha)
            if usuario.check_senha(senha):
                print(f'Senha correta para: {usuario.nome}')
                return usuario
            else:
                print(f'Senha incorreta para: {telefone}')
                return None
        except Usuario.DoesNotExist:
            print(f'Usuário não encontrado com o telefone: {telefone}')
            return None
    except Exception as e:
        print(f'Erro na autenticação (authenticate_by_phone): {str(e)}')
        return None

# --- Views da Aplicação ---

@ensure_csrf_cookie # Garante que o cookie CSRF seja definido para o JS poder acessá-lo
def login_page(request):
    """
    View para renderizar a página de login.
    """
    return render(request, 'login.html')

@require_http_methods(["POST"])
def login_view(request):
    """
    View para processar login via AJAX.
    """
    try:
        data = json.loads(request.body)
        telefone = data.get('telefone', '').strip()
        senha = data.get('senha', '')

        print(f'Tentativa de login - Telefone: {telefone}') # Debug

        errors = {}

        # Validações dos campos
        if not telefone:
            errors['telefone'] = 'Telefone é obrigatório.'
        elif not validate_telefone(telefone):
            errors['telefone'] = 'Formato de telefone inválido. Use DDD+9 (ex: 629xxxxxxxxxx).'

        if not senha:
            errors['senha'] = 'Senha é obrigatória.'
        elif len(senha) < 4:
            errors['senha'] = 'Senha deve ter pelo menos 4 caracteres.'

        if errors:
            return JsonResponse({
                'success': False,
                'errors': errors
            }, status=400)

        # Autenticar o usuário usando a função customizada
        authenticated_user = authenticate_by_phone(request, telefone, senha)

        if authenticated_user is not None:
            # **RECOMENDADO:** Use o sistema de autenticação do Django
            # Isso configura a sessão de forma padrão e permite usar request.user
            login(request, authenticated_user)

            print(f'Login bem-sucedido para: {authenticated_user.nome}') # Debug

            return JsonResponse({
                'success': True,
                'message': f'Bem-vindo(a), {authenticated_user.nome}!',
                'redirect_url': '/apostas/',
                'user': {
                    'id': authenticated_user.id,
                    'nome': authenticated_user.nome,
                    'telefone': authenticated_user.get_telefone_formatado()
                }
            })
        else:
            print(f"Falha na autenticação para telefone: {telefone}") # Debug
            return JsonResponse({
                'success': False,
                'errors': {
                    'non_field_errors': 'Telefone ou senha incorretos.'
                }
            }, status=400)
    except json.JSONDecodeError: # Exceção correta para JSON inválido
        return JsonResponse({
            'success': False,
            'errors': {
                'non_field_errors': 'Dados inválidos enviados. O corpo da requisição não é um JSON válido.'
            }
        }, status=400)
    except Exception as e:
        # Log do erro para debugging
        print(f"Erro inesperado no login_view: {str(e)}")
        return JsonResponse({
            'success': False,
            'errors': {
                'non_field_errors': 'Erro interno do servidor. Tente novamente.'
            }
        }, status=500)

@login_required # Protege esta view, requer login
def apostas_view(request):
    """
    View para renderizar a página de apostas (após o login).
    """
    # Se o usuário estiver logado (devido ao @login_required),
    # request.user estará disponível e será uma instância do seu modelo Usuario
    usuario_logado = request.user
    context = {
        'nome_usuario': usuario_logado.nome,
        'telefone_usuario': usuario_logado.get_telefone_formatado() # Exemplo
    }
    # Renderiza o template 'apostas.html'
    return render(request, 'apostas.html', context)

# --- View de Logout (Opcional, mas altamente recomendado) ---
def logout_view(request):
    """
    View para deslogar o usuário.
    """
    logout(request) # Função do Django que limpa a sessão de autenticação
    return JsonResponse({'success': True, 'message': 'Deslogado com sucesso.', 'redirect_url': '/'})
    # Ou redirecione para a página de login:
    # from django.shortcuts import redirect
    # return redirect('login_page')
    
    
@require_http_methods(["GET", "POST"])
def cadastro_usuario(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')

    # ---- se for POST ----
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': 'JSON inválido.'}
        }, status=400)

    nome = data.get('nome', '').strip()
    telefone = data.get('telefone', '').strip()
    chave_pix = data.get('chave_pix', '').strip()
    senha = data.get('senha', '')
    confirma_senha = data.get('confirma_senha', '')
    termos_ok = data.get('termos', False)

    errors = {}

    # 1. Nome
    if not nome:
        errors['nome'] = 'Nome é obrigatório.'
    elif len(nome) < 3:
        errors['nome'] = 'Nome deve ter ao menos 3 caracteres.'

    # 2. Telefone
    if not telefone:
        errors['telefone'] = 'Telefone é obrigatório.'
    elif len(telefone) not in (10, 11) or not telefone.isdigit():
        errors['telefone'] = 'Telefone inválido (somente números, 10 ou 11 dígitos).'
    else:
        if Usuario.objects.filter(telefone=telefone).exists():
            errors['telefone'] = 'Já existe usuário com este telefone.'

    # 3. Chave PIX
    if not chave_pix:
        errors['chave_pix'] = 'Chave PIX é obrigatória.'

    # 4. Senha e confirmação
    if not senha:
        errors['senha'] = 'Senha é obrigatória.'
    elif len(senha) < 4:
        errors['senha'] = 'Senha deve ter pelo menos 4 caracteres.'

    if not confirma_senha:
        errors['confirma_senha'] = 'Confirme a senha.'
    elif senha and confirma_senha != senha:
        errors['confirma_senha'] = 'As senhas não coincidem.'

    # 5. Termos
    if not termos_ok:
        errors['termos'] = 'Você deve aceitar os termos de uso.'

    if errors:
        return JsonResponse({'success': False, 'errors': errors}, status=400)

    # Se chegou aqui, dados válidos → cria o usuário
    try:
        novo = Usuario(telefone=telefone, nome=nome, chave_pix=chave_pix)
        # NÃO faça novo.senha = senha_texto puro → use set_senha
        novo.set_senha(senha)
        novo.save()
        return JsonResponse({
            'success': True,
            'message': 'Cadastro realizado com sucesso!',
            'redirect_url': '/'  # redireciona para login, por exemplo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'errors': {'non_field_errors': f'Erro ao criar usuário: {str(e)}'}
        }, status=500)