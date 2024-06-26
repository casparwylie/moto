const introLoadingImage = document.getElementById('intro-loading-image');
const introLoadingText = document.getElementById('intro-loading-text');
const introCoverContainer = document.getElementById('intro-cover-container');
const introDevicePopupContainer = document.getElementById('intro-device-popup-container');

const introDeviceAppStoreOpt = document.getElementById('intro-device-appstore-opt');
const introDeviceAppOpt = document.getElementById('intro-device-app-opt');
//const introDeviceExitOpt = document.getElementById('intro-device-exit-opt');


function iOS() {
  return [
    'iPad Simulator',
    'iPhone Simulator',
    'iPod Simulator',
    'iPad',
    'iPhone',
    'iPod'
  ].includes(navigator.platform)
  // iPad on iOS 13 detection
  || (navigator.userAgent.includes("Mac") && "ontouchend" in document)
}


class Intro {
  constructor(racingPage) {
    this.sharedRaceId = racingPage.checkSharedRace()

    introDeviceAppStoreOpt.addEventListener('click', () => this.chooseAppStore());
    introDeviceAppOpt.addEventListener('click', () => this.chooseApp());
    //introDeviceExitOpt.addEventListener('click', () => this.exitDevicePopup());
  }

  async start() {
    if (iOS()) {
      _hide(introCoverContainer);
      _show(introDevicePopupContainer);
    } else if (this.sharedRaceId) {
      _hide(introCoverContainer);
      await racingPage.runRace(false, this.sharedRaceId);
    } else {
      this.runLoading();
    }
  }


  chooseAppStore() {
    // open app store
    window.location = "https://apps.apple.com/us/app/whatbikeswin/id6447978066";
  }

  chooseApp() {
    window.location = "whatbikeswin://?shareRaceId=" + this.sharedRaceId;
  }

  async exitDevicePopup() {
    // close
    _hide(introDevicePopupContainer);
    if (this.sharedRaceId) {
      await racingPage.runRace(false, this.sharedRaceId);
    }
  }

  runLoading() {
    setTimeout(function(){
      _hide(introLoadingText);
      let introInterval = setInterval(function(){
        introLoadingImage.style.marginLeft = parseInt(
        window.getComputedStyle(introLoadingImage).marginLeft
      ) + 10 + 'px';
      }, 20);
      setTimeout(function(){
        clearInterval(introInterval);
        _hide(introCoverContainer);
      }, 1000);
    }, 1000);
  }
}
