let CSRF,
    $vocabList,
    $cards;

function init() {
  $vocabList = $('.vocab-list');

  // if container element exists on current page
  if($vocabList.length) {

    // cache elements/setup vars
    CSRF = $('#csrf').val();
    $cards = $vocabList.find('.vocab-card');

    // Attach events
    $cards.on('click', '.icon', handleIconClick);
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
  init: init
};

export default api;
