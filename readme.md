# 🎉 Sistema de Palpites - É Menino ou Menina?

Sistema web desenvolvido em Django para realizar palpites sobre o sexo do bebê com sistema de odds e premiação.

## 📋 Descrição

Este é um sistema de apostas/palpites para chá revelação onde os participantes podem:
- Fazer palpites se o bebê será menino ou menina
- Acompanhar odds dinâmicas baseadas nas apostas
- Realizar pagamentos via PIX
- Ganhar prêmios baseados em odds
- Contribuir solidariamente para o enxoval

## 🚀 Tecnologias Utilizadas

- **Backend**: Django 4.x / Python 3.x
- **Frontend**: HTML5, CSS3, JavaScript
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Autenticação**: Django Authentication System
- **Pagamentos**: Integração PIX

## 📦 Pré-requisitos

Antes de começar, você precisa ter instalado:

- Python 3.8 ou superior
- uv (gerenciador de pacotes Python ultra-rápido)
- Git

### Instalando o uv

**Windows (PowerShell):**
```powershell
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**Linux/Mac:**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Ou via pip:
```bash
pip install uv
```

## ⚙️ Instalação e Configuração

### 1. Clone o repositório

```bash
git clone https://github.com/seu-usuario/e_menino_ou_menina.git
cd e_menino_ou_menina
```

### 2. Crie e ative o ambiente virtual com uv

O uv criará automaticamente um ambiente virtual e gerenciará as dependências:

```bash
uv venv
```

**Ative o ambiente virtual:**

**Windows:**
```bash
.venv\Scripts\activate
```

**Linux/Mac:**
```bash
source .venv/bin/activate
```
3. Instale as dependências com uv
O projeto usa pyproject.toml e uv.lock para gerenciar dependências (forma moderna e recomendada):
bash# Sincroniza e instala todas as dependências do uv.lock
uv sync
Pronto! O uv irá:

✅ Ler o pyproject.toml
✅ Usar o uv.lock para garantir versões exatas
✅ Instalar tudo automaticamente
✅ Criar o ambiente virtual se necessário

Alternativas (caso não tenha uv.lock):
Se por algum motivo não houver uv.lock, você pode:
bash# Instalar baseado no pyproject.toml
uv pip install -e .

# Ou gerar o lock file
uv lock

💡 Dica: O uv.lock garante que todos instalem exatamente as mesmas versões das dependências, evitando o famoso "na minha máquina funciona"!
### 4. Configure as variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto:

```env
SECRET_KEY=sua-chave-secreta-aqui
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Configurações de Banco de Dados (opcional)
DATABASE_URL=sqlite:///db.sqlite3

# Configurações PIX (se aplicável)
PIX_KEY=sua-chave-pix
```

### 5. Execute as migrações do banco de dados

```bash
python manage.py makemigrations
python manage.py migrate
```

### 6. Crie um superusuário (admin)

```bash
python manage.py createsuperuser
```

Siga as instruções no terminal para criar o usuário administrador.

### 7. Colete os arquivos estáticos

```bash
python manage.py collectstatic
```

## 🎮 Como Executar

### Modo Desenvolvimento

```bash
python manage.py runserver
```

O sistema estará disponível em: `http://127.0.0.1:8000/`

### Acessar o painel administrativo

```
http://127.0.0.1:8000/admin/
```

Use as credenciais do superusuário criado anteriormente.

## 📱 Funcionalidades Principais

### Para Usuários:
- ✅ Registro e login de usuários
- ✅ Fazer palpites (Menino ou Menina)
- ✅ Visualizar odds em tempo real
- ✅ Realizar pagamento via PIX
- ✅ Opção de palpite solidário (contribuir para o enxoval)
- ✅ Visualizar histórico de palpites
- ✅ Ver resultado final e premiação

### Para Administradores:
- ✅ Gerenciar usuários
- ✅ Validar pagamentos
- ✅ Encerrar palpites
- ✅ Definir resultado final
- ✅ Visualizar relatórios financeiros
- ✅ Gerenciar odds do sistema

## 🗂️ Estrutura do Projeto

```
e_menino_ou_menina/
│
├── core/                      # App principal
│   ├── migrations/           # Migrações do banco de dados
│   ├── static/              # Arquivos estáticos (CSS, JS)
│   ├── templates/           # Templates HTML
│   ├── models.py            # Modelos do banco de dados
│   ├── views.py             # Lógica das views
│   └── urls.py              # Rotas do app
│
├── config/                   # Configurações do projeto
│   ├── settings.py          # Configurações gerais
│   ├── urls.py              # URLs principais
│   └── wsgi.py              # Configuração WSGI
│
├── static/                   # Arquivos estáticos globais
├── media/                    # Arquivos de mídia (uploads)
├── manage.py                # Script de gerenciamento Django
├── requirements.txt         # Dependências do projeto
└── README.md               # Este arquivo
```

## 🔐 Segurança

- Senhas são hash com bcrypt
- CSRF protection habilitado
- Autenticação obrigatória para palpites
- Validação de dados no backend

## 📊 Modelo de Dados

### Principais Models:

**Palpite**
- Usuario (FK)
- Sexo escolhido (M/F)
- Valor da aposta
- Status (pendente/válida/cancelada)
- Palpite solidário (boolean)
- Valor a receber
- Data da aposta

**Usuario**
- Informações básicas (nome, email)
- Autenticação Django

## 🧪 Testes

Para executar os testes:

```bash
python manage.py test
```

## 🚀 Deploy (Produção)

### Preparação:

1. Configure `DEBUG=False` no `.env`
2. Configure `ALLOWED_HOSTS` adequadamente
3. Use um banco de dados robusto (PostgreSQL recomendado)
4. Configure servidor web (Nginx/Apache)
5. Use Gunicorn como servidor WSGI

```bash
uv pip install gunicorn
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## 💡 Comandos Úteis com uv

```bash
# Instalar uma nova dependência
uv pip install nome-do-pacote

# Atualizar requirements.txt
uv pip freeze > requirements.txt

# Sincronizar dependências (se usar pyproject.toml)
uv pip sync

# Ver pacotes instalados
uv pip list
```

**Desenvolvido com ❤️ para celebrar a chegada do bebê!** 🍼