class RacerRecommender {

  constructor(makeIn, modelIn, yearIn, container) {
    this.makeIn = makeIn;
    this.modelIn = modelIn;
    this.yearIn = yearIn;
    this.container = container;
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
        _show(this.container);
        this.addRecommendations(results);
        return;
      }
    }
    _hide(this.container);
  }

  addRecommendations(racerResults) {
    this.container.replaceChildren();
    racerResults.forEach((racer) => {
      let row = _el(
        'div', {
          className: 'recommendation-row',
          innerHTML: `${racer.name} ${racer.year}`
        }
      );
      row.addEventListener('click', () => this.selectRecommendation(racer.name, racer.year));
      this.container.appendChild(row);
    });
  }

  selectRecommendation(name, year) {
    this.modelIn.value = name;
    this.yearIn.value = year;
    this.container.replaceChildren();
    _hide(this.container);
  }

  assignTrigger(element) {
    element.addEventListener('keyup', () => this.get());
    element.addEventListener('focus', () => this.get());
  }
}
