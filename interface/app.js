const form = document.querySelector("#predictionForm");
const endpointUrl = document.querySelector("#endpointUrl");
const predictionCell = document.querySelector("#predictionCell");
const statusCell = document.querySelector("#statusCell");
const payloadPreview = document.querySelector("#payloadPreview");
const loadExample = document.querySelector("#loadExample");

const example = {
  id: 7129300520,
  date: "20141013T000000",
  bedrooms: 3,
  bathrooms: 1,
  sqft_living: 1180,
  sqft_lot: 5650,
  floors: 1,
  waterfront: 0,
  view: 0,
  condition: 3,
  grade: 7,
  sqft_above: 1180,
  sqft_basement: 0,
  yr_built: 1955,
  yr_renovated: 0,
  zipcode: 98178,
  lat: 47.5112,
  long: -122.257,
  sqft_living15: 1340,
  sqft_lot15: 5650,
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function setStatus(message) {
  statusCell.textContent = message;
}

function readPayload() {
  const formData = new FormData(form);
  const instance = { ...example };

  for (const [key, value] of formData.entries()) {
    instance[key] = Number(value);
  }

  return { instances: [instance] };
}

function fillExample() {
  for (const [key, value] of Object.entries(example)) {
    const input = form.elements[key];
    if (input) input.value = value;
  }
  const payload = readPayload();
  payloadPreview.textContent = JSON.stringify(payload, null, 2);
  predictionCell.textContent = "-";
  setStatus("Ejemplo cargado");
}

async function submitPrediction(event) {
  event.preventDefault();

  const payload = readPayload();
  payloadPreview.textContent = JSON.stringify(payload, null, 2);
  predictionCell.textContent = "-";
  setStatus("Calculando...");

  try {
    const response = await fetch(endpointUrl.value, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    const prediction = data.predictions?.[0];
    if (typeof prediction !== "number") {
      throw new Error("La respuesta no contiene predictions[0].");
    }

    predictionCell.textContent = formatCurrency(prediction);
    setStatus("Prediccion generada");
  } catch (error) {
    setStatus(error.message);
  }
}

form.addEventListener("submit", submitPrediction);
loadExample.addEventListener("click", fillExample);
fillExample();
