import refreshReviews from '../components/refreshReviews';
import pluralize from '../util/pluralize';

let recentlySynced,
		$refreshButton,
		$reviewButton;

function init() {
	// are we on home page?
	if (window.location.pathname === '/kw/') {
		$refreshButton = $("#forceSrs");
		$reviewButton = $("#reviewCount");
		recentlySynced = simpleStorage.get('recentlySynced');

		if (recentlySynced !== true) {
			syncUser();
		} else {
			refreshReviews();
		}

		// event handlers
		$refreshButton.click(() => refreshReviews());
		$reviewButton.click(ev => {
			if ($reviewButton.hasClass('-disabled')) ev.preventDefault();
		});

		$(document).keypress(handleKeyPress);

		// TODO: we should also load settings if we want to prevent syncing for unfollow users
		// settings should still be loaded in reviews in case user goes there directly after changing settings though
		// unless we decided to blanket update user, settings etc on every important page via logged_in template
		// that might be a better avenue to be honest
		let user = simpleStorage.get('user');
		if (user == null) simpleStorage.set('user', window.KWuserName);
	}
}

function syncUser() {
	animateSync();

	$.getJSON('/kw/sync/', {full_sync: false})
		.done(res => {
			const message = `Account synced with Wanikani!`,
					  newMaterial = `</br>You have unlocked ${pluralize('new vocab item', res.new_review_count)} & ${pluralize('new synonym', res.new_synonym_count)}.`;

 			simpleStorage.set('recentlySynced', res.profile_sync_succeeded, {TTL: 1800000}) // expire after 30mins
 			notie.alert(1, (newMaterial ? message + newMaterial : message), 5);
 			refreshReviews();
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

const api = {
	init,
	animateSync,
	syncUser,
}

export default api;
