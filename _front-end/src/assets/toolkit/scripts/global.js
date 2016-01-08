/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

import $ from 'jquery';

import expandToggle from './components/expand-toggle';
import revealToggle from './components/reveal-toggle';
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
  login.init();
  home.init();
  vocab.init();
  unlocks.init();
  reviews.init();

})
