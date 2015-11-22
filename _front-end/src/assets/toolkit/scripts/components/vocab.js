if (typeof KaniWani.Vocab === 'undefined') {
  KaniWani.Vocab = {};
}

KaniWani.Vocab = {
  vars: {
    initialised: false
  },

  DOM: {
    $vocabItems: null
  },

  init: function() {
    if($('.vocab__list').length > 0 && !KaniWani.Vocab.vars.initialised) {
      // Cache DOM elements
      KaniWani.Vocab.DOM.$vocabItems = $('.vocab__item');

      // Attach events
      KaniWani.Vocab.DOM.$vocabItems.on('click', '.vocab-lower__toggle', KaniWani.Vocab.events.vocabToggleClick);

      KaniWani.Vocab.vars.initialised = true;
    }
  },

  events: {
    vocabToggleClick: function(event) {
      event.preventDefault();
      KaniWani.Vocab.helpers.toggleVocabItem($(this));
    },
  },

  helpers: {
    toggleVocabItem: function($this) {
      $this.closest('.vocab__item').toggleClass('vocab__item--active');
    },
  }
};