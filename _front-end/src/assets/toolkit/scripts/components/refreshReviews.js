let $navCount,
    $buttonCount,
    storageCount,
    recentlyRefreshed,
    sessionFinished;

function pluralize(text, num) {
  return num + text + (num > 1 ? "s" : "");
}

function ajaxReviewCount() {
  $.get("/kw/force_srs/")
   .done(res => {
      res = parseInt(res, 10);

      if (sessionFinished) {
        $navCount.text('');
      }

      if (res > 0) {
        simpleStorage.set('reviewCount', res);
        $navCount.text(res)
        $navCount.closest('.nav-link').removeClass('-disabled');

        if ($buttonCount.length) $buttonCount.text(pluralize(' Review', res)).removeClass('-disabled');
      }

      console.log('Review count updated from server:', res)
      simpleStorage.set('recentlyRefreshed', true, {TTL: 5000});
      simpleStorage.set('reviewCount', res);
  });

}

function storageReviewCount() {
  if (storageCount > 0) {
    $navCount.text(storageCount);
    $navCount.closest('.nav-link').removeClass('-disabled');
    // if on home page update the reviews button too
    if ($buttonCount.length) {
      $buttonCount.text(pluralize(' Review', storageCount)).removeClass('-disabled');
    }
  }

  console.log('Review count updated from local storage:', storageCount)
}

let refreshReviews = function({forceGet} = {forceGet: false}) {
  $navCount = $("#navReviewCount");
  $buttonCount = $("#reviewCount");
  storageCount = simpleStorage.get('reviewCount') || 0;
  sessionFinished = simpleStorage.get('sessionFinished');
  recentlyRefreshed = simpleStorage.get('recentlyRefreshed');
  console.log(!recentlyRefreshed, forceGet, sessionFinished, storageCount < 1)

  if (!recentlyRefreshed || sessionFinished && storageCount < 1 && forceGet) {
    ajaxReviewCount();
  } else {
    storageReviewCount();
  }
}

export default refreshReviews;
