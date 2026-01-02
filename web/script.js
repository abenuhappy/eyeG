/**
 * Gabor Eye Game Logic
 */

// ==========================================
// 1. 핵심 엔진: 가보르 패치 이미지 생성 함수
// ==========================================
function createGaborPatch(canvas, size, theta, frequency, sigma, contrast) {
    const ctx = canvas.getContext('2d');
    canvas.width = size;
    canvas.height = size;

    const imageData = ctx.createImageData(size, size);
    const data = imageData.data;

    // Center coordinates
    const center = (size - 1) / 2;

    for (let y = 0; y < size; y++) {
        for (let x = 0; x < size; x++) {
            // Normalize coordinates to [-1, 1]
            const px = (x - center) / center;
            const py = (y - center) / center; // Note: Y axis behavior might differ slightly from numpy meshgrid depending on direction, but usually screen Y is down.

            // 회전 적용
            // Numpy: x_theta = x * cos + y * sin
            // But here y increases downwards. To match math standard where y increases upwards, we might negate y. 
            // However, for Gabor, symmetric/rotational property means we just need consistency.
            // Let's stick to standard rotation matrix.
            
            const x_theta = px * Math.cos(theta) + py * Math.sin(theta);
            const y_theta = -px * Math.sin(theta) + py * Math.cos(theta);

            // 1) 사인파 격자 (Sinusoidal grating)
            const grating = Math.cos(2 * Math.PI * frequency * x_theta);

            // 2) 가우시안 포락선 (Gaussian envelope)
            const envelope = Math.exp(-(x_theta * x_theta + y_theta * y_theta) / (2 * sigma * sigma));

            // 3) 결합 및 대비 조절
            const gabor = grating * envelope * contrast;

            // 4) 0-255 변환
            const val = Math.floor((gabor + 1) / 2 * 255);

            // Set pixel (Grayscale)
            const index = (y * size + x) * 4;
            data[index] = val;     // R
            data[index + 1] = val; // G
            data[index + 2] = val; // B
            data[index + 3] = 255; // Alpha
        }
    }

    ctx.putImageData(imageData, 0, 0);
    return canvas.toDataURL(); // Return as image source
}


// ==========================================
// 2. 게임 앱 컨트롤러
// ==========================================
const gameApp = {
    // Shared State
    score: 0,
    round: 1,
    mode: null, // 'target' or 'pair'
    
    // Target Match State
    tm_targetTheta: 0,
    
    // Pair Match State
    pm_selected: [], // {btn, theta, index}
    pm_matched: new Set(),
    pm_items: [], // [{theta, index}, ...]

    // Initialization
    init: function() {
        this.showMainMenu();
    },

    showMainMenu: function() {
        this.switchScreen('main-menu');
    },

    switchScreen: function(screenId) {
        document.querySelectorAll('.screen').forEach(el => el.classList.remove('active'));
        document.getElementById(screenId).classList.add('active');
    },

    // ------------------------------------------------------------------
    // Mode 1: Target Match
    // ------------------------------------------------------------------
    startTargetMatch: function() {
        this.mode = 'target';
        this.score = 0;
        this.round = 1;
        this.switchScreen('target-match-screen');
        this.startTmRound();
    },

    startTmRound: function() {
        // UI Update
        document.getElementById('tm-score').innerText = `Score: ${this.score}`;
        document.getElementById('tm-round').innerText = `Round: ${this.round}`;
        document.getElementById('tm-feedback').innerText = '';
        document.getElementById('tm-feedback').style.color = 'yellow';

        // Parameters
        const patchSize = 120;
        const frequency = 4.0 + (this.round * 0.2);
        const sigma = 0.35;
        const contrast = 0.9;

        // Target Theta
        const angles = [0, 30, 45, 60, 90, 120, 135, 150].map(d => d * Math.PI / 180);
        this.tm_targetTheta = angles[Math.floor(Math.random() * angles.length)];

        // Helper Canvas
        const helperCanvas = document.getElementById('hidden-generator');

        // Draw Target
        const targetUrl = createGaborPatch(helperCanvas, patchSize, this.tm_targetTheta, frequency, sigma, contrast);
        const targetCanvas = document.getElementById('target-canvas');
        const tCtx = targetCanvas.getContext('2d');
        const tImg = new Image();
        tImg.onload = () => tCtx.drawImage(tImg, 0, 0);
        tImg.src = targetUrl;

        // Grid Thetas
        const gridThetas = [this.tm_targetTheta];
        while (gridThetas.length < 9) {
            const diffDeg = Math.floor(Math.random() * 140) + 20; // 20~160
            const diffRad = diffDeg * Math.PI / 180;
            const distractor = (this.tm_targetTheta + diffRad) % (Math.PI); // Mod PI because 180 rotation is same
            gridThetas.push(distractor);
        }
        
        // Shuffle
        for (let i = gridThetas.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [gridThetas[i], gridThetas[j]] = [gridThetas[j], gridThetas[i]];
        }

        // Render Grid
        const gridContainer = document.getElementById('tm-grid');
        gridContainer.innerHTML = '';
        gridContainer.style.gridTemplateColumns = 'repeat(3, 1fr)'; // 3x3

        gridThetas.forEach((theta, index) => {
            const imgUrl = createGaborPatch(helperCanvas, patchSize, theta, frequency, sigma, contrast);
            
            const btn = document.createElement('button');
            btn.className = 'gabor-btn';
            btn.className = 'gabor-btn';
            btn.innerHTML = `<img src="${imgUrl}" width="${patchSize}" height="${patchSize}" draggable="false" ondragstart="return false;">`;
            
            btn.onclick = () => this.checkTmAnswer(btn, theta);
            gridContainer.appendChild(btn);
        });
    },

    checkTmAnswer: function(btn, theta) {
        if (btn.disabled) return;

        // Compare angles (allow small epsilon)
        const isCorrect = Math.abs(theta - this.tm_targetTheta) < 0.001;

        if (isCorrect) {
            btn.classList.add('correct');
            this.score += 10;
            this.round += 1;
            document.getElementById('tm-feedback').innerText = '정답입니다!';
            document.getElementById('tm-feedback').style.color = 'var(--accent-green)';
            this.disableTmButtons();
            setTimeout(() => this.startTmRound(), 1000);
        } else {
            btn.classList.add('wrong');
            document.getElementById('tm-feedback').innerText = '다시 집중해서 찾아보세요.';
            document.getElementById('tm-feedback').style.color = 'var(--accent-red)';
        }
    },

    disableTmButtons: function() {
        const btns = document.querySelectorAll('#tm-grid .gabor-btn');
        btns.forEach(b => b.disabled = true);
    },

    // ------------------------------------------------------------------
    // Mode 2: Pair Match
    // ------------------------------------------------------------------
    startPairMatch: function() {
        this.mode = 'pair';
        this.round = 1;
        this.switchScreen('pair-match-screen');
        this.startPmRound();
    },

    startPmRound: function() {
        this.pm_selected = [];
        this.pm_matched = new Set();
        this.pm_items = [];

        document.getElementById('pm-round').innerText = `Round: ${this.round}`;
        document.getElementById('pm-feedback').innerText = '';

        // Determine size
        const numPairs = Math.min(2 + (this.round - 1) * 2, 8);
        const numItems = numPairs * 2;
        
        // Grid Layout logic
        let cols = 2;
        if (numItems > 4) cols = 2; // 4x2
        if (numItems > 8) cols = 3; // 4x3
        if (numItems > 12) cols = 4; // 4x4
        
        // Parameters
        const patchSize = 100;
        const frequency = 4.0;
        const sigma = 0.35;
        const contrast = 0.9;
        const helperCanvas = document.getElementById('hidden-generator');

        // Generate Pairs
        let baseThetas = [];
        for (let i = 0; i < numPairs; i++) {
            baseThetas.push(Math.random() * Math.PI);
        }
        
        let gameThetas = [...baseThetas, ...baseThetas]; // Duplicate
        // Shuffle
        for (let i = gameThetas.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [gameThetas[i], gameThetas[j]] = [gameThetas[j], gameThetas[i]];
        }

        // Render
        const gridContainer = document.getElementById('pm-grid');
        gridContainer.innerHTML = '';
        gridContainer.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;

        gameThetas.forEach((theta, index) => {
            const imgUrl = createGaborPatch(helperCanvas, patchSize, theta, frequency, sigma, contrast);
            
            const btn = document.createElement('button');
            btn.className = 'gabor-btn';
            btn.className = 'gabor-btn';
            btn.innerHTML = `<img src="${imgUrl}" width="${patchSize}" height="${patchSize}" draggable="false" ondragstart="return false;">`;
            btn.id = `pm-btn-${index}`;
            
            btn.onclick = () => this.handlePmClick(btn, theta, index);
            gridContainer.appendChild(btn);
        });
    },

    handlePmClick: function(btn, theta, index) {
        if (this.pm_matched.has(index)) return;
        
        // Check if already selected (toggle off?) or max selected
        const alreadySelIdx = this.pm_selected.findIndex(item => item.index === index);
        if (alreadySelIdx !== -1) {
            // Already selected -> Deselect? No, let's just ignore or allow deselect. 
            // Implementation: Click to select, click again does nothing or deselects.
            // Let's implement ignore if same clicked.
            return;
        }

        if (this.pm_selected.length >= 2) return;

        // Select
        btn.classList.add('selected');
        this.pm_selected.push({btn, theta, index});

        // Check Pair
        if (this.pm_selected.length === 2) {
            setTimeout(() => this.checkPmPair(), 500);
        }
    },

    checkPmPair: function() {
        const [item1, item2] = this.pm_selected;
        
        // Compare
        const isMatch = Math.abs(item1.theta - item2.theta) < 0.001;

        if (isMatch) {
            document.getElementById('pm-feedback').innerText = '매치 성공!';
            document.getElementById('pm-feedback').style.color = 'var(--accent-green)';
            
            // Hide buttons
            item1.btn.classList.remove('selected');
            item2.btn.classList.remove('selected');
            item1.btn.classList.add('hidden');
            item2.btn.classList.add('hidden');
            
            this.pm_matched.add(item1.index);
            this.pm_matched.add(item2.index);

            // Check Win
            const numItems = document.getElementById('pm-grid').childElementCount;
            if (this.pm_matched.size === numItems) {
                document.getElementById('pm-feedback').innerText = '모든 짝을 찾았습니다!';
                this.round += 1;
                setTimeout(() => this.startPmRound(), 1000);
            }

        } else {
            document.getElementById('pm-feedback').innerText = '다릅니다.';
            document.getElementById('pm-feedback').style.color = 'var(--accent-red)';
            
            item1.btn.classList.remove('selected');
            item2.btn.classList.remove('selected');
        }

        this.pm_selected = [];
    }
};

// Start default
window.onload = function() {
    gameApp.init();
};
