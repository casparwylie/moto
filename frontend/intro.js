const introLoadingImage = document.getElementById('intro-loading-image');
const introLoadingText = document.getElementById('intro-loading-text');
const introCoverContainer = document.getElementById('intro-cover-container');

function runIntro() {
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
    }, 2000);
  }, 2000);
}
