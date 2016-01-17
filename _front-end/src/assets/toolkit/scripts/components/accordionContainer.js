// adds $(el).on('debouncedresize') event for listening
import debouncedResize from '../vendor/jquery.debouncedResize';
// scrolls to $.scrollto($el)
import scrollTo from '../vendor/jquery.scrollTo';

function init() {
  if ($('.accordion-container').length) {

    $('.-toggle').on('click', function(e) {
      e.preventDefault();

      let $acc = $(this).closest('.accordion-container'),
        $wrap = $acc.find('.wrap'),
        $content = $acc.find('.content'),
        accH = 0;

      $acc.toggleClass('-open');

      if ($acc.hasClass('-open')) {
        accH = $content.outerHeight();
        $.scrollTo($acc, 300);
      } else {
        accH = 0;
      }

      $wrap.css('max-height', accH);
    });

    $(window).on('debouncedresize', function (e) {
      $.each($('.accordion-container'), function (i, $acc) {
        if ($(this).hasClass('-open')) {
          let accH = $(this).find('.content').outerHeight();
          $(this).find('.wrap').css('max-height', accH);
        }
      });
    });

  }
};

const api = {
  init: init
}

export default api;
