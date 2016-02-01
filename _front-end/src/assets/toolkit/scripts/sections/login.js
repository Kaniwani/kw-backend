function init() {
  $(".login-form .button.-submit").click(function(ev){
    $(this).val('Signing in...');
    // login animation
    setTimeout(() => {
      $(this).closest('.login-section').addClass('-pending');
    }, 600);
  });
}

const api = {
  init: init
};

export default api;
