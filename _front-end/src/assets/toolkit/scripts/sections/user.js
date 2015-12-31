import $ from 'jquery';

const api = {

    init() {
        var $refresh = $("#forceSrs");

        if ($refresh.length > 0) {

            $refresh.click(function() {
                $.get("/kw/force_srs/").done(function(data) {
                    if (parseInt(data) > 0) {
                        $("#reviewCount").html(data + (parseInt(data) > 1 ? " Reviews" : " Review"));
                        $("#reviewCount").removeClass("-disabled");
                    }
                });
            });

            // start with a refresh on load
            // though maybe not because too many api calls?
            // I feel everyone is going to click this out of habit regardless
            // $refresh.click();


            //Binding R/S/H/U/C to refresh/start reviews/about/unlocks/contact
            $(document).keypress(function(e) {
                if (e.which == 83 || e.which == 115) {
                    window.location.href = "/kw/review/"
                } else if (e.which == 82 || e.which == 114) {
                    //as it needs a custom handler.
                    $refresh.click();
                } else if (e.which == 72 || e.which == 104) {
                    window.location.href = "/kw/about/"
                } else if (e.which == 85 || e.which == 117) {
                    window.location.href = "/kw/unlocks/"
                } else if (e.which == 67 || e.which == 99) {
                    window.location.href = "/kw/contact/"
                }

            });
        }
    }

}

export default api;
