import $ from 'jquery';

let initialised = false;
let $vocabItems = null;

const toggleClick = (event) => {
  event.preventDefault();
  toggleVocabExpand($(event.target));
}

const toggleVocabExpand = ($el) => {
  $el.closest('.vocab-card').toggleClass('-expanded');
};

const api = {
  init() {
    if($('.vocab-list').length > 0 && !initialised) {
      // Cache DOM elements
      $vocabItems = $('.vocab-card');

      // Attach events
      $vocabItems.on('click', '.extratoggle', toggleClick);
      initialised = true;
    }
  }
};

export default api;
