import $ from 'jquery';

// TODO: export hide, show, toggle etc for reviews.js to access

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
