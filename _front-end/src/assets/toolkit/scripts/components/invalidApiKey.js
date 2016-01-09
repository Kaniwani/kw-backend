function init() {
  let $api = $('#invalidApiKey');

  if ($api.length) {
    let message = $api.html();
    notie.alert(3, message, 15);
  }
}

let api = {
  init: init
}

export default api;
