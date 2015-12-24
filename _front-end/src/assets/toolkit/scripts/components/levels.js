import $ from 'jquery';

let $levels = null;

const levelClick = (event) => {
  event.preventDefault();
  levelLockToggle($(event.target))
}

// TODO: functionality
const levelLockToggle = ($el) => {
  console.log('data-level-id was ', $el.closest('.level__item').attr('data-level-id'));
}

const api = {
  init() {
    if($('.level__list').length > 0) {
      // Cache DOM elements
      $levels = $('.level__link');
      // Attach events
      $levels.on('click', levelClick);
    }
  }
};

export default api;
