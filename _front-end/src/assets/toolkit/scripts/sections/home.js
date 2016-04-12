import refreshReviews from '../components/refreshReviews';
import pluralize from '../util/pluralize';
import strToBoolean from '../util/strToBoolean';
import timeago from '../vendor/timeago';

// overriding settings by merging objects
Object.assign($.timeago.settings, {
	allowFuture: true,
	allowPast: false,
});
Object.assign($.timeago.settings.strings, {
  prefixFromNow: '~',
  suffixFromNow: "",
	minute: 'a minute',
	hour: 'an hour',
	hours: '%d hours',
	month: 'a month',
	year: 'a year',
})

let KW;

function init() {
	// let's update storage KW with any template provided changes
	KW = Object.assign(simpleStorage.get('KW') || {}, window.KW);
	KW.settings = strToBoolean(KW.settings);
	KW.nextReview = new Date(Math.ceil(+KW.nextReview));
	simpleStorage.set('KW', KW);

	// are we on home page?
	if (window.location.pathname === '/kw/') {
		let $refreshButton = $("#forceSrs");
		let $reviewButton = $("#reviewCount");

/*
    let recentlySynced = simpleStorage.get('recentlySynced');
		if (recentlySynced !== true) syncUser();
*/

    if (true /* !KW.messages.length */) {
      animateSync();
    }

		if (!KW.settings.onVacation) {
			updateReviewTime($reviewButton);
			KW.reviewTimer = setInterval(() => updateReviewTime($reviewButton), 20000 /* 20s */);
		}

		// event handlers
		$refreshButton.click(() => refreshReviews());
		$reviewButton.click(ev => {
			if ($reviewButton.hasClass('-disabled')) ev.preventDefault();
		});

		$(document).keypress(handleKeyPress);
	}
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
function syncUser() {
	animateSync();

	$.getJSON('/kw/sync/', {full_sync: false})
		.done(res => {
			const message = `Account synced with Wanikani!`,
					  newMaterial = `</br>You have unlocked ${pluralize('new vocab item', res.new_review_count)} & ${pluralize('new synonym', res.new_synonym_count)}.`;

 			// expire after 12 hours
 			simpleStorage.set('recentlySynced', res.profile_sync_succeeded, {TTL: 43200000});
 			notie.alert(1, (newMaterial ? message + newMaterial : message), 5);
		})
		.fail((res) => {
			notie.alert(3, `Something went wrong while trying to sync with Wanikani. If the problem persists, send us a <a href="/contact/">contact message</a>! with the following: <q class="failresponse">${res.status}: ${res.statusText}</q>`, 10);
		})
		.always(() => animateSync({clear: true}));
}*/


function animateSync() {
	const $logo = document.querySelector('.site-logo');
  $logo.classList.add('-is-animating')
	const [blue, purple, pink, tan] = [
		'hsl(217, 63%, 57%)',
		'hsl(282, 100%, 47%)',
		'hsl(314, 100%, 50%)',
		'hsl(37, 67%, 65%)'
	];
	const palette = [ blue, purple, pink, tan ]
	let paletteIndex = 0;

  setInterval( function() {
    $logo.style.color = palette[paletteIndex];
    paletteIndex += 1;
    paletteIndex %= palette.length;
	}, 1100 );
}

const api = {
	init,
}

export default api;
