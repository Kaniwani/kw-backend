function init() {
  // are we on settings page?
  if (/settings/.test(window.location.pathname)) {
    const saved = simpleStorage.get('settingsSaved');
    const $form = $('#settingsForm');
    const $button = $form.find('#submit-id-submit') // lolwut? crispy forms generated markup madness

    // if settings saved last time we were on page - notify user because page just refreshed on form submit
    if (!!saved) {
      simpleStorage.deleteKey('settingsSaved');
      // animation on page load can be a bit janky - let's delay notification slightly
      setTimeout(() => notie.alert(1, 'Settings saved!', 1), 300);
    }

    // on form submit, set flag for notification
    $form.submit(event => {
      simpleStorage.set('settingsSaved', true);
      $button.addClass('-hidden');
      $button.closest('div').append(`
        <span class="btn btn-primary pure-button pure-button-primary" style="width:75px; margin-top:10px;">
          <span class="-loading" style="margin-bottom: 3px;"></span>
        </span>`
      );
    });
  }
}

const api = {
  init,
}

export default api;
