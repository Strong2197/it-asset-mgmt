(function() {
    // --- НАЛАШТУВАННЯ ---
    const TARGET_SCORE = 400;
    const INITIAL_TIME = 120;
    const COLS = 8;
    const ROWS = 8;
    const CELL_SIZE = 50;
    const GAP = 6;
    const COLORS = ['🍎', '🍊', '🍇', '🥥', '🥝', '🍪'];
    const SECRET_CODES = ['чудо', 'xelj'];

    // --- СТАН ---
    let grid = [];
    let score = 0;
    let timeLeft = INITIAL_TIME;
    let timerId = null;
    let isBusy = false;
    let selectedCell = null;
    let activeRainbow = null;
    let inputBuffer = '';
    let lastSwappedPair = [];

    // DOM
    const overlay = document.getElementById('m3g-overlay');
    const gridEl = document.getElementById('m3g-grid');
    const scoreEl = document.getElementById('m3g-score');
    const timerEl = document.getElementById('m3g-timer');
    const msgEl = document.getElementById('m3g-msg');

    // --- GAME ENGINE ---
    function init() {
        const w = COLS * CELL_SIZE + (COLS - 1) * GAP + 20;
        const h = ROWS * CELL_SIZE + (ROWS - 1) * GAP + 20;
        gridEl.style.width = w + 'px';
        gridEl.style.height = h + 'px';
        document.addEventListener('keydown', handleKeyInput);
        document.getElementById('m3g-close').addEventListener('click', closeGame);
    }

    function handleKeyInput(e) {
        inputBuffer += e.key;
        if (inputBuffer.length > 10) inputBuffer = inputBuffer.slice(-10);
        if (SECRET_CODES.some(code => inputBuffer.toLowerCase().endsWith(code))) {
            openGame();
            inputBuffer = '';
        }
    }

    function openGame() { overlay.style.display = 'flex'; startGame(); }
    function closeGame() { overlay.style.display = 'none'; stopGame(); }
    function stopGame() { clearInterval(timerId); gridEl.innerHTML = ''; grid = []; }

    function startGame() {
        stopGame();
        score = 0; timeLeft = INITIAL_TIME; isBusy = false;
        selectedCell = null; activeRainbow = null;
        updateUI(); msgEl.innerText = ""; lastSwappedPair = [];

        do { createGridData(); } while (findMatches().matched.length > 0);
        renderGrid();

        timerId = setInterval(() => {
            timeLeft--; updateUI();
            if (timeLeft <= 0) endGame(false);
        }, 1000);
    }

    function updateUI() {
        scoreEl.innerText = score;
        timerEl.innerText = timeLeft;
        if(score >= TARGET_SCORE) scoreEl.style.color = '#00ff00';
        else scoreEl.style.color = '#ffcc00';
    }

    function createGridData() {
        grid = []; gridEl.innerHTML = '';
        for (let r = 0; r < ROWS; r++) {
            let row = [];
            for (let c = 0; c < COLS; c++) {
                const type = COLORS[Math.floor(Math.random() * COLORS.length)];
                row.push({ r, c, type, bonus: null, el: createCellEl(r, c, type) });
            }
            grid.push(row);
        }
    }

    function createCellEl(r, c, type) {
        const el = document.createElement('div');
        el.classList.add('m3g-cell');
        el.innerText = type;
        el.style.left = (c * (CELL_SIZE + GAP)) + 'px';
        el.style.top = (r * (CELL_SIZE + GAP)) + 'px';
        el.onclick = () => handleCellClick(r, c);
        gridEl.appendChild(el);
        return el;
    }

    // --- ВІЗУАЛІЗАЦІЯ ---
    function updateCellVisuals(cell) {
        cell.el.classList.remove('bonus-row', 'bonus-col', 'bonus-bomb', 'bonus-rainbow');

        if (cell.bonus) {
            let icon = '';
            let className = '';

            if (cell.bonus === 'row') { icon = '↔'; className = 'bonus-row'; }
            else if (cell.bonus === 'col') { icon = '↕'; className = 'bonus-col'; }
            else if (cell.bonus === 'bomb') { icon = '💣'; className = 'bonus-bomb'; }
            else if (cell.bonus === 'rainbow') { icon = '✨'; className = 'bonus-rainbow'; }

            cell.el.classList.add(className);
            cell.el.innerHTML = `<div class="m3g-bonus-bg"></div><div class="m3g-bonus-icon">${icon}</div>`;
        } else {
            cell.el.innerHTML = cell.type;
        }
    }

    function renderGrid() {
        grid.forEach(row => {
            row.forEach(cell => {
                if (!cell) return;
                cell.el.style.left = (cell.c * (CELL_SIZE + GAP)) + 'px';
                cell.el.style.top = (cell.r * (CELL_SIZE + GAP)) + 'px';

                updateCellVisuals(cell);

                cell.el.onclick = () => handleCellClick(cell.r, cell.c);
                cell.el.classList.remove('selected', 'active-bonus');

                if (selectedCell === cell) cell.el.classList.add('selected');
                if (activeRainbow === cell) cell.el.classList.add('active-bonus');
            });
        });
    }

    // --- ЛОГІКА ---
    async function handleCellClick(r, c) {
        if (isBusy || timeLeft <= 0 || !grid[r][c]) return;
        const clicked = grid[r][c];
        msgEl.innerText = "";

        if (activeRainbow) {
            if (clicked === activeRainbow) {
                activeRainbow = null; renderGrid(); return;
            }
            if (clicked.bonus) {
                activeRainbow = null; renderGrid();
            } else {
                isBusy = true;
                activeRainbow.el.classList.remove('active-bonus');

                // Якщо клікнули на звичайний фрукт - колір беремо з нього
                // Якщо це бонус (але ми домовились що бонуси не клікабельні для веселки)
                // Але про всяк випадок - веселка не спалює бонуси
                if (!clicked.bonus) {
                    let targetColor = clicked.type;
                    await explodeColor(targetColor, activeRainbow);
                }

                activeRainbow = null; selectedCell = null;
                await applyGravity();
                isBusy = false;
                return;
            }
        }

        if (clicked.bonus === 'rainbow') {
            activeRainbow = clicked;
            selectedCell = null;
            msgEl.innerText = "Оберіть колір!";
            renderGrid();
            return;
        }

        if (clicked.bonus) {
            isBusy = true;
            clicked.el.style.transform = "scale(1.2)";
            await wait(100);

            let targets = new Set();
            activateBonusEffect(r, c, clicked.bonus, targets);

            // Сам бонус теж зникає
            targets.add(`${r},${c}`);

            let destroyedCount = targets.size;
            score += destroyedCount * 2;
            updateUI();

            await destroyTargets(targets);
            selectedCell = null;
            renderGrid();
            await applyGravity();
            isBusy = false;
            return;
        }

        if (!selectedCell) {
            selectedCell = clicked;
            renderGrid();
        } else {
            const first = selectedCell;
            selectedCell = null;
            renderGrid();

            if (first === clicked) return;

            const isAdj = Math.abs(first.r - clicked.r) + Math.abs(first.c - clicked.c) === 1;
            if (isAdj) {
                await swap(first, clicked);
            } else {
                selectedCell = clicked;
                renderGrid();
            }
        }
    }

    async function swap(cellA, cellB) {
        isBusy = true;
        lastSwappedPair = [cellA, cellB];

        const tempType = cellA.type; const tempBonus = cellA.bonus;
        cellA.type = cellB.type; cellA.bonus = cellB.bonus;
        cellB.type = tempType; cellB.bonus = tempBonus;

        const ax = cellA.c * (CELL_SIZE + GAP); const ay = cellA.r * (CELL_SIZE + GAP);
        const bx = cellB.c * (CELL_SIZE + GAP); const by = cellB.r * (CELL_SIZE + GAP);

        cellA.el.style.transform = `translate(${bx - ax}px, ${by - ay}px)`;
        cellB.el.style.transform = `translate(${ax - bx}px, ${ay - by}px)`;

        await wait(150);
        cellA.el.style.transform = ''; cellB.el.style.transform = '';
        renderGrid();

        const matches = findMatches(lastSwappedPair);
        if (matches.matched.length > 0) {
            await processMatches(matches);
        } else {
            msgEl.innerText = "Хід неможливий";
            const tT = cellA.type; const tB = cellA.bonus;
            cellA.type = cellB.type; cellA.bonus = cellB.bonus;
            cellB.type = tT; cellB.bonus = tB;

            cellA.el.style.transition = 'transform 0.15s'; cellB.el.style.transition = 'transform 0.15s';
            cellA.el.style.transform = `translate(${bx - ax}px, ${by - ay}px)`;
            cellB.el.style.transform = `translate(${ax - bx}px, ${ay - by}px)`;

            await wait(20);
            cellA.el.style.transform = ''; cellB.el.style.transform = '';
            await wait(150);
            renderGrid();
        }
        lastSwappedPair = [];
        isBusy = false;
    }

    function findMatches(priorityCells = []) {
        let matchedSet = new Set();
        let bonuses = [];

        const isPriority = (r, c) => priorityCells.some(cell => cell.r === r && cell.c === c);

        // Горизонталь
        for (let r = 0; r < ROWS; r++) {
            for (let c = 0; c < COLS - 2; c++) {
                // ІГНОРУЄМО БОНУСИ У ЗБІГАХ
                if (!grid[r][c] || grid[r][c].bonus) continue;

                let matchLen = 1;
                while (c + matchLen < COLS &&
                       grid[r][c + matchLen] &&
                       !grid[r][c + matchLen].bonus &&
                       grid[r][c].type === grid[r][c + matchLen].type) {
                    matchLen++;
                }

                if (matchLen >= 3) {
                    let bType = null;
                    if (matchLen >= 5) bType = 'rainbow';
                    else if (matchLen === 4) bType = 'row';

                    let spawnR = r, spawnC = c + Math.floor(matchLen / 2);
                    if (bType) {
                        for(let k=0; k<matchLen; k++) if (isPriority(r, c + k)) { spawnC = c + k; break; }
                        bonuses.push({ r: spawnR, c: spawnC, type: bType });
                    }
                    for(let k=0; k<matchLen; k++) matchedSet.add(`${r},${c+k}`);
                    c += matchLen - 1;
                }
            }
        }

        // Вертикаль
        for (let c = 0; c < COLS; c++) {
            for (let r = 0; r < ROWS - 2; r++) {
                if (!grid[r][c] || grid[r][c].bonus) continue;

                let matchLen = 1;
                while (r + matchLen < ROWS &&
                       grid[r + matchLen][c] &&
                       !grid[r + matchLen][c].bonus &&
                       grid[r][c].type === grid[r + matchLen][c].type) {
                    matchLen++;
                }

                if (matchLen >= 3) {
                    let bType = null;
                    if (matchLen >= 5) bType = 'rainbow';
                    else if (matchLen === 4) bType = 'col';

                    let spawnR = r + Math.floor(matchLen / 2), spawnC = c;
                    let existingBonus = bonuses.find(b => b.r === spawnR && b.c === spawnC);

                    if (bType) {
                        for(let k=0; k<matchLen; k++) if (isPriority(r + k, c)) { spawnR = r + k; break; }
                        if (bType === 'rainbow') {
                            bonuses = bonuses.filter(b => !(b.r === spawnR && b.c === spawnC));
                            bonuses.push({ r: spawnR, c: spawnC, type: 'rainbow' });
                        } else if (!existingBonus) {
                             bonuses.push({ r: spawnR, c: spawnC, type: bType });
                        }
                    }
                    for(let k=0; k<matchLen; k++) matchedSet.add(`${r+k},${c}`);
                    r += matchLen - 1;
                }
            }
        }

        // Квадрати
        for (let r = 0; r < ROWS - 1; r++) {
            for (let c = 0; c < COLS - 1; c++) {
                if (!grid[r][c] || !grid[r+1][c] || !grid[r][c+1] || !grid[r+1][c+1]) continue;
                // Ігноруємо бонуси
                if (grid[r][c].bonus || grid[r+1][c].bonus || grid[r][c+1].bonus || grid[r+1][c+1].bonus) continue;

                let t = grid[r][c].type;
                if (t === grid[r+1][c].type && t === grid[r][c+1].type && t === grid[r+1][c+1].type) {
                    matchedSet.add(`${r},${c}`); matchedSet.add(`${r+1},${c}`);
                    matchedSet.add(`${r},${c+1}`); matchedSet.add(`${r+1},${c+1}`);

                    let conflict = bonuses.find(b => (b.r >= r && b.r <= r+1 && b.c >= c && b.c <= c+1 && b.type === 'rainbow'));
                    if (!conflict) {
                         let bonusPos = {r, c};
                         if (isPriority(r, c)) bonusPos = {r, c};
                         else if (isPriority(r+1, c)) bonusPos = {r: r+1, c: c};
                         else if (isPriority(r, c+1)) bonusPos = {r: r, c: c+1};
                         else if (isPriority(r+1, c+1)) bonusPos = {r: r+1, c: c+1};

                         bonuses = bonuses.filter(b => !(b.r === bonusPos.r && b.c === bonusPos.c));
                         bonuses.push({ r: bonusPos.r, c: bonusPos.c, type: 'bomb' });
                    }
                }
            }
        }

        return { matched: Array.from(matchedSet), bonuses };
    }

    async function processMatches(matchData) {
        const { matched, bonuses } = matchData;

        score += matched.length * 1;
        score += bonuses.length * 10;
        updateUI();

        let allTargets = new Set(matched);

        matched.forEach(key => {
            let [r, c] = key.split(',').map(Number);
            let cell = grid[r][c];
            if (cell && cell.bonus) {
                activateBonusEffect(r, c, cell.bonus, allTargets);
            }
        });

        await destroyTargets(allTargets);

        bonuses.forEach(b => {
            if (!grid[b.r][b.c]) {
                let type = COLORS[Math.floor(Math.random() * COLORS.length)];
                let el = createCellEl(b.r, b.c, type);

                // СТВОРЕННЯ БОНУСА (ТИП ЗМІНЮЄТЬСЯ НА НЕЙТРАЛЬНИЙ)
                grid[b.r][b.c] = { r: b.r, c: b.c, type: 'BONUS_ENTITY', bonus: b.type, el };
                updateCellVisuals(grid[b.r][b.c]);
                el.classList.add('new-spawn');
            } else {
                grid[b.r][b.c].bonus = b.type;
                grid[b.r][b.c].type = 'BONUS_ENTITY'; // Видаляємо фрукт з-під капоту
                updateCellVisuals(grid[b.r][b.c]);
            }
        });

        await applyGravity();
    }

    async function destroyTargets(targetSet) {
        targetSet.forEach(key => {
            let [r, c] = key.split(',').map(Number);
            if(grid[r][c]) {
                grid[r][c].el.style.transform = 'scale(0)';
                grid[r][c].el.style.opacity = '0';
            }
        });
        await wait(150);
        targetSet.forEach(key => {
            let [r, c] = key.split(',').map(Number);
            if(grid[r][c]) { grid[r][c].el.remove(); grid[r][c] = null; }
        });
    }

    function activateBonusEffect(r, c, type, targetSet) {
        // ДОДАТКОВА ПЕРЕВІРКА: БОНУСИ НЕ СПАЛЮЮТЬ ІНШІ БОНУСИ
        const safeAdd = (tr, tc) => {
            if (tr >= 0 && tr < ROWS && tc >= 0 && tc < COLS) {
                // Якщо це не поточний бонус (самознищення) і це клітинка з іншим бонусом - пропускаємо
                if ((tr !== r || tc !== c) && grid[tr][tc] && grid[tr][tc].bonus) return;
                targetSet.add(`${tr},${tc}`);
            }
        };

        if (type === 'row') for(let i=0; i<COLS; i++) safeAdd(r, i);
        if (type === 'col') for(let i=0; i<ROWS; i++) safeAdd(i, c);
        if (type === 'bomb') {
            for(let i=r-1; i<=r+1; i++)
                for(let j=c-1; j<=c+1; j++) safeAdd(i, j);
        }
    }

    async function applyGravity() {
        let moves = false;
        for (let c = 0; c < COLS; c++) {
            let emptyCount = 0;
            for (let r = ROWS - 1; r >= 0; r--) {
                if (grid[r][c] === null) {
                    emptyCount++;
                } else if (emptyCount > 0) {
                    let cell = grid[r][c];
                    grid[r + emptyCount][c] = cell;
                    grid[r][c] = null;
                    cell.r += emptyCount;
                    cell.el.style.top = (cell.r * (CELL_SIZE + GAP)) + 'px';
                    moves = true;
                }
            }
            for (let r = 0; r < emptyCount; r++) {
                let type = COLORS[Math.floor(Math.random() * COLORS.length)];
                let el = createCellEl(r - emptyCount, c, type);
                grid[r][c] = { r, c, type, bonus: null, el };
                void el.offsetWidth;
                el.style.top = (r * (CELL_SIZE + GAP)) + 'px';
            }
        }

        await wait(200);
        renderGrid();

        const newMatches = findMatches();
        if (newMatches.matched.length > 0) {
            await processMatches(newMatches);
        } else {
            if (!hasPossibleMoves()) {
                msgEl.innerText = "ПЕРЕМІШУЮ...";
                await wait(500);
                shuffleBoard();
            }
            if (score >= TARGET_SCORE) endGame(true);
        }
    }

    async function explodeColor(type, rainbowCell) {
        let targets = [];
        for(let r=0; r<ROWS; r++)
            for(let c=0; c<COLS; c++) {
                // ВЕСЕЛКА НЕ ЧІПАЄ БОНУСИ
                if(grid[r][c] && !grid[r][c].bonus && grid[r][c].type === type) {
                    targets.push(grid[r][c]);
                }
            }

        targets.forEach(c => {
            c.el.style.transition = 'all 0.2s';
            c.el.style.transform = 'scale(0) rotate(180deg)';
        });
        if(rainbowCell) rainbowCell.el.style.transform = 'scale(0)';

        await wait(200);

        targets.forEach(c => { c.el.remove(); grid[c.r][c.c] = null; });
        if(rainbowCell && grid[rainbowCell.r][rainbowCell.c]) {
            rainbowCell.el.remove(); grid[rainbowCell.r][rainbowCell.c] = null;
        }
        score += targets.length * 2;
        updateUI();
    }

    function hasPossibleMoves() {
        for (let r = 0; r < ROWS; r++) {
            for (let c = 0; c < COLS; c++) {
                if (c < COLS - 1 && checkSwap(r, c, r, c+1)) return true;
                if (r < ROWS - 1 && checkSwap(r, c, r+1, c)) return true;
                if (grid[r][c] && grid[r][c].bonus) return true;
            }
        }
        return false;
    }

    function checkSwap(r1, c1, r2, c2) {
        if(!grid[r1][c1] || !grid[r2][c2]) return false;
        let t = grid[r1][c1].type; grid[r1][c1].type = grid[r2][c2].type; grid[r2][c2].type = t;
        let matches = findMatches().matched.length > 0;
        t = grid[r1][c1].type; grid[r1][c1].type = grid[r2][c2].type; grid[r2][c2].type = t;
        return matches;
    }

    async function shuffleBoard() {
        isBusy = true;
        let items = [];
        for(let r=0; r<ROWS; r++) for(let c=0; c<COLS; c++) if(grid[r][c]) items.push(grid[r][c].type);
        items.sort(() => Math.random() - 0.5);
        let i = 0;
        for(let r=0; r<ROWS; r++) {
            for(let c=0; c<COLS; c++) {
                if(grid[r][c]) {
                    grid[r][c].type = items[i++];

                    if(grid[r][c].bonus) {
                        // Якщо ми перемішуємо бонус - він залишається бонусом без типу
                        grid[r][c].type = 'BONUS_ENTITY';
                    }

                    updateCellVisuals(grid[r][c]);
                    grid[r][c].el.classList.remove('new-spawn');
                    void grid[r][c].el.offsetWidth;
                    grid[r][c].el.classList.add('new-spawn');
                }
            }
        }
        msgEl.innerText = "";
        await wait(400);
        if (findMatches().matched.length > 0) {
            await processMatches(findMatches());
        } else if (!hasPossibleMoves()) {
             shuffleBoard();
        } else {
             isBusy = false;
        }
    }

    function endGame(win) {
        clearInterval(timerId); isBusy = true;
        setTimeout(() => {
            if(win) alert(`🎉 Перемога! Ви набрали ${score} очок!`);
            else alert(`⏰ Час вийшов! Ваш рахунок: ${score}`);
            closeGame();
        }, 100);
    }

    function wait(ms) { return new Promise(r => setTimeout(r, ms)); }
    init();
})();