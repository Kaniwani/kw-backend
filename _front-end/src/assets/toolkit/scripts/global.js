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
import revealToggle from './components/revealToggle';
import accordionContainer from './components/accordionContainer';
import login from './sections/login';
import home from './sections/home';
import vocab from './sections/vocabulary';
import levelVocab from './sections/levelVocab';
import reviews from './sections/reviews';
import contact from './sections/contact';
import settings from './sections/settings';

$(document).ready(() => {
  levelVocab.init(); // first so smoothscroll on deeplink can activate as early as possible
  invalidApiKey.init();
  revealToggle.init();
  accordionContainer.init();
  login.init();
  home.init();
  vocab.init();
  reviews.init();
  contact.init();
  settings.init();
})
