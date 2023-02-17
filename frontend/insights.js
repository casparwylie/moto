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
    results.races.forEach((race) => this.addRow(race));
  }

  addRow(race) {
    let row = _el('div', {className: 'popular-pair-row'});
    row.addEventListener('click', () => this.newRace(race.race_id));

    let vsItem = _el('span', {innerHTML: 'VS', className: 'vs-text'});
    row.innerHTML = race.racers.map(
      (racer) => racer.full_name
    ).join(vsItem.outerHTML);

    this.container.appendChild(row);
  }

  newRace(raceId) {
    racingPage.runRace(raceId);
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
