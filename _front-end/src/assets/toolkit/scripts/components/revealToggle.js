// TODO: export hide, show, toggle etc for reviews.js to access
// TODO: max-height inline by measuring inner-height of content
// might need opacity / overflow:hidden involved in the css

const revealToggle = ($el) => {
  $el.siblings('.revealTarget').toggleClass('-hidden');
};

const init = () => {
  $('.revealToggle').click(function(ev) {
    ev.preventDefault();
    let $this = $(this);
    if (!$this.hasClass('-disabled')) revealToggle($this);
  });
};

const api = {
  init,
  revealToggle,
}

export default api;
