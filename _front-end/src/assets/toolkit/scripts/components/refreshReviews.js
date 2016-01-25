import pluralize from '../util/pluralize.js';

let $navCount,
    $buttonCount,
    storageCount,
    recentlyRefreshed,
    sessionFinished;

function ajaxReviewCount() {
  $.get("/kw/force_srs/")
   .done(res => {
      res = parseInt(res, 10);

        $navCount.text(res)
        $navCount.closest('.nav-link');

        if ($buttonCount.length) $buttonCount.text(pluralize('Review', res)).removeClass('-disabled');

      console.log('Review count updated from server:', res)
      simpleStorage.set('recentlyRefreshed', true, {TTL: 45000}); // 45 seconds
  });

}

let refreshReviews = function({forceGet} = {forceGet: false}) {
  $navCount = $("#navReviewCount");
  $buttonCount = $("#reviewCount");
  recentlyRefreshed = simpleStorage.get('recentlyRefreshed');

  console.log(`
    recentlyRefreshed: ${recentlyRefreshed},
    forceGet: ${forceGet}`
  );

  if (!recentlyRefreshed || forceGet) ajaxReviewCount();
}

export default refreshReviews;
