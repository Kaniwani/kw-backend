import '../vendor/jquery.debouncedresize';

function init() {
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
      $('.accordion-title').each(function(i, title) {
        let $title = $(title);
        if ($title.hasClass('is-expanded')) {
          let $content = $title.closest('dt').next();
          let accH = $content.find('.content-inner').outerHeight();
          $content.css('max-height', accH);
        }
      });
    }

    function switchAccordion(e) {
      e.preventDefault();

      let $title = $(this).closest('.accordionTrigger');
      let $content = $title.closest('dt').next();
      let $inner = $content.find('.content-inner');

      $content.hasClass('is-collapsed') ?
        setAccordionAria($title, $content, 'true') :
        setAccordionAria($title, $content, 'false');

      $title.toggleClass('is-expanded');
      $content.toggleClass('is-collapsed');

      let hash = $title.attr('href');
      accH = $title.hasClass('is-expanded') ? $inner.outerHeight() : 0;

      $content.toggleClass('animateIn');
      $content.toggleClass('animateOut');
      $content.css('max-height', accH);
    }

    $('.accordionTrigger').click('.accordionTrigger', switchAccordion);
    $(window).on('debouncedresize', resizeAccordion);
  }
}

const api = {
  init: init,
}

export default api;
