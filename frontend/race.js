const API_URL = '/api';
let inputsContainer = document.getElementById('racer-inputs-container');
let racerContainer = document.getElementById('racer-container');
let raceGoOpt = document.getElementById('race-go-option');
let addMoreOpt = document.getElementById('add-more-option');
let recommendationsContainer = document.getElementById('recommendation-container');
let replayOption = document.getElementById('replay-option');
let resetOption = document.getElementById('reset-option');
let resultsContainer = document.getElementById('results-container');
let starterForm = document.getElementById('starter-form');
let lightsContainer = document.getElementById('lights-container');


class Racer {
  constructor(fullName, power, torque, weight, weightType, style, race) {

    this.power = parseInt(power);
    this.torque = parseInt(torque);
    this.weight = parseInt(weight);
    this.weightType = weightType;
    this.fullName = fullName;
    this.style = style;

    this.resolveWeight();

    this.race = race;
    this.finished = false;
    this.ptw = this.power / this.weight;
    this.acc = this.torque / this.weight;

    this.racerElement = document.createElement('div');
    this.racerElement.className = 'racer';
    this.racerElement.id = this.fullName;
    this.setImage();
    this.racerElement.setAttribute('power', this.power);
    this.racerElement.setAttribute('torque', this.torque);
    this.racerElement.setAttribute('weight', this.weight);
  }

  setImage() {
    this.racerElement.style = `background-image: url('/images/${this.style}_type.svg')`;
  }

  static async fromApi(make, model, race) {
    let result = await fetch(`${API_URL}/racer?make=${make}&model=${model}`);
    let racerData = await result.json();
    if (racerData) {
      return new Racer(
        racerData.full_name,
        racerData.power,
        racerData.torque,
        racerData.weight,
        racerData.weight_type,
        racerData.style,
        race,
      );
    }
  }

  render() {
    let label = document.createElement('div');
    label.className = 'racer-label';
    label.innerHTML = this.fullName;

    let racerOutline = document.createElement('div');
    racerOutline.className = 'racer-outline';

    this.racerElement.appendChild(label);
    racerOutline.appendChild(this.racerElement);
    racerContainer.appendChild(racerOutline);
  }

  resolveWeight() {
    if (this.weightType == 'dry') {
      this.weight = (parseInt(this.weight) + 20).toString();
    }
  }

  move() {
    this._progress = this.torque / 25;
    this._interval = setInterval(() => {
      var momentum = ((this.acc) * this._progress) + 1 + (this.ptw * 7);
      this.racerElement.style.marginLeft = parseInt(
        window.getComputedStyle(this.racerElement).marginLeft
      ) + momentum + 'px';
      this._progress  += 0.01;
      if (parseInt(this.racerElement.style.marginLeft) > (window.innerWidth - 200)) {
        this.finish();
        clearInterval(this._interval);
      }
    }, 40);
  }

  finish() {
    this.finished = true;
    this.race.checkFinished();
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
    row.innerHTML = `${posDisplay} - ${this.fullName}`;
    resultsContainer.appendChild(row);
  }
}


class Race {

  constructor() {
    this.racers = [];
  }

  reset() {
    racerContainer.replaceChildren();
    resultsContainer.replaceChildren();
  }

  async getRacers() {
    for (let item of inputsContainer.children) {
      let make = item.children[0].value.trim();
      let model = item.children[1].value.trim();
      if (make && model) {
        let racer = await Racer.fromApi(make, model, this);
        if (racer) {
          this.racers.push(racer);
        }
      }
    }
  }

  async race() {
    if (this.racers.length > 0) {
      starterForm.style.opacity = '0.2';
      this.reset();
      for (let racer of this.racers) {
        racer.render();
      }
      this.startLights();
      setTimeout(() => {
        for (let racer of this.racers) {
          racer.move();
        }
      }, 4000);
    }
  }

  checkFinished() {
      var finished = 0;
      for (let racer of this.racers) {
        if (racer.finished) {
          finished ++;
        }
      }
      if (finished == this.racers.length) {
        this.finish();
      }
  }

  startLights() {
    let lights = [
      document.getElementById('light-1'),
      document.getElementById('light-2'),
      document.getElementById('light-3'),
    ]
    for (let light of lights) {
      light.style.backgroundColor = 'transparent';
    }
    let green = '#39ae86';
    lightsContainer.style.display = 'block';
    setTimeout(function(){
      lights[0].style.backgroundColor = '#a31919';
    }, 1000);
    setTimeout(function(){
      lights[1].style.backgroundColor = '#da4820';
    }, 2000);
    setTimeout(function(){
      for (let light of lights) {
        light.style.backgroundColor = green;
      }
    }, 3000);
    setTimeout(function(){
      lightsContainer.style.display = 'none';
    }, 4000);
  }

  finish() {
    raceGoOpt.innerHTML = 'Race Again!';
    starterForm.style.opacity = '1';
  }
}


class RacerRecommender {

  constructor(makeIn, modelIn) {
    this.makeIn = makeIn;
    this.modelIn = modelIn;
  }

  async get() {
    let make = this.makeIn.value.trim();
    let model = this.modelIn.value.trim();
    if (make && model && model.length > 1) {
      let result = await fetch(`${API_URL}/search?make=${make}&model=${model}`);
      let racerResults = await result.json();
      if (racerResults.length > 0) {
        recommendationsContainer.style.display = 'block';
        this.addRecommendations(racerResults);
        return;
      }
    }
    recommendationsContainer.style.display = 'none';
  }

  addRecommendations(racerResults) {
    recommendationsContainer.replaceChildren();
    for (let racer of racerResults) {
      let row = document.createElement('div');
      row.innerHTML = `${racer.model} ${racer.year}`;
      row.className = 'recommendation-row';
      row.addEventListener('click', () => this.selectRecommendation(racer.model));
      recommendationsContainer.appendChild(row);
    }
  }

  selectRecommendation(model) {
    this.modelIn.value = model;
    recommendationsContainer.replaceChildren();
    recommendationsContainer.style.display = 'none';
  }
}


class RacingPage {

  constructor() {
    this.addEventListeners();
    this.renderInputs();
  }

  addEventListeners() {
    raceGoOpt.addEventListener('click', this.runRace);
    addMoreOpt.addEventListener('click', this.addInput);
    resetOption.addEventListener('click', () => this.resetInputs());
  }

  addInput() {
    let container = document.createElement('div');
    container.className = 'racer-input-row';

    let makeIn = document.createElement('input');
    makeIn.placeholder = "Make...";
    container.appendChild(makeIn);

    let modelIn = document.createElement('input');
    modelIn.placeholder = "Model...";

    let recommender = new RacerRecommender(makeIn, modelIn);
    modelIn.addEventListener('keyup', () => recommender.get())

    container.appendChild(modelIn);
    inputsContainer.appendChild(container);
  }

  renderInputs() {
    this.addInput();
    this.addInput();
  }

  resetInputs() {
    inputsContainer.replaceChildren();
    this.renderInputs();
  }

  async runRace() {
    let race = new Race();
    await race.getRacers();
    race.race();
  }
}
