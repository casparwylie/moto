const menuContainer = document.getElementById('menu');

class Windows {
  constructor() {
    for(let windowItem of menuContainer.children) {
      let windowId = windowItem.getAttribute('window');
      if (windowId) {
        windowItem.addEventListener('click', () => {
          _show(document.getElementById(windowId));
        });
      }
    }

    for(let closeOpt of document.getElementsByClassName('close')) {
      closeOpt.addEventListener('click', () => {
        _hide(document.getElementById(closeOpt.getAttribute('window')));
      });
    }
  }
}
