const informerContainer = document.getElementById('informer-container');

class Informer {

  static inform(message, mood, duration=3000) {
    let informerRow = _el(
      'div', {className: 'informer-row ' + mood, innerHTML: message},
    )
    informerContainer.prepend(informerRow);
    setTimeout(() => informerRow.remove(), duration);
  }

}
