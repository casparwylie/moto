function getOffset(el) {
  const rect = el.getBoundingClientRect();
  return {
    left: rect.left + window.scrollX,
    top: rect.top + window.scrollY
  };
}

class RacerRecommender {

  constructor(makeIn, modelIn, yearIn, container) {
    this.makeIn = makeIn;
    this.modelIn = modelIn;
    this.yearIn = yearIn;
    this.container = container;

    document.addEventListener('click', (el) =>{
      if (el.target.tagName != 'INPUT') {
        _hide(this.container);
      }
    });

    this.modelIn.addEventListener('keyup', () => this.getModel());
    this.modelIn.addEventListener('focus', () => this.getModel());

    this.makeIn.addEventListener('keyup', () => this.getMake());
    this.makeIn.addEventListener('focus', () => this.getMake());
  }


  setPosition() {
      const xPos = getOffset(this.makeIn.parentElement).left;
      const yPos = getOffset(this.makeIn.parentElement).top + this.makeIn.offsetHeight;
      const width = this.makeIn.parentElement.offsetWidth;
      this.container.style.marginTop = `${yPos}px`;
      this.container.style.marginLeft = `${xPos}px`;
      this.container.style.width = `${width}px`;
  }

  async getMake() {
    this.modelIn.value = "";
    this.yearIn.value = "";
    this.setPosition();
    let make = this.makeIn.value.trim();
    let results = await _get(
    `${RACING_API_URL}/racer/makes/search?make=${make}`);
    if (
      results.makes.length == 1 &&
      results.makes[0].toLowerCase() == make.toLowerCase()
    ) {
      this.selectMakeRecommendation(results.makes[0]);
    } else {
      _show(this.container);
      this.addMakeRecommendations(results.makes);
    }
  }

  async getModel() {
    this.setPosition();
    let make = this.makeIn.value.trim();
    let model = this.modelIn.value.trim();
    let year = this.yearIn.value.trim();
    this.yearIn.value = "";

    if (make) {
      let results = await _get(
        `${RACING_API_URL}/racer/search?make=${make}&model=${model}&year=${year}`
      );
      if (results.length > 0) {
        _show(this.container);
        this.addModelRecommendations(results);
        return;
      }
    }
    _hide(this.container);
  }

  addMakeRecommendations(makes) {
    this.container.replaceChildren();
    makes.forEach((make) => {
      let row = _el(
        'div', {
          className: 'recommendation-row',
          innerHTML: make,
        }
      );
      row.addEventListener('click', () => this.selectMakeRecommendation(make));
      this.container.appendChild(row);
    });
  }

  addModelRecommendations(racerResults) {
    this.container.replaceChildren();
    racerResults.forEach((racer) => {
      let row = _el(
        'div', {
          className: 'recommendation-row',
          innerHTML: `${racer.name} ${racer.year}`
        }
      );
      row.addEventListener('click', () => this.selectModelRecommendation(racer));
      this.container.appendChild(row);
    });
  }

  selectModelRecommendation(racer) {
    this.makeIn.value = racer.make_name;
    this.modelIn.value = racer.name;
    this.yearIn.value = racer.year;
    this.container.replaceChildren();
    _hide(this.container);
  }

  selectMakeRecommendation(make) {
    this.makeIn.value = make;
    this.container.replaceChildren();
    _hide(this.container);
  }
}
