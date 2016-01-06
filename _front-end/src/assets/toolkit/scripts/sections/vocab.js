import $ from 'jquery';

// setup variables inside closure, but functions can access them if needs be
let CSRF,
    $vocabList,
    $cards;

function init() {
  CSRF = $('#csrf').val();
  $vocabList = $('.vocab-list');

  // if parent element exists on page
  if($vocabList.length) {
    // Cache DOM elements
    $cards = $vocabList.find('.vocab-card');

    // Attach events
    $cards.on('click', '.extraToggle', toggleVocabExpand);
    $cards.on('click', '.icon', handleIconClick);
  }
}

function toggleVocabExpand(event) {
  event.preventDefault();
  $(this).closest('.vocab-card').toggleClass('-expanded');
}

function handleIconClick(event) {
  let $icon = $(this),
      $card = $icon.closest('.vocab-card'),
      review_pk = $card.data('pk');

    $.post('/kw/togglevocab/', { review_id: review_pk, csrfmiddlewaretoken: CSRF })
      .done(() =>  toggleClasses($icon, $card))
      .always(data => console.log(data));
}


function toggleClasses($icon, $card) {
    $card.toggleClass('-locked -unlockable');
    $icon.toggleClass('i-unlock').toggleClass('i-unlocked');
}

const api = {
  init: init
};

export default api;
