function _hide(element) {
  element.style.display = 'none';
}

function _show(element) {
  element.style.display = 'block';
}

function _el(type, info) {
  let element = document.createElement(type);
  Object.entries(info).forEach((entry) => {
    let [key, value] = entry;
    element[key] = value;
  });
  return element;
}

function isShowing(element) {
  return element.style.display != 'none' && element.style.display != '';
}

async function _post(url, data) {
  let response = await fetch(url,
    {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    }
  );
  var result = await response.json();
  result._status_code = response.status;
  return result;
}


async function _get(url) {
  let result = await fetch(url);
  return await result.json();
}


function getCookie(name) {
  return document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')?.pop() || ''
}

function resetForm(id) {
  document.querySelectorAll(`#${id} input`).forEach(
    (element) => element.value = ''
  )
}


function renderHeaderLoading(headerImageId) {
  let headerImage = document.getElementById(headerImageId);
  headerImage.style.backgroundImage = 'url("./static/images/loading.gif")';
  headerImage.style.marginTop = "9px";
}

function unrenderHeaderLoading(headerImageId) {
  let headerImage = document.getElementById(headerImageId);
  headerImage.style.backgroundImage = 'url("./static/images/street_type.svg")';
  headerImage.style.marginTop = "0px";
}
