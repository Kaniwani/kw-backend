import $ from 'jquery';

const api = {

  init() {
    $(".login-form .button.-submit").click(function(event){
      $(this).val('Signing in...');
      // give user impression of things happening
      setTimeout(() => $(this).closest('.container').addClass('-pending'), 750);
    });
  }

};

export default api;
