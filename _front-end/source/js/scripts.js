// Vendor
//@prepros-prepend vendor/jquery-1.11.1.js
//@prepros-prepend vendor/bootstrap.js
//@prepros-prepend vendor/notify.js

// Components
//@prepros-prepend helpers/helpers.js
//@prepros-prepend components/utilities.js
//@prepros-prepend components/levels.js
//@prepros-prepend components/vocab.js
//@prepros-prepend components/review.js


KaniWani.init = function() {
  KaniWani.Levels.init();
};

$(document).ready(KaniWani.init);