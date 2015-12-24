/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

import $ from 'jquery';

import login from './sections/login';
import expandToggle from './components/expand-toggle';
import vocabToggle from './components/vocab';
import levels from './components/levels';

$(document).ready(() => {
  // TODO: remove when/if using modernizr instead
  $('html').removeClass('no-js').addClass('js');

  login.init();
  expandToggle.init();
  vocabToggle.init();
  levels.init();
})
