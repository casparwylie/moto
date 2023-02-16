const INSIGHTS_API_URL = '/api/racing/insight';

const popularPairsContainer = document.getElementById('popular-pairs-container');
const popularPairsWindow = document.getElementById('popular-pairs-window');
const recentRacesWindow = document.getElementById('recent-races-window');
const recentRacesContainer = document.getElementById('recent-races-container');


class RaceListing {
  api_url = null;
  container = null;
  window_ = null;

  async populate() {
    let results = await _get(this.api_url);
    results.races.forEach((racers) => this.addRow(racers));
  }

  addRow(racers) {
    let row = _el('div', {className: 'popular-pair-row'});
    row.addEventListener('click', () => this.setRace(racers));

    let vsItem = _el('span', {innerHTML: 'VS', className: 'vs-text'});
    row.innerHTML = racers.map((racer) => racer.full_name).join(
      vsItem.outerHTML);

    this.container.appendChild(row);
  }

  setRace(racers) {
    racingPage.resetInputs(false);
    racers.forEach(
      (racer) => racingPage.addInput(racer.make, racer.model)
    );
    if (this.window_) _hide(this.window_);
  }
}


class PopularPairsInsight extends RaceListing {
  api_url = `${INSIGHTS_API_URL}/popular-pairs`;
  container = popularPairsContainer;
  window_ = popularPairsWindow;
}


class RecentRacesInsight extends RaceListing {
  api_url = `${INSIGHTS_API_URL}/recent-races`;
  container = recentRacesContainer;
  window_ = recentRacesWindow;
}
