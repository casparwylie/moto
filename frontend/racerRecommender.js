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

    this.makeIn.addEventListener('keyup', () => {
      this.modelIn.value = "";
      this.yearIn.value = "";
    })

  }


  setPosition() {
      const xPos = getOffset(this.makeIn.parentElement).left;
      const yPos = getOffset(this.makeIn.parentElement).top + this.makeIn.offsetHeight;
      const width = this.makeIn.parentElement.offsetWidth;
      this.container.style.marginTop = `${yPos}px`;
      this.container.style.marginLeft = `${xPos}px`;
      this.container.style.width = `${width}px`;
  }

  async get() {
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
      row.addEventListener('click', () => this.selectRecommendation(racer));
      this.container.appendChild(row);
    });
  }

  selectRecommendation(racer) {
    this.makeIn.value = racer.make_name;
    this.modelIn.value = racer.name;
    this.yearIn.value = racer.year;
    this.container.replaceChildren();
    _hide(this.container);
  }

  assignTrigger(element) {
    element.addEventListener('keyup', () => this.get());
    element.addEventListener('focus', () => this.get());
  }
}
