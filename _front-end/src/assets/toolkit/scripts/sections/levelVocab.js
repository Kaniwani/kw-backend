let CSRF,
    $vocabList,
    $cards;

function init() {
  // catch any window hashes if we arrived from summary page before anything else
  if (window.location.hash) {
    smoothScroll.init();
    smoothScrollDeepLink();
  }

  // only run on secondary vocab page
  if(/vocabulary\/.+\//.test(window.location.pathname)) {
    $vocabList = $('.vocab-list');
    CSRF = $('#csrf').val();
    $cards = $vocabList.find('.vocab-card');

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
  let $icon = $(this),
      $card = $icon.closest('.vocab-card'),
      review_pk = $card.data('pk');

    $.post('/kw/togglevocab/', { review_id: review_pk, csrfmiddlewaretoken: CSRF })
      .done(res =>  {
        toggleClasses($icon, $card);
      })
      .always(res => console.log(res));
}


function toggleClasses($icon, $card) {
    $card.toggleClass('-locked -unlockable');
    $icon.toggleClass('i-unlock').toggleClass('i-unlocked');
}

const api = {
  init,
};

export default api;
