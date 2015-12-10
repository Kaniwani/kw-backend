import $ from 'jquery';

const api = {
  init() {
    $(document).ready(function() {
      $(".login-form > .button.-submit").click(function(event){
        console.log(event.target, 'clicked')
        event.preventDefault();

        $('.login-form').fadeOut(500);
        $('.login > .container').addClass('-pending');
        setTimeout(() => $('login-form').submit(), 600);
      });
    });
  }
};

export default api;
