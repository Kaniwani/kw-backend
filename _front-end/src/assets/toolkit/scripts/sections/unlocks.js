import $ from 'jquery';

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
    // TODO: TEST IF $levelList works as well as '.level-card -unlockable'
    $levelList.on('click', '[class*="i-unlock"]', handleLockClick);
  }
}

function handleLockClick(event) {
  event.preventDefault();

  $icon = $(this),
  $card = $icon.closest(".level-card"),
  level = $card.data("level-id"),
  reviews = parseInt($reviewCount.text(), 10);

  $icon.removeClass("i-unlock i-unlocked").addClass('-loading');

  console.log(level, $card.hasClass('-unlocked'))

  $card.hasClass('-unlocked') ? reLockPost()
                              : unLockPost();
}

function unLockPost() {
  $.post("/kw/levelunlock/", {level: level, csrfmiddlewaretoken: CSRF})
   .done(res => {

      updateReviewCount(res);

      $icon.removeClass("-loading").addClass('i-unlocked');
      $card.removeClass("-locked -unlockable");
      $card.addClass("-unlocked");
      $card.find('.i-link').removeClass('-hidden');

    })
   .fail(handleAjaxFail)
   .always(res => console.log(res));
}

function reLockPost() {
  $.post("/kw/levellock/", {level: level, csrfmiddlewaretoken: CSRF})
   .done(res => {

      updateReviewCount(res)

      // the post succeeds almost instantly, lets see the loading icon briefly for UI feedback
      setTimeout(() => {
        $icon.removeClass("-loading").addClass("i-unlock");
        $card.removeClass("-unlocked");
        $card.addClass("-locked -unlockable");
        $card.find('.i-link').addClass('-hidden');
      }, 400);
    })
   .fail(handleAjaxFail)
   .always(res => console.log(res));
}

function updateReviewCount(responseString) {
  let changed = parseInt(responseString.match(/^\d+/), 10);
  let newCount = Number.isNaN(reviews) ? changed : reviews += changed;

  $reviewCount.text(newCount < 0 ? 0 : newCount);
}

function handleAjaxFail(res) {
  window.alert('Something went wrong - please submit a bug report via contact form');
}


const api = {
  init: init
};

export default api;
