import config from '../config';
import im from '../vendor/include-media';
import toastr from '../vendor/toastr';
import kwlog from '../util/kwlog';
import jump from 'jump.js';

let CSRF;

function init() {
  CSRF = $('#csrf').val();

  // vendor js configuration
  if (im.lessThan('md')) config.toastr.positionClass = 'toast-top-full-width';
  toastr.options = config.toastr;

  // catch any window hashes if we arrived from summary page before anything else
  const deeplink = window.location.hash;
  if (deeplink) smoothScrollDeepLink(deeplink);

  // only run on vocab page
  if (/vocabulary\/.+\//.test(window.location.pathname)) {
    let $cards = $('.vocab-list').find('.vocab-card');

    // Attach events
    $cards.on('click', '.icon', handleIconClick);
  }
}

function smoothScrollDeepLink(target) {
  const el = document.querySelector(target);
  if (el != null) {
    setTimeout(() => jump(el, { duration: 2000, offset: -50 }), 1000);
    el.classList.add('-standout');
  }
}

function handleIconClick(event) {
  let $icon = $(this);
  let $card = $icon.closest('.vocab-card');

  if ($icon.hasClass('removeSynonym')) {
    removeSynonym($icon.data('synonym-id'));
  } else if ($icon.hasClass('toggleLock')) {
    toggleLock($card.data('vocab-id'));
  }

  function removeSynonym(id) {
    $.post('/kw/synonym/remove', {
      synonym_id: id,
      csrfmiddlewaretoken: CSRF,
    })
    .done(res => {
      [$icon.closest('.kanji'),
       $icon.closest('.kanji').prev('.kana')].forEach(el => $(el).fadeOut(600));
    })
    .always(res => kwlog(res));
  }

  function toggleLock(id) {
    $.post('/kw/togglevocab/', {
      review_id: id,
      csrfmiddlewaretoken: CSRF,
    })
    .done(res => {
      $card.toggleClass('-locked -unlockable');
      $icon.toggleClass('i-unlock').toggleClass('i-unlocked');
    })
    .always(res => kwlog(res));
  }
}

const api = {
  init,
};

export default api;
