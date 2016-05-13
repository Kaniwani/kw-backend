import config from '../config';
import refreshReviews from '../components/refreshReviews';
import pluralize from '../util/pluralize';
import strToBoolean from '../util/strToBoolean';
import timeago from '../vendor/timeago';
<<<<<<< HEAD
import toastr from '../vendor/toastr';
import im from '../vendor/include-media';
=======
import okayNav from '../vendor/jquery.okayNav';
const sitenav = $('#nav-main').okayNav();
>>>>>>> dev

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

<<<<<<< HEAD
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
=======
function syncUser() {
	animateSync();

	$.getJSON('/kw/sync/', {full_sync: false})
		.done(res => {
			const message = `Account synced with Wanikani!`,
					  newMaterial = `</br>You have unlocked ${pluralize('new vocab item', res.new_review_count)} & ${pluralize('new synonym', res.new_synonym_count)}.`;

 			// expire after 6 hours
 			simpleStorage.set('recentlySynced', res.profile_sync_succeeded, {TTL: 21600000});
 			notie.alert(1, (newMaterial ? message + newMaterial : message), 5);
		})
		.fail((res) => {
			notie.alert(3, `Something went wrong while trying to sync with Wanikani. If the problem persists, send us a <a href="/contact/">contact message</a>! with the following: <q class="failresponse">${res.status}: ${res.statusText}</q>`, 10);
		})
		.always(() => animateSync({clear: true}));
}

// shortcut to section based on R/S/U/H/C
function handleKeyPress(key) {
	let k = key.which;
	switch(true) {
		case (k == 82 || k == 114): // R
 		  window.location.href = "/kw/review/";
			break;
		case (k == 83 || k == 115): // S
			refreshReviews();
			break;
		case (k == 85 || k == 117): // U
			window.location.href = "/kw/unlocks/";
			break;
		case (k == 72 || k == 104): // H
			window.location.href = "/kw/about/";
			break;
		case (k == 67 || k == 99): // C
			window.location.href = "/contact/";
			break;
	}
}

function animateSync({clear = false} = {}) {
	let $site = $('.site'),
			$loader = $('.sync-loader');

	if (clear) {
		$site.removeClass('-syncing');
		$loader.removeClass('-syncing');
		return;
	} else {
		$site.addClass('-syncing');
		$loader.addClass('-syncing');
	}

	const container = $loader.find('.title').get(0);
	const [blue, purple, pink, tan] = [
		'hsl(217, 63%, 57%)',
		'hsl(282, 100%, 47%)',
		'hsl(314, 100%, 50%)',
		'hsl(37, 67%, 65%)'
	];
	const palette = [ blue, purple, pink, tan]
	let paletteIndex = 0;

	setInterval( function() {

	  // Debounce change to allow for css changes
	  setTimeout( function() {
	    container.style.color = palette[paletteIndex];
	    paletteIndex += 1;
	    paletteIndex %= palette.length;
	  }, 10 );

	}, 1600 );
}
>>>>>>> dev

const api = {
	init,
}

export default api;
