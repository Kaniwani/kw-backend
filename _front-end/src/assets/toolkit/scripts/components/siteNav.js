function init() {
  const $mobileMenu = $('#js-mobilemenu');
  const $menuButton = $('#js-mobilemenu-toggle');

  $menuButton.click(function() {
    $mobileMenu.toggleClass('js-mobilemenu-open');
    $menuButton.toggleClass('-active');
  });

}

const api = {
  init,
}

export default api;
