class Windows {
  constructor() {
    for(let windowItem of document.getElementsByClassName('menu-item')) {
      windowItem.addEventListener('click', () => {
        _show(document.getElementById(windowItem.getAttribute('window')));
      });
    }

    for(let closeOpt of document.getElementsByClassName('close')) {
      closeOpt.addEventListener('click', () => {
        _hide(document.getElementById(closeOpt.getAttribute('window')));
      });
    }
  }
}
