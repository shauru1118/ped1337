// SPA Client JS for Ped1337 SteganoSuite

let currentTab = 'embed';
let currentPayloadMode = 'text';

// Setup dropzones on window load
document.addEventListener('DOMContentLoaded', () => {
    setupDropZone('drop-zone-cover', 'input-cover', handleCoverSelect, 'preview-cover-container');
    setupDropZone('drop-zone-payload', 'input-payload-file', handlePayloadFileSelect, 'preview-payload-container');
    setupDropZone('drop-zone-stego', 'input-stego', handleStegoSelect, 'preview-stego-container');
    setupDropZone('drop-zone-verify', 'input-verify', handleVerifySelect, 'preview-verify-container');
    setupDropZone('drop-zone-capacity', 'input-capacity', handleCapacitySelect, 'preview-capacity-container');
    setupDropZone('drop-zone-steganalysis', 'input-steganalysis', handleSteganalysisSelect, 'preview-steganalysis-container');

    // Setup preview zones for drop-on-preview interaction
    setupPreviewZone('preview-cover-container', 'input-cover', handleCoverSelect);
    setupPreviewZone('preview-payload-container', 'input-payload-file', handlePayloadFileSelect);
    setupPreviewZone('preview-stego-container', 'input-stego', handleStegoSelect);
    setupPreviewZone('preview-verify-container', 'input-verify', handleVerifySelect);
    setupPreviewZone('preview-capacity-container', 'input-capacity', handleCapacitySelect);
    setupPreviewZone('preview-steganalysis-container', 'input-steganalysis', handleSteganalysisSelect);

    // Form Submissions
    document.getElementById('embed-form').addEventListener('submit', handleEmbedSubmit);
    document.getElementById('extract-form').addEventListener('submit', handleExtractSubmit);
    document.getElementById('verify-form').addEventListener('submit', handleVerifySubmit);
    document.getElementById('capacity-form').addEventListener('submit', handleCapacitySubmit);
    document.getElementById('steganalysis-form').addEventListener('submit', handleSteganalysisSubmit);
});
// Switch active tabs
function switchTab(tab) {
    currentTab = tab;
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(panel => panel.classList.remove('active'));

    document.getElementById(`tab-${tab}-btn`).classList.add('active');
    document.getElementById(`panel-${tab}`).classList.add('active');
}

// Switch payload input mode (text vs file)
function switchPayloadMode(mode) {
    currentPayloadMode = mode;
    document.querySelectorAll('.payload-tab').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.payload-input-wrapper').forEach(wrap => wrap.classList.remove('active'));

    const activeTabBtn = Array.from(document.querySelectorAll('.payload-tab')).find(t => t.innerText.includes(mode === 'text' ? 'Текст' : 'Файл'));
    if (activeTabBtn) activeTabBtn.classList.add('active');

    document.getElementById(`payload-${mode}-wrapper`).classList.add('active');
}

function assignInputFile(input, file) {
    const dt = new DataTransfer();
    dt.items.add(file);
    input.files = dt.files;
}

function bindFileDropTarget(target, input, onFileSelect) {
    if (!target) return;

    target.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.stopPropagation();
        target.classList.add('dragover');
    });

    target.addEventListener('dragleave', (e) => {
        e.preventDefault();
        if (!target.contains(e.relatedTarget)) {
            target.classList.remove('dragover');
        }
    });

    target.addEventListener('drop', (e) => {
        e.preventDefault();
        e.stopPropagation();
        target.classList.remove('dragover');
        const file = e.dataTransfer.files?.[0];
        if (!file) return;
        assignInputFile(input, file);
        onFileSelect(file);
    });
}

// Setup drag and drop zones (also allow replacing via drop on preview)
function setupDropZone(zoneId, inputId, onFileSelect, previewId = null) {
    const zone = document.getElementById(zoneId);
    const input = document.getElementById(inputId);
    const preview = previewId ? document.getElementById(previewId) : null;

    if (!zone || !input) return;

    zone.addEventListener('click', () => input.click());
    bindFileDropTarget(zone, input, onFileSelect);
    bindFileDropTarget(preview, input, onFileSelect);

    if (preview) {
        preview.addEventListener('click', (e) => {
            if (e.target.closest('.remove-btn')) return;
            input.click();
        });
    }

    input.addEventListener('change', () => {
        if (input.files.length > 0) {
            onFileSelect(input.files[0]);
        }
    });
}

// Setup interactive preview zones for seamless replacement
function setupPreviewZone(containerId, inputId, onFileSelect) {
    const container = document.getElementById(containerId);
    const input = document.getElementById(inputId);

    if (!container || !input) return;

    container.addEventListener('click', (e) => {
        // If they clicked the remove button, let clearInput handle it
        if (e.target.classList.contains('remove-btn')) return;
        input.click();
    });

    container.addEventListener('dragover', (e) => {
        e.preventDefault();
        container.classList.add('dragover');
    });

    container.addEventListener('dragleave', () => {
        container.classList.remove('dragover');
    });

    container.addEventListener('drop', (e) => {
        e.preventDefault();
        container.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            input.files = e.dataTransfer.files;
            onFileSelect(e.dataTransfer.files[0]);
        }
    });
}

// Handle selected file previews
function handleCoverSelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-cover').src = e.target.result;
        document.getElementById('preview-cover-container').classList.add('active');
        document.getElementById('drop-zone-cover').style.display = 'none';
    };
    reader.readAsDataURL(file);
}

function handleStegoSelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-stego').src = e.target.result;
        document.getElementById('preview-stego-container').classList.add('active');
        document.getElementById('drop-zone-stego').style.display = 'none';
        
        // Auto submit
        document.getElementById('extract-form').dispatchEvent(new Event('submit'));
    };
    reader.readAsDataURL(file);
}

function handlePayloadFileSelect(file) {
    document.getElementById('preview-payload-name').innerText = file.name;
    document.getElementById('preview-payload-container').classList.add('active');
    document.getElementById('drop-zone-payload').style.display = 'none';
}

function handleVerifySelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-verify').src = e.target.result;
        document.getElementById('preview-verify-container').classList.add('active');
        document.getElementById('drop-zone-verify').style.display = 'none';
        
        // Auto submit
        document.getElementById('verify-form').dispatchEvent(new Event('submit'));
    };
    reader.readAsDataURL(file);
}

function handleCapacitySelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-capacity').src = e.target.result;
        document.getElementById('preview-capacity-container').classList.add('active');
        document.getElementById('drop-zone-capacity').style.display = 'none';
        
        // Auto submit
        document.getElementById('capacity-form').dispatchEvent(new Event('submit'));
    };
    reader.readAsDataURL(file);
}

function handleSteganalysisSelect(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        document.getElementById('preview-steganalysis').src = e.target.result;
        document.getElementById('preview-steganalysis-container').classList.add('active');
        document.getElementById('drop-zone-steganalysis').style.display = 'none';
        
        // Auto submit
        document.getElementById('steganalysis-form').dispatchEvent(new Event('submit'));
    };
    reader.readAsDataURL(file);
}

// Clear Drag & Drop Zones
function clearInput(type) {
    if (type === 'cover') {
        document.getElementById('input-cover').value = '';
        document.getElementById('preview-cover-container').classList.remove('active');
        document.getElementById('drop-zone-cover').style.display = 'block';
    } else if (type === 'stego') {
        document.getElementById('input-stego').value = '';
        document.getElementById('preview-stego-container').classList.remove('active');
        document.getElementById('drop-zone-stego').style.display = 'block';
    } else if (type === 'payload') {
        document.getElementById('input-payload-file').value = '';
        document.getElementById('preview-payload-container').classList.remove('active');
        document.getElementById('drop-zone-payload').style.display = 'block';
    } else if (type === 'verify') {
        document.getElementById('input-verify').value = '';
        document.getElementById('preview-verify-container').classList.remove('active');
        document.getElementById('drop-zone-verify').style.display = 'block';
    } else if (type === 'capacity') {
        document.getElementById('input-capacity').value = '';
        document.getElementById('preview-capacity-container').classList.remove('active');
        document.getElementById('drop-zone-capacity').style.display = 'block';
    } else if (type === 'steganalysis') {
        document.getElementById('input-steganalysis').value = '';
        document.getElementById('preview-steganalysis-container').classList.remove('active');
        document.getElementById('drop-zone-steganalysis').style.display = 'block';
    }
}

// Key generation helper
async function generateNewKey() {
    try {
        const response = await fetch('/api/keygen');
        const data = await response.json();
        document.getElementById('input-key').value = data.key;
    } catch (e) {
        alert('Не удалось сгенерировать ключ: ' + e);
    }
}

// Show/Hide loaders
function toggleLoader(btnId, loaderId, show) {
    const btn = document.getElementById(btnId);
    const loader = document.getElementById(loaderId);
    if (!btn || !loader) return;

    if (show) {
        btn.disabled = true;
        loader.style.display = 'inline-block';
    } else {
        btn.disabled = false;
        loader.style.display = 'none';
    }
}

// EMBED FORM SUBMISSION
async function handleEmbedSubmit(e) {
    e.preventDefault();
    toggleLoader('embed-submit-btn', 'embed-loader', true);
    hideResults();

    const formData = new FormData();
    const coverFile = document.getElementById('input-cover').files[0];
    const key = document.getElementById('input-key').value;

    if (!coverFile) {
        alert('Пожалуйста, выберите картинку-обложку.');
        toggleLoader('embed-submit-btn', 'embed-loader', false);
        return;
    }

    formData.append('cover', coverFile);
    if (key) formData.append('key', key);

    if (currentPayloadMode === 'text') {
        const text = document.getElementById('input-payload-text').value.trim();
        if (!text) {
            alert('Пожалуйста, введите текст сообщения.');
            toggleLoader('embed-submit-btn', 'embed-loader', false);
            return;
        }
        formData.append('text', text);
    } else {
        const payloadFile = document.getElementById('input-payload-file').files[0];
        if (!payloadFile) {
            alert('Пожалуйста, выберите скрываемый файл.');
            toggleLoader('embed-submit-btn', 'embed-loader', false);
            return;
        }
        formData.append('payload_file', payloadFile);
    }

    try {
        const response = await fetch('/api/embed', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Неизвестная ошибка сервера');
        }

        // Handle file download
        const blob = await response.blob();
        const downloadUrl = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = 'stego_container.png';
        document.body.appendChild(a);
        a.click();
        a.remove();

        // Run visualizations automatically on generated container
        await generateVisualizations(blob);

    } catch (err) {
        alert('Ошибка маскирования: ' + err.message);
    } finally {
        toggleLoader('embed-submit-btn', 'embed-loader', false);
    }
}

// Generate LSB visualizations
async function generateVisualizations(stegoBlob) {
    const formData = new FormData();
    formData.append('stego', stegoBlob, 'stego.png');

    try {
        const response = await fetch('/api/visualize', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) return;

        const data = await response.json();
        if (data.urls && data.urls.length === 4) {
            document.getElementById('vis-full').src = data.urls[0];
            document.getElementById('vis-0').src = data.urls[1];
            document.getElementById('vis-1').src = data.urls[2];
            document.getElementById('vis-2').src = data.urls[3];

            document.getElementById('visualization-gallery-wrapper').classList.add('active');
        }
    } catch (e) {
        console.error('Ошибка генерации визуализации: ', e);
    }
}

// EXTRACT FORM SUBMISSION
async function handleExtractSubmit(e) {
    e.preventDefault();
    toggleLoader('extract-submit-btn', 'extract-loader', true);
    hideResults();

    const stegoFile = document.getElementById('input-stego').files[0];
    const key = document.getElementById('extract-key').value;

    if (!stegoFile) {
        alert('Пожалуйста, выберите стего-картинку.');
        toggleLoader('extract-submit-btn', 'extract-loader', false);
        return;
    }

    const formData = new FormData();
    formData.append('stego', stegoFile);
    if (key) formData.append('key', key);

    try {
        const response = await fetch('/api/extract', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Неизвестная ошибка сервера');
        }

        const data = await response.json();
        
        document.getElementById('result-extract-wrapper').classList.add('active');

        if (data.type === 'file') {
            const filename = data.filename;
            const contentBytes = base64ToArrayBuffer(data.content);
            const blob = new Blob([contentBytes], { type: 'application/octet-stream' });
            
            const fileUrl = window.URL.createObjectURL(blob);
            const downloadBtn = document.getElementById('extracted-download-link');
            downloadBtn.href = fileUrl;
            downloadBtn.download = filename;

            document.getElementById('extracted-filename').innerText = filename;
            document.getElementById('extracted-file-box').style.display = 'flex';
            document.getElementById('extracted-text-box').style.display = 'none';
        } else {
            // Text mode
            document.getElementById('extracted-text-content').innerText = data.text;
            document.getElementById('extracted-text-box').style.display = 'block';
            document.getElementById('extracted-file-box').style.display = 'none';
        }

    } catch (err) {
        alert('Ошибка демаскирования: ' + err.message);
    } finally {
        toggleLoader('extract-submit-btn', 'extract-loader', false);
    }
}

// Reset results section
function hideResults() {
    document.getElementById('result-extract-wrapper').classList.remove('active');
    document.getElementById('result-verify-wrapper').classList.remove('active');
    document.getElementById('result-capacity-wrapper').classList.remove('active');
    document.getElementById('result-steganalysis-wrapper').classList.remove('active');
    document.getElementById('verify-success-box').classList.remove('active');
    document.getElementById('verify-fail-box').classList.remove('active');
    document.getElementById('visualization-gallery-wrapper').classList.remove('active');
}

// VERIFY FORM SUBMISSION
async function handleVerifySubmit(e) {
    e.preventDefault();
    toggleLoader('verify-submit-btn', 'verify-loader', true);
    hideResults();

    const stegoFile = document.getElementById('input-verify').files[0];
    const key = document.getElementById('verify-key').value;

    if (!stegoFile) {
        alert('Пожалуйста, выберите стего-картинку.');
        toggleLoader('verify-submit-btn', 'verify-loader', false);
        return;
    }

    const formData = new FormData();
    formData.append('stego', stegoFile);
    if (key) formData.append('key', key);

    try {
        const response = await fetch('/api/verify', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Неизвестная ошибка сервера');
        }

        const data = await response.json();
        
        document.getElementById('result-verify-wrapper').classList.add('active');

        if (data.valid) {
            document.getElementById('verify-payload-info').innerText = data.info;
            document.getElementById('verify-success-box').classList.add('active');
            document.getElementById('verify-fail-box').classList.remove('active');
        } else {
            document.getElementById('verify-fail-reason').innerText = `Причина: ${data.reason}`;
            document.getElementById('verify-fail-box').classList.add('active');
            document.getElementById('verify-success-box').classList.remove('active');
        }

    } catch (err) {
        alert('Ошибка проверки подлинности: ' + err.message);
    } finally {
        toggleLoader('verify-submit-btn', 'verify-loader', false);
    }
}

// CAPACITY FORM SUBMISSION
async function handleCapacitySubmit(e) {
    e.preventDefault();
    toggleLoader('capacity-submit-btn', 'capacity-loader', true);
    hideResults();

    const coverFile = document.getElementById('input-capacity').files[0];

    if (!coverFile) {
        alert('Пожалуйста, выберите картинку.');
        toggleLoader('capacity-submit-btn', 'capacity-loader', false);
        return;
    }

    const formData = new FormData();
    formData.append('cover', coverFile);

    try {
        const response = await fetch('/api/capacity', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Неизвестная ошибка сервера');
        }

        const data = await response.json();
        
        // Format values
        const bytes = data.bytes;
        let formattedBytes = `${bytes} Б`;
        if (bytes >= 1024 * 1024) {
            formattedBytes = `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
        } else if (bytes >= 1024) {
            formattedBytes = `${(bytes / 1024).toFixed(2)} KB`;
        }

        document.getElementById('result-capacity-wrapper').classList.add('active');

        document.getElementById('capacity-val-bytes').innerText = formattedBytes;
        document.getElementById('capacity-val-chars').innerText = data.symbols.toLocaleString();
        document.getElementById('capacity-val-words').innerText = Math.floor(data.symbols / 6).toLocaleString();

    } catch (err) {
        alert('Ошибка расчета вместимости: ' + err.message);
    } finally {
        toggleLoader('capacity-submit-btn', 'capacity-loader', false);
    }
}

// Convert Base64 payload to ArrayBuffer
function base64ToArrayBuffer(base64) {
    const binaryString = atob(base64);
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

let stegoChartInstance = null;

// STEGANALYSIS FORM SUBMISSION
async function handleSteganalysisSubmit(e) {
    e.preventDefault();
    toggleLoader('steganalysis-submit-btn', 'steganalysis-loader', true);
    hideResults();

    const imgFile = document.getElementById('input-steganalysis').files[0];

    if (!imgFile) {
        alert('Пожалуйста, выберите картинку для анализа.');
        toggleLoader('steganalysis-submit-btn', 'steganalysis-loader', false);
        return;
    }

    const formData = new FormData();
    formData.append('image', imgFile);

    try {
        const response = await fetch('/api/steganalysis', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Неизвестная ошибка сервера');
        }

        const data = await response.json();
        
        document.getElementById('result-steganalysis-wrapper').classList.add('active');

        // Render verdict
        const verdictBox = document.getElementById('steganalysis-verdict');
        const verdictIcon = document.getElementById('verdict-icon');
        const verdictTitle = document.getElementById('verdict-title');
        const verdictDesc = document.getElementById('verdict-desc');

        verdictBox.className = 'steganalysis-verdict-box'; // reset classes

        const formatP = (value) => {
            if (value === null || value === undefined || Number.isNaN(Number(value))) {
                return 'н/д';
            }
            const num = Number(value);
            if (num <= 0) {
                return '0';
            }
            if (num < 1e-4) {
                return num.toExponential(2);
            }
            return num.toFixed(4);
        };
        const formatE = (value) => {
            if (value === null || value === undefined || Number.isNaN(Number(value))) {
                return 'н/д';
            }
            return Number(value).toFixed(4);
        };
        const lastFinite = (series) => {
            if (!Array.isArray(series)) return null;
            for (let i = series.length - 1; i >= 0; i -= 1) {
                const v = series[i];
                if (v !== null && v !== undefined && !Number.isNaN(Number(v))) {
                    return Number(v);
                }
            }
            return null;
        };
        const peakFinite = (series) => {
            if (!Array.isArray(series)) return null;
            let peak = null;
            for (const v of series) {
                if (v === null || v === undefined || Number.isNaN(Number(v))) continue;
                const num = Number(v);
                if (peak === null || num > peak) peak = num;
            }
            return peak;
        };

        // Verdict uses FINAL p (100% pixels). Chart shows the progressive Westfeld curve.
        const r_p = data.channels?.red?.p_value ?? lastFinite(data.results.red.p_values);
        const g_p = data.channels?.green?.p_value ?? lastFinite(data.results.green.p_values);
        const b_p = data.channels?.blue?.p_value ?? lastFinite(data.results.blue.p_values);

        const r_peak = peakFinite(data.results.red.p_values);
        const g_peak = peakFinite(data.results.green.p_values);
        const b_peak = peakFinite(data.results.blue.p_values);

        const r_e = data.channels?.red?.entropy ?? lastFinite(data.results.red.entropies);
        const g_e = data.channels?.green?.entropy ?? lastFinite(data.results.green.entropies);
        const b_e = data.channels?.blue?.entropy ?? lastFinite(data.results.blue.entropies);

        const avgP = data.avg_p ?? ((r_p + g_p + b_p) / 3);
        const maxP = data.max_p ?? Math.max(r_p, g_p, b_p);
        const maxEntropy = data.max_entropy ?? Math.max(r_e, g_e, b_e);
        const curvePeak = Math.max(r_peak ?? 0, g_peak ?? 0, b_peak ?? 0);

        const statsHtml = `<br><span style="font-size: 0.9rem; display: block; margin-top: 10px; opacity: 0.95; line-height: 1.6;">
            📊 <b>Итоговый χ² p-value при 100% пикселей</b> (Westfeld: высокий ≈ случайные LSB ≈ подозрение на стего):<br>
            🔴 R: итог = <b>${formatP(r_p)}</b>, пик на кривой = <b>${formatP(r_peak)}</b> (энтропия LSB: ${formatE(r_e)})<br>
            🟢 G: итог = <b>${formatP(g_p)}</b>, пик на кривой = <b>${formatP(g_peak)}</b> (энтропия LSB: ${formatE(g_e)})<br>
            🔵 B: итог = <b>${formatP(b_p)}</b>, пик на кривой = <b>${formatP(b_peak)}</b> (энтропия LSB: ${formatE(b_e)})<br>
            🌐 <b>Итог по каналам:</b> средний = <b>${formatP(avgP)}</b>, макс. итог = <b>${formatP(maxP)}</b>, макс. пик кривой = <b>${formatP(curvePeak)}</b><br>
            <span style="opacity: 0.85;">График ниже — прогрессивный скан (слева мало пикселей, справа 100%). Вердикт смотрит только на правый край (итог).</span>
        </span>`;

        if (data.verdict === 'detected') {
            verdictBox.classList.add('detected');
            verdictIcon.innerText = '⚠️';
            verdictTitle.innerText = 'Обнаружено скрытое сообщение!';
            verdictDesc.innerHTML = 'Итоговый χ² p-value высокий: LSB-плоскость выглядит псевдослучайной (типичный признак внедрения). Макс. энтропия LSB: ' + formatE(maxEntropy) + '.' + statsHtml;
        } else if (data.verdict === 'anomaly') {
            verdictBox.classList.add('anomaly');
            verdictIcon.innerText = '⚠️';
            verdictTitle.innerText = 'Незначительные аномалии / Подозрение на стего';
            verdictDesc.innerHTML = 'Итоговый χ² p-value повышен относительно естественного изображения. Возможны частичное внедрение или сильная постобработка. Макс. энтропия LSB: ' + formatE(maxEntropy) + '.' + statsHtml;
        } else {
            verdictBox.classList.add('clean');
            verdictIcon.innerText = '🛡️';
            verdictTitle.innerText = 'Внедрение не обнаружено';
            verdictDesc.innerHTML = 'Итоговый χ² p-value низкий: пары значений PoV выглядят естественно структурированными (не как после LSB-embedding). Макс. энтропия LSB: ' + formatE(maxEntropy) + '.' + statsHtml;
        }

        // Draw / Update Chart
        const ctx = document.getElementById('stego-chart').getContext('2d');
        if (stegoChartInstance) {
            stegoChartInstance.destroy();
        }

        const labels = Array.from({length: data.results.red.p_values.length}, (_, i) => `${Math.round(((i + 1) / data.results.red.p_values.length) * 100)}%`);

        stegoChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: 'Красный канал (p-value)',
                        data: data.results.red.p_values,
                        borderColor: '#ff1744',
                        backgroundColor: 'rgba(255, 23, 68, 0.05)',
                        borderWidth: 2.5,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 1.5,
                        spanGaps: true
                    },
                    {
                        label: 'Зеленый канал (p-value)',
                        data: data.results.green.p_values,
                        borderColor: '#00e676',
                        backgroundColor: 'rgba(0, 230, 118, 0.05)',
                        borderWidth: 2.5,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 1.5,
                        spanGaps: true
                    },
                    {
                        label: 'Синий канал (p-value)',
                        data: data.results.blue.p_values,
                        borderColor: '#2979ff',
                        backgroundColor: 'rgba(41, 121, 255, 0.05)',
                        borderWidth: 2.5,
                        fill: false,
                        tension: 0.3,
                        pointRadius: 1.5,
                        spanGaps: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        labels: {
                            color: '#f0f4f8',
                            font: { family: 'Outfit', size: 11 }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#8aa1b9', font: { family: 'Outfit', size: 9 } },
                        title: { display: true, text: 'Прогресс скана → (вердикт = правый край / 100%)', color: '#f0f4f8', font: { family: 'Outfit', weight: 'bold', size: 11 } }
                    },
                    y: {
                        min: 0,
                        max: 1,
                        grid: { color: 'rgba(255, 255, 255, 0.05)' },
                        ticks: { color: '#8aa1b9', font: { family: 'Outfit', size: 9 } },
                        title: { display: true, text: 'χ² p-value (прогрессивно)', color: '#f0f4f8', font: { family: 'Outfit', weight: 'bold', size: 11 } }
                    }
                }
            }
        });

    } catch (err) {
        alert('Ошибка стегоанализа: ' + err.message);
    } finally {
        toggleLoader('steganalysis-submit-btn', 'steganalysis-loader', false);
    }
}
