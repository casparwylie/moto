const RACING_API_URL = '/api/racing';

const inputsContainer = document.getElementById('racer-inputs-container');
const racerContainer = document.getElementById('racer-container');
const raceGoOpt = document.getElementById('race-go-option');
const raceGoSkipOpt = document.getElementById('race-go-skip-option');
const raceShareOpt = document.getElementById('link-share-opt');
const addMoreOpt = document.getElementById('add-more-option');
const recommendationsContainer = document.getElementById('racer-recommender');
const replayOption = document.getElementById('replay-option');
const resetOption = document.getElementById('reset-option');
const resultsContainer = document.getElementById('results-container');
const starterForm = document.getElementById('starter-form');
const lightsContainer = document.getElementById('lights-container');
const controlPanel = document.getElementById('control-panel');
const menu = document.getElementById('menu');
const fbShareOpt = document.getElementById('fb-share-opt');
const resultsWindow = document.getElementById('results-window');

const raceUpvotes = document.getElementById('race-upvotes');
const raceDownvotes = document.getElementById('race-downvotes');
const upvoteRaceOpt = document.getElementById('upvote-result-opt');
const downvoteRaceOpt = document.getElementById('downvote-result-opt');


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
    this.ptw = this.power / this.weight / 5;
    this.acc = this.torque / this.weight / 5;


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
      `${RACING_API_URL}/racer?make=${make}&model=${model}&year=${year}`
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

  async move(speed) {
    this._finished = false;
    this._progress = this.torque / 25;
    this._interval = setInterval(() => {
      let momentum = ((this.acc) * this._progress) + 1 + (this.ptw * this._progress);
      this.racerElement.style.marginLeft = parseInt(
        window.getComputedStyle(this.racerElement).marginLeft
      ) + momentum + 'px';
      this._progress  += 0.3;
      if (
        parseInt(this.racerElement.style.marginLeft)
        > (window.innerWidth * 0.9)
      ) {
        this.finish();
        clearInterval(this._interval);
      }
    }, speed);
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

  async finish() {
    this._finished = true;
    await this.race.checkFinished();

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
    this.raceUniqueId = result.race_unique_id;
  }

  async race(save, skip) {
    if (this.racers.length == 0) return;
    var speed = 40;
    if (save) {
      await this.save();
    }
    if(
      this.racers.length > 4
      || window.matchMedia('(max-width: 1200px)').matches
    ) {
      _hide(controlPanel);
      _hide(menu);
    }
    this.reset();
    var startDelay = 4000;
    if (skip) {
      startDelay = 0;
      speed = 0;
    } else {
      this.startLights();
    }
    _hide(raceGoOpt);
    _hide(raceGoSkipOpt);
    this.racers.forEach((racer) => racer.render());
    setTimeout(() => this.racers.forEach(
      (racer) => racer.move(speed)), startDelay
    );
  }

  async save() {
      let modelIds = this.racers.map((racer) => racer.modelId);
      let data = await _post(`${RACING_API_URL}/race/save`, {'model_ids': modelIds});
      this.raceId = data.race_id;
      this.raceUniqueId = data.race_unique_id;
      await userState.refresh();
  }

  getShareLink() {
    return `${window.location.host}/r/${this.raceId}`;
  }

  shareLink() {
    let shareLink = this.getShareLink();
    navigator.clipboard.writeText(shareLink);
    Informer.inform('Copied sharable URL!', 'good')
  }

  setShare() {
    fbShareOpt.setAttribute(
      'onclick',
      `window.open('https://www.facebook.com/sharer/sharer.php?u='+
      encodeURIComponent('${this.getShareLink()}'),
      'facebook-share-dialog',
      'width=626,height=436');
      return false;`
    );
  }

  async vote(vote) {
    let result = await _post(
      `${RACING_API_URL}/race/vote`, {race_unique_id: this.raceUniqueId, vote: vote}
    );
    if (result.success) {
      Informer.inform('Successfully voted', 'good');
    } else if (result._status_code == 403) {
      Informer.inform('You must have an account to vote.', 'bad');
    }
    await this.setVotes();
  }

  async setVotes() {
    let result = await _get(
      `${RACING_API_URL}/race/votes?race_unique_id=${this.raceUniqueId}`
    );
    let alreadyVoted = await _get(
      `${RACING_API_URL}/race/vote/voted?race_unique_id=${this.raceUniqueId}`
    );

    raceUpvotes.innerHTML = result.upvotes;
    raceDownvotes.innerHTML = result.downvotes;

    if (alreadyVoted.voted) {
      downvoteRaceOpt.classList.add('disabled-vote-opt');
      upvoteRaceOpt.classList.add('disabled-vote-opt');
    } else {
      downvoteRaceOpt.classList.remove('disabled-vote-opt');
      upvoteRaceOpt.classList.remove('disabled-vote-opt');
    }
  }

  async checkFinished() {
      let finished = this.racers.every((racer) => racer._finished);
      if (finished) await this.finish();
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

  async finish() {
    raceGoOpt.innerHTML = 'Race Again!';
    _show(controlPanel);
    _show(menu);
    _show(raceGoOpt);
    _show(raceGoSkipOpt);
    _show(resultsWindow);
    this.setShare();
    await this.setVotes();
  }
}


class Racing {

  constructor() {
    this.addEventListeners();
    this.renderInputs();
    this.inputState = this.getInputState();
    this.race = null;
  }

  addEventListeners() {
    raceGoOpt.addEventListener('click', () => this.runRace(false, null));
    raceGoSkipOpt.addEventListener('click', () => this.runRace(true, null));
    addMoreOpt.addEventListener('click', () => this.addInput());
    raceShareOpt.addEventListener('click', () => this.share());
    resetOption.addEventListener('click', () => this.resetInputs());

    downvoteRaceOpt.addEventListener('click', () => this.voteRace(0));
    upvoteRaceOpt.addEventListener('click', () => this.voteRace(1));
  }

  voteRace(vote) {
    if (this.race && this.race.raceId) {
      this.race.vote(vote);
    }
  }

  share() {
    if (this.race && this.race.raceId && this.race.racers.length > 0) {
      this.race.shareLink();
    }
  }

  addInput(make=null, model=null, year=null) {
    if (inputsContainer.children.length > 8) {
      return
    }
    let container = _el('div', {className: 'racer-input-row'});
    let makeIn = _el('input', {placeholder: 'Make...'});
    let modelIn = _el('input', {placeholder: 'Model...'});
    let yearIn = _el('input', {placeholder: 'Year...'});

    let recommender = new RacerRecommender(
      makeIn,
      modelIn,
      yearIn,
      recommendationsContainer,
    );

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
    return state.trim();
  }

  async runRace(skip, raceId) {
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
    } else if (!this.inputState){
      return;
    } else {
      // Unchanged / replay - don't save
    }
    this.inputState = this.getInputState();
    await this.race.race(save, skip);
  }

  checkSharedRace() {
    let sharedUrlMatch = window.location.pathname.match("/r/\([0-9]+)/?$");
    if (sharedUrlMatch) {
      return parseInt(sharedUrlMatch[1]);
    }
  }
}
