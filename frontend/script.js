// Steps
const steps = [document.getElementById('step1'), document.getElementById('step2'), document.getElementById('step3'), document.getElementById('step4')];
let currentStep = 0;

function showStep(step) {
    steps.forEach((s, i) => {
        s.classList.toggle('hidden', i !== step);
    });
    currentStep = step;
}

document.getElementById('next1').addEventListener('click', () => showStep(1));
document.getElementById('prev2').addEventListener('click', () => showStep(0));
document.getElementById('next2').addEventListener('click', () => showStep(2));
document.getElementById('prev3').addEventListener('click', () => showStep(1));
document.getElementById('next3').addEventListener('click', () => showStep(3));
document.getElementById('prev4').addEventListener('click', () => showStep(2));

// Suggest Colors
document.getElementById('suggestColors').addEventListener('click', async () => {
    const industry = document.getElementById('industry').value;
    if (!industry) return alert("Select an industry first");

    try {
        const response = await fetch('http://localhost:8000/suggest-colors', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ industry })
        });
        const data = await response.json();
        if (data.colors) {
            document.getElementById('color1').value = data.colors[0] || '#ff0000';
            document.getElementById('color2').value = data.colors[1] || '#00ff00';
            document.getElementById('color3').value = data.colors[2] || '#0000ff';
            document.getElementById('color4').value = data.colors[3] || '#ffff00';
        } else {
            alert("Error: " + data.error);
        }
    } catch (error) {
        alert("Error contacting server");
    }
});

// Font Preview
const primaryFont = document.getElementById('primaryFont');
const secondaryFont = document.getElementById('secondaryFont');
const previewText = document.getElementById('previewText');

function updatePreview() {
    previewText.style.fontFamily = primaryFont.value + ', sans-serif';
}

primaryFont.addEventListener('change', updatePreview);
secondaryFont.addEventListener('change', updatePreview);
updatePreview(); // initial

// Generate Kit
document.getElementById('generateBtn').addEventListener('click', async () => {
    const brandName = document.getElementById('brandName').value;
    const industry = document.getElementById('industry').value;
    const description = document.getElementById('description').value;
    const colorPalette = [
        document.getElementById('color1').value,
        document.getElementById('color2').value,
        document.getElementById('color3').value,
        document.getElementById('color4').value
    ];
    const fonts = [primaryFont.value, secondaryFont.value];
    const formats = Array.from(document.querySelectorAll('#formats input:checked')).map(cb => cb.value);
    const tagline = document.getElementById('tagline').value;
    const ctaText = document.getElementById('ctaText').value;
    const language = document.getElementById('language').value;

    if (!brandName || !industry || !formats.length || !tagline || !ctaText) return alert("Fill all required fields");

    document.getElementById('generateBtn').disabled = true;
    document.getElementById('loader').classList.remove('hidden');
    document.getElementById('results').classList.add('hidden');

    try {
        const response = await fetch('http://localhost:8000/generate-kit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                brand_name: brandName,
                industry,
                description,
                color_palette: colorPalette,
                fonts,
                formats,
                tagline,
                cta_text: ctaText,
                language
            })
        });
        const data = await response.json();
        if (data.images) {
            const imagesDiv = document.getElementById('images');
            imagesDiv.innerHTML = '';
            for (const [fmt, img] of Object.entries(data.images)) {
                const div = document.createElement('div');
                div.className = 'image-item';
                div.innerHTML = `<h3>${fmt}</h3><img src="data:image/png;base64,${img}" alt="${fmt}">`;
                imagesDiv.appendChild(div);
            }
            document.getElementById('results').classList.remove('hidden');
        } else {
            alert("Error: " + data.error);
        }
    } catch (error) {
        alert("Error contacting server");
    } finally {
        document.getElementById('generateBtn').disabled = false;
        document.getElementById('loader').classList.add('hidden');
    }
});