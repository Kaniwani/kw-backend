/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

// safari fix zzzzzz - must come first in entrypoint
import "babel-polyfill";

// components
import invalidApiKey from './components/invalidApiKey';
import expandToggle from './components/expandToggle';
import revealToggle from './components/revealToggle';
import accordionContainer from './components/accordionContainer';
import login from './sections/login';
import home from './sections/home';
import vocab from './sections/vocabulary';
import levelVocab from './sections/levelVocab';
import reviews from './sections/reviews';
import summary from './sections/summary';
import settings from './sections/settings';

import modals from './vendor/modals';

$(document).ready(() => {

  invalidApiKey.init();
  expandToggle.init();
  revealToggle.init();
  accordionContainer.init();
  login.init();
  home.init();
  vocab.init();
  levelVocab.init();
  reviews.init();
  summary.init();
  settings.init();

modals.init({
    selectorToggle: '[data-modal]', // Modal toggle selector
    selectorWindow: '[data-modal-window]', // Modal window selector
    selectorClose: '[data-modal-close]', // Modal window close selector
    modalActiveClass: 'active', // Class applied to active modal windows
    modalBGClass: 'modal-bg', // Class applied to the modal background overlay
    preventBGScroll: false, // Boolean, prevents background content from scroll if true
    preventBGScrollHtml: true, // Boolean, adds overflow-y: hidden to <html> if true (preventBGScroll must also be true)
    preventBGScrollBody: true, // Boolean, adds overflow-y: hidden to <body> if true (preventBGScroll must also be true)
    backspaceClose: true, // Boolean, whether or not to enable backspace/delete button modal closing
    callbackOpen: function ( toggle, modalID ) {}, // Functions to run after opening a modal
    callbackClose: function () {} // Functions to run after closing a modal
});

})


