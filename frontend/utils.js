function _hide(element) {
  element.style.display = 'none';
}

function _show(element) {
  element.style.display = 'block';
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
