/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

import $ from 'jquery';

import login from './sections/login';
import expandToggle from './components/expand-toggle';
import revealToggle from './components/reveal-toggle';
import vocab from './sections/vocab';
import user from './sections/user';
import unlocks from './sections/unlocks';
import reviews from './sections/reviews';

$(document).ready(() => {

  login.init();
  expandToggle.init();
  revealToggle.init();
  vocab.init();
  unlocks.init();
  user.init();
  reviews.init();

})
