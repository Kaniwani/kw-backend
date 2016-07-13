import '../util/serializeObject';
import config from '../config';
import im from '../vendor/include-media';
import toastr from '../vendor/toastr';


function followChanged(formData) {
  return simpleStorage.get('KW').settings.followWanikani === false && formData.follow_me === 'on'
}

function init() {
  // vendor js configuration
  if (im.lessThan('md')) config.toastr.positionClass = 'toast-top-full-width';
  toastr.options = config.toastr;

  // are we on settings page?
  if (/settings/.test(window.location.pathname)) {
    const saved = simpleStorage.get('settingsSaved');
    const $form = $('#settingsForm');
    const $button = $form.find('#submit-id-submit')

    // if settings saved last time we were on page - notify user because page just refreshed on form submit
    if (!!saved) {
      simpleStorage.deleteKey('settingsSaved');
      // animation on page load can be a bit janky - let's delay notification slightly
      setTimeout(() => toastr.success('Settings saved.'), 300);
    }

    // on form submit, set flag for notification
    $form.submit(function(event) {
      const formData = $(this).serializeObject();
      if (followChanged(formData)) simpleStorage.set('recentlySynced', false);
      // force sync if user turns followme back on
      simpleStorage.set('settingsSaved', true);
      $button.addClass('-hidden');
      $button.closest('div').append(`
        <span class="btn btn-primary pure-button pure-button-primary" style="margin-top:10px;">
          <span class="-loading"></span>
        </span>`
      );
    });
  }
}

const api = {
  init,
}

export default api;

