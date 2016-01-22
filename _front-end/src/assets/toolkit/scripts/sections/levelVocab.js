let CSRF,
    $vocabList,
    $cards;

function init() {
  $vocabList = $('.vocab-list');
  // only run on vocab page
  if(/vocabulary\/\d+/.test(window.location.pathname)) {
    CSRF = $('#csrf').val();
    $cards = $vocabList.find('.vocab-card');

    // if user has deeplinked from summary or elsewhere let's draw attention to the card
    let specificVocab = window.location.href.match(/.*vocabulary\/\d+\/(\#.+)/)[1];
    if (specificVocab) {
      $(specificVocab).addClass('-standout -ghost');
      setTimeout(() => $(specificVocab).removeClass('-ghost'), 200);
    }

    // Attach events
    $cards.on('click', '.extraToggle', toggleVocabExpand); // refactor accordionToggle
    $cards.on('click', '.icon', handleIconClick);
  }
}

// refactor to use accordiontoggle
function toggleVocabExpand(event) {
  event.preventDefault();
  $(this).closest('.vocab-card').toggleClass('-expanded');
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
  init: init
};

export default api;
