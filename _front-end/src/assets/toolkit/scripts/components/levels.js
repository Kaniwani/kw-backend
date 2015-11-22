if (typeof KaniWani.Levels === 'undefined') {
  KaniWani.Levels = {};
}

KaniWani.Levels = {
  vars: {
  },

  DOM: {
    $levels: null
  },

  init: function() {
    if($('.level__list').length > 0) {
      // Cache DOM elements
      KaniWani.Levels.DOM.$levels = $('.level__link');

      // Attach events
      KaniWani.Levels.DOM.$levels.on('click.levels', KaniWani.Levels.events.levelClick);
    }
  },

  events: {
    levelClick: function(event) {
      if(!$(event.target).hasClass('level__link')) {
        event.preventDefault();
        KaniWani.Levels.helpers.levelLockToggle($(this));
      }
    },
  },

  helpers: {
    levelLockToggle: function($this) {
      console.log($this.closest('.level__item').attr('data-level-id'));
    },
  }
};