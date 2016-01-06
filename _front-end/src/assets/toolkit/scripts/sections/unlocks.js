import $ from 'jquery';

// TODO: refactor like vocab.js both click functions are almost identical
// TODO: change click target to not include i-link / level vocab link currently blocked/hijacked

const api = {

  init() {
    const CSRF_TOKEN = $('#csrf').val();
    let $levels = $('.level-list');

    if($levels.length > 0) {

      // TODO: listen for clicks on the two different lock icons
      // this implementation blocks link clicks to view level vocab
      $('body').on("click", ".level-card.-unlockable", function(event) {
        event.preventDefault();

        // cache el in init
        let $reviewCount = $('.nav-link > .text > .count')

        let $card = $(this),
            $icon = $card.find(".icon:not(.i-link)"),
            level = $card.data("level-id"),
            reviews = parseInt($reviewCount.text(), 10);

        $icon.removeClass("i-unlock").addClass('-loading');

        $.post("/kw/levelunlock/", {"level": level, csrfmiddlewaretoken: CSRF_TOKEN})
         .done(data => {
            let changed = +data.match(/^\d+/);
            let newCount = Number.isNaN(reviews) ? changed : reviews += changed;

            console.log(reviews, changed);

            $reviewCount.text(newCount < 0 ? 0 : newCount);

            $icon.removeClass("-loading").addClass("i-unlocked");
            $card.removeClass("-locked -unlockable");
		        $card.addClass("-unlocked");
            $card.find('.i-link').removeClass('-hidden');
          })
         .always(res => console.log(res));

      });

		$('body').on("click", ".level-card.-unlocked", function(event) {
		    event.preventDefault();

        // cache el in init
        let $reviewCount = $('.nav-link > .text > .count')

        let $card = $(this),
            $icon = $card.find(".icon:not(.i-link)"),
            level = $card.data("level-id"),
            reviews = parseInt($reviewCount.text(), 10);

        $icon.removeClass("i-unlocked").addClass('-loading');

        $.post("/kw/levellock/", {"level": level, csrfmiddlewaretoken: CSRF_TOKEN})
         .done(data => {
            let changed = +data.match(/^\d+/);
            let newCount = reviews - changed;

            console.log(reviews, changed);

            $reviewCount.text(newCount < 0 ? 0 : newCount);

            // suceeds almost instantly, lets see the loading icon briefly for UI feedback
            setTimeout(() => {
              $icon.removeClass("-loading").addClass("i-unlock");
              $card.removeClass("-unlocked");
              $card.addClass("-locked -unlockable");
              $card.find('.i-link').addClass('-hidden');
            }, 400);
          })
         .always(res => console.log(res));
      });
    }
  }

};


export default api;
