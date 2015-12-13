/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */

import $ from 'jquery';

import expandToggle from './components/expand-toggle';

import login from './sections/login';

$(document).ready(() => {
  // TODO: remove when/if using modernizr instead
  $('html').removeClass('no-js').addClass('js');

  login.init();
  expandToggle.init();
})
