import refreshReviews from '../components/refreshReviews';

let prevSync,
		$refreshButton,
		$reviewButton;

function init() {
	// are we on home page?
	if (window.location.pathname === '/kw/') {
		$refreshButton = $("#forceSrs");
		$reviewButton = $("#reviewCount");
		prevSync = simpleStorage.get('prevSync');
		console.log('prevSync?', prevSync);
		if (prevSync !== true) syncUser();

		// event handlers
		$refreshButton.click(() => refreshReviews({forceGet: true}));
		$reviewButton.click(ev => {
			if ($reviewButton.hasClass('-disabled')) ev.preventDefault();
		});
		$(document).keypress(handleKeyPress);
	}

	// update from sessionstorage, if nothing there then hit server
	refreshReviews();
}


function syncUser() {
	animateSync();

	// FIXME: @tadgh I'm not getting any json responses, I think I'm getting redirected to /kw/ if I try
	// getJSON no proper response, post fails.
	// maybe I don't have my local server setup correctly and this works fine on live?
	$.getJSON('/kw/sync/')
		.done(res => {
			const message = `Account synced with Wanikani!`,
					  newMaterial = `</br>You have ${res.new_review_count} new reviews & ${res.new_synonym_count} new synonyms.`;

			console.log(res);

 			simpleStorage.set('prevSync', res.profile_sync_succeeded, {TTL: 180000}) // expire after 30mins
 			notie.alert(1, (newMaterial ? message + newMaterial : message), 5);
		})
		.fail(() => {
			notie.alert(3, 'Something went wrong while trying to sync with Wanikani. If the problem persists, send us a <a href="/contact/">contact message</a>!', 10);
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

	}, 2000 );
}

const api = {
	init,
	animateSync,
}

export default api;
