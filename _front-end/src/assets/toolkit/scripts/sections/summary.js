import refreshReviews from '../components/refreshReviews';

let init = function() {
	// are we on summary page? clear reviews count because server doesn't update in header =/
	if (/summary/.test(window.location.pathname)) {
    // NOTE: turned off for early termination testing
    // $("#navReviewCount").text('');
	}
}

const api = {
	init,
};

export default api;
