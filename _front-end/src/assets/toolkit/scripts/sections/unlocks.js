import $ from 'jquery';

const api = {

  init() {
    const CSRF_TOKEN = $('#csrf').val();
    let $levels = $('.level-list');

    if($levels.length > 0) {

      $('body').on("click", ".level-card.-unlockable", function(event) {
        event.preventDefault();

        let $card = $(this);
        let $icon = $card.find(".fa-unlock-alt");
        let level = $card.data("level-id");

        $icon.removeClass("fa-unlock-alt").addClass('-loading');

        $.post("/kw/levelunlock/", {"level": level, csrfmiddlewaretoken: CSRF_TOKEN})
         .done(data => {
            $icon.removeClass("-loading").addClass("fa-unlock");
            $card.removeClass("-locked -unlockable");
          })
         .always(res => console.log(res));

      });
    }
  }

};

export default api;
