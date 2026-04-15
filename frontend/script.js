async function generateImage() {
    const prompt = document.getElementById("prompt").value;
    const loader = document.getElementById("loader");
    const result = document.getElementById("result");

    loader.classList.remove("hidden");
    result.src = "";

    const res = await fetch("http://127.0.0.1:8000/generate", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ prompt })
    });

    const data = await res.json();

    loader.classList.add("hidden");
    result.src = data.image;
}