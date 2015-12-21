import $ from 'jquery';

const api = {
  init() {
    $('.expandToggle').click((ev) => {
      ev.preventDefault();
      $(ev.target).siblings('.toggleTarget').toggleClass('-open');
    });
  }
}

export default api;
