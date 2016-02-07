import pluralize from '../util/pluralize.js';

let $navCount,
    $buttonCount,
    recentlyRefreshed;

function ajaxReviewCount() {
  $.get("/kw/force_srs/")
   .done(res => {
      res = parseInt(res, 10);
      $navCount.text('');

      if (res > 0) {
        $navCount.text(res)
        if ($buttonCount.length) $buttonCount.text(pluralize('Review', res)).removeClass('-disabled');
      }

      console.log('Review count updated from server:', res)
      simpleStorage.set('recentlyRefreshed', true, {TTL: 30000}); // 30 seconds
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
