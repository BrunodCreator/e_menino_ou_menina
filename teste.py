python [manage.py](http://manage.py) shell

*# ❌ NÃO funciona (modelo padrão)*

from django.contrib.auth.models import User

*# ✅ Use seu modelo customizado*

from core.models import Usuario

*# Ou use o get_user_model() (recomendado)*

from django.contrib.auth import get_user_model
User = get_user_model()

*# Opção 1: Importar diretamente*

from core.models import Usuario

*# Ver todos os usuários*

usuarios = Usuario.objects.all()
for user in usuarios:
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")

*# Opção 2: Usar get_user_model() (mais flexível)*

from django.contrib.auth import get_user_model
User = get_user_model()

usuarios = User.objects.all()
for user in usuarios:
    print(f"ID: {user.id}, Username: {user.username}, Email: {user.email}")

*# Ver superusuários*

superusers = User.objects.filter(is_superuser=True)
for su in superusers:
    print(f"Superuser: {su.username}")

*# Apagar um usuário específico*

user = User.objects.get(username='nome_do_usuario')
user.delete()

*# Apagar todos os usuários (CUIDADO!)*

User.objects.all().delete()