import pluralize from '../util/pluralize';
import kwlog from '../util/kwlog';
var Favico = require('../vendor/favico');

let $navCount;
let $buttonCount;
let recentlyRefreshed;
let favicon = new Favico({
  animation: 'pop',
  position: 'down',
  bgColor: '#8523E7', // $purple-light
});


function ajaxReviewCount() {
  $.get('/kw/force_srs/')
  .done(res => {
    const count = parseInt(res, 10);
    $navCount.text('');

    if (count > 0) {
      $navCount.text(count);
      favicon.badge(count);

      if ($buttonCount.length) {
        $buttonCount.text(pluralize('Review', count)).removeClass('-disabled');
      }
    }

    kwlog('Review count updated from server:', count);
    // 19s throttle (updateReviewTime on 20s loop)
    simpleStorage.set('recentlyRefreshed', true, { TTL: 19000 });
  });
}

function refreshReviews({ forceGet } = { forceGet: false }) {
  $navCount = $('#navReviewCount');
  $buttonCount = $('#reviewCount');
  recentlyRefreshed = simpleStorage.get('recentlyRefreshed');

  const faviconCount = +$('#navReviewCount').text();
  if (faviconCount > 0) favicon.badge(faviconCount);

  kwlog(`
    --- refreshReviews ---
    recentlyRefreshed: ${recentlyRefreshed}, forceGet: ${forceGet}
    Are we hitting server? ${!recentlyRefreshed || forceGet ? 'yes' : 'no'}
    `
  );

  if (!recentlyRefreshed || forceGet) ajaxReviewCount();
}

export default refreshReviews;
