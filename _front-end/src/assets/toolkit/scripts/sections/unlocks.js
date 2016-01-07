import $ from 'jquery';
// docs -- http://github.com/jaredreich/notie.js/
import notie from '../vendor/notie';

// setup variables inside module closure, but functions in this file can modify and access them
let CSRF,
    $reviewCount,
    $levelList,
    $levels,
    $icon,
    $card,
    level,
    reviews;

function init() {
  $levelList = $('.level-list');

  // if container element exists on current page
  if($levelList.length) {

    // cache selector elements/unchanging vars
    CSRF = $('#csrf').val();
    $levels = $levelList.find('.level-card');
    $reviewCount = $('.nav-link > .text > .count')

    // Attach events
    $levelList.on('click', '[class*="i-unlock"]', handleLockClick);
    $levelList.on('click', '[class*="i-lock"]', () => notie.alert(3, 'Level is locked. No cheating!', 1));
  }
}

function handleLockClick(event) {
  event.preventDefault();

  $icon = $(this),
  $card = $icon.closest(".level-card"),
  level = $card.data("level-id"),
  reviews = parseInt($reviewCount.text(), 10);

  if ($card.hasClass('-unlocked')) {
    notie.confirm(`Are you sure you want to relock level ${level}? This will reset your SRS levels.`, 'Yeah!', 'Nope', reLockLevel);
  } else {
    unLockLevel();
  }
}

function unLockLevel() {
  $icon.removeClass("i-unlock i-unlocked").addClass('-loading');

  $.post("/kw/levelunlock/", {level: level, csrfmiddlewaretoken: CSRF})
   .done(res => {

      updateReviewCount(res);
      notie.alert(1, res, 1.5);

      $icon.removeClass("-loading").addClass('i-unlocked');
      $card.removeClass("-locked -unlockable");
      $card.addClass("-unlocked");
      $card.find('.i-link').removeClass('-hidden');


    })
   .fail(handleAjaxFail);
}

function reLockLevel() {
  $icon.removeClass("i-unlock i-unlocked").addClass('-loading');

  $.post("/kw/levellock/", {level: level, csrfmiddlewaretoken: CSRF})
   .done(res => {

      updateReviewCount(res, true)
      notie.alert(1, res, 1.5);

      $icon.removeClass("-loading").addClass("i-unlock");
      $card.removeClass("-unlocked");
      $card.addClass("-locked -unlockable");
      $card.find('.i-link').addClass('-hidden');

    })
   .fail(handleAjaxFail);
}

function updateReviewCount(responseString, subtract = false) {
  let changed = parseInt(responseString.match(/^\d+/), 10);
  !!subtract ? reviews -= changed : reviews += changed;

  let newCount = Number.isNaN(reviews) ? changed : reviews;
  $reviewCount.text(newCount < 0 ? 0 : newCount);
}

function handleAjaxFail(res) {
  let message = `Something went wrong - please try again. If the problem persists, submit a bug report via <a href="/contact"> the contact form</a> with the following information: <q>${res.responseText} - ${res.status}: ${res.statusText}</q>.`;

  notie.alert(3, message, 60);
}

const api = {
  init: init
};

export default api;
