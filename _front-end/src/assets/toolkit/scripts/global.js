/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

// safari fix zzzzzz
import "babel-polyfill";

// components
import expandToggle from './components/expandToggle';
import revealToggle from './components/revealToggle';
import accordionContainer from './components/accordionContainer';
import invalidApiKey from './components/invalidApiKey';
import login from './sections/login';
import home from './sections/home';
import vocab from './sections/vocabulary';
import levelVocab from './sections/levelVocab';
import reviews from './sections/reviews';
import summary from './sections/summary';

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

})
