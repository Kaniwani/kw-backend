function init() {

  if (/contact/.test(window.location.pathname)) {
    const $form = $('.contact-form');
    const $button = $form.find('button.-submit')

    // on form submit, set flag for notification
    $form.submit(function(event) {
      $button.html('<span class="-loading" style="margin-bottom: 0; width: 1.25em; height: 1.25em;"></span>');
    });
  }

}

const api = {
  init,
}

export default api;
