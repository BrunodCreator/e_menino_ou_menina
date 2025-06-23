const blocks = document.querySelectorAll('.option-block');
const betButton = document.getElementById('betButton');
const selectionText = document.getElementById('selectionText');
const selectedOption = document.getElementById('selectedOption');
const logoutButton = document.getElementById('logoutButton');
const totalBetElement = document.getElementById('totalBet');
const betCountElement = document.getElementById('betCount');
const lastBetElement = document.getElementById('lastBet');
const menuToggle = document.getElementById('menuToggle');
const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('mainContent');

let currentSelection = null;
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

blocks.forEach(block => {
    block.addEventListener('click', function() {
        // Remove seleção anterior
        blocks.forEach(b => b.classList.remove('selected'));
        
        // Adiciona seleção ao bloco clicado
        this.classList.add('selected');
        
        // Atualiza a seleção atual
        currentSelection = this.dataset.option;
        
        // Mostra o texto de seleção
        selectedOption.textContent = currentSelection.toUpperCase();
        selectionText.classList.add('show');
        
        // Remove classes anteriores do botão e adiciona a nova
        betButton.classList.remove('menino', 'menina');
        betButton.classList.add(currentSelection);
        
        // Mostra o botão de aposta
        betButton.classList.add('show');
    });
});

betButton.addEventListener('click', function() {
    if (currentSelection) {
        // Simula valor da aposta (pode ser alterado para um input real)
        const betAmount = 10.00;
        
        // Atualiza os dados
        totalBetAmount += betAmount;
        betCount++;
        
        // Atualiza a interface
        totalBetElement.textContent = `R$ ${totalBetAmount.toFixed(2).replace('.', ',')}`;
        betCountElement.textContent = betCount;
        lastBetElement.textContent = currentSelection.toUpperCase();
        
        alert(`Aposta de R$ ${betAmount.toFixed(2).replace('.', ',')} confirmada para: ${currentSelection.toUpperCase()}!`);
        
        // Reset da seleção
        blocks.forEach(b => b.classList.remove('selected'));
        selectionText.classList.remove('show');
        betButton.classList.remove('show', 'menino', 'menina');
        currentSelection = null;
    }
});

logoutButton.addEventListener('click', function() {
    if (confirm('Tem certeza que deseja sair da sua conta?')) {
        // Aqui você pode adicionar a lógica real de logout
        alert('Logout realizado com sucesso!');
        
        // Reset dos dados (opcional)
        totalBetAmount = 0;
        betCount = 0;
        totalBetElement.textContent = 'R$ 0,00';
        betCountElement.textContent = '0';
        lastBetElement.textContent = '-';
    }
});