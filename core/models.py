# core/models.py

from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    """
    Manager customizado para criar usuários e superusuários.
    """

    def create_user(self, telefone, nome, senha=None, chave_pix=None, **extra_fields):
        """
        Cria e salva um usuário comum.
        - telefone e nome são obrigatórios.
        - senha (texto puro) será passada para set_password().
        - chave_pix é opcional.
        """
        if not telefone:
            raise ValueError("O campo 'telefone' deve ser preenchido.")
        if not nome:
            raise ValueError("O campo 'nome' deve ser preenchido.")

        # normaliza o telefone se necessário (remover espaços, traços, etc.)
        telefone = telefone.strip()

        user = self.model(telefone=telefone, nome=nome, chave_pix=chave_pix, **extra_fields)
        user.set_password(senha)
        user.save(using=self._db)
        return user

    def create_superuser(self, telefone, nome, senha=None, **extra_fields):
        """
        Cria e salva um superusuário com is_staff=True e is_superuser=True.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        # is_active já está True por padrão

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(telefone, nome, senha, **extra_fields)


class Usuario(AbstractBaseUser, PermissionsMixin):
    """
    Modelo de usuário que herda de AbstractBaseUser + PermissionsMixin.
    - Substituímos o campo 'senha' por 'password' herdado.
    - Adicionamos is_active, is_staff, is_superuser, last_login (herdados).
    """

    telefone_validator = RegexValidator(
        regex=r'^\d{9,11}',
        message="Telefone deve conter apenas números (9 ou 11 dígitos)"
    )

    telefone = models.CharField(
        verbose_name='Telefone',
        max_length=11,
        validators=[telefone_validator],
        unique=True,
        help_text="Digite apenas números, sem espaços ou símbolos (ex: 62999887766)"
    )

    nome = models.CharField(
        verbose_name='Nome Completo',
        max_length=100,
        help_text="Nome completo do participante"
    )

    # Removemos o campo 'senha = CharField(...)'
    # porque AbstractBaseUser já fornece:
    #     password = models.CharField(_('password'), max_length=128)
    # então não precisamos declará-lo novamente.
    #
    # Se quiséssemos renomear para 'senha', teríamos que
    # configurar explicitamente e redefinir toda a lógica.
    # É mais simples deixar o nome padrão 'password'.

    data_cadastro = models.DateTimeField(
        verbose_name='Data de Cadastro',
        auto_now_add=True,
        help_text="Data e hora em que o usuário se cadastrou"
    )

    ativo = models.BooleanField(
        verbose_name='Usuário Ativo',
        default=True,
        help_text="Determina se o usuário pode fazer apostas. Desmarque para desativar."
    )

    chave_pix = models.CharField(
        verbose_name='Chave PIX',
        max_length=128,
        blank=True,
        null=True,
        help_text='Chave PIX para o pagamento dos ganhadores'
    )

    # Campos obrigatórios para o Django Auth:
    is_staff = models.BooleanField(
        verbose_name='Staff Status',
        default=False,
        help_text="Define se o usuário tem acesso ao site do admin."
    )
    is_active = models.BooleanField(
        verbose_name='Active',
        default=True,
        help_text="Define se o usuário deve ser tratado como ativo. Desmarcar para desativá-lo."
    )
    # is_superuser é fornecido pelo PermissionsMixin

    # O campo last_login vem de AbstractBaseUser

    USERNAME_FIELD = 'telefone'
    REQUIRED_FIELDS = ['nome']  # além de telefone, deve informar nome

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['nome']
        db_table = 'core_usuario'

    def __str__(self):
        return f"{self.nome}"

    def get_telefone_formatado(self):
        if len(self.telefone) == 11:
            return f"({self.telefone[:2]}) {self.telefone[2:7]}-{self.telefone[7:]}"
        elif len(self.telefone) == 10:
            return f"({self.telefone[:2]}) {self.telefone[2:6]}-{self.telefone[6:]}"
        return self.telefone

    def pode_apostar(self):
        return self.ativo



from django.db import models
from django.conf import settings
from decimal import Decimal
from django.core.validators import MinValueValidator
from django.db.models import Sum, F

class ApostaManager(models.Manager):
    
    def get_total_pote_masculino(self):
        """Retorna o total do pote masculino (75% dos valores apostados)"""
        return self.filter(
            sexo_escolha='M',
            aposta_valida=True
        ).aggregate(
            total=models.Sum('valor_para_pote')
        )['total'] or Decimal('0.00')
    
    def get_total_pote_feminino(self):
        """Retorna o total do pote feminino (75% dos valores apostados)"""
        return self.filter(
            sexo_escolha='F',
            aposta_valida=True
        ).aggregate(
            total=models.Sum('valor_para_pote')
        )['total'] or Decimal('0.00')
    
    def get_total_pote(self):
        """Retorna o total geral disponível para pagamentos"""
        return self.get_total_pote_masculino() + self.get_total_pote_feminino()
    
    def get_total_arrecadado_bruto(self):
        """Retorna o total bruto arrecadado (100% dos valores apostados)"""
        return self.filter(
            aposta_valida=True
        ).aggregate(
            total=models.Sum('valor_aposta')
        )['total'] or Decimal('0.00')
    
    def get_total_para_pais(self):
        """Retorna o total destinado aos pais (25% do total arrecadado)"""
        return (self.get_total_arrecadado_bruto() * Decimal('0.25')).quantize(Decimal('0.01'))
    
    def calcular_odds(self):
        """
        Sua função original, agora integrada ao manager
        """
        total_masculino = self.get_total_pote_masculino()
        total_feminino = self.get_total_pote_feminino()
        total_geral = total_masculino + total_feminino
        
        if total_geral == Decimal('0.00'):
            return {'M': Decimal('1.00'), 'F': Decimal('1.00')}
        
        # Se algum pote estiver vazio, definir um valor mínimo simbólico
        min_value = Decimal('0.01')
        total_menino_calc = max(total_masculino, min_value)
        total_feminino_calc = max(total_feminino, min_value)
        
        odd_menino = (total_geral / total_menino_calc).quantize(Decimal('0.01'))
        odd_feminino = (total_geral / total_feminino_calc).quantize(Decimal('0.01'))
        
        return {'M': odd_menino, 'F': odd_feminino}
    
    def validar_balanco_financeiro(self):
        """
        MÉTODO CRÍTICO: Valida se você consegue pagar todos os ganhadores
        """
        odds = self.calcular_odds()
        total_pote = self.get_total_pote()
        
        # Simula pagamento para cada cenário
        cenarios = []
        
        for sexo_vencedor in ['M', 'F']:
            apostas_vencedoras = self.filter(
                sexo_escolha=sexo_vencedor,
                aposta_valida=True
            )
            
            total_a_pagar = Decimal('0.00')
            for aposta in apostas_vencedoras:
                pagamento = aposta.valor_aposta * odds[sexo_vencedor]
                total_a_pagar += pagamento
            
            cenarios.append({
                'sexo': sexo_vencedor,
                'total_a_pagar': total_a_pagar,
                'pote_disponivel': total_pote,
                'deficit': max(Decimal('0.00'), total_a_pagar - total_pote),
                'ok': total_a_pagar <= total_pote
            })
        
        return cenarios
    
    def get_relatorio_financeiro(self):
        """
        Relatório completo da situação financeira
        """
        return {
            'total_arrecadado_bruto': self.get_total_arrecadado_bruto(),
            'total_para_pais': self.get_total_para_pais(),
            'total_pote_disponivel': self.get_total_pote(),
            'pote_masculino': self.get_total_pote_masculino(),
            'pote_feminino': self.get_total_pote_feminino(),
            'odds_atuais': self.calcular_odds(),
            'balanco_cenarios': self.validar_balanco_financeiro(),
        }
            
class Aposta(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apostas'
    )

    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Feminino'),
    ]
    sexo_escolha = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        help_text="Seu palpite para o sexo do bebê: 'M' para Menino, 'F' para Feminino."
    )

    # Este é o valor BRUTO que o usuário contribuiu
    valor_aposta = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=False,
        null=False,
        default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Valor da sua contribuição (mínimo de R$0,01)."
    )

    # Valor efetivamente adicionado ao pote (75% do valor_aposta)
    valor_para_pote = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        blank=True,
        null=True,
        help_text="Valor líquido da contribuição após a dedução da taxa."
    )

    data_aposta = models.DateTimeField(auto_now_add=True)

    aposta_valida = models.BooleanField(
        default=False,
        help_text="Indica se a aposta foi validada pelo administrador."
    )

    comprovante_pagamento = models.FileField(
        upload_to='comprovantes/',
        null=True,
        blank=True,
        help_text="Anexe o comprovante de pagamento (imagem ou PDF)."
    )

    objects = ApostaManager()

    class Meta:
        verbose_name = "Aposta"
        verbose_name_plural = "Apostas"
        ordering = ['-data_aposta']

    def __str__(self):
        return f"Aposta de {self.usuario.nome} - Palpite: {self.get_sexo_escolha_display()} - Valor Bruto: R${self.valor_aposta} - No Pote: R${self.valor_para_pote}"

    def save(self, *args, **kwargs):
        # Calcula 75% do valor_aposta antes de salvar
        if self.valor_aposta is not None:
            self.valor_para_pote = (self.valor_aposta * Decimal('0.75')).quantize(Decimal('0.01'))
        else:
            self.valor_para_pote = Decimal('0.00')

        super().save(*args, **kwargs)

    @property
    def odd_da_aposta(self):
        # Assumindo que você tem um método calcular_odds no manager ou na classe
        # Você precisa implementar este método no ApostaManager
        try:
            odds_atuais = self.objects.calcular_odds()
            return odds_atuais.get(self.sexo_escolha, Decimal('1.00'))
        except:
            return Decimal('1.00')  # Fallback seguro

    @property
    def retorno_potencial(self):
        """
        IMPORTANTE: O retorno é baseado no valor_aposta (bruto) do usuário
        multiplicado pela odd calculada sobre o pote líquido.
        Isso pode gerar expectativas incorretas!
        """
        return (self.valor_aposta * self.odd_da_aposta).quantize(Decimal('0.01'))

    @property
    def retorno_real_possivel(self):
        """
        Este seria o retorno real baseado apenas no que está no pote.
        Use este para validar se você consegue pagar.
        """
        return (self.valor_para_pote * self.odd_da_aposta).quantize(Decimal('0.01'))

    def validar_pagamento_possivel(self):
        """
        Valida se o pagamento desta aposta é possível com o dinheiro disponível
        """
        total_pote = self.objects.get_total_pote()
        total_apostas_mesmo_sexo = self.objects.filter(
            sexo_escolha=self.sexo_escolha
        ).aggregate(
            total=models.Sum('valor_para_pote')
        )['total'] or Decimal('0.00')
        
        if total_apostas_mesmo_sexo > Decimal('0.00'):
            odd_real = total_pote / total_apostas_mesmo_sexo
            pagamento_necessario = self.valor_aposta * odd_real
            return pagamento_necessario <= total_pote
        
        return True



