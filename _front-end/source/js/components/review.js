if (typeof KaniWani.Example === 'undefined') {
  KaniWani.Example = {};
}

KaniWani.Example = {
  vars: {
  },

  DOM: {
  },

  init: function() {
    if($('body').length > 0) {
      // Cache DOM elements
      console.log('working!');

      // Attach events
      $('body').on('click', 'a.not-yet', KaniWani.Example.events.linkClick);
    }
  },

  events: {
    linkClick: function(event) {
      event.preventDefault();
      KaniWani.Example.helpers.exampleHelper($(this));
    },
  },

  helpers: {
    exampleHelper: function($this) {
      console.log('woot');
    },
  }
};