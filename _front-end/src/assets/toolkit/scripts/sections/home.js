import config from '../config';
import refreshReviews from '../components/refreshReviews';
import pluralize from '../util/pluralize';
import strToBoolean from '../util/strToBoolean';
import timeago from '../vendor/timeago';
import toastr from '../vendor/toastr';
import im from '../vendor/include-media';

// vendor js configuration
Object.assign($.timeago.settings, config.timeago.settings);
Object.assign($.timeago.settings.strings, config.timeago.strings)
if (im.lessThan('sm')) config.toastr.positionClass = 'toast-top-full-width';
toastr.options = config.toastr;

let KW;

function init() {
	// let's update storage KW with any template provided changes
	KW = Object.assign(simpleStorage.get('KW') || {}, window.KW);
	KW.settings = strToBoolean(KW.settings);
	KW.nextReview = new Date(Math.ceil(+KW.nextReview));
	simpleStorage.set('KW', KW);

  console.log(KW.user.lastWKSyncDate);
  console.table(window.KW.messages);
  displayMessages();

	// are we on home page?
	if (window.location.pathname === '/kw/') {
		let $refreshButton = $("#forceSrs");
		let $reviewButton = $("#reviewCount");

		if (!KW.settings.onVacation) {
			updateReviewTime($reviewButton);
			KW.reviewTimer = setInterval(() => updateReviewTime($reviewButton), 10000 /* 10s */);
		}

		// event handlers
		$refreshButton.click(() => refreshReviews());
		$reviewButton.click(ev => {
			if ($reviewButton.hasClass('-disabled')) ev.preventDefault();
		});
	}
}

function displayMessages() {
  KW.messages.forEach(({text, level}) => toastr[level](text));
}

function updateReviewTime($el) {
	let now = Date.now(),
			next = Date.parse(KW.nextReview)

	if (now > next) {
		refreshReviews();
		clearInterval(KW.reviewTimer);
	} else {
		$el.text(`Next review: ${$.timeago(KW.nextReview)}`);
	}
}

/*
function animateSync() {
	const $logo = document.querySelector('.site-logo');
  const $logotext = Array.from($logo.children).reduce((_, el) => {
    return el.classList.contains('text') ? el : null;
  });

  const [blue, purple, pink, tan] = [
    'hsl(217, 63%, 57%)',
    'hsl(282, 100%, 47%)',
    'hsl(314, 100%, 50%)',
    'hsl(27, 67%, 65%)'
  ];
  const palette = [ blue, purple, pink, tan ]
  let paletteIndex = 0;

  $logo.classList.add('is-animating');

  setInterval(function() {
    $logotext.style.backgroundColor = palette[paletteIndex];
    paletteIndex += 1;
    paletteIndex %= palette.length;
	}, 2900 );
}*/

const api = {
	init,
}

export default api;
