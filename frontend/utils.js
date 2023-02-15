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

async function _post(url, data) {
  let response = await fetch(url,
    {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(data),
    }
  );
  return await response.json();
}


async function _get(url) {
  let result = await fetch(url);
  return await result.json();
}
