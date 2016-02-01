// this is used in the NAV MENU
// something similar is being called in vocab.js
// should extract that to here for re-use in other areas

const api = {
  init() {
    $('.expandToggle').click((ev) => {
      ev.preventDefault();
      $(ev.target).siblings('.toggleTarget').toggleClass('-open');
    });
  }
}

export default api;
