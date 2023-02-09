
const API_URL = '/api';
let inputsContainer = document.getElementById('racer-inputs-container');
let racerContainer = document.getElementById('racer-container');
let raceStartOpt = document.getElementById('race-start-option');
let addMoreOpt = document.getElementById('add-more-option');
let recommendationsContainer = document.getElementById('recommendation-container');

raceStartOpt.addEventListener('click', getBikes);
addMoreOpt.addEventListener('click', addInput);

async function getBikes() {
  for (item of inputsContainer.children) {
    let make = item.children[0].value;
    let model = item.children[1].value;
    let result = await fetch(`${API_URL}/racer?make=${make}&model=${model}`);
    let racer_data = await result.json();
    if (racer_data) {
      addRacer(racer_data);
    } else {
      reportFailedBike(make, model);
    }
  }
}

function getBikesTest() {
  let testData = [["Indian FTR", "120", "120", "233"], ["Triumph Triple", "120", "79", "188"]]
  for (item of testData) {
    addRacer(item);
  }
}

function reportFailedBike(make, model) {
    alert(`Failed to find ${make} ${model}`);
}

function addRacer(data) {
  let racer = document.createElement('div');
  racer.className = 'racer';
  racer.setAttribute('power', data.power);
  racer.setAttribute('torque', data.torque);
  racer.setAttribute('weight', data.weight);
  racer.id = data.full_name;

  let label = document.createElement('div');
  label.className = 'racer-label';
  label.innerHTML = data.full_name;
  racer.appendChild(label);
  racerContainer.appendChild(racer);
}

function addInput() {
  let container = document.createElement('div');
  container.className = 'racer-input-row';

  let makeIn = document.createElement('input');
  makeIn.placeholder = "Make...";
  container.appendChild(makeIn);

  let modelIn = document.createElement('input');
  modelIn.placeholder = "Model...";
  modelIn.addEventListener(
    'keydown', () => {getRecommendations(makeIn, modelIn)}
  );
  container.appendChild(modelIn);
  inputsContainer.appendChild(container);
}

async function getRecommendations(makeIn, modelIn) {
  let make = makeIn.value;
  let model = modelIn.value;
  if (make && model && model.length > 1) {
    let result = await fetch(`${API_URL}/search?make=${make}&model=${model}`);
    let racerResults = await result.json();
    addRecommendation(modelIn, racerResults);
  }

}

function addRecommendation(modelIn, racerResults) {
  recommendationsContainer.replaceChildren();
  for (racer of racerResults) {
    let row = document.createElement('div');
    row.innerHTML = racer.model;
    row.className = 'recommendation-row';
    row.addEventListener('click', function(model) {
      return () => {
        modelIn.value = model;
        recommendationsContainer.replaceChildren();
      };
    }(racer.model));
    recommendationsContainer.appendChild(row);
  }
}

function go() {
  let racers = document.getElementsByClassName('racer');
  var as = {};
  var ints = {};
  for (racer of racers) {
    var power = parseInt(racer.getAttribute('power'));
    let weight = racer.getAttribute('weight');
    var torque = parseInt(racer.getAttribute('torque'));

    let ptw = parseInt(power) / parseInt(weight);
    let a = parseInt(torque) / parseInt(weight);
    as[racer.id] = torque / 15;
    ints[racer.id] = setInterval(function(racer, a, ptw){
      return () => {
        m = ((a) * as[racer.id]) + 1 + (ptw * 7);
        racer.style.marginLeft = parseInt(window.getComputedStyle(racer).marginLeft) + m + 'px';
        as[racer.id] += 0.01;
        console.log(parseInt(racer.style.marginLeft));
        if (parseInt(racer.style.marginLeft) > 1000) {
          clearInterval(ints[racer.id]);
        }
      }
    }(racer, a, ptw), 40);
  }
}


function run() {
  addInput();
  addInput();
}

run();
