const RACING_API_URL = '/api/racing';

const inputsContainer = document.getElementById('racer-inputs-container');
const racerContainer = document.getElementById('racer-container');
const raceGoOpt = document.getElementById('race-go-option');
const raceShareOpt = document.getElementById('link-share-opt');
const addMoreOpt = document.getElementById('add-more-option');
const recommendationsContainer = document.getElementById('recommendation-container');
const replayOption = document.getElementById('replay-option');
const resetOption = document.getElementById('reset-option');
const resultsContainer = document.getElementById('results-container');
const starterForm = document.getElementById('starter-form');
const lightsContainer = document.getElementById('lights-container');
const controlPanel = document.getElementById('control-panel');
const fbShareOpt = document.getElementById('fb-share-opt');
const resultsWindow = document.getElementById('results-window');


class Racer {
  constructor(
    modelId,
    name,
    fullName,
    makeName,
    style,
    year,
    power,
    torque,
    weight,
    weightType,
    race,
  ) {
    this.modelId = modelId;
    this.name = name;
    this.fullName = fullName;
    this.makeName = makeName;
    this.style = style;
    this.year = year;
    this.power = parseInt(power);
    this.torque = parseInt(torque);
    this.weight = parseInt(weight);
    this.weightType = weightType;
    this.race = race;

    this.resolveWeight();
    this.raceId = null;
    this.ptw = this.power / this.weight;
    this.acc = this.torque / this.weight;


    this.logData();
  }

  logData() {
    console.log(`${this.fullName}:`);
    console.log(`   ID: ${this.modelId}`);
    console.log(`   makeName: ${this.makeName}`);
    console.log(`   power: ${this.power}`);
    console.log(`   torque: ${this.torque}`);
    console.log(`   weight: ${this.weight}`);
    console.log(`   weight_type: ${this.weightType}`);
    console.log(`   style: ${this.style}`);
    console.log(`   year: ${this.year}`);
  }

  setImage() {
    this.racerElement.style = (
      `background-image: url('/static/images/${this.style}_type_white.svg')`
    );
  }

  static async fromApi(make, model, year, race) {
    let data = await _get(
      `${RACING_API_URL}?make=${make}&model=${model}&year=${year}`
    );
    if (data) return Racer.fromData(data, race);
  }

  static fromData(data, race) {
    return new Racer(
      data.model_id,
      data.name,
      data.full_name,
      data.make_name,
      data.style,
      data.year,
      data.power,
      data.torque,
      data.weight,
      data.weight_type,
      race,
    );
  }

  render() {
    this.racerElement = _el(
      'div', {className: 'racer', id: this.fullName}
    );
    this.label = _el(
      'div', {className: 'racer-label', innerHTML: this.fullName}
    )
    this.racerOutline = _el(
      'div', {className: 'racer-outline'}
    );
    this.setImage();
    this.racerElement.appendChild(this.label);
    this.racerOutline.appendChild(this.racerElement);
    racerContainer.appendChild(this.racerOutline);
  }

  resolveWeight() {
    if (this.weightType == 'dry') {
      this.weight = (parseInt(this.weight) + 20).toString();
    }
  }

  move() {
    this._finished = false;
    this._progress = this.torque / 25;
    this._interval = setInterval(() => {
      let momentum = ((this.acc) * this._progress) + 1 + (this.ptw * 7);
      this.racerElement.style.marginLeft = parseInt(
        window.getComputedStyle(this.racerElement).marginLeft
      ) + momentum + 'px';
      this._progress  += 0.01;
      if (
        parseInt(this.racerElement.style.marginLeft)
        > (window.innerWidth - 200)
      ) {
        this.finish();
        clearInterval(this._interval);
      }
    }, 40);
  }

  getStatsString() {
    var weightType = 'wet';
    if (this.weightType == 'dry') weightType = 'adjusted to wet';
    return `
      <b>Power:</b> ${this.power} hp<br>
      <b>Torque:</b> ${this.torque} Nm<br>
      <b>Weight (${weightType}):</b> ${this.weight} kg
    `
  }

  finish() {
    this._finished = true;
    this.race.checkFinished();

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
    let resultContainer = _el('div', {className: 'result-container'});
    let posText = _el('div', {innerHTML: posDisplay, className: 'pos-text'});
    let racerNameText = _el('div', {
      className: 'result-heading',
      innerHTML: this.fullName,
    });
    let statsContainer = _el(
      'div', {innerHTML: this.getStatsString(), className: 'stats-container'}
    );
    resultContainer.appendChild(posText);
    resultContainer.appendChild(racerNameText);
    resultContainer.appendChild(statsContainer);
    resultsContainer.appendChild(resultContainer);
  }
}


class Race {

  constructor() {
    this.racers = [];
    this.unseenRace = false;
  }

  reset() {
    racerContainer.replaceChildren();
    resultsContainer.replaceChildren();
  }

  async setRacersFromForm() {
    for (let item of inputsContainer.children) {
      let make = item.children[0].value.trim();
      let model = item.children[1].value.trim();
      let year = item.children[2].value.trim();
      if (make && model && year) {
        let racer = await Racer.fromApi(make, model, year, this);
        if (racer) this.racers.push(racer);
      }
    };
  }

  async setRacersFromRaceId(raceId) {
    let result = await _get(`${RACING_API_URL}/race?race_id=${raceId}`);
    result.racers.forEach((racer) => this.racers.push(
      Racer.fromData(racer, this)
    ));
    this.raceId = result.race_id;
  }

  async race(save) {
    if (this.racers.length == 0) return;
    if (save) {
      this.unseenRace = true;
      await this.save();
    }
    if(
      this.racers.length > 4
      || window.matchMedia('(max-width: 1200px)').matches
    ) {
      _hide(controlPanel);
    }
    this.reset();
    this.startLights();
    this.racers.forEach((racer) => racer.render());
    setTimeout(() => this.racers.forEach((racer) => racer.move()), 4000);
  }

  async save() {
      let modelIds = this.racers.map((racer) => racer.modelId);
      let data = await _post(`${RACING_API_URL}/save`, {'model_ids': modelIds});
      this.raceId = data.race_id;
  }

  getShareLink() {
    return `${window.location.host}/r/${this.raceId}`;
  }

  shareLink() {
    let shareLink = this.getShareLink();
    navigator.clipboard.writeText(shareLink);
    raceShareOpt.innerHTML = shareLink + ' copied &#10003;';
    raceShareOpt.classList.add('shared-link');
    setTimeout(this.setShare, 3000);
  }

  setShare() {
    raceShareOpt.innerHTML = '&#x2704; Share Race URL';
    raceShareOpt.classList.remove('shared-link');
    fbShareOpt.setAttribute(
      'onclick',
      `window.open('https://www.facebook.com/sharer/sharer.php?u='+
      encodeURIComponent('${this.getShareLink()}'),
      'facebook-share-dialog',
      'width=626,height=436');
      return false;`
    );
  }

  checkFinished() {
      let finished = this.racers.every((racer) => racer._finished);
      if (finished) this.finish();
  }

  startLights() {
    let green = '#39ae86';
    let red = '#a31919';
    let orange = '#da4820';
    let lights = [
      document.getElementById('light-1'),
      document.getElementById('light-2'),
      document.getElementById('light-3'),
    ]
    lights.forEach((light) => light.style.backgroundColor = 'transparent');
    _show(lightsContainer);
    setTimeout(() => lights[0].style.backgroundColor = red, 1000);
    setTimeout(() => lights[1].style.backgroundColor = orange, 2000);
    setTimeout(() => {
      lights[0].style.backgroundColor = green;
      lights[1].style.backgroundColor = green;
      lights[2].style.backgroundColor = green;
    }, 3000);
    setTimeout(() => _hide(lightsContainer), 4000);
  }

  finish() {
    raceGoOpt.innerHTML = 'Race Again!';
    _show(controlPanel);
    _show(resultsWindow);
    this.setShare();
  }
}


class RacerRecommender {

  constructor(makeIn, modelIn, yearIn) {
    this.makeIn = makeIn;
    this.modelIn = modelIn;
    this.yearIn = yearIn;
  }

  async get() {
    let make = this.makeIn.value.trim();
    let model = this.modelIn.value.trim();
    let year = this.yearIn.value.trim();
    if (make) {
      let results = await _get(
        `${RACING_API_URL}/search?make=${make}&model=${model}&year=${year}`
      );
      if (results.length > 0) {
        _show(recommendationsContainer);
        this.addRecommendations(results);
        return;
      }
    }
    _hide(recommendationsContainer);
  }

  addRecommendations(racerResults) {
    recommendationsContainer.replaceChildren();
    racerResults.forEach((racer) => {
      let row = _el(
        'div', {
          className: 'recommendation-row',
          innerHTML: `${racer.name} ${racer.year}`
        }
      );
      row.addEventListener('click', () => this.selectRecommendation(racer.name, racer.year));
      recommendationsContainer.appendChild(row);
    });
  }

  selectRecommendation(name, year) {
    this.modelIn.value = name;
    this.yearIn.value = year;
    recommendationsContainer.replaceChildren();
    _hide(recommendationsContainer);
  }
}


class RacingPage {

  constructor() {
    this.addEventListeners();
    this.renderInputs();
    this.inputState = this.getInputState();
    this.race = null;
  }

  addEventListeners() {
    raceGoOpt.addEventListener('click', () => this.runRace());
    addMoreOpt.addEventListener('click', () => this.addInput());
    raceShareOpt.addEventListener('click', () => this.share());
    resetOption.addEventListener('click', () => this.resetInputs());
    controlPanel.addEventListener('click', (evt) => {
      if (evt.target == controlPanel) _hide(recommendationsContainer);
    });
  }

  share() {
    if (this.race && this.race.raceId && this.race.racers.length > 0) {
      this.race.shareLink();
    }
  }

  addInput(make=null, model=null, year=null) {
    let container = _el('div', {className: 'racer-input-row'});
    let makeIn = _el('input', {placeholder: 'Make...'});
    let modelIn = _el('input', {placeholder: 'Model...'});
    let yearIn = _el('input', {placeholder: 'Year...'});

    let recommender = new RacerRecommender(makeIn, modelIn, yearIn);
    modelIn.addEventListener('keyup', () => recommender.get())
    modelIn.addEventListener('focus', () => recommender.get())

    if (make && model && year) {
      makeIn.value = make;
      modelIn.value = model;
      yearIn.value = year;
    }

    container.appendChild(makeIn);
    container.appendChild(modelIn);
    container.appendChild(yearIn);
    inputsContainer.appendChild(container);
  }

  renderInputs() {
    this.addInput();
    this.addInput();
  }

  resetInputs(add=true) {
    inputsContainer.replaceChildren();
    if (add) this.renderInputs();
  }

  setInputsFromRace() {
    this.resetInputs(false);
    this.race.racers.forEach(
      (racer) => this.addInput(racer.makeName, racer.name, racer.year)
    );
  }

  getInputState() {
    var state = "";
    for (let item of inputsContainer.children) {
      let make = item.children[0].value.trim();
      let model = item.children[1].value.trim();
      let year = item.children[2].value.trim();
      state += `${make} ${model} ${year}`;
    }
    return state;
  }

  async runRace(raceId=null) {
    var save = false;
    if (this.inputState !== this.getInputState()) {
      // changed / new - load and save
      save = true;
      this.race = new Race();
      await this.race.setRacersFromForm();
    } else if (raceId) {
      // first visit shared - don't save, but load
      this.race = new Race();
      await this.race.setRacersFromRaceId(raceId);
      await this.setInputsFromRace();
    } else {
      // Unchanged / replay - don't save
    }
    this.inputState = this.getInputState();
    await this.race.race(save);
  }

  async checkSharedRace() {
    let sharedUrlMatch = window.location.pathname.match("/r/\([0-9]+)/?$");
    if (sharedUrlMatch) {
      let raceId = parseInt(sharedUrlMatch[1]);
      await this.runRace(raceId);
    }
  }
}

