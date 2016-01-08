let $refreshButton,
		$reviewCount;

function init() {
	$refreshButton = $("#forceSrs");
	$reviewCount = $("#reviewCount");

	if ($refreshButton.length) {

		// event handlers
		$refreshButton.click(refreshReviews);
		$(document).keypress(handleKeyPress);

	}
}

function refreshReviews() {
	let $icon = $refreshButton.find('span[class^="i-"]');
	$icon.removeClass('i-refresh').addClass('-loading');

	// TODO: update localStorage instead, then update reviewCount from storage (both in button as well as nav)
	$.get("/kw/force_srs/")
	 .done(function(data) {
	 		data = parseInt(data, 10);
			if (data > 0) {
				$reviewCount.html(data + (data > 1 ? " Reviews" : " Review"))
										.removeClass("-disabled");
			}
			$icon.removeClass('-loading').addClass('i-refresh');
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
