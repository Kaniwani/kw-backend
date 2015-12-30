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
import vocabToggle from './components/vocab';
import levels from './components/levels';
import reviews from './sections/reviews';

$(document).ready(() => {

  login.init();
  expandToggle.init();
  revealToggle.init();
  vocabToggle.init();
  levels.init();
  reviews.init();

})
