from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UsuarioManager(BaseUserManager):
    """
    Manager customizado para criar usuários e superusuários.
    """

    def create_user(self, telefone, nome,  chave_pix, password=None, **extra_fields):
        """
        Cria e salva um usuário comum.
        - telefone e nome são obrigatórios.
        - senha (texto puro) será passada para set_password().
        - chave_pix é obrigatório.
        """
        if not telefone:
            raise ValueError("O campo 'telefone' deve ser preenchido.")
        if not nome:
            raise ValueError("O campo 'nome' deve ser preenchido.")
        if not chave_pix:
            raise ValueError("O campo chave-PIX deve ser preenchido")

        # normaliza o telefone se necessário (remover espaços, traços, etc.)
        telefone = telefone.strip()

        user = self.model(telefone=telefone, nome=nome, chave_pix=chave_pix, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, telefone, nome, chave_pix, password=None, **extra_fields):
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

        return self.create_user(telefone, nome, chave_pix, password, **extra_fields)


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

    # Removi o campo 'senha = CharField(...)'
    # porque AbstractBaseUser já fornece:
    #     password = models.CharField(_('password'), max_length=128)
    # então não precisamos declará-lo novamente.
    #
    # Para renomear para 'senha', tem que
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
        blank=False,
        null=False,
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
    REQUIRED_FIELDS = ['nome', 'chave_pix']  # além de telefone, deve informar nome

    objects = UsuarioManager()

    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'
        ordering = ['id']
        db_table = 'core_usuario'

    def __str__(self):
        return f"{self.nome}"

    def get_telefone_formatado(self):
        if len(self.telefone) == 11:
            return f"({self.telefone[:2]}) {self.telefone[2:7]}-{self.telefone[7:]}"
        elif len(self.telefone) == 10:
            return f"({self.telefone[:2]}) {self.telefone[2:6]}-{self.telefone[6:]}"
        return self.telefone

    #TODO depois olhar se quero escrever uma função para desabilitar o usuário
    def pode_apostar(self):
        return self.ativo


from django.db import models
from django.conf import settings
from decimal import Decimal, ROUND_HALF_UP, getcontext
from django.core.validators import MinValueValidator
from django.db.models import Sum

def money(x: Decimal) -> Decimal:
    return (x or Decimal('0')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


class ApostaManager(models.Manager):
    """
    Manager personalizado para a classe Aposta, contendo métodos
    para cálculos sobre valóres líquidos relacionados às apostas.
    """
    
    def get_total_pote_masculino(self):
        """
        Retorna o total do pote masculino (75% dos valores apostados validados).
        """
        return self.filter(
            sexo_escolha='M',
            status='valida' # Filtra por status 'valida'
        ).aggregate(
            total=Sum('valor_para_pote')
        )['total'] or Decimal('0.00')
    
    def get_total_pote_feminino(self):
        """
        Retorna o total do pote feminino (75% dos valores apostados validados).
        """
        return self.filter(
            sexo_escolha='F',
            status='valida'
        ).aggregate(
            total=Sum('valor_para_pote')
        )['total'] or Decimal('0.00')
    
    def get_total_pote(self):
        """
        Retorna o total geral disponível para pagar vencedores
        """
        return self.get_total_pote_masculino() + self.get_total_pote_feminino()
    
    def get_total_arrecadado_bruto(self):
        """
        Retorna o total bruto arrecadado (100% dos valores apostados validados).
        """
        return self.filter(
            status='valida'
        ).aggregate(
            total=Sum('valor_aposta')
        )['total'] or Decimal('0.00')
    
    def get_total_para_pais(self):
        """
        Retorna o total destinado aos pais (25% do total bruto arrecadado).
        """
        return money(self.get_total_arrecadado_bruto() * Decimal('0.25'))
    
    def calcular_odds(self):
        """
        Pari-mutuel: odd(sexo) = pote_total / pote_do_sexo.
        Calcula e retorna as odds atuais para cada sexo (Menino/Menina)
        com base nos valores presentes nos potes.
        """
        total_masculino = self.get_total_pote_masculino()
        total_feminino = self.get_total_pote_feminino()
        total_geral_pote = total_masculino + total_feminino
        
        # Se não há apostas válidas, as odds são 1.00 para ambos
        if total_geral_pote == Decimal('0.00'):
            return {'M': Decimal('1.00'), 'F': Decimal('1.00')}
        
        # Para evitar divisão por zero se um pote estiver vazio, usa um valor mínimo simbólico
        min_value_for_odds_calc = Decimal('0.01')
        total_menino_calc = max(total_masculino, min_value_for_odds_calc)
        total_feminino_calc = max(total_feminino, min_value_for_odds_calc)
        
        odd_menino = (total_geral_pote / total_menino_calc).quantize(Decimal('0.01'))
        odd_feminino = (total_geral_pote / total_feminino_calc).quantize(Decimal('0.01'))
        
        return {'M': odd_menino, 'F': odd_feminino}
    
    def validar_balanco_financeiro(self):
        """
        MÉTODO CRÍTICO: Verifica se o pote cobre Todos os pagamentos em cada cenário.
        Pagamento = valor_para_porte * odd(sexo_vencedor).
        """
        odds = self.calcular_odds()
        total_pote = self.get_total_pote()
        
        cenarios = []
        for sexo_vencedor in ['M', 'F']:
            apostas_vencedoras = self.filter(
                sexo_escolha=sexo_vencedor,
                status='valida'
            )
            
            total_a_pagar = Decimal('0.00')

            for aposta in apostas_vencedoras:
                total_a_pagar += aposta.valor_para_pote * odds[sexo_vencedor]    
            
            total_a_pagar = money(total_a_pagar)
            cenarios.append({
                'sexo': sexo_vencedor,
                'total_a_pagar': total_a_pagar,
                'pote_disponivel': money(total_pote),
                'deficit': money(max(Decimal('0.00'), total_a_pagar - total_pote)),
                'ok': total_a_pagar <= total_pote,
            })
        return cenarios
    
    def get_relatorio_financeiro(self):
        """ 
        Retorna um relatório completo da situação financeira das apostas.
        """
        return {
            'total_arrecadado_bruto': money(self.get_total_arrecadado_bruto()),
            'total_para_pais': money(self.get_total_para_pais()),

            'total_pote_disponivel': money(self.get_total_pote()),
            'pote_masculino': money(self.get_total_pote_masculino()),
            'pote_feminino': money(self.get_total_pote_feminino()),
            'odds_atuais': self.calcular_odds(),
            'balanco_cenarios': self.validar_balanco_financeiro(),
        }
            
class Aposta(models.Model):
    """
    Modelo para registrar as apostas dos usuários no palpite do sexo do bebê.
    """
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='apostas',
        verbose_name="Usuário"
    )

    SEXO_CHOICES = [
        ('M', 'Menino'),
        ('F', 'Menina'),
    ]
    sexo_escolha = models.CharField(
        max_length=1,
        choices=SEXO_CHOICES,
        help_text="Seu palpite para o sexo do bebê: 'M' para Menino, 'F' para Menina.",
        verbose_name="Palpite"
    )

    # Este é o valor BRUTO que o usuário contribuiu
    valor_aposta = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        blank=False,
        null=False,
        default=Decimal('0.01'),
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text="Valor da sua contribuição (mínimo de R$0,01).",
        verbose_name="Valor da Aposta"
    )

    # Valor efetivamente adicionado ao pote (75% do valor_aposta)
    valor_para_pote = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00'),
        blank=True,
        null=False,
        help_text="Valor líquido da contribuição após a dedução da taxa.",
        verbose_name="Valor para o Pote"
    )

    data_aposta = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Data da Aposta"
    )

    STATUS_PAYMENT = [
        ('pendente', 'Pendente de Pagamento'),
        ('aguardando_validacao', 'Aguardando Validação'),
        ('valida', 'Válida'),
        ('cancelada','Cancelada'),
        ('rejeitada', 'Rejeitada'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_PAYMENT,
        default='pendente',
        help_text="Status atual da aposta (ex: pendente, aguardando validação, válida).",
        verbose_name="Status da Aposta"
    )

    # Atribui o manager personalizado à classe Aposta
    objects = ApostaManager()

    class Meta:
        verbose_name = "Aposta"
        verbose_name_plural = "Apostas"
        ordering = ['-data_aposta'] # Ordena as apostas da mais recente para a mais antiga
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['sexo_escolha', 'status']),
            models.Index(fields=['-data_aposta']),
         ]

    def __str__(self):
        return f"Aposta de {self.usuario.nome} - {self.get_sexo_escolha_display()} - {self.get_status_display()}"
                
    

    def save(self, *args, **kwargs):
        """
        Sobrescreve o método save para calcular 'valor_para_pote' antes de salvar.
        """
        # Calcula 75% do valor_aposta antes de salvar
        if self.valor_aposta is not None:
            self.valor_para_pote = money(self.valor_aposta * Decimal('0.75'))
        else:
            self.valor_para_pote = Decimal('0.00')

        super().save(*args, **kwargs)

    @property
    def odd_da_aposta(self) -> Decimal:
        """
        Odd pari-mutuel atual do sexo escolhido
        """
        try:
            # Acessa o manager através da instância do modelo para obter as odds
            odds_atuais = Aposta.objects.calcular_odds()
            return odds_atuais.get(self.sexo_escolha, Decimal('1.00'))
        except Exception as e:
            # Idealmente, você pode logar este erro para depuração
            print(f"Erro ao calcular odd_da_aposta: {e}")
            return Decimal('1.00')  # Fallback seguro

    @property
    def retorno_potencial(self) -> Decimal:
        """
        Calcula o retorno potencial desta aposta com base no valor líquido
        apostado e nas odds atuais.
        """
        return money(self.valor_para_pote * self.odd_da_aposta)


    def validar_pagamento_possivel(self) -> bool:
        """
        Verifica se o sistema conseguiria pagar ESTA aposta
        com base no pote total e nas odds atuais (todos líquidos).
        """
        total_pote = Aposta.objects.get_total_pote()

        total_mesmo_sexo = (
            Aposta.objects.filter(sexo_escolha=self.sexo_escolha, status='valida')
            .aggregate(total=Sum('valor_para_pote'))['total']
            or Decimal('0.00')
        )

        if total_mesmo_sexo > Decimal('0.00'):
            odd_real = money(total_pote / total_mesmo_sexo)
            pagamento_necessario = money(self.valor_para_pote * odd_real)
            return pagamento_necessario <= total_pote

        # Sem outras apostas do mesmo sexo → nada a pagar além desta
        # (consideramos possível por padrão)
        return True