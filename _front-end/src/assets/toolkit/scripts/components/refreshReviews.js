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
      simpleStorage.set('recentlyRefreshed', true, {TTL: 19000}); // 19s throttle (updateReviewTime on 20s loop)
  });
}

let refreshReviews = function({forceGet} = {forceGet: false}) {
  $navCount = $("#navReviewCount");
  $buttonCount = $("#reviewCount");
  recentlyRefreshed = simpleStorage.get('recentlyRefreshed');

  console.log(`
    --- Refresh reviews attempted to be called ---
    recentlyRefreshed: ${recentlyRefreshed}, forceGet: ${forceGet}
    Are we hitting server? ${!recentlyRefreshed || forceGet ? 'yes' : 'no'}
    `
  );

  if (!recentlyRefreshed || forceGet) ajaxReviewCount();
}

export default refreshReviews;
