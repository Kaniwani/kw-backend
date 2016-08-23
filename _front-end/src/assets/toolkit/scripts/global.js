/**
 * Toolkit JavaScript
 *
 * This should be the full compiled js from project src (same as public/assets/js/)
 *
 */
import documentReady from './util/documentReady';

// safari fix zzzzzz - must come first in entrypoint
import 'babel-polyfill';

// components
import invalidApiKey from './components/invalidApiKey';
import accordionContainer from './components/accordionContainer';
import login from './sections/login';
import home from './sections/home';
import vocab from './sections/vocabulary';
import levelVocab from './sections/levelVocab';
import reviews from './sections/reviews';
import contact from './sections/contact';
import settings from './sections/settings';
import summary from './sections/summary';

import okayNav from './vendor/jquery.okayNav';

documentReady(() => {
  const sitenav = $('#nav-main').okayNav({ swipe_enabled: false });
  invalidApiKey.init();
  accordionContainer.init();
  login.init();
  home.init();
  vocab.init();
  levelVocab.init();
  reviews.init();
  contact.init();
  settings.init();
  summary.init();
});
