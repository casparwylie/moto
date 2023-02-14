const API_URL = '/api/racing';

const inputsContainer = document.getElementById('racer-inputs-container');
const racerContainer = document.getElementById('racer-container');
const raceGoOpt = document.getElementById('race-go-option');
const raceShareOpt = document.getElementById('race-share-option');
const addMoreOpt = document.getElementById('add-more-option');
const recommendationsContainer = document.getElementById('recommendation-container');
const replayOption = document.getElementById('replay-option');
const resetOption = document.getElementById('reset-option');
const resultsContainer = document.getElementById('results-container');
const starterForm = document.getElementById('starter-form');
const lightsContainer = document.getElementById('lights-container');


class Racer {
  constructor(
    modelId,
    fullName,
    power,
    torque,
    weight,
    weightType,
    style,
    year,
    race,
  ) {
    this.modelId = modelId;
    this.power = parseInt(power);
    this.torque = parseInt(torque);
    this.weight = parseInt(weight);
    this.weightType = weightType;
    this.fullName = fullName;
    this.style = style;
    this.year = year;
    this.race = race;

    this.raceId = null;
    this.finished = false;
    this.ptw = this.power / this.weight;
    this.acc = this.torque / this.weight;


    this.resolveWeight();
    this.logData();
  }

  logData() {
    console.log(`${this.fullName}:`);
    console.log(`   ID: ${this.modelId}`);
    console.log(`   power: ${this.power}`);
    console.log(`   torque: ${this.torque}`);
    console.log(`   weight: ${this.weight}`);
    console.log(`   weight_type: ${this.weightType}`);
    console.log(`   style: ${this.style}`);
    console.log(`   year: ${this.year}`);
  }

  setImage() {
    this.racerElement.style = `background-image: url('/static/images/${this.style}_type.svg')`;
  }

  static async fromApi(make, model, race) {
    let result = await fetch(`${API_URL}?make=${make}&model=${model}`);
    let racerData = await result.json();
    if (racerData) {
      return Racer.fromData(racerData, race);
    }
  }

  static fromData(data, race) {
    return new Racer(
      data.model_id,
      data.full_name,
      data.power,
      data.torque,
      data.weight,
      data.weight_type,
      data.style,
      data.year,
      race,
    );
  }

  render() {
    this.racerElement = document.createElement('div');
    this.racerElement.className = 'racer';
    this.racerElement.id = this.fullName;
    this.setImage();
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
    this.unseenRace = true;
  }

  reset() {
    racerContainer.replaceChildren();
    resultsContainer.replaceChildren();
  }

  async setRacersFromForm() {
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

  async setRacersFromRaceId(raceId) {
    this.unseenRace = false;
    let result = await fetch(`${API_URL}/race?race_id=${raceId}`);
    let racerData = await result.json();
    for (let racer of racerData) {
      this.racers.push(Racer.fromData(racer, this));
    }
  }

  async race(save=true) {
    if (this.racers.length > 0) {
      if (save) {
        await this.save();
      }
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

  async save() {
      var modelIds = [];
      for (let racer of this.racers) {
        modelIds.push(racer.modelId);
      }
      let response = await fetch(`${API_URL}/save`,
        {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({'model_ids': modelIds}),
        }
      );
      let data = await response.json();
      this.raceId = data.race_id;
  }

  share() {
    alert(this.raceId);
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
    if (this.unseenRace) {
      raceShareOpt.style.display = 'block';
    }
    starterForm.style.opacity = '1';
  }
}


class RacerRecommender {

  constructor(makeIn, modelIn) {
    this.makeIn = makeIn;
    this.modelIn = modelIn;
  }

  async get() {
    raceShareOpt.style.display = 'none';
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
    this.race = null;
  }

  addEventListeners() {
    raceGoOpt.addEventListener('click', () => this.runRace());
    addMoreOpt.addEventListener('click', () => this.addInput());
    raceShareOpt.addEventListener('click', () => this.share());
    resetOption.addEventListener('click', () => this.resetInputs());
  }

  share() {
    if (this.race && this.race.raceId && this.race.racers.length > 0) {
      this.race.share();
    }
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
    raceShareOpt.style.display = 'none';
    inputsContainer.replaceChildren();
    this.renderInputs();
  }

  async raceChanged() {
    let dummyRace = new Race();
    await dummyRace.setRacersFromForm();
    if (dummyRace.racers.length == 0) {
      return false;
    }
    if (dummyRace.racers.length != this.race.racers.length) {
      return true;
    }
    for (let i in dummyRace.racers) {
      if (dummyRace.racers[i].modelId != this.race.racers[i].modelId) {
        return true;
      }
    }
    return false;
  }

  async runRace(raceId = null) {
    if (!this.race || await this.raceChanged()) {
      await this.runNewRace(raceId);
    } else {
      await this.race.race(false);
    }
  }

  async runNewRace(raceId = null) {
    this.race = new Race();
    if (raceId) {
      await this.race.setRacersFromRaceId(raceId);
      await this.race.race(false);
    } else {
      await this.race.setRacersFromForm();
      await this.race.race(true);
    }
  }

  async checkSharedRace() {
    let sharedUrlMatch = window.location.pathname.match("/r/\([0-9]+)/?$");
    if (sharedUrlMatch) {
      let raceId = parseInt(sharedUrlMatch[1]);
      await this.runRace(raceId);
    }
  }
}

