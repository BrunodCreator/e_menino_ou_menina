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
const content1 = document.querySelector('.container'); 
const content2 = document.querySelector('.container2'); 
const confirmButton1 = document.querySelector('#confirmButton1');
const confirmButton2 = document.querySelector('#confirmButton2');
const blocks = [content1, content2];
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
    if (!messageModalOverlay || !messageModalConfirmButton || !messageModalCancelButton || !messageModalText) {
        console.error('Elementos do modal não encontrados no DOM.');
        return Promise.resolve(false);
    }

    messageModalText.textContent = message;
    messageModalConfirmButton.style.display = 'block';
    messageModalCancelButton.style.display = isConfirm ? 'block' : 'none';
    messageModalOverlay.classList.add('show');

    return new Promise(resolve => {
        const closeModal = () => {
            messageModalOverlay.classList.remove('show');
            messageModalConfirmButton.removeEventListener('click', onOk);
            messageModalCancelButton.removeEventListener('click', onCancel);
            messageModalOverlay.removeEventListener('click', onOverlayClick);
        };

        const onOk = () => {
            closeModal();
            resolve(true);
        };

        const onCancel = () => {
            closeModal();
            resolve(false);
        };

        const onOverlayClick = (e) => {
            if (e.target === messageModalOverlay && !isConfirm) {
                closeModal();
                resolve(true);
            }
        };

        messageModalConfirmButton.addEventListener('click', onOk);
        messageModalCancelButton.addEventListener('click', onCancel);
        messageModalOverlay.addEventListener('click', onOverlayClick);
    });
}


// --- Função initLogout ---
function initLogout() {
    const logoutBtn = document.getElementById('logoutButton');
    const logoutForm = document.getElementById('logoutForm');

    if (!logoutBtn) return; // Se não houver botão, não faz nada
    if (!logoutForm) {
        console.error('Formulário de logout não encontrado!');
        return;
    }

    logoutBtn.addEventListener('click', async function () {
        if (!messageModalOverlay || !messageModalConfirmButton || !messageModalCancelButton) {
            alert('Tem certeza que deseja sair da sua conta?'); // fallback simples
            logoutForm.submit();
            return;
        }

        const confirmed = await showMessageModal(
            'Tem certeza que deseja sair da sua conta?',
            true
        );
        if (confirmed) {
            logoutBtn.disabled = true;
            logoutForm.submit();
        }
    });
}

// --- Inicializa quando o DOM estiver pronto ---
document.addEventListener('DOMContentLoaded', () => {
    carregarDados(); // já existia
    initLogout();    // chamamos aqui para garantir que o logout funcione
});
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
                oddMeninoElement.textContent = `Odd: ${oddMenino.toFixed(1)}x`;
            } else {
                console.warn('carregarDados: Elemento oddMeninoElement não encontrado.');
            }
            if (oddMeninaElement) {
                oddMeninaElement.textContent = `Odd: ${oddMenina.toFixed(1)}x`;
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
            document.querySelector("#menuToggle").style.display = 'none'
        } else {
            sidebar.classList.remove('open');
            menuToggle.classList.remove('open');
            mainContent.classList.remove('shifted');
        }
    });
}

//Ação bebes
console.log(confirmButton1,confirmButton2)

function selectBoy (){
    currentSelection = 'menino';
    currentOdds = parseFloat(content1.dataset.odds);
    content1.style.filter = 'brightness(100%)';
    content2.style.filter = 'brightness(50%)';

    confirmButton1.style.fontSize = '2em';
    confirmButton1.style.padding = "10px";
    confirmButton2.style.fontSize = '1em';
    confirmButton2.style.padding = "1px";
    
    content2.style.width = "100vw";
    content1.style.width = "200%";
    document.querySelector("#menuToggle").style.display = 'flex'
    document.querySelector("#sidebar").classList

    const sidebar = document.getElementById("sidebar");

    if (sidebar.classList.contains("open")) {
        document.querySelector("#menuToggle").click()
    } 

}

function selectGirl (){
    currentSelection = 'menina';
    currentOdds = parseFloat(content2.dataset.odds);
    content2.style.filter = 'brightness(100%)';
    content2.style.width = "200%";
    content1.style.filter = 'brightness(50%)';

    confirmButton2.style.fontSize = '2em';
    confirmButton2.style.padding = "10px";
    
    confirmButton1.style.fontSize = '1em';
    confirmButton1.style.padding = "1px";
    content1.style.width = "100vw";

        document.querySelector("#menuToggle").style.display = 'flex'
    document.querySelector("#sidebar").classList

    const sidebar = document.getElementById("sidebar");

    if (sidebar.classList.contains("open")) {
        document.querySelector("#menuToggle").click()
    } 
    
}

content1.addEventListener('click',(selectBoy))
content2.addEventListener('click',(selectGirl))

// =======================
// Abrir modal de aposta
// =======================
function openBetModal() {
    if (!currentSelection) return; // Evita abrir sem seleção
    if (!currentOdds || currentOdds === 0) {
        console.warn('openBetModal: currentOdds inválido', currentOdds);
        return;
    }

    selectedOptionDisplay.textContent = currentSelection === 'menino' ? 'MENINO' : 'MENINA';
    modalOverlay.classList.add('show');

    // Reset do input e retorno
    betAmountInput.value = '';
    expectedReturnElement.textContent = 'R$ 0,00';
    betAmountInput.focus();
}

// Botões de confirmação
[confirmButton1, confirmButton2].forEach(btn => btn.addEventListener('click', openBetModal));

// =======================
// Cancelar aposta / fechar modal
// =======================
cancelBetButton.addEventListener('click', () => {
    modalOverlay.classList.remove('show');
    currentSelection = null;
    currentOdds = 0;
});

modalOverlay.addEventListener('click', e => {
    if (e.target === modalOverlay) {
        modalOverlay.classList.remove('show');
        currentSelection = null;
        currentOdds = 0;
    }
});

// =======================
// Calcular retorno esperado
// =======================
betAmountInput.addEventListener('input', function() {
    const value = this.value.replace(',', '.'); // Substitui vírgula por ponto
    const betAmount = parseFloat(value) || 0;

    if (!currentOdds || currentOdds === 0) {
        expectedReturnElement.textContent = 'R$ 0,00';
        return;
    }

    const valueForPot = betAmount * 0.70;
    const expectedReturn = valueForPot * currentOdds;

    expectedReturnElement.textContent = `R$ ${expectedReturn.toFixed(2).replace('.', ',')}`;
});


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

                const container = document.getElementById('pixQrCodeContainer');
                container.innerHTML = '';  // wipe out any old QR
                const canvas = document.createElement('canvas'); 
                container.appendChild(canvas);

                QRCode.toCanvas(canvas, data.pix_payload, {
                width: 300,   // size in px; tweak as you like
                margin: 1     // small white border
                }, err => {
                if (err) {
                    console.error('QR gen error:', err);
                    showMessageModal('Erro ao gerar QR Code.');
                }
                });

                document.getElementById('pixPayload').textContent = data.pix_payload;
                document.getElementById('pixKey').textContent = data.chave_pix;
                document.getElementById('pixValue').textContent = `R$ ${data.valor_aposta}`;
                
                // Show the PIX modal after content is updated
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
