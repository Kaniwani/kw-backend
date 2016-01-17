/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

// components
import expandToggle from './components/expandToggle';
import revealToggle from './components/revealToggle';
import accordionContainer from './components/accordionContainer';
import invalidApiKey from './components/invalidApiKey';
import login from './sections/login';
import home from './sections/home';
import vocab from './sections/vocab';
import unlocks from './sections/unlocks';
import reviews from './sections/reviews';

$(document).ready(() => {

  invalidApiKey.init();
  expandToggle.init();
  revealToggle.init();
  accordionContainer.init();
  login.init();
  home.init();
  vocab.init();
  unlocks.init();
  reviews.init();

})