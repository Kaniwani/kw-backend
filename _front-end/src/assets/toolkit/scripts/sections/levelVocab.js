import config from '../config';
import im from '../vendor/include-media';
import toastr from '../vendor/toastr';
import kwlog from '../util/kwlog';


let CSRF;

function init() {
  CSRF = $('#csrf').val();

  // vendor js configuration
  if (im.lessThan('md')) config.toastr.positionClass = 'toast-top-full-width';
  toastr.options = config.toastr;

  // catch any window hashes if we arrived from summary page before anything else
  if (window.location.hash) {
    smoothScroll.init();
    smoothScrollDeepLink();
  }

  // only run on vocab page
  if(/vocabulary\/.+\//.test(window.location.pathname)) {
    let $cards = $('.vocab-list').find('.vocab-card');

    // if user has deeplinked from summary or elsewhere let's draw attention to the card
    let specificVocab = (window.location.href.match(/.*vocabulary\/.+\/(\#.+)/) || [])[1];
    if (specificVocab) $(specificVocab).addClass('-standout');

    // Attach events
    $cards.on('click', '.icon', handleIconClick);
  }
}

function smoothScrollDeepLink() {
  let hash = smoothScroll.escapeCharacters(window.location.hash); // Escape the hash
  let el = document.querySelector(hash);
  if (el != null) {
    smoothScroll.animateScroll(hash, null /* toggle */, {offset: 50});
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
      csrfmiddlewaretoken: CSRF
    })
    .done(res => {
      // brittle selecting, but user synonyms always have both present so it's safe unless markup changes...
      [$icon.closest('.kanji'), $icon.closest('.kanji').prev('.kana')].forEach(el => $(el).fadeOut(600));
    })
    .always(res => kwlog(res));
  }

  function toggleLock(id) {
    $.post('/kw/togglevocab/', {
      review_id: id,
      csrfmiddlewaretoken: CSRF
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
