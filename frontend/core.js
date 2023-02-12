
const API_URL = '/api';
let inputsContainer = document.getElementById('racer-inputs-container');
let racerContainer = document.getElementById('racer-container');
let raceGoOpt = document.getElementById('race-go-option');
let addMoreOpt = document.getElementById('add-more-option');
let recommendationsContainer = document.getElementById('recommendation-container');
let replayOption = document.getElementById('replay-option');
let resultsContainer = document.getElementById('results-container');
let starterForm = document.getElementById('starter-form');
let resetOption = document.getElementById('reset-option');

raceGoOpt.addEventListener('click', getBikes);
addMoreOpt.addEventListener('click', addInput);
resetOption.addEventListener('click', resetInputs);

function resetInputs() {
  inputsContainer.replaceChildren();
  addInput();
  addInput();
}

async function getBikes() {
  racerContainer.replaceChildren();
  resultsContainer.replaceChildren();
  var atleastOne = false;
  for (item of inputsContainer.children) {
    let make = item.children[0].value.trim();
    let model = item.children[1].value.trim();
    if (make.trim() && model.trim()) {
      let result = await fetch(`${API_URL}/racer?make=${make}&model=${model}`);
      let racer_data = await result.json();
      if (racer_data) {
        addRacer(racer_data);
        atleastOne = true;
      } else {
        reportFailedBike(make, model);
      }
    }
  }
  if (atleastOne) {
    starterForm.style.opacity = '0.2';
    initiateGo();
  }
}

function initiateGo() {
  let container = document.getElementById('lights-container');
  let lights = [
    document.getElementById('light-1'),
    document.getElementById('light-2'),
    document.getElementById('light-3'),
  ]
  for (light of lights) {
    light.style.backgroundColor = 'transparent';
  }
  let green = '#39ae86';
  container.style.display = 'block';
  setTimeout(function(){
    lights[0].style.backgroundColor = '#a31919';
  }, 1000);
  setTimeout(function(){
    lights[1].style.backgroundColor = '#da4820';
  }, 2000);
  setTimeout(function(){
    for (light of lights) {
      light.style.backgroundColor = green;
    }
  }, 3000);
  setTimeout(function(){
    container.style.display = 'none';
    go();
  }, 4000);
}

function reportFailedBike(make, model) {
    alert(`Failed to find ${make} ${model}`);
}

function addRacer(data) {
  let racerOutline = document.createElement('div');
  racerOutline.className = 'racer-outline';
  let racer = document.createElement('div');
  if (data.weight_type == 'dry') {
    data.weight = (parseInt(data.weight) + 20).toString();
  }
  racer.className = 'racer';
  racer.style = `background-image: url('/images/${data.style}_type.svg')`;
  racer.setAttribute('power', data.power);
  racer.setAttribute('torque', data.torque);
  racer.setAttribute('weight', data.weight);
  racer.id = data.full_name;

  let label = document.createElement('div');
  label.className = 'racer-label';
  label.innerHTML = data.full_name;
  racer.appendChild(label);
  racerOutline.appendChild(racer);
  racerContainer.appendChild(racerOutline);
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
    'keyup', async function() {await getRecommendations(makeIn, modelIn)}
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
    if (racerResults.length > 0) {
      recommendationsContainer.style.display = 'block';
      addRecommendations(modelIn, racerResults);
      return null;
    }
  }
  recommendationsContainer.style.display = 'none';
}

function addRecommendations(modelIn, racerResults) {
  recommendationsContainer.replaceChildren();
  for (racer of racerResults) {
    let row = document.createElement('div');
    row.innerHTML = `${racer.model} ${racer.year}`;
    row.className = 'recommendation-row';
    row.addEventListener('click', function(model) {
      return () => {
        modelIn.value = model;
        recommendationsContainer.replaceChildren();
        recommendationsContainer.style.display = 'none';
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
    as[racer.id] = torque / 25;
    ints[racer.id] = setInterval(function(racer, a, ptw){
      return () => {
        m = ((a) * as[racer.id]) + 1 + (ptw * 7);
        racer.style.marginLeft = parseInt(window.getComputedStyle(racer).marginLeft) + m + 'px';
        as[racer.id] += 0.01;
        if (parseInt(racer.style.marginLeft) > (window.innerWidth - 200)) {
          reportFinish(racer);
          clearInterval(ints[racer.id]);
          delete ints[racer.id];
        }
        if (Object.values(ints).length == 0) {
          raceGoOpt.innerHTML = 'Race Again!';
          starterForm.style.opacity = '1';
        }
      }
    }(racer, a, ptw), 40);
  }
}

function reportFinish(racer) {
  let row = document.createElement('div');
  row.className = 'result-row';
  let position = resultsContainer.children.length + 1;
  var posDisplay;
  switch (position) {
    case 1:
      posDisplay = '1st';
      break;
    case 2:
      posDisplay = '2nd';
      break;
    case 3:
      posDisplay = '3rd';
      break;
    default:
      posDisplay = position.toString() + 'th';
  }
  row.innerHTML = `${posDisplay} - ${racer.id}`;
  resultsContainer.appendChild(row);
}


function run() {
  addInput();
  addInput();
}

run();
