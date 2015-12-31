import $ from 'jquery';

let CSRF = null;

const toggleVocabExpand = (event) => {
  event.preventDefault();
  $(event.target).closest('.vocab-card').toggleClass('-expanded');
};

// const handleIconClick = (event) => {
//   event.preventDefault();
//   event.stopPropagation();
//   let $icon = $(event.target);
//   let $el = $icon.closest('.vocab-card');
//   let level = $el.data("level-id");
//   console.log($el, level);

//   if ($el.hasClass('fa-unlock-alt')) {
//     postUnlock($el, $icon, level);
//   }

// }

// const postUnlock = ($el, $icon, level) => {
//   $.post("/kw/levelunlock/", {"level": level, csrfmiddlewaretoken: CSRF})
//    .done(function(data) {
//       $icon.removeClass("fa-unlock-alt");
//       $icon.addClass("fa-unlock");
//       $el.removeClass("-locked -unlockable");
//   });
// };

// const postlock = () => {};

const api = {
  init() {
    CSRF = $('#csrf').val();
    let $vocabList = $('.vocab-list');

    if($vocabList.length > 0) {
      // Cache DOM elements
      let $cards = $vocabList.find('.vocab-card');

      // Attach events
      $cards.on('click', '.extratoggle', toggleVocabExpand);
      // $cards.on('click', '.fa', handleIconClick);
    }
  }
};

export default api;
