import $ from 'jquery';

let initialised = false;
let $vocabItems = null;

const toggleClick = (ev) => {
  ev.preventDefault();
  toggleVocabItem($(ev.target));
}

const toggleVocabItem = ($el) => {
  $el.closest('.vocab__item').toggleClass('vocab__item--active');
};

const api = {
  init() {
    if($('.vocab__list').length > 0 && !initialised) {
      // Cache DOM elements
      $vocabItems = $('.vocab__item');

      // Attach events
      $vocabItems.on('click', '.vocab-lower__toggle', toggleClick);
      initialised = true;
    }
  }
};

export default api;
