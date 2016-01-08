let $refreshButton,
		$reviewCount;

function init() {
	$refreshButton = $("#forceSrs");
	$reviewCount = $("#reviewCount");

	// are we on home page?
	if ($refreshButton.length) {
		$refreshButton.click(refreshReviews);
		$(document).keypress(handleKeyPress);
	}
}

function pluralizeReviews(num) {
	return num + (num > 1 ? " Reviews" : " Review");
}

function refreshReviews() {
	let sessionVocab = (simpleStorage.get('sessionVocab') || []).length;
	if (sessionVocab > 0) {
		return $reviewCount.html(pluralizeReviews(sessionVocab));
	}

	$.get("/kw/force_srs/")
	 .done(function(data) {
	 		data = parseInt(data);
			if (data > 0) {
				$reviewCount.html(pluralizeReviews(data)).removeClass("-disabled");
			}
	});
}

// shortcut to section based on R/S/U/H/C
function handleKeyPress(key) {
	let k = key.which;
	switch(true) {
		case (k == 82 || k == 114): // R
 		  window.location.href = "/kw/review/";
			break;
		case (k == 83 || k == 115): // S
			$refreshButton.click();
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

const api = {
	init: init
}

export default api;
