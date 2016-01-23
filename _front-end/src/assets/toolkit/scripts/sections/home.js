import refreshReviews from '../components/refreshReviews';

let $refreshButton,
		$reviewButton;

function init() {
	$refreshButton = $("#forceSrs");
	$reviewButton = $("#reviewCount");

	// are we on home page?
	if ($refreshButton.length) {
		// event handlers
		$refreshButton.click(() => refreshReviews({forceGet: true}) );
		$reviewButton.click(ev => {
			if ($reviewButton.hasClass('-disabled')) ev.preventDefault();
		});
		$(document).keypress(handleKeyPress);
	}

	// update from sessionstorage, if nothing there then hit server
	refreshReviews();
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
			window.location.href = "/kw/contact/";
			break;
	}
}

function animateSyncing() {
	$('.site').addClass('_blurry');
	const container = $('.sync-loader .title').get(0);
	const [green, blue, purple, pink] = [
		'hsl(107, 56%, 62%)',
		'hsl(217, 63%, 57%)',
		'hsl(282, 100%, 47%)',
		'hsl(314, 100%, 50%)'
	];
	const palette = [ blue, green, purple, pink]
	let paletteIndex = 0;

	setInterval( function() {

	  // Debounce change to allow for css changes
	  setTimeout( function() {
	    container.style.color = palette[paletteIndex];
	    container.className = 'title -animating';
	    paletteIndex += 1;
	    paletteIndex %= palette.length;
	  }, 10 );

	}, 2500 );
}

const api = {
	init,
	animateSyncing,
}

export default api;
