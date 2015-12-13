import $ from 'jquery';

const api = {
  init() {
    $(".login-form > .button.-submit").click(function(event){
      event.preventDefault();

      $('.login-form').fadeOut(500);
      $('.login > .container').addClass('-pending');
      setTimeout(() => $('login-form').submit(), 600);
    });
  }
};

export default api;
