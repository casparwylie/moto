const INSIGHTS_API_URL = '/api/racing/insight';

const popularPairsContainer = document.getElementById('popular-pairs-container');
const popularPairsWindow = document.getElementById('popular-pairs-window');
const recentRacesWindow = document.getElementById('recent-races-window');
const recentRacesContainer = document.getElementById('recent-races-container');
const h2hReloader = document.getElementById('h2h-insight-reload');
const rrReloader = document.getElementById('recent-races-insight-reload');

class RaceListing {
  api_url = null;
  container = null;
  window_ = null;
  reloader = null;

  setReloader() {
    this.reloader.addEventListener('mouseover', () => this.populate());
  }

  async populate() {
    this.container.replaceChildren();
    let results = await _get(this.api_url);
    if (results.races.length > 0) {
      results.races.forEach((race) => this.addRow(race));
    } else {
      this.container.innerHTML = 'There aren\'t any races here yet.';
    }
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
    racingPage.runRace(false, raceId);
    if (this.window_) _hide(this.window_);
  }
}


class PopularPairsInsight extends RaceListing {
  api_url = `${INSIGHTS_API_URL}/popular-pairs`;
  container = popularPairsContainer;
  window_ = popularPairsWindow;
  reloader = h2hReloader;
}


class RecentRacesInsight extends RaceListing {
  api_url = `${INSIGHTS_API_URL}/recent-races`;
  container = recentRacesContainer;
  window_ = recentRacesWindow;
  reloader = rrReloader;
}
