let CSRF;

function init() {
  let $vocabList = $('.vocab-list');
  // only run on vocab page
  if (/vocabulary\/\d+/.test(window.location.pathname)) {
    let $cards = $vocabList.find('.vocab-card');
    CSRF = $('#csrf').val();

    // im no longer imported at top of file.
    // seems flexbox is adjusting okay and we don't need this anymore
    // keeping it for a few commits then feel free to blow away the function
    //    if(im.greaterThan('md')) adjustCardHeight($cards);

    // if user has deeplinked from summary or elsewhere let's draw attention to the card
    let specificVocab = (window.location.href.match(/.*vocabulary\/\d+\/(\#.+)/) || [])[1];
    if (specificVocab) $(specificVocab).addClass('-standout');

    // Attach events
    $cards.on('click', '.icon', handleIconClick);
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
    .always(res => console.log(res));
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
    .always(res => console.log(res));
  }
}


const api = {
  init,
};

export default api;
