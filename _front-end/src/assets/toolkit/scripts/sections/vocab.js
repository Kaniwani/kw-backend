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
      .done(res =>  {
        toggleClasses($icon, $card);
        let $count = $('#navReviewCount');
        let count = simpleStorage.get('reviewCount');
        let increase = /^added/i.test(res);
        increase ? count++ : count--;

        console.log(increase, $count, count);

        simpleStorage.set('reviewCount', count)
        $count.html(count);
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
