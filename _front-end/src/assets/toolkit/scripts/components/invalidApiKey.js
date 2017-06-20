function init() {
  let $api = $('#invalidApiKey');

  if ($api.length) {
    notie.alert({
      type: 3,
      text: $api.html(),
      stay: true,
    });
  }
}

let api = {
  init,
}

export default api;
