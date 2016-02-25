import '../vendor/jquery.debouncedresize';

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

function init2() {
  if ($('.accordion-list').length) {

    let accH;

    const skipClickDelay = (e) => {
      e.preventDefault();
      e.target.click();
    };

    const setAriaAttr = ($el, ariaType, newProperty) => $el.attr(ariaType, newProperty);

    const setAccordionAria = ($el1, $el2, expanded) => {
      if (expanded) {
        setAriaAttr($el1, 'aria-expanded', 'true');
        setAriaAttr($el2, 'aria-hidden', 'false');
      } else {
        setAriaAttr($el1, 'aria-expanded', 'false');
        setAriaAttr($el2, 'aria-hidden', 'true');
      }
    };

    function resizeAccordion(e) {
      $('.accordion-title').each(function(i, $title) {
        if ($title.hasClass('-is-expanded')) {
          let $content = $title.closest('dt').next();
          let accH = $content.outerHeight();
          $content.css('max-height', accH);
        }
      });
    }

    function switchAccordion(e) {
      e.preventDefault();

      let $title = $(this).closest('.accordionTrigger');
      let $content = $title.closest('dt').next();

      $content.hasClass('is-collapsed') ?
        setAccordionAria($title, $content, 'true') :
        setAccordionAria($title, $content, 'false');

      $title.toggleClass('is-expanded');
      $content.toggleClass('is-collapsed');

      let hash = $title.attr('href');
      setTimeout(() => {
        smoothScroll.animateScroll(hash, null, {offset: 50, speed: 1000 });
      }, 300)
      // accH = $title.hasClass('is-expanded') ? $content.outerHeight() : 0;

      // $content.css('max-height', accH);
      // $content.toggleClass('animateIn');
    }

    $('.accordionTrigger').click('.accordionTrigger', switchAccordion);
    // $(window).on('debouncedresize', resizeAccordion);
  }
}

const api = {
  init: init2,
}

export default api;
