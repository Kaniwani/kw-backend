import config from '../config';
import refreshReviews from '../components/refreshReviews';
import strToBoolean from '../util/strToBoolean';
import kwlog from '../util/kwlog';
import timeago from '../vendor/timeago';
import toastr from '../vendor/toastr';
import im from '../vendor/include-media';
import okayNav from '../vendor/jquery.okayNav';
const sitenav = $('#nav-main').okayNav();

// vendor js configuration
Object.assign($.timeago.settings, config.timeago.settings);
Object.assign($.timeago.settings.strings, config.timeago.strings);

let KW;

function displayMessages() {
  kwlog('messages', KW.messages);
  KW.messages.forEach(({ text, level }) => toastr[level](text));
}

function updateReviewTime($el) {
  let now = Date.now(),
      next = Date.parse(KW.nextReview);

  kwlog(now, next, $el.get(0), $.timeago(KW.nextReview));
  if (now > next) {
    refreshReviews();
    clearInterval(KW.reviewTimer);
  } else {
    $el.html(`Next review: ${$.timeago(KW.nextReview)}`);
  }
}

function init() {
  if (im.lessThan('md')) config.toastr.positionClass = 'toast-top-full-width';
  toastr.options = config.toastr;

  // let's update storage KW with any template provided changes
  KW = Object.assign(simpleStorage.get('KW') || {}, window.KW);
  KW.settings = strToBoolean(KW.settings);
  KW.nextReview = new Date(Math.ceil(+KW.nextReview));
  simpleStorage.set('KW', KW);

  // need to get some promises happening instead, too many race conditions
  setTimeout(() => displayMessages(), 1500);

  // are we on home page?
  if (window.location.pathname === '/kw/') {
    let $refreshButton = $("#forceSrs");
    let $reviewButton = $("#reviewCount");

    if (KW.settings.onVacation === false) {
      updateReviewTime($reviewButton);
      KW.reviewTimer = setInterval(() => updateReviewTime($reviewButton), 10000 /* 10s */);
    }

    // event handlers
    $refreshButton.click(() => refreshReviews());
    $reviewButton.click(ev => {
      if ($reviewButton.hasClass('-disabled')) ev.preventDefault();
    });
  }
}


const api = {
  init,
}

export default api;
