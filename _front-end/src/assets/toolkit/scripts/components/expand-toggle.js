import $ from 'jquery';

const api = {
  init() {
    $('.expandToggle').each((_,toggle) => {
      const $toggle = $(toggle);

      $toggle.click((ev) => {
        console.log($toggle, $toggle.siblings('.toggleTarget'));
        ev.preventDefault();
        $toggle.siblings('.toggleTarget').toggleClass('-open');
      });
    });
  }
}

export default api;
