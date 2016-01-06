import $ from 'jquery';

const api = {

  init() {
    $(".login-form .button.-submit").click(function(event){
      $(this).val('Signing in...');
      // login animation
      setTimeout(() => $(this).closest('.container').addClass('-pending'), 750);
    });
  }

};

export default api;
