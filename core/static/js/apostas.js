// Seletores de elementos DOM
const blocks = document.querySelectorAll('.option-block');
const confirmButton = document.getElementById('confirmButton');
const modalOverlay = document.getElementById('modalOverlay');
const selectedOptionDisplay = document.getElementById('selectedOptionDisplay');
const betAmountInput = document.getElementById('betAmount');
const expectedReturnElement = document.getElementById('expectedReturn');
const placeBetButton = document.getElementById('placeBet');
const cancelBetButton = document.getElementById('cancelBet');
const logoutButton = document.getElementById('logoutButton');
const totalBetElement = document.getElementById('totalBet');
const betCountElement = document.getElementById('betCount');
const lastBetElement = document.getElementById('lastBet');
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');
const userNameElement = document.getElementById('userName'); 
const oddMeninoElement = document.getElementById('oddMenino');
const oddMeninaElement = document.getElementById('oddMenina');

// Seletores para o novo modal de mensagem
const messageModalOverlay = document.getElementById('messageModalOverlay');
const messageModalContent = document.getElementById('messageModalContent');
const messageModalText = document.getElementById('messageModalText');
const messageModalConfirmButton = document.getElementById('messageModalConfirmButton');
const messageModalCancelButton = document.getElementById('messageModalCancelButton');

// Variáveis de estado
let currentSelection = null;
let currentOdds = 0;
let sidebarOpen = false;
let resolveMessagePromise = null; 

/**
 * Exibe um modal de mensagem personalizado.
 * @param {string} message - A mensagem a ser exibida.
 * @param {boolean} [isConfirm=false] - Se true, exibe botões de confirmação/cancelamento.
 * @returns {Promise<boolean>} Retorna uma Promise que resolve para true se confirmado, false se cancelado (apenas para isConfirm=true).
 */
function showMessageModal(message, isConfirm = false) {
    messageModalText.textContent = message;
    messageModalConfirmButton.style.display = isConfirm ? 'block' : 'none';
    messageModalCancelButton.style.display = isConfirm ? 'block' : 'none';
    messageModalOverlay.classList.add('show');

    if (isConfirm) {
        return new Promise(resolve => {
            resolveMessagePromise = resolve;
        });
    } else {
        const closeHandler = () => {
            messageModalOverlay.classList.remove('show');
            messageModalConfirmButton.removeEventListener('click', closeHandler);
        };
        messageModalConfirmButton.addEventListener('click', closeHandler);
        messageModalOverlay.addEventListener('click', function(e) {
            if (e.target === messageModalOverlay && !isConfirm) {
                closeHandler();
            }
        });
        return Promise.resolve(true); 
        
    }
}

// Event listeners para os botões do modal de mensagem
if (messageModalConfirmButton) {
    messageModalConfirmButton.addEventListener('click', () => {
        if (resolveMessagePromise) {
            resolveMessagePromise(true);
            resolveMessagePromise = null;
        }
        messageModalOverlay.classList.remove('show');
    });
}

if (messageModalCancelButton) {
    messageModalCancelButton.addEventListener('click', () => {
        if (resolveMessagePromise) {
            resolveMessagePromise(false);
            resolveMessagePromise = null;
        }
        messageModalOverlay.classList.remove('show');
    });
}

if (messageModalOverlay) {
    messageModalOverlay.addEventListener('click', function(e) {
        if (e.target === messageModalOverlay && !messageModalCancelButton.style.display === 'block') { 
            messageModalOverlay.classList.remove('show');
        }
    });
}


/**
 * Carrega os dados do usuário, odds e informações de apostas do backend.
 */
async function carregarDados() {
    console.log('carregarDados: Iniciando carregamento de dados...');
    try {
        const response = await fetch('/dados/', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            }
        });

        if (response.ok) {
            const data = await response.json();
            console.log('carregarDados: Dados recebidos e analisados (JSON):', data);

            // Adicionado log para verificar os elementos antes de usá-los
            console.log('carregarDados: Elementos DOM verificados:');
            console.log('  userNameElement:', userNameElement);
            console.log('  oddMeninoElement:', oddMeninoElement);
            console.log('  oddMeninaElement:', oddMeninaElement);
            console.log('  totalBetElement:', totalBetElement);
            console.log('  betCountElement:', betCountElement);
            console.log('  lastBetElement:', lastBetElement);
            console.log('  blocks[0]:', blocks[0]);
            console.log('  blocks[1]:', blocks[1]);


            // Atualizar nome do usuário
            if (userNameElement && data.usuario && data.usuario.nome) {
                userNameElement.textContent = data.usuario.nome;
            } else {
                console.warn('carregarDados: Não foi possível atualizar o nome do usuário. Elemento ou dados ausentes.');
            }

            // Atualizar odds na interface
            const oddMenino = parseFloat(data.odd_menino);
            const oddMenina = parseFloat(data.odd_menina);

            if (oddMeninoElement) {
                oddMeninoElement.textContent = `odd: ${oddMenino.toFixed(1)}x`;
            } else {
                console.warn('carregarDados: Elemento oddMeninoElement não encontrado.');
            }
            if (oddMeninaElement) {
                oddMeninaElement.textContent = `odd: ${oddMenina.toFixed(1)}x`;
            } else {
                console.warn('carregarDados: Elemento oddMeninaElement não encontrado.');
            }

            // Atualizar data-odds nos blocos
            if (blocks[0]) blocks[0].setAttribute('data-odds', oddMenino);
            if (blocks[1]) blocks[1].setAttribute('data-odds', oddMenina);

            // Atualizar dados do usuário
            if (totalBetElement && data.usuario) {
                totalBetElement.textContent = data.usuario.total_apostado;
            } else {
                console.warn('carregarDados: Elemento totalBetElement ou dados do usuário ausentes.');
            }
            if (betCountElement && data.usuario) {
                betCountElement.textContent = data.usuario.quantidade_apostas;
            } else {
                console.warn('carregarDados: Elemento betCountElement ou dados do usuário ausentes.');
            }
            if (lastBetElement && data.usuario) {
                lastBetElement.textContent = data.usuario.ultima_aposta;
            } else {
                console.warn('carregarDados: Elemento lastBetElement ou dados do usuário ausentes.');
            }
            
            console.log('carregarDados: Dados atualizados com sucesso!');

        } else {
            const errorText = await response.text();
            console.error('carregarDados: Erro ao carregar dados (resposta não OK):', response.status, errorText);
            showMessageModal('Erro ao carregar dados iniciais. Por favor, tente novamente. Detalhes: ' + response.status);
        }
    } catch (error) {
        console.error('carregarDados: Erro catastrófico na requisição de carregamento de dados:', error); 
        showMessageModal('Erro de conexão ao carregar dados. Verifique sua internet ou tente novamente.');
    }
}

// CORRIGIDO: Erro de digitação `carrergarDados` para `carregarDados`
document.addEventListener('DOMContentLoaded', carregarDados);

// Toggle do menu lateral
if (menuToggle && sidebar && mainContent) {
    menuToggle.addEventListener('click', function() {
        sidebarOpen = !sidebarOpen;

        if (sidebarOpen) {
            sidebar.classList.add('open');
            menuToggle.classList.add('open');
            mainContent.classList.add('shifted');
        } else {
            sidebar.classList.remove('open');
            menuToggle.classList.remove('open');
            mainContent.classList.remove('shifted');
        }
    });
}


// Seleção das opções
if (blocks && confirmButton) { // Adicionado confirmButton para garantir que ele exista
    blocks.forEach(block => {
        block.addEventListener('click', function() {
            blocks.forEach(b => b.classList.remove('selected'));
            
            this.classList.add('selected');
            
            currentSelection = this.dataset.option;
            currentOdds = parseFloat(this.dataset.odds);

            confirmButton.classList.remove('menino', 'menina');
            if (currentSelection === 'menino') { 
                confirmButton.classList.add('menino');
            } else {
                confirmButton.classList.add('menina');
            }

            confirmButton.classList.add('show');
        });
    });
}


// Confirmar seleção - abre modal
if (confirmButton && selectedOptionDisplay && modalOverlay && betAmountInput && expectedReturnElement) { // Adicionado expectedReturnElement
    confirmButton.addEventListener('click', function() {
        if (currentSelection) {
            const displayText = currentSelection === 'menino' ? 'MENINO' : 'MENINA';
            selectedOptionDisplay.textContent = displayText;
            modalOverlay.classList.add('show');
            betAmountInput.value = '';
            expectedReturnElement.textContent = 'R$ 0,00';
            betAmountInput.focus();
        }
    });
}


// Calcular retorno esperado
if (betAmountInput && expectedReturnElement) {
    betAmountInput.addEventListener('input', function() {
        const betAmount = parseFloat(this.value) || 0;
        const expectedReturn = betAmount * currentOdds;
        expectedReturnElement.textContent = `R$ ${expectedReturn.toFixed(2).replace('.', ',')}`;
    });
}


// Fazer aposta
if (placeBetButton && betAmountInput && totalBetElement && betCountElement && lastBetElement) {
    placeBetButton.addEventListener('click', async function() {
        const betAmount = parseFloat(betAmountInput.value);

        if (!betAmount || betAmount < 0.01) {
            showMessageModal('Por favor, insira um valor válido para a aposta (mínimo R$ 0,01).');
            return;
        }

        try {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                document.querySelector('meta[name=csrf-token]')?.getAttribute('content');

            if (!csrfToken) {
                showMessageModal('Erro: Token CSRF não encontrado. Recarregue a página.');
                return;
            }

            placeBetButton.disabled = true;
            placeBetButton.textContent = 'Processando...';

            const response = await fetch('/registrar/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: JSON.stringify({
                    sexo_escolha: currentSelection === 'menino' ? 'M' : 'F',
                    valor_aposta: betAmount
                })
            });

            const data = await response.json();
            console.log('Response from /registrar/:', data);

            placeBetButton.disabled = false;
            placeBetButton.textContent = 'Fazer Aposta';

            if (response.ok && data.success) {
                // Store aposta_id for confirmation
                window.currentApostaId = data.aposta_id;

                // Show PIX modal
                document.getElementById('pixQrCode').src = data.qr_code_base64;
                document.getElementById('pixPayload').textContent = data.pix_payload;
                document.getElementById('pixKey').textContent = data.chave_pix;
                document.getElementById('pixValue').textContent = `R$ ${data.valor_aposta}`;
                document.getElementById('pixModalOverlay').classList.add('show');

                // Close bet modal and reset UI
                modalOverlay.classList.remove('show');
                blocks.forEach(b => b.classList.remove('selected'));
                confirmButton.classList.remove('show', 'menino', 'menina');
                currentSelection = null;
                currentOdds = 0;

                await carregarDados(); // Refresh odds
            } else {
                showMessageModal(data.error || 'Erro ao registrar aposta. Tente novamente.');
            }

        } catch (error) {
            console.error('Erro ao processar aposta:', error);
            placeBetButton.disabled = false;
            placeBetButton.textContent = 'Fazer Aposta';
            showMessageModal('Erro ao processar aposta. Tente novamente.');
        }
    });
}

// Confirm payment
document.getElementById('copyPixButton').addEventListener('click', function() {
    const pixPayload = document.getElementById('pixPayload').textContent;
    navigator.clipboard.writeText(pixPayload).then(() => {
        showMessageModal('Código PIX copiado para a área de transferência!');
    }).catch(err => {
        console.error('Erro ao copiar código PIX:', err);
        showMessageModal('Erro ao copiar código PIX.');
    });
});

// New button to confirm payment
document.getElementById('confirmPixPayment').addEventListener('click', async function() {
    if (!window.currentApostaId) {
        showMessageModal('Erro: ID da aposta não encontrado.');
        return;
    }

    try {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
            document.querySelector('meta[name=csrf-token]')?.getAttribute('content');

        const response = await fetch('/confirmar_pagamento_aposta/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
            body: JSON.stringify({
                aposta_id: window.currentApostaId
            })
        });

        const data = await response.json();
        console.log('Response from /confirmar_pagamento_aposta/:', data);

        if (response.ok && data.success) {
            showMessageModal(data.message);
            document.getElementById('pixModalOverlay').classList.remove('show');
            await carregarDados(); // Refresh user data
        } else {
            showMessageModal(data.error || 'Erro ao confirmar pagamento.');
        }

    } catch (error) {
        console.error('Erro ao confirmar pagamento:', error);
        showMessageModal('Erro ao confirmar pagamento. Tente novamente.');
    }
});

// Close PIX modal
document.getElementById('closePixModal').addEventListener('click', function() {
    document.getElementById('pixModalOverlay').classList.remove('show');
});

// Close PIX modal when clicking outside
document.getElementById('pixModalOverlay').addEventListener('click', function(e) {
    if (e.target === document.getElementById('pixModalOverlay')) {
        document.getElementById('pixModalOverlay').classList.remove('show');
    }
});

// Cancelar aposta
if (cancelBetButton && modalOverlay) {
    cancelBetButton.addEventListener('click', function() {
        modalOverlay.classList.remove('show');
    });
}


// Fechar modal clicando fora
if (modalOverlay) {
    modalOverlay.addEventListener('click', function(e) {
        if (e.target === modalOverlay) {
            modalOverlay.classList.remove('show');
        }
    });
}


// Logout
if (logoutButton) {
    logoutButton.addEventListener('click', async function () {
        const confirmed = await showMessageModal('Tem certeza que deseja sair da sua conta?', true);
        if (confirmed) {
            const logoutForm = document.getElementById('logoutForm');
            if (logoutForm) {
                logoutButton.disabled = true;  // Proteção opcional
                logoutForm.submit();
            } else {
                showMessageModal('Erro: Formulário de logout não encontrado.');
            }
        }
    });
}
