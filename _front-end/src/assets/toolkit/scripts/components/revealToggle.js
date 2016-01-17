// TODO: export hide, show, toggle etc for reviews.js to access
// TODO: max-height inline by measuring inner-height of content
// TODO: replace expand-toggle with this
// might need opacity / overflow:hidden involved in the css

const api = {
  init() {
    $('.revealToggle').click(function(ev) {
      ev.preventDefault();
      if (!$(this).hasClass('-disabled')) {
        $(this).siblings('.revealTarget').toggleClass('-hidden');
      }
    });
  }
}

export default api;
