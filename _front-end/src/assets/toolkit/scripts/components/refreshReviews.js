let $navCount,
    $buttonCount,
    storageCount;

function pluralize(text, num) {
  return num + text + (num > 1 ? "s" : "");
}

function ajaxReviewCount() {
  $.get("/kw/force_srs/")
   .done(res => {
      res = parseInt(res, 10);

      if (res > 0) {
        simpleStorage.set('reviewCount', res);
        $navCount.text(res);
        if ($buttonCount.length) $buttonCount.text(pluralize(' Review', res)).removeClass('-disabled');
      }

      console.log('Review count updated from server:', res)
  });
}

function storageReviewCount() {
  $navCount.text(storageCount);
  // if on home page update the reviews button too
  if ($buttonCount.length) {
    $buttonCount.text(pluralize(' Review', storageCount)).removeClass('.-disabled');
  }

  console.log('Review count updated from local storage:', storageCount)
}

const refreshReviews = function({forceGet} = {forceGet: false}) {
  $navCount = $("#navReviewCount");
  $buttonCount = $("#reviewCount");
  storageCount = simpleStorage.get('reviewCount') || 0;

  if (forceGet == true || storageCount < 1) {
    ajaxReviewCount();
  } else {
    storageReviewCount();
  }
}

export default refreshReviews;
