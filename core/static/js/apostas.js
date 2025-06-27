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

let currentSelection = null;
let currentOdds = 0;
let totalBetAmount = 0;
let betCount = 0;
let sidebarOpen = false;

// Toggle do menu lateral
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

// Seleção das opções
blocks.forEach(block => {
    block.addEventListener('click', function() {
        // Remove seleção anterior
        blocks.forEach(b => b.classList.remove('selected'));
        
        // Adiciona seleção ao bloco clicado
        this.classList.add('selected');
        
        // Atualiza a seleção atual
        currentSelection = this.dataset.option;
        currentOdds = parseFloat(this.dataset.odds);
        
        // Remove classes anteriores do botão e adiciona a nova
        confirmButton.classList.remove('menino', 'menina');
        confirmButton.classList.add(currentSelection);
        
        // Mostra o botão de confirmar
        confirmButton.classList.add('show');
    });
});

// Confirmar seleção - abre modal
confirmButton.addEventListener('click', function() {
    if (currentSelection) {
        selectedOptionDisplay.textContent = currentSelection.toUpperCase();
        modalOverlay.classList.add('show');
        betAmountInput.value = '';
        expectedReturnElement.textContent = 'R$ 0,00';
        betAmountInput.focus();
    }
});

// Calcular retorno esperado
betAmountInput.addEventListener('input', function() {
    const betAmount = parseFloat(this.value) || 0;
    const expectedReturn = betAmount * currentOdds;
    expectedReturnElement.textContent = `R$ ${expectedReturn.toFixed(2).replace('.', ',')}`;
});

// Fazer aposta
placeBetButton.addEventListener('click', function() {
    const betAmount = parseFloat(betAmountInput.value);
    
    if (!betAmount || betAmount <= 0) {
        alert('Por favor, insira um valor válido para a aposta.');
        return;
    }
    
    // Atualiza os dados
    totalBetAmount += betAmount;
    betCount++;
    
    // Atualiza a interface
    totalBetElement.textContent = `R$ ${totalBetAmount.toFixed(2).replace('.', ',')}`;
    betCountElement.textContent = betCount;
    lastBetElement.textContent = `${currentSelection.toUpperCase()} - R$ ${betAmount.toFixed(2).replace('.', ',')}`;
    
    alert(`Aposta de R$ ${betAmount.toFixed(2).replace('.', ',')} confirmada para: ${currentSelection.toUpperCase()}!\nRetorno esperado: R$ ${(betAmount * currentOdds).toFixed(2).replace('.', ',')}`);
    
    // Fecha modal e reset da seleção
    modalOverlay.classList.remove('show');
    blocks.forEach(b => b.classList.remove('selected'));
    confirmButton.classList.remove('show', 'menino', 'menina');
    currentSelection = null;
    currentOdds = 0;
});

// Cancelar aposta
cancelBetButton.addEventListener('click', function() {
    modalOverlay.classList.remove('show');
});

// Fechar modal clicando fora
modalOverlay.addEventListener('click', function(e) {
    if (e.target === modalOverlay) {
        modalOverlay.classList.remove('show');
    }
});

// Logout
logoutButton.addEventListener('click', function() {
    if (confirm('Tem certeza que deseja sair da sua conta?')) {
        alert('Logout realizado com sucesso!');
        
        // Reset dos dados
        totalBetAmount = 0;
        betCount = 0;
        totalBetElement.textContent = 'R$ 0,00';
        betCountElement.textContent = '0';
        lastBetElement.textContent = '-';
    }
});