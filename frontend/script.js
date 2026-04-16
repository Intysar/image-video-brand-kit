const generateBtn = document.getElementById('generateBtn');
const promptInput = document.getElementById('promptInput');
const resultImage = document.getElementById('resultImage');

generateBtn.addEventListener('click', async () => {
    const prompt = promptInput.value;
    if (!prompt) return alert("Entrez une idée !");

    generateBtn.innerText = "IA en cours de création...";
    generateBtn.disabled = true;
    resultImage.classList.add('hidden');

    try {
        const response = await fetch('http://localhost:8000/generate-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();

        if (data.image) {
            // On affiche l'image base64
            resultImage.src = `data:image/png;base64,${data.image}`;
            resultImage.classList.remove('hidden');
        } else {
            alert("Erreur : " + data.error);
        }
    } catch (error) {
        alert("Impossible de contacter le serveur.");
    } finally {
        generateBtn.innerText = "Générer Image";
        generateBtn.disabled = false;
    }
});